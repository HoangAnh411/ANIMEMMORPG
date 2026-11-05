"""Continuous 120/300 second real-input measurement, focus split into 60s blocks."""
import argparse,json,time
from datetime import datetime,timezone
from pathlib import Path
import cv2,numpy as np
from PIL import ImageGrab
from F60Input import Client,mouse,key
cv2.setNumThreads(1)
p=argparse.ArgumentParser();p.add_argument('--stage',choices=('F','G'),default='F');p.add_argument('--session',type=Path,required=True);p.add_argument('--seconds',type=int,choices=(120,300),default=120);a=p.parse_args()
def utc():return datetime.now(timezone.utc).isoformat()
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));clients=[Client(r,stage=a.stage) for r in records if r['role']!='Server'];events=[];writers={};video_times={};last_frames={};active=None;started=None;completed=False
def save():
 (a.session/'input.json').write_text(json.dumps({'start':started,'end':utc(),'requestedSeconds':a.seconds,'completed':completed,'events':events,'videos':video_times,'method':'Guarded Win32 real input; continuous wall interval, includes focus/Resume transitions; not transform-to-photon latency'},indent=2),encoding='utf8',newline='\n')
def mark(action,**kwargs):events.append(dict(action=action,utc=utc(),elapsed=time.perf_counter()-start,**kwargs))
def schedule():
 e=[]
 for i in range(10):
  for name,t,d in [('W',3+5*i,True),('W',4.2+5*i,False),('S',5+5*i,True),('S',6.2+5*i,False)]:e.append((t,'key',name,d))
 e += [(18,'key','Ctrl',True),(42,'key','Ctrl',False),(23.3,'key','Space',True),(23.9,'key','Space',False),(33.3,'key','Space',True),(33.9,'key','Space',False),(52,'key','V',True),(52.2,'key','V',False),(54,'key','Escape',True),(54.2,'key','Escape',False),(56,'resume','',False)]
 if len(clients)==2:e.append((58.5,'observer','',False))
 return sorted(e)
try:
 # Setup is outside the measured interval, identical reset/road for all caps.
 for c in clients:
  active=c;c.prepare();c.console('U01NetFixture reset');time.sleep(.4);c.finish()
 if len(clients)==2:
  active=clients[1];active.prepare();mouse(1,-430,0);time.sleep(.3);active.finish()
 active=clients[0];active.prepare()
 started=utc();start=time.perf_counter();phase=-1;pending=[];next_video=0
 while True:
  elapsed=time.perf_counter()-start
  if elapsed>=a.seconds:break
  current=int(elapsed//60)
  if current!=phase:
   if phase>=0:
    active.finish();active=clients[current%len(clients)];active.prepare()
    if len(clients)==2:mouse(1,-430 if active is clients[0] else 430,0)
   phase=current;pending=schedule();mark('phase',phase=phase,role=active.record['role'],pid=active.pid,metrics=active.metrics())
   boxes=[c.bounds() for c in clients];width=900*len(clients);path=a.session/f'Phase{phase}.mp4';writers[phase]=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),30,(width,540));assert writers[phase].isOpened();video_times[phase]={'frames':0,'wallTimes':[],'duplicates':0,'seconds':8,'encodedHz':30};next_video=0
  active.guard();local=time.perf_counter()-start-phase*60
  while pending and local>=pending[0][0]:
   nominal,action,name,down=pending.pop(0)
   if action=='key':active.press(name,down)
   elif action=='resume':active.click(450,241)
   elif action=='observer':mouse(1,430 if active is clients[0] else -430,0)
   mark(action,role=active.record['role'],pid=active.pid,key=name,down=down,phase=phase,nominal=nominal)
  if local<8 and local>=next_video:
   # Only a short excerpt, same 30Hz capture in every configuration.
   lo=min(b[0] for b in boxes);top=min(b[1] for b in boxes);hi=max(b[2] for b in boxes);bottom=max(b[3] for b in boxes)
   frame=np.asarray(ImageGrab.grab(bbox=(lo,top,hi,bottom),all_screens=True));frame=np.concatenate([frame[b[1]-top:b[3]-top,b[0]-lo:b[2]-lo,:3] for b in boxes],axis=1)
   v=video_times[phase];v.setdefault('firstLocalSecond',local)
   while phase in last_frames and v['frames']<int((local-v['firstLocalSecond'])*30):writers[phase].write(last_frames[phase]);v['frames']+=1;v['duplicates']+=1
   last_frames[phase]=cv2.cvtColor(frame,cv2.COLOR_RGB2BGR);writers[phase].write(last_frames[phase]);v['frames']+=1;v['wallTimes'].append(time.perf_counter()-start);next_video=local+1/30
  elif local>=8 and phase in writers:writers.pop(phase).release()
  time.sleep(.002)
 completed=True
finally:
 if active:active.finish()
 for v in writers.values():v.release()
 if started:save()
print(json.dumps({'completed':completed,'seconds':a.seconds,'session':str(a.session)}),flush=True)
