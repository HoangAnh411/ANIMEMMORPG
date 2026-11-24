"""Build-03 dedicated session with one retained handle and log per role."""
import argparse
import json
from pathlib import Path
import re
import socket
import subprocess
import time

from C1ForegroundBatch import git, identities, inventory, snap
from C1Identity import path_key
from C1Run import ROOT, NATIVE, read, sha, write
from C1Win32 import Backend
from C1Readiness import FileLog, Journal
from C1ProfileRun import ProfileSession
from C1FocusedProof import replicated_damage

MAP = '/Game/AnimeMMORPG/Maps/L_NetworkLab'
ROLES = ('Server', 'ClientA', 'ClientB')


def pins():
    receipt = ROOT.parent/'Runs/Build-03/BUILD-IDENTITY.json'
    build = read(receipt)
    if Path(build['clone']).resolve() != ROOT or build['sourceSHA'] != NATIVE:
        raise ValueError('wrong_clone_or_native')
    if git('diff', NATIVE, '--', 'Source', 'Content', 'Config', 'Plugins', 'AnimeMMORPG.uproject'):
        raise ValueError('native_inputs_differ')
    exe = Path(build['engineExecutable']).resolve(strict=True)
    module = (ROOT/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll').resolve(strict=True)
    for path, key in [(exe, 'engineSHA256'), (module, 'moduleSHA256')]:
        if sha(path) != build[key]:
            raise ValueError(key + '_mismatch')
    for item in build['receipts']:
        if sha(Path(item['path'])) != item['sha256']:
            raise ValueError('build_receipt_mismatch')
    return exe, module, build


def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind(('0.0.0.0', port))


def plan(run, role, port, exe, module, build):
    folder = run/role
    user, log = folder/'User', folder/'Game.log'
    project = ROOT/'AnimeMMORPG.uproject'
    server = role == 'Server'
    mode = [MAP, '-server', f'-port={port}', '-NullRHI', '-nosound'] if server else [
        f'127.0.0.1:{port}', '-game', '-windowed', '-ResX=1280', '-ResY=720',
        '-WinX=' + ('0' if role == 'ClientA' else '150'), '-WinY=100']
    cvars = 't.MaxFPS 30,t.IdleWhenNotForeground 0' if server else (
        't.MaxFPS 60,t.IdleWhenNotForeground 0,r.ScreenPercentage 50,'
        'r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,'
        'r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2')
    argv = [str(exe), str(project), *mode, '-DisablePython', '-NoLiveCoding', '-nop4', '-nosplash',
            '-U04R1InputTrace', '-U01FProbe', '-U01Trace', '-U02FProbe', '-U02Trace',
            f'-U01SourceSHA={NATIVE}', f'-U02SourceSHA={NATIVE}', f'-U02RunId={run.name}',
            f'-UserDir={user}', f'-abslog={log}', f'-ExecCmds={cvars}',
            '-ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False']
    return dict(role=role, port=port, runId=run.name, sourceSHA=NATIVE, executable=str(exe),
                module=str(module), moduleSHA256=build['moduleSHA256'], binarySHA256=build['engineSHA256'],
                project=str(project), userDir=str(user), log=str(log), arguments=argv)


def loaded_module(record):
    pid = int(record['pid'])
    paths = subprocess.check_output([
        'powershell.exe', '-NoProfile', '-Command',
        f"(Get-Process -Id {pid} -ErrorAction Stop).Modules | Where-Object ModuleName -eq 'UnrealEditor-AnimeMMORPG.dll' | ForEach-Object FileName"
    ], text=True).splitlines()
    if len(paths) != 1 or path_key(paths[0]) != path_key(record['module']) or sha(Path(paths[0])) != record['moduleSHA256']:
        raise ValueError('loaded_module_mismatch')
    return paths[0]


def fresh_state(record, offset):
    with Path(record['log']).open('rb') as stream:
        stream.seek(0, 2)
        if stream.tell() < offset:
            raise ValueError('log_truncated')
        stream.seek(offset)
        raw = stream.read()
    offset_now = offset
    if offset:
        with Path(record['log']).open('rb') as stream:
            stream.seek(offset-1)
            if stream.read(1)!=b'\n':
                cut=raw.find(b'\n')+1
                if not cut:
                    return None,offset
                raw=raw[cut:]
                offset_now+=cut
    match = None
    for line in raw.splitlines(keepends=True):
        if not line.endswith(b'\n'):
            break
        start = offset_now
        offset_now += len(line)
        if b'U02F_STATE {' not in line:
            continue
        row = json.loads(line.split(b'U02F_STATE ', 1)[1])
        verify_state(record, row)
        match = dict(offset=start, endOffset=offset_now, state=row)
    return match, offset_now


def verify_state(record, row):
    server = record['role'] == 'Server'
    for key, value in [('pid', record['pid']), ('run', record['runId']), ('sourceSHA', NATIVE),
                       ('worldType', 1), ('netMode', 1 if server else 3), ('localPlayers', 0 if server else 1)]:
        if row.get(key) != value:
            raise ValueError('state_mismatch:' + key)
    if row.get('world') != MAP + '.L_NetworkLab':
        raise ValueError('state_mismatch:world')


def wait_ready(record, backend, timeout=180):
    offset = 0
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        backend.require_alive(backend.owned_handle)
        if Path(record['log']).exists() and record['role'] == 'Server':
            # No client is connected yet. The NetDriver listen line is startup
            # evidence only. Require a fresh Game-world sample after clients join.
            with Path(record['log']).open('rb') as stream:
                for line in stream:
                    if re.search(rb'IpNetDriver listening on port ' + str(record['port']).encode() + rb'\s', line):
                        return dict(listen=line.decode().strip(), identity=backend.verify_owned(record),
                                    loadedModule=loaded_module(record))
        if Path(record['log']).exists() and record['role'] != 'Server':
            sample, offset = fresh_state(record, offset)
            if sample and (record['role'] == 'Server' or any(
                    p['local'] and p['role'] == 2 and p['owner'] != 'None' for p in sample['state']['pawns'])):
                identity = backend.verify_owned(record)
                module = loaded_module(record)
                backend.assert_record_handle(record, backend.capture_owned())
                return dict(sample=sample, identity=identity, loadedModule=module)
        time.sleep(.25)
    raise TimeoutError('ready_timeout:' + record['role'])


def verify_owners(server_sample, readiness):
    if not server_sample:
        raise ValueError('authority_game_world_missing')
    server = server_sample['state']
    players = {pawn['id']: pawn for pawn in server['pawns']}
    owners = {}
    for role in ROLES[1:]:
        state = readiness[role]['sample']['state']
        pawns = [pawn for pawn in state['pawns'] if pawn['local']]
        if len(pawns) != 1 or pawns[0]['role'] != 2:
            raise ValueError('client_local_pawn_missing:' + role)
        pawn = pawns[0]
        identity = pawn['id']
        authority = players.get(identity)
        if (not authority or authority['role'] != 3 or
                authority['owner'] == 'None' or pawn['owner'] == 'None' or
                authority['life'] != pawn['life']):
            raise ValueError('authority_owner_life_mismatch:' + role)
        matches = [e for e in server['encounters'] if e['player'] == identity and not e['closed']]
        local_matches = [e for e in state['encounters'] if e['player'] == identity and not e['closed']]
        keys = ('id', 'owner', 'player', 'monster')
        if len(matches) != 1 or len(local_matches) != 1 or any(matches[0][k] != local_matches[0][k] for k in keys):
            raise ValueError('authority_encounter_mismatch:' + role)
        owners[role] = dict(pawn=identity, life=pawn['life'], clientOwner=pawn['owner'],
                            authorityOwner=authority['owner'], encounter=matches[0])
    if (owners['ClientA']['pawn'] == owners['ClientB']['pawn'] or
            owners['ClientA']['encounter']['id'] == owners['ClientB']['encounter']['id']):
        raise ValueError('shared_client_identity')
    return owners


def capture_gameplay(run, owned, owners):
    handles = {role: (backend, record) for role,backend,record in owned}
    backend, client = handles['ClientA']

    class ClientSession(ProfileSession):
        def validate_metrics(self, metrics):
            if metrics.get('netMode')!=3 or not metrics.get('map','').endswith('/L_NetworkLab'):
                self.fail('dedicated_metrics_world')
            adapted=dict(metrics,netMode=0,map='/L_CharacterCombatLab')
            super().validate_metrics(adapted)
            target=owners['ClientA']
            if metrics['combat']['pawnId']!=target['pawn'] or metrics['combat']['life']!=target['life']:
                self.fail('dedicated_metrics_owner')

    journal=Journal(run/'gameplay-journal.jsonl',backend.now)
    try:
        session=ClientSession(dict(client,targetReady=True),backend,FileLog(client['log']),journal,
                              workload={},output=run)
        session.select()
        session.focus_once()
        metrics=session.fresh_metrics()['metrics']
        if metrics['controlState'] in (1,2):
            resume=metrics['menuButtons']['Resume']
            session.click_resume(resume['x'],resume['y'])
            session.wait(.25)
        session.playing()
        before={}
        for role,(live,record) in handles.items():
            live.verify_owned(record)
            sample,_=fresh_state(record,0)
            if not sample:
                raise ValueError('before_state_missing:'+role)
            before[role]=sample
        write(run/'gameplay-before.json',before)
        offsets={role:Path(record['log']).stat().st_size for role,(_,record) in handles.items()}
        journal.append('network_action_boundary',offsets=offsets)
        session.tap('CHAR:e')
        deadline=time.monotonic()+8
        authority=handles['Server'][1]
        action=None
        matches={}
        receipt=None
        while time.monotonic()<deadline:
            session.guard('network_collect')
            for live,record in handles.values():
                live.require_alive(live.owned_handle)
            with Path(authority['log']).open('rb') as stream:
                stream.seek(offsets['Server'])
                block=stream.read()
            for line in block.splitlines(keepends=True):
                if b'U02B_EVENT {' not in line or not line.endswith(b'\n'):
                    continue
                event=json.loads(line.split(b'U02B_EVENT ',1)[1])
                a=owners['ClientA']
                if (event.get('event')=='ActionStarted' and event.get('pawnId')==a['pawn']
                        and event.get('life')==a['life'] and event.get('definition')==4):
                    if any(event.get(k)!=v for k,v in [('pid',authority['pid']),('sourceSHA',NATIVE),
                            ('runId',run.name),('netMode',1),('worldType',1),('world',MAP+'.L_NetworkLab')]):
                        raise ValueError('authority_action_identity')
                    action=dict(source=a['pawn'],sourceLife=a['life'],action=event['action'],at=event['gameplaySeconds'])
                    break
            if action:
                for role,(_,record) in handles.items():
                    if role in matches:
                        continue
                    sample,_=fresh_state(record,offsets[role])
                    if sample and any((r['source'],r['sourceLife'],r['action'])==
                            (action['source'],action['sourceLife'],action['action']) for r in sample['state']['results']):
                        matches[role]=sample
                if len(matches)==3:
                    receipt=replicated_damage(before['Server']['state'],
                        {role:s['state'] for role,s in matches.items()},owners['ClientA'],action)
                    prior=[p for p in before['Server']['state']['pawns'] if p['id']==receipt['target']]
                    if len(prior)!=1 or prior[0]['life']!=receipt['targetLife'] or prior[0]['vital']['hp']-receipt['damage']!=receipt['hp']:
                        raise ValueError('authority_hp_delta')
                    return dict(replicatedDamage='PASS',ownerIsolation='ISOLATION_NOT_PROVEN',
                                isolationReason='Build-03 logs lack contemporaneous attack geometry, hurtbox poses and LOS for A',
                                action=action,receipt=receipt,before=before,replicated=matches,offsets=offsets)
            session.wait(.05)
        write(run/'gameplay-partial.json',dict(action=action, matches=matches, offsets=offsets))
        raise TimeoutError('new_action_or_replicated_receipt_timeout')
    finally:
        journal.close()


def start_roles(run, port, roles):
    exe, module, build = pins()
    check_port(port)
    protected = snap()
    before, games = inventory()
    if games:
        raise ValueError('package_active')
    run.mkdir()
    owned = []
    verdict = dict(status='INCOMPLETE', readiness={}, stops={}, tooling=git('rev-parse', 'HEAD'))
    try:
        for role in (("Server","ClientB","ClientA") if tuple(roles)==ROLES else roles):
            record = plan(run, role, port, exe, module, build)
            Path(record['userDir']).mkdir(parents=True)
            backend = Backend(input_enabled=role=="ClientA")
            owned.append((role, backend, record))
            write(run/role/'command.json', record)
            backend.launch(record['arguments'], ROOT)
            record.update(backend.capture_owned())
            write(run/role/'process.json', record)
            verdict['readiness'][role] = wait_ready(record, backend)
            write(run/role/'readiness.json', verdict['readiness'][role])
        if tuple(roles) == ROLES:
            _, server_backend, server_record = owned[0]
            server_backend.verify_owned(server_record)
            server_sample, _ = fresh_state(server_record, 0)
            verdict['connection'] = verify_owners(server_sample, verdict['readiness'])
            verdict['gameplay'] = capture_gameplay(run, owned, verdict['connection'])
    except Exception as exc:
        verdict.update(status='INVALID', error=f'{type(exc).__name__}: {exc}')
    finally:
        for role, backend, record in reversed(owned):
            if backend.has_owned():
                try:
                    if 'creationTicks' in record:
                        backend.assert_record_handle(record, backend.capture_owned())
                    verdict['stops'][role] = backend.stop_launched()
                except Exception as exc:
                    verdict['stops'][role] = dict(error=str(exc), processExited=False)
                finally:
                    backend.close_owned()
        after, games = inventory()
        verdict['preservation'] = dict(workspace=protected==snap(), editors=identities(before)<=identities(after),
                                       noPackage=not games)
        if not all(verdict['preservation'].values()) or any(
                stop.get('wait') != 'signaled' or stop.get('identityVerifiedAtStop') is not True
                for stop in verdict['stops'].values()):
            verdict['status'] = 'INVALID'
        write(run/'final.json', verdict)
    return verdict


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--server-only', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'C1-Dedicated-[a-zA-Z0-9-]+', args.id) or not 1024 <= args.port <= 65535:
        parser.error('invalid run ID or port')
    result = start_roles(ROOT.parent/'Runs'/args.id, args.port, ROLES[:1] if args.server_only else ROLES)
    raise SystemExit(1 if result['status'] == 'INVALID' else 0)
