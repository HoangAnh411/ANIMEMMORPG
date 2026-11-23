"""Replay target transfer, continuation order and guarded readiness."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

from C1Baseline import authorized_matrix, load_continuation, next_row
from C1ForegroundCoordinator import transfer_target
from C1Offline import FakeBackend, FakeLog, record
from C1ProfileRun import ProfileSession, WORKLOAD
from C1Readiness import Journal, ProbeError
from C1Run import write


def main(out, ledger):
    out.mkdir()
    rows=[]
    worker=dict(pid=9,creationTicks=19,executable='D:/Worker.exe')
    target=dict(pid=8,creationTicks=18,executable='D:/Game.exe')
    base=dict(runId='test',worker=worker,target=target,hwnd=80)
    cases=[
        ('game',{},(80,8),8,False,True,'already_foreground',0),
        ('coordinator',{},(70,7),8,False,True,'coordinator_direct',1),
        ('third_party',{},(60,6),8,False,True,'third_party_foreground',0),
        ('wrong_hwnd',{},(70,7),6,False,True,'target_hwnd_owner',0),
        ('wrong_pid',dict(target=dict(target,pid=6)),(70,7),8,False,True,'target_hwnd_owner',0),
        ('wrong_ticks',dict(target=dict(target,creationTicks=17)),(70,7),8,False,True,'target_process_identity',0),
        ('old_worker',dict(worker=dict(worker,creationTicks=17)),(70,7),8,False,True,'duplicate_or_wrong_worker_session',0),
        ('duplicate',{},(70,7),8,True,True,'duplicate_or_wrong_worker_session',0),
        ('api_false',{},(70,7),8,False,False,'coordinator_direct',1),
    ]
    for name,overrides,fg,owner,seen,api,expected,count in cases:
        calls=[]
        result=transfer_target(dict(base,**overrides),worker,'test',target['executable'],seen,7,
                               identity_reader={8:target,9:worker}.__getitem__,
                               owner_reader=lambda _:owner,current_foreground=lambda:fg,
                               focus=lambda hwnd:calls.append(hwnd) or api)
        assert result.get('branch',result.get('reason'))==expected and len(calls)==result['calls']==count
        if count:assert result['apiResult'] is api
        rows.append(dict(case=name,expected=expected,result=result))
    for name in ('api_false','loss_after_focus'):
        backend=FakeBackend(FakeLog())
        backend.fg,backend.fgpid=202,9999
        r=dict(record(),targetReady=True)
        j=Journal(out/(name+'.jsonl'),backend.now)
        session=ProfileSession(r,backend,backend.log,j,workload=WORKLOAD,output=out)
        def wait_step(b):
            if name=='loss_after_focus':
                b.fg,b.fgpid=(101,1234) if b.t<10.15 else (202,9999)
        backend.sleep_fault=wait_step
        with patch('C1ForegroundCoordinator.process_identity',return_value={k:r[k] for k in ('pid','creationTicks','executable')}), patch('C1ForegroundCoordinator.ready_target',return_value=dict(ok=True,apiResult=False)):
            try:
                session.select();session.focus_once()
            except ProbeError as error:
                wanted='initial_foreground_timeout' if name=='api_false' else 'foreground_hwnd_mismatch'
                assert str(error)==wanted
            else:
                raise AssertionError('input gate should fail')
            try:session.emit('W',True)
            except ProbeError:pass
            assert not backend.sent and backend.focus_calls==0
        j.close()
        rows.append(dict(case=name+'_worker',inputs=0,workerFocusCalls=0))
    plan=load_continuation(ledger,authorized_matrix())
    assert [row['status'] for row in plan[:15]]==['PASS']*15
    assert len(plan[15:])==33 and next_row(plan)['id']=='Timing-r2-1x3-out-R1'
    assert [row['kind'] for row in plan[15:]]==['timing']*21+['memory']*12
    write(out/'receipt.json',dict(cases=rows,skipped=15,next=plan[15]['id'],launches=0,
          planned=[dict(logicalId=r['logicalId'],runId=r['id'],kind=r['kind']) for r in plan[15:]]))
    print('11 TARGET_READY replays; 15 historic PASS verified; 33 planned launches')


if __name__=='__main__':
    main(Path(sys.argv[1]),Path(sys.argv[2]).resolve())
