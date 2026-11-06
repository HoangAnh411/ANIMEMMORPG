"""Ten guarded focus transfers, no gameplay/smoothing modifications."""
import argparse,json,time,threading,ctypes as ct,cv2,numpy as np
from ctypes import wintypes as wt
from PIL import ImageGrab
from pathlib import Path
from datetime import datetime,timezone
from FClient import FClient as Client,mouse,u
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--label',default='Baseline');p.add_argument('--count',type=int,default=10);p.add_argument('--seconds',type=float,default=15);p.add_argument('--single',action='store_true');a=p.parse_args();out=a.session/a.label;out.mkdir(exist_ok=False)
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));clients=[Client(r) for r in records if r['role']!='Server'];events=[];trials=[];done=False

def utc():return datetime.now(timezone.utc).isoformat()
def event(action,**kw):events.append(dict(utc=utc(),wall=time.perf_counter(),action=action,**kw))
def save():(out/'input.json').write_text(json.dumps({'completed':done,'sourceSHA':records[0]['sourceSHA'],'windowSeconds':a.seconds,'count':a.count,'trials':trials,'events':events,'method':'Real SendInput; raw native per-frame and 5Hz control metrics retained in session; no added wait for FPS after activation'},indent=2))
active=None
stop=threading.Event();video=[];windows=[];errors=[];start=time.perf_counter();startutc=datetime.now(timezone.utc).isoformat()
u.IsIconic.argtypes=[wt.HWND];u.IsWindowVisible.argtypes=[wt.HWND]
editors=json.loads((a.session/'original-editor-windows.json').read_text(encoding='utf-8-sig'));editors=editors if isinstance(editors,list) else [editors]
writer=None

def capture():
 global writer
 boxes=[c.bounds() for c in clients];box=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes));cv2.setNumThreads(1);writer=cv2.VideoWriter(str(out/'Focus.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),15,(box[2]-box[0],box[3]-box[1]));encoded=0;previous=None
 try:
  assert writer.isOpened()
  while not stop.is_set():
   before=time.perf_counter();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=box,all_screens=True)),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
   while encoded/15<now:writer.write(previous if previous is not None else frame);encoded+=1
   previous=frame;video.append(dict(t=now,acquireMs=(time.perf_counter()-before)*1000))
   windows.append(dict(utc=utc(),t=now,foreground=int(u.GetForegroundWindow() or 0),editors=[dict(pid=e['pid'],hwnd=e['hwnd'],iconic=bool(u.IsIconic(e['hwnd'])),visible=bool(u.IsWindowVisible(e['hwnd']))) for e in editors]));stop.wait(max(0,1/15-(time.perf_counter()-before)))
  while encoded/15<time.perf_counter()-start:writer.write(previous);encoded+=1
 except Exception as e:errors.append(str(e))
 finally:writer.release();(out/'video.json').write_text(json.dumps(dict(startUTC=startutc,seconds=time.perf_counter()-start,frames=encoded,fps=15,samples=video,errors=errors)));(out/'windows.json').write_text(json.dumps(windows))
thread=threading.Thread(target=capture);thread.start()
try:
 for c in clients:
  active=c;c.prepare();c.console('U01NetFixture reset');c.release()
 active=clients[0];active.prepare();time.sleep(3)
 for index in range(a.count):
  source=clients[index%len(clients)];target=clients[(index+1)%len(clients)];assert active is source
  event('pre-window',index=index,role=source.record['role']);time.sleep(4)
  source.press('W',True);event('source-key-down',index=index,pid=source.pid);time.sleep(.8)
  event('focus-request',index=index,source=source.pid,target=target.pid);t={'index':index,'from':source.record['role'],'to':target.record['role'],'focusUTC':utc(),'beforeTarget':target.metrics()};trials.append(t);save()
  source.release();active=target
  if a.single:
   u.ShowWindow(target.hwnd,6);time.sleep(.3)
  target.focus();event('focus-return',index=index,pid=target.pid,metrics=target.metrics());t['activatedUTC']=utc()
  # Preserve AwaitingResume; a real explicit Resume click is required.
  target.click(450,241);event('resume-clicked',index=index,pid=target.pid);t['resumeUTC']=utc()
  time.sleep(.05);target.press('W',True);t['keyUTC']=utc();event('target-key-down',index=index,pid=target.pid)
  time.sleep(1.2);target.press('W',False);event('target-key-up',index=index,pid=target.pid)
  time.sleep(.35);target.press('S',True);event('target-second-down',index=index,pid=target.pid);time.sleep(1.2);target.press('S',False)
  remaining=a.seconds-(datetime.now(timezone.utc)-datetime.fromisoformat(t['focusUTC'])).total_seconds()
  if remaining>0:time.sleep(remaining)
  t['endUTC']=utc();t['afterTarget']=target.metrics();event('post-window',index=index,pid=target.pid);save();print(a.label,index+1,'complete',flush=True)
 done=True
finally:
 for c in clients:
  if c.ime:c.focus()
  c.finish()
 stop.set();thread.join();save()
