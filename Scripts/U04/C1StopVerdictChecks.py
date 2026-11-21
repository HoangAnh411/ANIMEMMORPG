"""Offline entry-to-exit verdict replay with the actual stop adapter and fake kernel.

No live Backend constructor, process, HWND, focus, input, Game or Editor calls.
"""
import argparse
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import ctypes as c
from ctypes import wintypes as w
import C1Run
from C1Identity import creation_ticks
from C1Offline import CREATED
from C1Win32 import Backend

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);rows=[];suite=unittest.TestSuite()
    def entry_case(mode):
        events=[];phase=dict(probePassed=False,metadataReads=0,terminated=False,closed=False)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'C1/Source';root.mkdir(parents=True)
            build=root.parent/'Runs/Build-03';build.mkdir(parents=True)
            exe=build/'Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
            exe.parent.mkdir(parents=True);exe.write_bytes(b'OFFLINE FIXTURE ONLY; NOT AN EXECUTABLE')
            (build/'BUILD-IDENTITY.json').write_text(json.dumps(dict(sourceSHA=C1Run.NATIVE,clone=str(root),gameSHA256=C1Run.sha(exe))))
            ticks=creation_ticks(CREATED)
            class Handle:
                def __int__(self):return 456
                def Close(self):events.append('close_original');phase['closed']=True
            class Kernel:
                def OpenProcess(self,*args):raise AssertionError('stop cannot reopen by PID')
                def GetProcessId(self,h):assert h.value==456;return 1234
                def QueryFullProcessImageNameW(self,h,flags,buffer,size):assert h.value==456;buffer.value=str(exe);return 1
                def GetExitCodeProcess(self,h,code):assert h.value==456;code._obj.value=0 if phase['terminated'] else 259;return 1
                def TerminateProcess(self,h,code):
                    assert h.value==456 and phase['probePassed'];phase['terminated']=True;events.append('terminate_original');return 1
                def WaitForSingleObject(self,h,ms):assert h.value==456 and ms==30000;events.append('wait_signaled');return 0
            backend=Backend.__new__(Backend);backend.k=Kernel();backend.process=None;backend.owned_handle=None
            backend.owned_pid=None;backend.pinned_ticks=None;backend.expected_executable=None;backend.stop_evidence=None;backend.handle_closed=False
            backend.dpi=dict(fake=True);backend.now=lambda:1.
            backend.inventory=lambda:[dict(ProcessId=9999,ExecutablePath='D:/Engine/UnrealEditor.exe',CommandLine='protected fixture',creationUTC=CREATED)]
            def launch(args,cwd):
                events.append('launch_fake_original');backend.expected_executable=args[0]
                backend.process=types.SimpleNamespace(pid=1234,_handle=Handle());backend.owned_handle=w.HANDLE(456);backend.owned_pid=1234
            backend.launch=launch
            def get_ticks(h):
                phase['metadataReads']+=1;events.append('metadata_at_stop' if phase['probePassed'] else 'metadata_before_probe')
                if phase['probePassed'] and mode=='stop_oserror':raise OSError('injected stop-only metadata failure')
                return ticks
            backend.ticks=get_ticks
            def verify(record):
                info=backend.capture_owned();assert info['pid']==record['pid'] and info['creationTicks']==record['creationTicks']
                events.append('launch_verify_pass');return info
            backend.verify_owned=verify
            actual_stop=backend.stop_launched
            def stop(timeout):
                proof=actual_stop(timeout)
                if mode=='missing_flag':proof.pop('identityVerifiedAtStop')
                elif mode=='null_flag':proof['identityVerifiedAtStop']=None
                elif mode=='numeric_flag':proof['identityVerifiedAtStop']=1
                elif mode=='string_flag':proof['identityVerifiedAtStop']='True'
                elif mode=='false_flag':proof['identityVerifiedAtStop']=False
                return proof
            backend.stop_launched=stop
            def probe(*args,**kwargs):
                assert kwargs['cleanup'] is False;phase['probePassed']=True;events.append('probe_pass');return dict(status='PASS',inputCalls=0)
            module=types.SimpleNamespace(Backend=lambda:backend)
            with patch.object(C1Run,'ROOT',root),patch.object(C1Run,'run_probe',probe),patch.dict(sys.modules,{'C1Win32':module}),patch('subprocess.check_output',return_value=b''),patch('subprocess.Popen',side_effect=AssertionError('REAL LAUNCH FORBIDDEN')) as popen:
                code=C1Run.main(['--readiness-only','--build',str(build),'--id',mode,'--trace','off'])
                assert popen.call_count==0
            folder=root.parent/'Runs'/mode;result=json.loads((folder/'result.json').read_text());final=json.loads((folder/'final.json').read_text())
            assert phase['probePassed'] and phase['metadataReads']==3 and phase['terminated'] and phase['closed']
            assert result['processExited'] is True and final['processExited'] is True
            assert result['exitEvidence']==final['exitEvidence']
            assert result['exitEvidence']['wait']=='signaled' and result['exitEvidence']['handleSource']=='original_Popen'
            expected='PASS' if mode=='normal' else 'INVALID'
            assert result['status']==final['status']==expected
            assert code==(0 if mode=='normal' else 1)
            if mode=='normal':assert result['exitEvidence']['identityVerifiedAtStop'] is True
            if mode=='stop_oserror':
                assert result['exitEvidence']['identityVerifiedAtStop'] is False
                assert 'injected stop-only metadata failure' in result['exitEvidence']['identityCaptureError']
                assert result['exitEvidence']['creationTicks']==ticks
            dest=a.out/mode;dest.mkdir()
            for f in folder.iterdir():
                if f.is_file():(dest/f.name).write_bytes(f.read_bytes())
            return dict(case=mode,expected=expected,actual=result['status'],passed=result['status']==expected,cliExitCode=code,
                        result=result,final=final,events=events,phase=phase,realLaunches=0,realInputCalls=0)
    for mode in ('normal','stop_oserror','missing_flag','null_flag','numeric_flag','string_flag','false_flag'):
        def test(self,mode=mode):rows.append(entry_case(mode))
        suite.addTest(type(mode,(unittest.TestCase,),{'runTest':test})())
    stream=io.StringIO();outcome=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    transcript=stream.getvalue();(a.out/'transcript.txt').write_text(transcript,encoding='utf-8');print(transcript)
    (a.out/'results.json').write_text(json.dumps(dict(scope='OFFLINE ONLY',testsRun=outcome.testsRun,passed=outcome.wasSuccessful(),cases=rows),indent=2),encoding='utf-8')
    with (a.out/'cases.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['case','expected','actual','passed','cliExitCode']);writer.writeheader()
        writer.writerows({k:r[k] for k in writer.fieldnames} for r in rows)
    return 0 if outcome.wasSuccessful() else 1
if __name__=='__main__':raise SystemExit(main())
