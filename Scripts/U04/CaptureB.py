"""Guarded Windows inputs and media. Python sleeps only schedule input; analysis uses raw world time."""
import argparse, json, time, threading, traceback
from datetime import datetime,timezone
from pathlib import Path
import cv2
import numpy as np
from PIL import ImageGrab
from BClient import BClient
from AnalyzeB import analyze,vector

def main():
    p=argparse.ArgumentParser();p.add_argument('--record',required=True,type=Path);p.add_argument('--cases',nargs='+',default=['walk','sprint','forward','back','left','right','combo']);a=p.parse_args()
    record=json.loads(a.record.read_text(encoding='utf-8-sig'));session=a.record.parent
    out=session/'Capture';out.mkdir(exist_ok=False);c=BClient(record);cv2.setNumThreads(1)
    ledger={'process':record,'completed':False,'trials':[]};events=[];stop=threading.Event();video=None;worker=None
    def clock():return dict(qpcSeconds=time.perf_counter(),nativeWall=time.perf_counter()+16777216.,utc=datetime.now(timezone.utc).isoformat())
    def press(key,down):
        before=clock();c.attack(down) if key=='LMB' else c.press(key,down)
        events.append(dict(key=key,down=down,before=before,after=clock()))
    def tap(key):press(key,True);wait(.035);press(key,False)
    def wait(seconds):
        deadline=time.perf_counter()+seconds
        while time.perf_counter()<deadline:c.guard();time.sleep(min(.005,max(0,deadline-time.perf_counter())))
    def console(text):
        events.append(dict(console=text,before=clock()));c.console(text);events[-1]['after']=clock()
    def movie(path,label):
        nonlocal video,worker
        stop.clear();video=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert video.isOpened()
        def run():
            start=time.perf_counter();encoded=0;previous=None
            while not stop.is_set():
                try:
                    c.guard();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=c.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR)
                    cv2.putText(frame,label+' | video30FPS, game cadence in raw', (15,30),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,255),1)
                    now=time.perf_counter()-start
                    while encoded/30<now:video.write(previous if previous is not None else frame);encoded+=1
                    previous=frame
                except Exception as e:events.append(dict(mediaError=repr(e),at=clock()))
                stop.wait(.025)
        worker=threading.Thread(target=run);worker.start()
    def end_movie():
        nonlocal video,worker
        stop.set()
        if worker:worker.join();worker=None
        if video:video.release();video=None
    try:
        c.focus();observed=c.probe_w()
        if observed!='W':c.toggle_ime();c.ime=True;observed=c.probe_w()
        assert observed=='W'
        if c.metrics()['controlState']!=0:
            b=c.metrics()['menuButtons']['Resume'];c.click(round(b['x']),round(b['y']));wait(.5)
        assert c.metrics()['controlState']==0
        console('U04B prepare');wait(.8)
        console('U04B begin readiness');wait(.3)
        samples=[]
        for _ in range(4):samples.append(c.metrics());wait(.3)
        assert all(y['worldSeconds']>x['worldSeconds'] for x,y in zip(samples,samples[1:]))
        assert len({s['pawn'] for s in samples})==1
        before=c.metrics();press('W',True);wait(.35);press('W',False);wait(.3);after=c.metrics()
        assert before['pawn']==after['pawn'] and before['capsuleCenterWorldCm']!=after['capsuleCenterWorldCm']
        console('U04B end');wait(.3)
        readiness_frames=[json.loads(x) for x in (session/'Raw/readiness.jsonl').read_text(encoding='utf-8').splitlines() if json.loads(x)['kind']=='frame']
        assert len(readiness_frames)>=4
        assert all(y['frame']==x['frame']+1 and y['wall']>x['wall'] for x,y in zip(readiness_frames,readiness_frames[1:]))
        readiness=dict(completed=True,frames=readiness_frames,processIdentity=c.processIdentity,samples=samples,physicalInputBefore=before,physicalInputAfter=after)
        (out/'READINESS.json').write_text(json.dumps(readiness,indent=2),encoding='utf-8')
        # Actual launch warmup is at least30 seconds; no measured window uses this sleep as a clock.
        wait(30)
        for case in a.cases:
            need=5 if case=='combo' else 3;limit=7 if case=='combo' else 5;passed=0
            for attempt in range(1,limit+1):
                trial=f"fps{record['targetFPS']}-{case}-{attempt}";trialout=out/trial;trialout.mkdir()
                events=[];console('U04B prepare'+(' combo' if case=='combo' else ''));wait(.8)
                (trialout/'FixtureState.json').write_text(json.dumps(c.metrics(),indent=2),encoding='utf-8')
                ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(trialout/'Fixture.png')
                console('U04B begin '+trial);wait(.4);movie(trialout/'Video.mp4',trial)
                if case in ('walk','sprint'):
                    if case=='sprint':press('Ctrl',True)
                    press('W',True);wait(12);press('W',False)
                    if case=='sprint':press('Ctrl',False)
                    wait(.3)
                elif case=='combo':
                    start=time.perf_counter();tap('LMB')
                    wait(max(0,.32-(time.perf_counter()-start)));tap('LMB')
                    wait(max(0,.77-(time.perf_counter()-start)));tap('LMB');wait(1.1)
                else:
                    key={'forward':'W','back':'S','left':'A','right':'D'}[case]
                    # Consecutive real edges before a game frame, so direction is held at admission without pre-walking.
                    press(key,True);press('Shift',True);wait(.035);press('Shift',False);press(key,False);wait(.65)
                end_movie();console('U04B end');wait(.3)
                raw=session/'Raw'/(trial+'.jsonl');assert raw.exists(),'collector did not flush closed capture'
                result=analyze(raw,record['targetFPS'],case)
                frame_rows=[json.loads(x) for x in raw.read_text(encoding='utf-8').splitlines() if json.loads(x)['kind']=='frame']
                if any(r['pid']!=record['pid'] or r['source']!=record['sourceSHA'] for r in frame_rows):result.update(status='INVALID',reason='process/source mismatch')
                result['trial']=trial;result['inputEvents']=events;result['process']=record
                (trialout/'ASSERTIONS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
                ledger['trials'].append(result);(out/'LEDGER.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8')
                print(trial,result['status'],result.get('cadence',{}).get('fps'),flush=True)
                if result['status']=='FAIL':raise RuntimeError('Gameplay FAIL; affected gate stopped: '+trial)
                if result['status']=='PASS':passed+=1
                if passed==need:break
            ledger.setdefault('counts',{})[case]={'passed':passed,'required':need,'attempts':attempt}
        ledger['completed']=True
    except Exception as e:
        end_movie()
        try:c.guard();c.console('U04B end')
        except Exception as flush_error:ledger['flushError']=repr(flush_error)
        ledger['error']=repr(e);ledger['traceback']=traceback.format_exc();raise
    finally:
        end_movie();c.finish();ledger['remainingEvents']=events
        (out/'LEDGER.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8')

if __name__=='__main__':main()
