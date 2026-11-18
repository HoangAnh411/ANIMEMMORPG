"""Fixed diagnostic inventory. Never imports the acceptance analyzer or sends combo attacks."""
import argparse,ctypes,json,time,threading,traceback
from datetime import datetime,timezone
from pathlib import Path
import cv2,numpy as np
from PIL import ImageGrab
from BClient import BClient,u,Input,Payload,Key,VK

def main():
    p=argparse.ArgumentParser();p.add_argument('--record',required=True,type=Path);p.add_argument('--mode',choices=['input','timing'],required=True);a=p.parse_args()
    record=json.loads(a.record.read_text(encoding='utf-8-sig'));session=a.record.parent;out=session/'Diagnostic';out.mkdir(exist_ok=False)
    c=BClient(record);cv2.setNumThreads(1);events=[];stop=threading.Event();worker=None;writer=None
    ledger=dict(status='DIAGNOSTIC_ONLY',acceptance=False,completed=False,mode=a.mode,process=record,windows=[])
    def clock():return dict(wall=time.perf_counter()+16777216.,utc=datetime.now(timezone.utc).isoformat())
    def wait(duration,poll=.005):
        end=time.perf_counter()+duration
        while time.perf_counter()<end:c.guard();time.sleep(min(poll,max(0,end-time.perf_counter())))
    def press(key,down):
        before=clock();c.press(key,down);events.append(dict(key=key,down=down,before=before,after=clock()))
    def command(text):
        before=clock();c.console(text);events.append(dict(console=text,before=before,after=clock()))
    def start_video(path,label):
        nonlocal writer,worker
        stop.clear();writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert writer.isOpened()
        def run():
            origin=time.perf_counter();encoded=0;previous=None
            while not stop.is_set():
                try:
                    c.guard();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=c.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR)
                    cv2.putText(frame,label+' DIAGNOSTIC ONLY | video30FPS',(10,28),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,255),1)
                    now=time.perf_counter()-origin
                    while encoded/30<now:writer.write(previous if previous is not None else frame);encoded+=1
                    previous=frame
                except Exception as e:events.append(dict(videoError=repr(e),at=clock()))
                stop.wait(.025)
        worker=threading.Thread(target=run);worker.start()
    def end_video():
        nonlocal writer,worker
        stop.set()
        if worker:worker.join();worker=None
        if writer:writer.release();writer=None
    try:
        c.focus();seen=c.probe_w()
        if seen!='W':c.toggle_ime();c.ime=True;seen=c.probe_w()
        assert seen=='W'
        if c.metrics()['controlState']!=0:
            b=c.metrics()['menuButtons']['Resume'];c.click(round(b['x']),round(b['y']));wait(.4)
        command('U04B prepare');wait(.7);command('U04B begin diagnostic-readiness');wait(.35)
        before=c.metrics();press('W',True);wait(.35);press('W',False);wait(.35);after=c.metrics();command('U04B end')
        assert before['pawn']==after['pawn'] and before['capsuleCenterWorldCm']!=after['capsuleCenterWorldCm']
        native=[json.loads(line) for line in (session/'Raw/diagnostic-readiness.jsonl').read_text(encoding='utf-8-sig').splitlines()]
        frames=[r for r in native if r['kind']=='frame'];assert len(frames)>4 and all(b['frame']==a['frame']+1 and b['wall']>a['wall'] for a,b in zip(frames,frames[1:]))
        readiness=dict(completed=True,processIdentity=c.processIdentity,before=before,after=after,frames=frames)
        (out/'READINESS.json').write_text(json.dumps(readiness,indent=2),encoding='utf-8');wait(30)
        if a.mode=='input':
            inventory=[(f'{variant}-{i}',variant) for i in range(1,5) for variant in ['legacy','batch','previous']]
        else:
            order=['passive','poll','video','video','passive','poll','poll','video','passive'];inventory=[(f'{mode}-{i+1}',mode) for i,mode in enumerate(order)]
        for trial,mode in inventory:
            directory=out/trial;directory.mkdir();events=[];command('U04B prepare'+(' combo' if a.mode=='timing' else ''));wait(.8)
            (directory/'SETUP.json').write_text(json.dumps(c.metrics(),indent=2),encoding='utf-8')
            ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(directory/'Setup.png')
            command('U04B begin '+trial)
            if a.mode=='input' or mode=='video':start_video(directory/'Video.mp4',trial)
            wait(1.5)
            if a.mode=='input':
                if mode=='batch':
                    c.guard();before=clock()
                    batch=(Input*2)(Input(type=1,payload=Payload(key=Key(vk=VK['W']))),Input(type=1,payload=Payload(key=Key(vk=0,scan=0x2a,flags=8))))
                    assert u.SendInput(2,batch,ctypes.sizeof(Input))==2;c.held.update({'W','Shift'})
                    events.append(dict(batch=['W down','Shift down'],before=before,after=clock()))
                else:
                    press('W',True)
                    if mode=='previous':wait(.10) # membership is verified from raw previous-frame held state, not assumed from delay
                    press('Shift',True)
                wait(.035);press('Shift',False);press('W',False);wait(.75)
            else:
                # A fixed no-action15-world-second slice is selected from retained native samples after capture.
                wait(16.5,.05 if mode=='passive' else .005)
            end_video();command('U04B end');wait(.2)
            raw=session/'Raw'/(trial+'.jsonl');assert raw.exists()
            (directory/'INPUT.json').write_text(json.dumps(dict(trial=trial,mode=mode,acceptance=False,events=events),indent=2),encoding='utf-8')
            ledger['windows'].append(dict(trial=trial,mode=mode,raw=str(raw.resolve()),input=str((directory/'INPUT.json').resolve())))
            (out/'LEDGER.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8');print(trial,'RECORDED_DIAGNOSTIC_ONLY',flush=True)
        ledger['completed']=True
    except Exception as e:
        ledger.update(error=repr(e),traceback=traceback.format_exc());end_video()
        try:c.guard();c.console('U04B end')
        except Exception as close_error:ledger['flushError']=repr(close_error)
        raise
    finally:
        end_video();c.finish();ledger['remainingEvents']=events
        (out/'LEDGER.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8')

if __name__=='__main__':main()
