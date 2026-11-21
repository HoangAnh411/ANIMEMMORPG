"""Additional offline identity/lifecycle cases; no native process or input calls."""
import argparse
import copy
import csv
import io
import json
from pathlib import Path
import unittest
import types
from C1Identity import creation_ticks, verify_identity, render_command
from C1Offline import record, CREATED
from C1Run import run_owned_launch, write
from C1Win32 import utc_from_ticks

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);rows=[];suite=unittest.TestSuite()
    def add(name,expected,run):
        def test(self):
            actual,detail=run();rows.append(dict(case=name,expected=expected,actual=actual,passed=actual==expected,**detail));self.assertEqual(actual,expected)
        suite.addTest(type(name,(unittest.TestCase,),{'runTest':test})())
    def precision(delta,reused=False,missing=False):
        r=record();r['creationTicks']=134397380556959859;r['creationUTC']=utc_from_ticks(r['creationTicks'])
        live=dict(pid=r['pid'],executable=r['executable'],commandLine=render_command(r['arguments']),
                  creationTicks=r['creationTicks']+(1 if reused else 0),creationUTC=utc_from_ticks(r['creationTicks']-delta))
        if missing:live.pop('creationTicks')
        try:proof=verify_identity(r,live);actual='PASS'
        except Exception as e:proof=None;actual=str(e)
        return actual,dict(record=r,live=live,proof=proof,cimDeltaTicks=delta)
    for delta in (0,1,2,6,9):add('cim_diagnostic_delta_'+str(delta),'PASS',lambda delta=delta:precision(delta))
    add('pid_reused_one_filetime_tick','process_creation_mismatch',lambda:precision(9,reused=True))
    add('cim_alone_cannot_supply_identity','win32_creation_ticks_missing',lambda:precision(9,missing=True))
    def popen_gap():
        from C1Win32 import Backend
        events=[]
        class Handle:
            def __int__(self):return 456
            def Close(self):events.append('close_original')
        backend=Backend.__new__(Backend);backend.process=types.SimpleNamespace(pid=1234,_handle=Handle())
        backend.owned_handle=None;backend.owned_pid=None;backend.handle_closed=False;backend.stop_evidence=None
        assert backend.has_owned() and backend.owned_pid==1234 and backend.owned_handle.value==456
        backend.close_owned();assert not backend.has_owned() and events==['close_original']
        return 'PASS',dict(recoveredHandleSource='original_Popen_object',replacementPIDLookups=0,events=events)
    add('ownership_gap_after_popen_assignment','PASS',popen_gap)
    def persistent_metadata_error():
        from C1Win32 import Backend
        events=[]
        class Handle:
            def __int__(self):return 456
            def Close(self):events.append('close_original')
        class Kernel:
            def GetExitCodeProcess(self,h,code):code._obj.value=0 if 'terminate_original' in events else 259;return 1
            def TerminateProcess(self,h,code):events.append('terminate_original');return 1
            def WaitForSingleObject(self,h,ms):events.append('wait_original');return 0
            def OpenProcess(self,*a):raise AssertionError('no PID lookup for cleanup')
        b=Backend.__new__(Backend);b.process=types.SimpleNamespace(pid=1234,_handle=Handle())
        b.owned_handle=None;b.owned_pid=None;b.handle_closed=False;b.stop_evidence=None;b.pinned_ticks=None
        b.expected_executable=record()['executable'];b.k=Kernel()
        def unavailable():raise OSError('persistent GetProcessTimes failure')
        b.capture_owned=unavailable
        proof=b.stop_launched(30);b.close_owned()
        assert proof['wait']=='signaled' and proof['identityVerifiedAtStop'] is False and proof['creationTicks'] is None
        return 'PASS',dict(exitEvidence=proof,events=events,identityAcceptance=False,replacementPIDLookups=0)
    add('persistent_metadata_error_still_stops_original_child','PASS',persistent_metadata_error)

    def initialization(stage):
        out=a.out/stage;out.mkdir();r=record();events=[];calls=dict(probe=0,stop=0,close=0)
        class FakeBackend:
            owned=False
            def now(self):return 10.
            def launch(self,args,cwd):
                self.owned=True;events.append('original_handle_owned')
                if stage=='launch_after_spawn':raise OSError('fake failure after process creation')
            def has_owned(self):return self.owned
            def capture_owned(self):
                events.append('capture_original_handle')
                if stage=='capture_identity':raise OSError('fake identity acquisition failure')
                return {k:r[k] for k in ('pid','creationUTC','creationTicks','executable')}
            def verify_owned(self,record):
                events.append('verify_identity')
                if stage=='verify_identity':raise RuntimeError('fake CIM read failure')
                return dict(creationTicks=r['creationTicks'])
            def stop_launched(self,timeout):
                calls['stop']+=1;events.append('stop_original_handle')
                if stage=='stop_timeout':raise RuntimeError('owned_exit_timeout')
                return dict(pid=r['pid'],creationTicks=r['creationTicks'],wait='fake-signaled',handleSource='original_Popen',identityVerifiedAtStop=True)
            def close_owned(self):calls['close']+=1;events.append('close_original_handle');self.owned=False
        backend=FakeBackend()
        def writer(path,value):
            events.append('write:'+path.name)
            if stage=='disk_full' or stage=='process_record_write' and path.name=='process.json':raise OSError('fake disk failure')
            write(path,value)
        def journal_factory(path,clock):
            from C1Readiness import Journal
            events.append('open_journal')
            if stage=='journal_open':raise OSError('fake journal open failure')
            journal=Journal(path,clock)
            if stage=='journal_first_write':
                def fail(*a,**k):raise OSError('fake journal append failure')
                journal.append=fail
            return journal
        def probe(*args,**kwargs):calls['probe']+=1;return dict(status='PASS',fakeInputCalls=0)
        result=run_owned_launch(backend,r['arguments'],out,out,r,probe=probe,writer=writer,journal_factory=journal_factory)
        assert calls['stop']==1
        assert calls['close']==(0 if stage=='stop_timeout' else 1)
        assert calls['probe']==(1 if stage in ('normal','stop_timeout') else 0)
        assert result['processExited']==(stage!='stop_timeout')
        assert events.index('stop_original_handle')<events.index('write:result.json')
        return result['status'],dict(result=result,events=events,calls=calls,realLaunches=0,realInputCalls=0)
    for stage in ('normal','launch_after_spawn','capture_identity','process_record_write','journal_open','verify_identity','journal_first_write','disk_full','stop_timeout'):
        add('owned_lifecycle_'+stage,'PASS' if stage=='normal' else 'INVALID',lambda stage=stage:initialization(stage))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    transcript=stream.getvalue();(a.out/'transcript.txt').write_text(transcript,encoding='utf-8');print(transcript)
    (a.out/'results.json').write_text(json.dumps(dict(scope='OFFLINE ONLY',testsRun=result.testsRun,passed=result.wasSuccessful(),cases=rows),indent=2),encoding='utf-8')
    with (a.out/'cases.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['case','expected','actual','passed']);w.writeheader();w.writerows({k:r[k] for k in w.fieldnames} for r in rows)
    return 0 if result.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())
