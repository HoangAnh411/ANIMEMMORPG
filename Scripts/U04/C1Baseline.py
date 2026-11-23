"""Run the frozen C1 baseline and retain independently verified exports."""
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

from C1ForegroundBatch import git, identities, inventory, snap
from C1ProfileEvidence import inspect
from C1ProfileValidate import validate
from C1Run import ROOT, NATIVE, read, sha, write
from C1StorageCheck import roundtrip

DOC = ROOT/'Docs/U04/C1'
RUNS = ROOT.parent/'Runs'


def authorized_matrix():
    gates=read(DOC/'GATES.json')
    a=gates['baselineAuthorization']
    if not (a['state']=='AUTHORIZED' and gates['sourceSHA']==NATIVE
            and gates['counterCorrectness']=='ACCEPTED_12_OF_12'
            and gates['methodology']=='ACCEPTED_SINGLE_PROCESS_SINGLE_GAME_WORLD_SINGLE_WINDOW'
            and gates['overheadPairs']==dict(valid=3,required=3) and a['pilots']==2
            and gates['traceCapacityForecast']=='ACCEPTED_GZIP_ON_D'):
        raise RuntimeError('baseline gates incomplete')
    for item in a['evidence'].values():
        if sha(ROOT.parent/item['path'])!=item['sha256']:
            raise RuntimeError('gated evidence hash mismatch: '+item['path'])
    matrix=DOC/'MATRIX.json'
    if sha(matrix)!=a['matrixSHA256']:
        raise RuntimeError('frozen matrix hash mismatch')
    data=read(matrix)
    expected=[(kind,n,h,p) for kind in ('timing','timing','timing','memory')
              for n in (1,10,40) for h in (1,3) for p in ('in','out')]
    rows=data['rows']
    if (data['profile']!='review-B' or len({r['id'] for r in rows})!=48
        or [(r['kind'],r['subjects'],r['boxes'],r['placement']) for r in rows]!=expected
        or any((r['warmup'],r['seconds'],r['status'])!=(30,60,'NOT_RUN') for r in rows)):
        raise RuntimeError('frozen matrix structure mismatch')
    return rows


def next_row(rows):
    for row in rows:
        if row['status']=='PASS':
            continue
        if row['status'] not in ('NOT_RUN','WAITING_FOR_ACTIVATION') or row.get('packageLaunched') or row.get('workerCreated'):
            raise RuntimeError('cannot skip or relaunch unresolved member '+row['id'])
        return row
    return None


def export_run(run, folder, mode):
    def invoke(dest, extra):
        args=[sys.executable,'-B',str(ROOT/'Scripts/U04/C1Export.py'),str(run),'--output',str(dest),*extra]
        subprocess.run(args,check=True)
        receipt=read(dest/'exit.json')
        if receipt['exitCode'] or read(dest/'process.json')['traceSHA256']!=trace:
            raise RuntimeError('Insights receipt mismatch')
        return [(dest/f['path'],f) for f in receipt['exports']]
    trace=sha(run/'capture.utrace')
    staging=folder/'Stage'
    memory=mode=='memory'
    staged=invoke(staging,['--memory','--compact-memory'] if memory else [])
    if memory:
        log=(staging/'Insights.log').read_text(encoding='utf-8-sig',errors='replace')
        match=re.search(r"TimeA:\s+([0-9.]+) \(from bookmark 'U04C1_START'\)",log)
        if not match:
            raise RuntimeError('memory start bookmark not exported')
        sample=float(match.group(1))+.13
        staged+=invoke(folder/'StackStage',['--memory','--compact-memory','--stack-only','--stack-sample-start',str(sample)])
    pending=folder/'Archive-pending';pending.mkdir()
    shutil.copyfile(staging/'Insights.log',pending/'Insights.log')
    records=[]
    for source,receipt in staged:
        dest=pending/(source.name+'.gz')
        record=roundtrip(source,dest,receipt)
        record['archive']=dest.name
        records.append(record)
    evidence=inspect(run,pending,mode)
    write(pending/'receipt.json',dict(traceSHA256=trace,files=records,evidence=evidence,
                                     sampleTraceSeconds=[sample,sample+.05] if memory else None))
    archive=folder/'Archive'
    pending.rename(archive)
    # These exact files were produced in this run's new staging folders.
    for source,_ in staged:
        source.unlink()
    return dict(archive=str(archive),traceSHA256=trace,evidence=evidence,
                stagingBytes=sum(f['rawBytes'] for f in records),
                gzipBytes=sum(f['gzipBytes'] for f in records))


def run_batch(control, granted, commit, messages):
    rows=[dict(r,workerCreated=False,packageLaunched=False) for r in authorized_matrix()]
    if git('rev-parse','HEAD')!=commit or git('status','--porcelain'):
        raise RuntimeError('tooling commit/cleanliness')
    if git('diff',NATIVE,'--','Source','Content','Config','Plugins','AnimeMMORPG.uproject'):
        raise RuntimeError('native input diff')
    gate=read(DOC/'GATES.json')['baselineAuthorization']
    build=RUNS/'Build-03'
    identity=read(build/'BUILD-IDENTITY.json')
    game=build/'Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
    if (identity['sourceSHA']!=NATIVE or Path(identity['clone']).resolve()!=ROOT
        or identity['gameSHA256']!=gate['gameSHA256'] or sha(game)!=gate['gameSHA256']
        or sha(game.with_suffix('.pdb'))!=gate['pdbSHA256']):
        raise RuntimeError('Game/PDB/build identity')
    if any((RUNS/r['id']).exists() for r in rows):
        raise RuntimeError('baseline run ID already exists')
    initial,games=inventory()
    if games:raise RuntimeError('package already present')
    protected=snap()
    estimate=read(ROOT.parent/gate['evidence']['storage']['path'])
    rates={mode:estimate[mode+'PerRunBytes'] for mode in ('timing','memory')}
    staging=estimate['extraTemporaryPeakBytes']
    def checkpoint():
        tmp=control/'baseline-ledger.pending.json'
        write(tmp,rows)
        os.replace(tmp,control/'baseline-ledger.json')
    def capacity(row, present=0):
        left=Counter(r['kind'] for r in rows if r['status']!='PASS')
        retained=sum(rates[k]*n for k,n in left.items())
        reserve=(retained+staging+3)//4
        required=max(0,retained+staging+reserve-present)
        free=shutil.disk_usage(RUNS).free
        report=dict(required=required,free=free,shortfall=max(0,required-free),present=present,retained=retained,staging=staging,reserve=reserve)
        row.setdefault('capacity',[]).append(report)
        checkpoint()
        if required>free:raise RuntimeError('storage BLOCKED on D: '+str(required-free)+' bytes')
    write(control/'baseline-preflight.json',dict(commit=commit,native=NATIVE,gameSHA256=gate['gameSHA256'],pdbSHA256=gate['pdbSHA256'],editors=initial,protected=protected,limits=gate['limits']))
    checkpoint()
    try:
        while (row:=next_row(read(control/'baseline-ledger.json'))) is not None:
            row=next(r for r in rows if r['id']==row['id'])
            run=RUNS/row['id'];folder=control/row['id'];folder.mkdir()
            capacity(row)
            before,games=inventory()
            if run.exists() or games or not identities(initial)<=identities(before):
                raise RuntimeError('per-run identity/ID preflight')
            args=['method','--baseline','--id',row['id'],'--mode',row['kind']]
            row.update(status='WAITING_FOR_ACTIVATION',raw=str(run),argv=args)
            checkpoint()
            messages.put(row['id'])
            def created(pid):
                row.update(status='WORKER_CREATED',workerCreated=True,workerPID=pid)
                checkpoint()
            with (folder/'launcher.stdout').open('x') as out,(folder/'launcher.stderr').open('x') as err:
                row['launcherExit']=granted(args,out,err,created)
            row.update(status='INVALID',packageLaunched=(run/'process.json').is_file())
            checkpoint()
            after,games=inventory()
            row['preservation']=dict(workspace=protected==snap(),editors=identities(before)<=identities(after),packageExited=not games)
            row['final']=read(run/'final.json') if (run/'final.json').exists() else None
            row['postcheck']=validate(run)
            checkpoint()
            if row['postcheck']['status']=='FAIL':
                row['status']='FAIL';break
            if row['launcherExit'] or row['postcheck']['status']!='PASS' or not all(row['preservation'].values()):
                break
            present=sum(f.stat().st_size for f in run.rglob('*') if f.is_file())
            capacity(row,present)
            row['export']=export_run(run,folder,row['kind'])
            total=sum(f.stat().st_size for d in (run,folder) for f in d.rglob('*') if f.is_file())
            rates[row['kind']]=max(rates[row['kind']],total)
            staging=max(staging,row['export']['stagingBytes']+(run/'capture.ucache').stat().st_size if (run/'capture.ucache').exists() else row['export']['stagingBytes'])
            row.update(status='PASS',retainedBytes=total)
            checkpoint()
            print(row['id'],'PASS',flush=True)
    except Exception as error:
        write(control/'baseline-error.json',dict(error=repr(error)))
        raise
    finally:
        checkpoint()
    if all(r['status']=='PASS' for r in rows):
        write(control/'baseline-review.json',dict(status='BASELINE_READY_FOR_REVIEW',rows=rows,rates=rates,
              stagingPeak=staging,free=shutil.disk_usage(RUNS).free,limits=gate['limits']))
