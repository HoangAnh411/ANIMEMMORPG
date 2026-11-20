"""Offline harness checks. No game process, physical input or acceptance evidence."""
import ast,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import CaptureNumericR1b as runner
from R1bSession import Session,dodge_edges
from R1bContract import CASES,write,read

class FakeSession:
    failure=False
    def __init__(self,record):self.record=record;self.active=False;self.events=[];self.client=self
    def readiness(self):pass
    def setup(self,case):return {}
    def photo(self,path):assert not self.active;Path(path).write_bytes(b'fake')
    def begin(self,trial):self.active=True
    def wait(self,t):pass
    def action(self,case):
        if self.failure:raise RuntimeError('synthetic tool failure')
    def end(self,trial):
        self.active=False;p=Path(self.record['log']).parent/(trial+'.jsonl')
        raw=[dict(kind='frame',pid=123,source='native')];write(p,raw);return p,raw
    def finish(self):pass

class Harness(unittest.TestCase):
    def test_ordered_batch(self):
        for case,key in zip(CASES[2:6],'WSAD'):self.assertEqual(dodge_edges(case),[(key,True),('Shift',True)])
    def test_no_numeric_media_import(self):
        for name in ['CaptureNumericR1b.py','R1bClient.py','R1bSession.py']:
            tree=ast.parse(Path(__file__).with_name(name).read_text())
            for node in tree.body:
                if isinstance(node,(ast.Import,ast.ImportFrom)):
                    text=ast.unparse(node);self.assertFalse(any(x in text for x in ['cv2','PIL','numpy','ImageGrab']))
    def test_photo_denied_in_window(self):
        s=Session.__new__(Session);s.active=True
        with self.assertRaises(AssertionError):s.photo('forbidden.png')
    def execute(self,root,fps,status='PASS',failure=False):
        session=root/str(fps);session.mkdir();record=dict(purpose='NUMERIC',batchManifest=str(root/'manifest.json'),targetFPS=fps,pid=123,sourceSHA='native',log=str(session/'Game.log'))
        write(session/'process.json',record)
        m=dict(batchId='synthetic',isolationRoot=str(root),fpsOrder=[30,60,120],cases={c:dict(required=5 if c=='combo' else 3,limit=7 if c=='combo' else 5) for c in CASES})
        write(root/'manifest.json',m)
        def analyze(path,target,case):return dict(status='FAIL' if status=='FAIL' and case=='forward' else status if status!='FAIL' else 'PASS',gameplay={'pass_':case!='forward' or status!='FAIL'},cadence={'fps':fps,'within10Percent':1})
        with patch.object(runner,'frozen',return_value=m),patch.object(runner,'Session',FakeSession),patch.object(runner,'analyze',side_effect=analyze),patch.object(FakeSession,'failure',failure),patch('sys.argv',['test','--record',str(session/'process.json')]):runner.main()
        return read(root/'Runs/BATCH-LEDGER.json')
    def test_all_69_stop_on_quota(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'Runs').mkdir()
            for fps in [30,60,120]:ledger=self.execute(root,fps)
            self.assertEqual(len(ledger['trials']),69);self.assertEqual(ledger['completedCaps'],[30,60,120])
    def test_invalid_counts_to_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'Runs').mkdir();ledger=self.execute(root,30,'INVALID')
            self.assertEqual(len(ledger['trials']),37)
    def test_fail_stops_related_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'Runs').mkdir();self.execute(root,30,'FAIL');ledger=self.execute(root,60)
            self.assertEqual(len([t for t in ledger['trials'] if t['case']=='forward']),1)
    def test_tool_error_halts_and_counts_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'Runs').mkdir()
            with self.assertRaises(RuntimeError):self.execute(root,30,failure=True)
            ledger=read(root/'Runs/BATCH-LEDGER.json');self.assertTrue(ledger['halted']);self.assertEqual(len(ledger['trials']),1);self.assertEqual(ledger['trials'][0]['status'],'INVALID')

if __name__=='__main__':unittest.main(verbosity=2)
