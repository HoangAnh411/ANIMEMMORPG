"""Selected-action corner reconstruction with guarded real input and wall-time video."""
import argparse,json,time,cv2,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from DClient import DClient,mouse
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
r=json.loads(a.record.read_text(encoding='utf-8-sig'));c=DClient(r);writer=None
m=dict(process=r,completed=False,stages=[],frames=[],events=[],checks=[])
def check(label,v):m['checks'].append(dict(check=label,result='PASS' if v else 'FAIL'));assert v,label
try:
 c.prepare();bounds=c.bounds();l,t,rr,b=bounds;cv2.setNumThreads(1)
 writer=cv2.VideoWriter(str(a.out/'Corner.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(rr-l,b-t));assert writer.isOpened()
 start=time.perf_counter();m['utc']=datetime.now(timezone.utc).isoformat();encoded=0;previous=None
 def grab():
  global encoded,previous
  c.guard();assert c.bounds()==bounds
  frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=bounds,all_screens=True)),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
  while encoded/30<now:writer.write(previous if previous is not None else frame);encoded+=1
  previous=frame;m['frames'].append(now)
 def wait(seconds):
  end=time.perf_counter()+seconds
  while time.perf_counter()<end:grab()
 for label,command,expected in [('Action66Open','U02CornerCase open',1),('AllBlocked','U02CornerCase blocked',0),('PartialHead','U01FixtureReset CombatD3',1),('Outside','U02CornerCase outside',0)]:
  c.console(command);wait(.8)
  if label=='PartialHead':c.console('U02DebugAction 0');wait(.5)
  before=c.metrics();c.attack(True);time.sleep(.06);c.attack(False);wait(.8)
  after=c.metrics();check(label+' hit count',after['combat']['geometryConfirmed']-before['combat']['geometryConfirmed']==expected)
  check(label+' one complete action',after['combat']['accepted']-before['combat']['accepted']==1 and not after['combat']['locked'])
  stage=dict(label=label,before=before,after=after,expectedHits=expected,wallSeconds=time.perf_counter()-start)
  # Pitch camera after gameplay; selected geometry is frozen, hit yaw cannot change.
  mouse(1,0,180);wait(.8);ImageGrab.grab(bbox=bounds,all_screens=True).save(a.out/(label+'.png'));grab();wait(.8)
  stage['screenshotWallSeconds']=time.perf_counter()-start;m['stages'].append(stage)
 m['processingEndSeconds']=time.perf_counter()-start;m['captureSeconds']=m['frames'][-1];m['videoSeconds']=encoded/30;m['encodedFrames']=encoded;m['encodedFPS']=30
 check('Video matches wall time',abs(m['captureSeconds']-m['videoSeconds'])<1/30+.01);m['completed']=True
except Exception as e:m['error']=str(e);raise
finally:
 if 'start' in locals():m.setdefault('captureSeconds',time.perf_counter()-start);m.setdefault('videoSeconds',encoded/30)
 if writer:writer.release()
 c.finish();m['externalInputMethodRestored']=not c.ime
 (a.out/'input.json').write_text(json.dumps(m,indent=2))
print(json.dumps(dict(completed=m['completed'],checks=len(m['checks']),wall=m['captureSeconds'],video=m['videoSeconds'])))
