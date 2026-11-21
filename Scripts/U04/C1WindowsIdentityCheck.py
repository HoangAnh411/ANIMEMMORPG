"""Authorized Windows identity check on hidden, harmless Python timer children only.

No user32 backend, HWND selection, focus, input, game, Editor, build or Unreal tests.
Each child has a retained original Popen HANDLE and an exact known command line.
"""
import argparse
import csv
import json
from pathlib import Path
import sys
from C1Run import run_owned_launch, NATIVE, write
from C1Win32 import Backend, sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    executable=Path(sys.executable).resolve()
    if executable.name.casefold() not in ('python.exe','python3.exe'):raise RuntimeError('only Python timer children allowed')
    protected=Backend(input_enabled=False).inventory();write(out/'protected-before.json',protected)
    samples=[];mismatch=False
    for n in range(1,11):
        folder=out/f'Sample-{n:02d}';folder.mkdir();backend=Backend(input_enabled=False)
        run_id=out.name+f'-Sample-{n:02d}'
        args=[str(executable),'-c','import time; time.sleep(120)',f'-U02SourceSHA={NATIVE}',f'-U02RunId={run_id}',
              f'-UserDir={folder/"User With Spaces"}',f'-abslog={folder/"unused.log"}']
        base=dict(role='BENIGN_WINDOWS_IDENTITY_CHILD',executable=str(executable),binarySHA256=sha(executable),sourceSHA=NATIVE,runId=run_id,userDir=str(folder/'User With Spaces'),log=str(folder/'unused.log'))
        write(folder/'command.json',dict(arguments=args,inputEnabled=False,childBehavior='time.sleep(120) only; metadata args ignored by child'))
        def verify_only(record,backend,log,journal,cleanup):
            proof=backend.verify_owned(record)
            journal.append('benign_identity_verified',proof=proof)
            return dict(status='PASS',identity=proof,hwndSelectionCalls=0,inputCalls=0)
        result=run_owned_launch(backend,args,folder,folder,base,probe=verify_only)
        write(folder/'check.json',result)
        samples.append(dict(sample=n,status=result['status'],processExited=result['processExited'],identity=result.get('identity'),exitEvidence=result.get('exitEvidence'),error=result.get('error')))
        write(out/f'progress-{n:02d}.json',samples[-1])
        if result['status']!='PASS' or not result['processExited']:break
        proof=result['identity'];mismatch=mismatch or proof['cimDeltaTicks'] not in (None,0)
        if len(samples)>=5 and mismatch:break
    # Actual initialization-failure path on another harmless child. No metadata
    # success is fabricated; only original-HANDLE exit is accepted as cleanup.
    folder=out/'Metadata-Failure-Recovery';folder.mkdir();recovery_backend=Backend(input_enabled=False)
    recovery_id=out.name+'-Metadata-Recovery'
    recovery_args=[str(executable),'-c','import time; time.sleep(120)',f'-U02SourceSHA={NATIVE}',f'-U02RunId={recovery_id}',f'-UserDir={folder/"User"}',f'-abslog={folder/"unused.log"}']
    recovery_base=dict(role='BENIGN_METADATA_FAILURE_CHILD',executable=str(executable),binarySHA256=sha(executable),sourceSHA=NATIVE,runId=recovery_id,userDir=str(folder/'User'),log=str(folder/'unused.log'))
    def unavailable():raise OSError('injected persistent metadata acquisition failure')
    recovery_backend.capture_owned=unavailable
    def forbidden_probe(*args,**kwargs):raise AssertionError('must not enter probe after initialization failure')
    write(folder/'command.json',dict(arguments=recovery_args,injection='capture_owned raises OSError persistently',inputEnabled=False))
    recovery=run_owned_launch(recovery_backend,recovery_args,folder,folder,recovery_base,probe=forbidden_probe)
    write(folder/'check.json',recovery)
    after=Backend(input_enabled=False).inventory();write(out/'protected-after.json',after)
    preserved=all(row in after for row in protected)
    passed=len(samples)>=5 and mismatch and preserved and all(s['status']=='PASS' and s['processExited'] for s in samples) and recovery['status']=='INVALID' and recovery['processExited']
    summary=dict(status='PASS' if passed else 'INCOMPLETE',scope='real Win32 identity only; harmless hidden Python children',samples=samples,
                 observedCIMFILETIMEMismatch=mismatch,metadataFailureRecovery=recovery,protectedProcessesUnchanged=preserved,gameLaunches=0,editorOperations=0,hwndSelectionCalls=0,inputCalls=0)
    write(out/'summary.json',summary)
    with (out/'samples.csv').open('x',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['sample','status','pid','originalFILETIME','queryFILETIME','cimCreationUTC','cimDeltaTicks','processExited'])
        for s in samples:
            i=s.get('identity') or {};w.writerow([s['sample'],s['status'],i.get('pid'),i.get('originalHandle',{}).get('creationTicks'),i.get('queryHandle',{}).get('creationTicks'),i.get('cimCreationUTC'),i.get('cimDeltaTicks'),s['processExited']])
    print(json.dumps(summary,indent=2))
    return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
