"""Prepare immutable pilot receipt before opening the foreground coordinator."""
import json
import shutil
import sys
from pathlib import Path

from C1ProfileBatch import remaining_members
from C1ProfileValidate import validate
from C1Run import ROOT, read, sha, write


def make_receipt(out, commit):
    out.mkdir(exist_ok=False)
    parent=ROOT.parent
    old=parent/'CC-B-Foreground-Control-20261123-090341'
    saved=read(old/'method-ledger.json')
    pilots=saved[:2]
    assert [p['mode'] for p in pilots]==['timing','memory']
    assert all(p['status']=='PASS' and p['launcherExit']==0 for p in pilots)
    prior=saved[2]
    assert prior['status']=='INVALID' and 'launcherExit' not in prior and not Path(prior['raw']).exists()
    assert read(old/'method-error.json')['error']=="RuntimeError('coordinator_not_foreground_before_worker')"
    prior=dict(prior,packageLaunched=False,workerCreated=False,ledger=str(old/'method-ledger.json'))
    for row in pilots:
        run=Path(row['raw'])
        export=Path(row['exportPath'])
        assert run.is_absolute() and export.is_absolute() and run.name==row['id']
        assert all(row['preservation'][k] for k in ('workspace','editors','packageExited'))
        assert read(run/'process.json')['runId']==row['id']
        post=validate(run);assert post['status']=='PASS'
        row['postcheck']=post
        trace=run/'capture.utrace'; digest=sha(trace)
        assert digest==row['trace']['sha256']==read(export/'process.json')['traceSHA256']
        final=read(run/'final.json')
        assert final['status']=='PASS' and final['exitEvidence']==row['final']['exitEvidence']
        receipt=read(export/'exit.json');assert receipt['exitCode']==0
        for f in receipt['exports']:
            path=export/f['path']
            assert path.stat().st_size==f['bytes'] and sha(path)==f['sha256'],f['path']
        row['verifiedExportReceipt']=str(export/'exit.json')
        row['verifiedExportReceiptSHA256']=sha(export/'exit.json')
    memory=pilots[1]['export']
    assert memory==read(parent/'C1-Method-Offline-R1/P2-metrics.json')
    for k in ('count','bytes'):
        assert memory['allocations'][k]-memory['frees'][k]==memory['outstanding-end'][k]-memory['outstanding-start'][k]==memory['outstandingDelta'][k]
    assert memory['outstandingDelta']==dict(count=36194,bytes=-1850756)
    timing=pilots[0]['retainedBytes']
    budget=8*timing+2*timing
    free=shutil.disk_usage(parent/'Runs').free
    assert free>=budget
    fixture=pilots+[dict(id=str(i),status='NOT_RUN') for i in range(6)]
    # Reopen checkpoint twice and ensure an earlier PASS never appears again.
    assert remaining_members(fixture)[0]['id']=='0'
    fixture[2].update(status='WAITING_FOR_ACTIVATION',workerCreated=False,packageLaunched=False)
    assert remaining_members(json.loads(json.dumps(fixture)))[0]['id']=='0'
    fixture[2].update(status='PASS',workerCreated=True,packageLaunched=True)
    assert remaining_members(json.loads(json.dumps(fixture)))[0]['id']=='1'
    write(out/'pilot-receipt.json',dict(commit=commit,pilots=pilots,priorAttempt=prior,
          overheadBudgetBytes=budget,overheadFreeBytes=free,
          budgetFormula='6 retained members + 2 simultaneous export allowances + 25% reserve on 8 allowances; each allowance is P1 retained bytes',
          stackCoverage='All allocation/free rows use top function; full allocation stacks sampled in [39.10,39.15] trace seconds.'))
    print('pilot receipt verified',flush=True)


if __name__=='__main__':
    make_receipt(Path(sys.argv[1]).resolve(),sys.argv[2])
