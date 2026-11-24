"""Drive the opt-in diagnostic with the C1 owned-process adapter."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time

from AnalyzeC1Isolation import evaluate

ROOT = Path(__file__).resolve().parents[2]
C1 = ROOT.parents[1]
sys.path.insert(0, str(C1/'Source/Scripts/U04'))
original_directory = Path.cwd()
try:
    os.chdir(C1/'Source')
    import C1Dedicated as adapter
    from C1ForegroundBatch import identities, inventory, snap
    from C1Run import read, sha, write
finally:
    os.chdir(original_directory)


def log_records(path, marker):
    with path.open('rb') as stream:
        while line:=stream.readline():
            if line.endswith(b'\n') and marker in line:
                offset=stream.tell()-len(line)
                yield offset,json.loads(line.split(marker,1)[1])


def capture(run, owned, owners):
    logs={role:Path(record['log']) for role,(_,record) in owned.items()}
    anchor={}
    for role, (backend, record) in owned.items():
        backend.verify_owned(record)
        anchor[role],_=adapter.fresh_state(record,0)
        if not anchor[role]:
            raise ValueError('fresh_prearm_state_missing')
    write(run/'prearm.json',anchor)
    players={pawn['id']:pawn for pawn in anchor['Server']['state']['pawns']}
    for owner in owners.values():
        pawn=players[owner['pawn']]
        vital=pawn['vital']
        if pawn['life']!=owner['life'] or vital['dead'] or vital['hp']<=0 or vital['shield']!=0:
            raise ValueError('prearm_owner_ineligible')
    watermark=max((r['serial'] for r in anchor['Server']['state']['results']),default=0)
    (run/'ready.txt').write_text(run.name,encoding='ascii')
    deadline=time.monotonic()+12
    observed=[]
    while time.monotonic()<deadline:
        for backend,_ in owned.values():
            backend.require_alive(backend.owned_handle)
        observed=list(log_records(logs['Server'],b'U04_ISOLATION '))
        if observed:
            break
        time.sleep(.20)
    if not observed:
        return dict(verdict='INVALID',reason='observer timeout or placement did not arm')
    first=observed[0][1]
    if first['source']!=owners['ClientB']['encounter']['monster']:
        raise ValueError('wrong_monster_owner')
    identity={key:first[key] for key in ('run','world','source','sourceLife','action','definition','version','sourceEncounter')}
    for role in ('A','B'):
        owner=owners['Client'+role]
        identity[role]=dict(target=owner['pawn'],targetLife=owner['life'],targetEncounter=owner['encounter']['id'])
    time.sleep(1)
    states={}
    for role, (_, record) in owned.items():
        states[role]=list(log_records(logs[role],b'U02F_STATE '))
        for _,row in states[role]:
            adapter.verify_state(record,row)
    rows=[r for _,r in observed]
    start=min(r['sliceBegin'] for r in rows if r['action']==first['action'])
    end=max(r['sliceEnd'] for r in rows if r['action']==first['action'])
    bound_before=[pair for pair in states['Server'] if pair[1]['time']<start]
    bound_after=[pair for pair in states['Server'] if pair[1]['time']>end]
    if not bound_before or not bound_after:
        raise ValueError('authority_action_interval_unbracketed')
    before,after=bound_before[-1],bound_after[0]
    receipts=[r for r in after[1]['results'] if r['serial']>watermark]
    new=[r for r in receipts if r['source']==first['source'] and r['action']==first['action']]
    def hp(row):
        by_id={p['id']:p for p in row['pawns']}
        values={}
        for role in ('A','B'):
            expected=identity[role]
            p=by_id[expected['target']]
            if p['life']!=expected['targetLife'] or p['vital']['shield']!=0 or p['vital']['dead']:
                raise ValueError('owner_life_shield_or_death')
            values[role]=p['vital']['hp']
        return values
    hp_before,hp_after=hp(before[1]),hp(after[1])
    replication={}
    for role in ('ClientA','ClientB'):
        for offset,row in states[role]:
            if new and all(r in row['results'] for r in new) and hp(row)==hp_after:
                replication[role]=offset
                break
    status,reason=evaluate(rows,identity,hp_before,hp_after,receipts,
        bool(receipts) and sorted(r['serial'] for r in receipts)==list(range(watermark+1,max(r['serial'] for r in receipts)+1)),
        len(replication)==2)
    return dict(verdict=status,reason=reason,identity=identity,observerOffsets=[o for o,_ in observed],
                authorityOffsets=[before[0],after[0]],replicationOffsets=replication,watermark=watermark,
                hpBefore=hp_before,hpAfter=hp_after,matchedReceipts=new)


def run_session(run, port, build):
    native=adapter.git('rev-parse','HEAD')
    if adapter.git('diff',build['sourceSHA'],'--','Source','Content','Config','Plugins','AnimeMMORPG.uproject') or adapter.git('status','--porcelain'):
        raise ValueError('dirty or wrong diagnostic source')
    exe,module=Path(build['engineExecutable']),Path(build['module'])
    for path,key in ((exe,'engineSHA256'),(module,'moduleSHA256'),
                     (Path(build['receipt']),'receiptSHA256')):
        if sha(path)!=build[key]:
            raise ValueError('diagnostic hash mismatch:'+key)
    adapter.check_port(port)
    editors,games=inventory()
    if games:
        raise ValueError('package active')
    preserved=snap()
    adapter.ROOT,adapter.NATIVE=ROOT,build['sourceSHA']
    run.mkdir()
    owned={}
    verdict=dict(status='INVALID',readiness={},stops={},build=build,toolSHA=native)
    try:
        for role in adapter.ROLES:
            planned=adapter.plan(run,role,port,exe,module,build)
            if role=='Server':
                planned['arguments']+=['-U04IsolationObserver',f'-U04IsolationReady={run/"ready.txt"}']
            Path(planned['userDir']).mkdir(parents=True)
            backend=adapter.Backend(input_enabled=False)
            owned[role]=(backend,planned)
            write(run/role/'command.json',planned)
            backend.launch(planned['arguments'],ROOT)
            planned.update(backend.capture_owned())
            write(run/role/'process.json',planned)
            if role=='Server':
                verdict['readiness'][role]=adapter.wait_ready(planned,backend)
            elif role=='ClientA':
                time.sleep(2)
        for role in adapter.ROLES[1:]:
            backend,planned=owned[role]
            verdict['readiness'][role]=adapter.wait_ready(planned,backend)
        server,_=adapter.fresh_state(owned['Server'][1],0)
        owners=adapter.verify_owners(server,verdict['readiness'])
        verdict['owners']=owners
        verdict['proof']=capture(run,owned,owners)
        verdict['status']=verdict['proof']['verdict']
    except Exception as exc:
        verdict['error']=str(exc)
    finally:
        for role,(backend,record) in reversed(tuple(owned.items())):
            if backend.has_owned():
                try:
                    verdict['stops'][role]=backend.stop_launched()
                except Exception as exc:
                    verdict['stops'][role]=dict(error=str(exc))
                finally:
                    backend.close_owned()
        after,games=inventory()
        verdict['preservation']=dict(workspace=preserved==snap(),editors=identities(editors)<=identities(after),noPackage=not games)
        stops=verdict['stops']
        if not all(verdict['preservation'].values()) or any(
                proof.get('wait')!='signaled' or proof.get('identityVerifiedAtStop') is not True or
                any(proof.get(k)!=owned[role][1].get(k) for k in ('pid','creationTicks','executable'))
                for role,proof in stops.items()):
            verdict['status']='INVALID'
        write(run/'final.json',verdict)
    return verdict['status']


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--id',required=True)
    parser.add_argument('--port',required=True,type=int)
    parser.add_argument('--build-number',choices=(1,2),type=int,default=1)
    args=parser.parse_args()
    if not re.fullmatch(r'C1-Isolation-[0-9]+',args.id):
        parser.error('invalid run ID')
    name='BUILD-IDENTITY.json' if args.build_number==1 else 'BUILD-IDENTITY-02.json'
    result=run_session(ROOT.parent/'Runs'/args.id,args.port,read(ROOT.parent/name))
    raise SystemExit(0 if result=='PASS' else 1)
