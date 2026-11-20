"""Guarded R1b input/fixture session. Numeric windows buffer events in memory.
Media API is available only in photo(), guarded outside every native window.
"""
import ctypes,json,time
from datetime import datetime,timezone
from pathlib import Path
from R1bClient import R1bClient,u,Input,Payload,Key,VK
from R1bContract import frozen,write
from AnalyzeR1 import PROFILE,cadence

def clock():return dict(qpcSeconds=time.perf_counter(),nativeWall=time.perf_counter()+16777216.,utc=datetime.now(timezone.utc).isoformat())
def dodge_edges(case):return [({'forward':'W','back':'S','left':'A','right':'D'}[case],True),('Shift',True)]

class Session:
    def __init__(self,record):
        self.record=record;self.client=R1bClient(record);self.path=Path(record['log']).parent
        self.contract=frozen(record['batchManifest']);self.active=False;self.events=[]
    def wait(self,seconds):
        end=time.perf_counter()+seconds
        while time.perf_counter()<end:self.client.guard();time.sleep(min(.05,max(0,end-time.perf_counter())))
    def command(self,text):
        before=clock();self.client.console(text);self.events.append(dict(console=text,before=before,after=clock()))
    def press(self,key,down):
        before=clock()
        self.client.attack(down) if key=='LMB' else self.client.press(key,down)
        self.events.append(dict(key=key,down=down,before=before,after=clock()))
    def tap(self,key):self.press(key,True);self.wait(.035);self.press(key,False)
    def batch(self,edges):
        values=[Input(type=1,payload=Payload(key=Key(vk=0,scan=0x2a,flags=8|(0 if down else 2)) if key=='Shift' else Key(vk=VK.get(key,ord(key) if len(key)==1 else 0),flags=0 if down else 2))) for key,down in edges]
        self.client.guard();before=clock();sent=u.SendInput(len(values),(Input*len(values))(*values),ctypes.sizeof(Input))
        self.events.append(dict(batch=edges,sent=sent,before=before,after=clock()));assert sent==len(values)
        for key,down in edges:
            if down:self.client.held.add(key)
            else:self.client.held.discard(key)
    def photo(self,path):
        assert not self.active,'No screenshot/media inside native capture'
        self.client.guard()
        from PIL import ImageGrab
        ImageGrab.grab(bbox=self.client.bounds(),all_screens=True).save(path)
    def closed(self,trial):
        path=self.path/'Raw'/(trial+'.jsonl');deadline=time.perf_counter()+30
        while time.perf_counter()<deadline:
            self.client.guard()
            try:
                rows=[json.loads(l) for l in path.read_text(encoding='utf-8-sig').splitlines()]
                if rows and rows[-1]['kind']=='end':return path,rows
            except (PermissionError,FileNotFoundError,json.JSONDecodeError):pass
            time.sleep(.05)
        raise RuntimeError('Tool error: native closed-buffer timeout')
    def begin(self,trial):
        assert not self.active;self.active=True
        self.command('U04B begin '+trial)
    def end(self,trial):
        self.command('U04B end');path,raw=self.closed(trial);self.active=False;return path,raw
    def action(self,case):
        if case in ('walk','sprint'):
            if case=='sprint':self.press('Ctrl',True)
            self.press('W',True);self.wait(12.5);self.press('W',False)
            if case=='sprint':self.press('Ctrl',False)
            self.wait(.3)
        elif case=='combo':
            start=time.perf_counter();self.tap('LMB')
            self.wait(max(0,.32-(time.perf_counter()-start)));self.tap('LMB')
            self.wait(max(0,.77-(time.perf_counter()-start)));self.tap('LMB');self.wait(1.25)
        else:
            self.batch(dodge_edges(case));self.wait(.10)
            self.press('Shift',False);self.press(dodge_edges(case)[0][0],False);self.wait(.85)
    def setup(self,case):
        assert not self.active;frozen(self.record['batchManifest'])
        self.client.guard();assert not self.client.held and not self.client.mouse_held
        self.command('U04B prepare'+(' combo' if case=='combo' else ''));self.wait(.8)
        metrics=self.client.metrics();assert metrics['controlState']==0 and metrics['windowActive']
        return metrics
    def readiness(self):
        c=self.client;c.focus();observed=c.probe_w()
        if observed!='W':c.toggle_ime();c.ime=True;observed=c.probe_w()
        assert observed=='W'
        if c.metrics()['controlState']!=0:
            b=c.metrics()['menuButtons']['Resume'];c.click(round(b['x']),round(b['y']));self.wait(.5)
        assert c.metrics()['controlState']==0
        self.command('U04B prepare');self.wait(.8);self.begin('r1b-readiness');self.wait(.35)
        samples=[]
        for _ in range(4):samples.append(c.metrics());self.wait(.3)
        assert len({r['pawn'] for r in samples})==1 and all(b['worldSeconds']>a['worldSeconds'] for a,b in zip(samples,samples[1:]))
        before=c.metrics();self.press('W',True);self.wait(.35);self.press('W',False);self.wait(.35);after=c.metrics()
        assert before['pawn']==after['pawn'] and before['capsuleCenterWorldCm']!=after['capsuleCenterWorldCm']
        path,raw=self.end('r1b-readiness');frames=[r for r in raw if r['kind']=='frame'];assert len(frames)>4
        quality=cadence(frames,self.record['targetFPS']);timing={'mean FPS outside 5%','fewer than 95% intervals within 10%','frame exceeds two periods'}
        assert not [r for r in quality['reasons'] if r not in timing],quality
        assert all(r['pid']==self.record['pid'] and r['source']==self.record['sourceSHA'] and r['worldType']==1 and r['netMode']==0 for r in frames)
        assert all(r['smoothing']==self.contract['expectedSmoothing'] and r['frame']==r['frameBeginCounter']==r['worldBeginCounter'] for r in frames)
        write(self.path/'READINESS.json',dict(completed=True,processIdentity=c.processIdentity,process=self.record,samples=samples,before=before,after=after,raw=str(path),quality=quality,inputEvents=self.events))
        self.events=[];self.wait(30) # launch warmup AND cap settling; excluded from trials
        write(self.path/'WARMUP.json',dict(completed=True,secondsAfterReadiness=30,capStableMinimumSeconds=10,at=clock()))
