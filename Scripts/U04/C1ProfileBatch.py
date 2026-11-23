"""Method pilot and paired overhead driver, run from the foreground coordinator."""
import shutil
import subprocess
import sys
from pathlib import Path

from C1ForegroundBatch import git, identities, inventory, snap
from C1ProfileEvidence import inspect
from C1ProfileValidate import validate
from C1Run import ROOT, read, sha, write


def run_batch(control, granted, commit, messages):
    runs=ROOT.parent/'Runs'
    if git('rev-parse','HEAD')!=commit or git('status','--porcelain'):
        raise RuntimeError('tooling preflight')
    modes=('timing','memory','off','timing','timing','off','off','timing')
    ledger=[dict(id=f'C1-Method-{control.name[-15:]}-{i:02d}-{mode}',mode=mode,status='NOT_RUN') for i,mode in enumerate(modes,1)]
    initial,games=inventory()
    if games:
        raise RuntimeError('package already running')
    protected=snap()
    write(control/'profile-preflight.json',dict(commit=commit,editors=initial,
          freeBytes=shutil.disk_usage(runs).free,workspace=protected))
    try:
        for row in ledger:
            run=runs/row['id']
            if run.exists():
                raise RuntimeError('method run already exists')
            before,games=inventory()
            if games or not identities(initial)<=identities(before):
                raise RuntimeError('per-run inventory preflight')
            folder=control/row['id'];folder.mkdir()
            args=['method','--id',row['id'],'--mode',row['mode']]
            write(folder/'launch-argv.json',args)
            messages.put(row['id'])
            row.update(raw=str(run),status='INVALID')
            with (folder/'launcher.stdout').open('x') as stdout,(folder/'launcher.stderr').open('x') as stderr:
                row['launcherExit']=granted(args,stdout,stderr)
            after,games=inventory()
            row['preservation']=dict(workspace=snap()==protected,editors=identities(before)<=identities(after),
                                     packageExited=not games, before=before, after=after)
            if (run/'final.json').exists():
                row['final']=read(run/'final.json')
            verdict=validate(run)
            row['postcheck']=verdict
            if not all(row['preservation'][k] for k in ('workspace','editors','packageExited')) or verdict['status']!='PASS' or row['launcherExit']!=0:
                row['status']='FAIL' if verdict['status']=='FAIL' and row.get('final',{}).get('status')=='FAIL' else 'INVALID'
                break
            if row['mode']!='off':
                trace=run/'capture.utrace'
                row['trace']=dict(path=str(trace),bytes=trace.stat().st_size,sha256=sha(trace))
                destination=folder/'Exports'
                export=[sys.executable,'-B',str(ROOT/'Scripts/U04/C1Export.py'),str(run),'--output',str(destination)]
                if row['mode']=='memory':
                    export.append('--memory')
                subprocess.run(export,check=True)
                row['export']=inspect(run,destination,row['mode'])
            row['retainedBytes']=sum(f.stat().st_size for parent in (run,folder) for f in parent.rglob('*') if f.is_file())
            row['status']='PASS'
            print(row['id'],'PASS',flush=True)
    except Exception as error:
        write(control/'method-error.json',dict(error=repr(error)))
        raise
    finally:
        write(control/'method-ledger.json',ledger)
    if all(r['status']=='PASS' for r in ledger):
        overhead=[]
        for a,b in zip(ledger[2::2],ledger[3::2]):
            off,on=(a,b) if a['mode']=='off' else (b,a)
            x,y=off['postcheck'],on['postcheck']
            before=dict(fps=x['fps'],**x['frameMs']);after=dict(fps=y['fps'],**y['frameMs'])
            overhead.append(dict(order=[a['id'],b['id']],values={
                k:dict(off=v,on=after[k],delta=after[k]-v,percent=100*(after[k]-v)/v)
                for k,v in before.items()}))
        write(control/'overhead.json',overhead)
        timing=max(r['retainedBytes'] for r in ledger if r['mode']=='timing')
        memory=ledger[1]['retainedBytes']
        base=36*timing+12*memory
        write(control/'capacity.json',dict(timingPerRun=timing,memoryPerRun=memory,base=base,
              simultaneousExportAllowance=max(timing,memory),reserve=base//4,
              required=base+max(timing,memory)+base//4,free=shutil.disk_usage(runs).free,
              limitation='Pilot only sampled 10x3/in, not 40x3.'))
