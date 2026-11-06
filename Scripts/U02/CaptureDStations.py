"""Guarded Windows input, actual server query/results, real-time bounded video."""
import argparse,json,time,cv2,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from DClient import DClient,mouse
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
record=json.loads(a.record.read_text(encoding='utf-8-sig'));c=DClient(record);writer=None
m=dict(process=record,completed=False,events=[],checks=[],frames=[],method='guarded SendInput, real Game-world native metrics; not Automation')
def check(name,condition):
 m['checks'].append(dict(check=name,result='PASS' if condition else 'FAIL'));assert condition,name
try:
 c.prepare();time.sleep(.3);bounds=c.bounds();l,t,r,b=bounds;cv2.setNumThreads(1)
 writer=cv2.VideoWriter(str(a.out/'Input-D.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(r-l,b-t));assert writer.isOpened()
 pending={}
 def reset(lane):c.console('U01FixtureReset CombatD'+str(lane))
 def attack(label,expected,hold=False):
  metrics=c.metrics();pending[label]=dict(before=metrics['combat']['geometryConfirmed'],accepted=metrics['combat']['accepted'],expected=expected)
  c.attack(True)
  if not hold:time.sleep(.06);c.attack(False)
 def verify(label):
  current=c.metrics();before=pending[label]
  check(label+' geometry result delta',current['combat']['geometryConfirmed']-before['before']==before['expected'])
  check(label+' exactly one action',current['combat']['accepted']-before['accepted']==1)
  check(label+' completed and locomotion restored',not current['combat']['locked'] and not current['attackPresented'])
  before['after']=current
 actions=[(.3,'reset multi',lambda:reset(1)),(1.8,'held attack multi',lambda:attack('MultiHold',2,True)),(2.4,'verify held attack',lambda:verify('MultiHold')),(2.5,'release LMB',lambda:c.attack(False)),
 (2.7,'second action multi',lambda:attack('MultiSecond',2)),(3.3,'verify second action',lambda:verify('MultiSecond')),
 (3.6,'reset full wall',lambda:reset(2)),(5.1,'full wall attack',lambda:attack('FullWall',0)),(5.7,'verify full wall',lambda:verify('FullWall')),
 (6.,'reset partial wall',lambda:reset(3)),(7.5,'partial wall attack',lambda:attack('PartialWallHead',1)),(8.1,'verify partial wall',lambda:verify('PartialWallHead')),
 (8.4,'reset corner',lambda:reset(4)),(9.9,'corner attack',lambda:attack('Corner',0)),(10.5,'verify corner',lambda:verify('Corner'))]
 m['utc']=datetime.now(timezone.utc).isoformat();start=time.perf_counter();i=0;encoded=0;previous=None;offset=0.
 while time.perf_counter()-start<11.3+offset:
  elapsed=time.perf_counter()-start
  while i<len(actions) and elapsed>=actions[i][0]+offset:
   scheduled,label,op=actions[i];c.guard();began=time.perf_counter()-start
   offset+=max(0.,began-(scheduled+offset));op();actual=time.perf_counter()-start;offset+=actual-began
   m['events'].append(dict(label=label,scheduled=scheduled,actual=actual,operationStart=began,offset=offset));i+=1
  c.guard();assert c.bounds()==bounds
  frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=bounds,all_screens=True)),cv2.COLOR_RGB2BGR);captured=time.perf_counter()-start
  while encoded/30<captured:writer.write(previous if previous is not None else frame);encoded+=1
  previous=frame;m['frames'].append(captured)
 m['timingPolicy']='planned gaps start after preceding operation completes; delayed capture/input shifts later events, never gameplay deadlines'
 m['captureSeconds']=time.perf_counter()-start;m['videoSeconds']=encoded/30;m['encodedFrames']=encoded;m['encodedFPS']=30;m['stages']=pending
 check('Video real-time within one output frame',abs(m['videoSeconds']-m['captureSeconds'])<1/30+.01)
 check('All planned inputs performed',i==len(actions));m['completed']=True;m['finalMetrics']=c.metrics()
 ImageGrab.grab(bbox=bounds,all_screens=True).save(a.out/'Final.png')
except Exception as e:m['error']=str(e);raise
finally:
 if 'start' in locals():
  m.setdefault('captureSeconds',time.perf_counter()-start);m.setdefault('videoSeconds',encoded/30);m.setdefault('encodedFrames',encoded);m.setdefault('stages',pending)
 if writer:writer.release()
 c.finish();m['externalInputMethodRestored']=not c.ime
 (a.out/'input.json').write_text(json.dumps(m,indent=2))
print(json.dumps(dict(completed=m['completed'],checks=len(m['checks']),videoSeconds=m['videoSeconds'],wallSeconds=m['captureSeconds'])))
