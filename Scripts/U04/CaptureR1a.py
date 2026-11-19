"""R1a only. Fixed attempt budgets; numeric path never invokes media APIs in window."""
import argparse, ctypes, hashlib, json, time, traceback
from datetime import datetime, timezone
from pathlib import Path
from BClient import BClient, u, Input, Payload, Key, VK
from AnalyzeR1a import load, repro, idle, write_result

def main():
    p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True)
    p.add_argument('--mode',choices=['numeric','video'],default='numeric');a=p.parse_args()
    record=json.loads(a.record.read_text(encoding='utf-8-sig'));session=a.record.parent
    out=session/('R1a-'+a.mode);out.mkdir(exist_ok=False);c=BClient(record)
    events=[];ledger=dict(completed=False,acceptance=False,phase='R1a',mode=a.mode,process=record,
                          guardPeriodSeconds=.05,primaryClock='sampleEntryWall',trials=[])
    def clock():return dict(qpc=time.perf_counter(),nativeWall=time.perf_counter()+16777216.,utc=datetime.now(timezone.utc).isoformat())
    def wait(seconds):
        end=time.perf_counter()+seconds
        while time.perf_counter()<end:c.guard();time.sleep(min(.05,max(0,end-time.perf_counter())))
    def press(name,down):
        before=clock();c.press(name,down);events.append(dict(key=name,down=down,before=before,after=clock()))
    def command(text):
        before=clock();c.console(text);events.append(dict(console=text,before=before,after=clock()))
    def photo(path):
        # Called exclusively before U04B begin or after U04B end.
        from PIL import ImageGrab
        ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(path)
    def save():write_result(out/'LEDGER.json',ledger)
    def batch(edges):
        values=[]
        for key,down in edges:
            values.append(Input(type=1,payload=Payload(key=Key(vk=0,scan=0x2a,flags=8|(0 if down else 2)) if key=='Shift' else Key(vk=VK[key],flags=0 if down else 2))))
        c.guard();before=clock();sent=u.SendInput(len(values),(Input*len(values))(*values),ctypes.sizeof(Input))
        events.append(dict(batch=edges,sent=sent,before=before,after=clock()));assert sent==len(values)
        for key,down in edges:
            if down:c.held.add(key)
            else:c.held.discard(key)
    try:
        c.focus();seen=c.probe_w()
        if seen!='W':c.toggle_ime();c.ime=True;seen=c.probe_w()
        assert seen=='W'
        if c.metrics()['controlState']!=0:
            b=c.metrics()['menuButtons']['Resume'];c.click(round(b['x']),round(b['y']));wait(.5)
        command('U04B prepare');wait(.8);command('U04B begin r1a-readiness');wait(.35)
        before=c.metrics();press('W',True);wait(.35);press('W',False);wait(.35);after=c.metrics();command('U04B end')
        assert before['pawn']==after['pawn'] and before['capsuleCenterWorldCm']!=after['capsuleCenterWorldCm']
        frames=[r for r in load(session/'Raw/r1a-readiness.jsonl') if r['kind']=='frame']
        assert len(frames)>4 and all(b['frame']==x['frame']+1 and b['sampleEntryWall']>x['sampleEntryWall'] for x,b in zip(frames,frames[1:]))
        ready=dict(completed=True,processIdentity=c.processIdentity,before=before,after=after,frames=frames)
        write_result(out/'READINESS.json',ready)
        # Required placement tool reads a session-local readiness. No Editor mutation before it.
        write_result(session/'READINESS.json',ready)
        wait(30)
        if a.mode=='video':
            trial=f"fps{record['targetFPS']}-illustration";directory=out/trial;directory.mkdir()
            command('U04B prepare');wait(.8);photo(directory/'Before.png')
            import cv2,numpy as np
            from PIL import ImageGrab
            cv2.setNumThreads(1);video=cv2.VideoWriter(str(directory/'Illustration.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert video.isOpened()
            command('U04B begin '+trial);batch([('W',True),('Shift',True)])
            start=time.perf_counter();encoded=0
            try:
                while time.perf_counter()-start<2:
                    c.guard();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=c.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR)
                    cv2.putText(frame,trial+' ILLUSTRATIVE ONLY | video30FPS',(12,28),cv2.FONT_HERSHEY_SIMPLEX,.55,(0,255,255),1)
                    while encoded/30<time.perf_counter()-start:video.write(frame);encoded+=1
                    if time.perf_counter()-start>.10 and c.held:press('Shift',False);press('W',False)
                    time.sleep(.025)
            finally:video.release()
            command('U04B end');photo(directory/'After.png')
            ledger['trials'].append(dict(trial=trial,purpose='ILLUSTRATION_ONLY',acceptance=False,encodedFrames=encoded))
        else:
            for case in ('w-shift','shift-w','w-up-shift','previous'):
                qualified=0
                for attempt in range(1,5):
                    trial=f"fps{record['targetFPS']}-{case}-{attempt}";directory=out/trial;directory.mkdir();events=[]
                    ledger['activeTrial']=dict(trial=trial,case=case,attempt=attempt,status='IN_PROGRESS');save()
                    command('U04B prepare');wait(.8);write_result(directory/'SETUP.json',c.metrics());photo(directory/'Before.png')
                    command('U04B begin '+trial);wait(.6)
                    if case=='previous':press('W',True);wait(.12);batch([('Shift',True)])
                    else:batch({'w-shift':[('W',True),('Shift',True)],'shift-w':[('Shift',True),('W',True)],'w-up-shift':[('W',True),('W',False),('Shift',True)]}[case])
                    wait(.10)
                    if 'Shift' in c.held:press('Shift',False)
                    if 'W' in c.held:press('W',False)
                    wait(.8);command('U04B end');photo(directory/'After.png')
                    raw=session/'Raw'/(trial+'.jsonl')
                    try:result=repro(load(raw),case,record['targetFPS'])
                    except (AssertionError,ValueError,KeyError,StopIteration) as error:
                        result=dict(status='INVALID',acceptance=False,purpose='REPRO_ONLY',preconditionReasons=[repr(error)],gameplayReasons=[])
                    write_result(directory/'INPUT.json',dict(events=events));write_result(directory/'ASSERTIONS.json',result)
                    ledger['trials'].append(dict(trial=trial,case=case,attempt=attempt,status=result['status'],raw=str(raw),rawSHA256=hashlib.sha256(raw.read_bytes()).hexdigest(),assertions=str(directory/'ASSERTIONS.json')));save()
                    ledger.pop('activeTrial',None)
                    print(trial,result['status'],result['preconditionReasons'],result.get('gameplayReasons'),flush=True)
                    if result['status']=='FAIL':raise RuntimeError('Valid-precondition gameplay FAIL: '+trial)
                    if result['status']=='PASS':qualified+=1
                    if qualified==2:break
                if qualified<2:ledger.setdefault('incompleteCases',[]).append(case)
            for index in range(1,4):
                trial=f"fps{record['targetFPS']}-idle-{index}";directory=out/trial;directory.mkdir();events=[]
                command('U04B prepare');wait(.8);photo(directory/'Before.png');command('U04B begin '+trial)
                # Sleep schedules capture length only. Native world samples define exact 15s and bracketing frames.
                wait(18);command('U04B end');photo(directory/'After.png')
                raw=session/'Raw'/(trial+'.jsonl');result=idle(load(raw),record['targetFPS'])
                write_result(directory/'INPUT.json',dict(events=events));write_result(directory/'ASSERTIONS.json',result)
                ledger['trials'].append(dict(trial=trial,status=result['status'],purpose='METHOD_ONLY',raw=str(raw),rawSHA256=hashlib.sha256(raw.read_bytes()).hexdigest(),assertions=str(directory/'ASSERTIONS.json')));save()
                print(trial,result['status'],result['primary']['fps'],result['primary']['within10Percent'],flush=True)
        ledger['completed']=True
    except Exception as e:
        ledger.update(error=repr(e),traceback=traceback.format_exc())
        try:c.guard();c.console('U04B end')
        except Exception as close:ledger['flushError']=repr(close)
        raise
    finally:
        c.finish();ledger['remainingEvents']=events
        if ledger.get('activeTrial'):
            active=ledger['activeTrial'];active.update(status='INVALID',reason=ledger.get('error','aborted capture'))
            write_result(out/active['trial']/'ABORTED-INPUT.json',dict(events=events,trial=active))
        save()

if __name__=='__main__':main()
