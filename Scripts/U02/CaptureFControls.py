import argparse,json,time,cv2,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from FClient import FClient,mouse
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);a=p.parse_args();out=a.session/'Controls';out.mkdir(exist_ok=True);records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));by={r['role']:r for r in records};cs={k:FClient(by[k]) for k in ['ClientA','ClientB']};active=cs['ClientA'];writer=None;meta=dict(completed=False,processes=records,events=[])
try:
 active.prepare();active.console('U01NetFixture reset');time.sleep(1);meta['before']=active.metrics();bounds=[c.bounds() for c in cs.values()];box=(min(b[0] for b in bounds),min(b[1] for b in bounds),max(b[2] for b in bounds),max(b[3] for b in bounds));cv2.setNumThreads(1);writer=cv2.VideoWriter(str(out/'Controls-F.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(box[2]-box[0],box[3]-box[1]));assert writer.isOpened();start=time.perf_counter();meta['utc']=datetime.now(timezone.utc).isoformat();encoded=0;previous=None
 def focus(k):
  global active
  active=cs[k];active.prepare()
  if k=='ClientA':
   now=time.perf_counter()-start;actions[-2]=(now+.3,'Fresh W',key('W',True));actions[-1]=(now+1.0,'W release',key('W',False));end_at[0]=now+1.5
 def click():active.attack(True);time.sleep(.04);active.attack(False)
 def key(k,d):return lambda:active.press(k,d)
 actions=[(0,'W down',key('W',True)),(.55,'Attack',click),(.65,'Startup camera',lambda:mouse(1,dx=10)),(.8,'Locked camera',lambda:mouse(1,dx=25)),(1.6,'W up',key('W',False)),(2,'Sprint W',key('W',True)),(2.02,'Sprint Ctrl',key('Ctrl',True)),(3,'Ctrl up',key('Ctrl',False)),(3.02,'W up',key('W',False)),(3.5,'Jump down',key('Space',True)),(3.57,'Jump up',key('Space',False)),(3.7,'Menu down',key('Escape',True)),(3.76,'Menu up',key('Escape',False)),(4.6,'Resume',lambda:active.click(450,241)),(5,'Focus B',lambda:focus('ClientB')),(6.3,'Focus A Resume',lambda:focus('ClientA')),(7.1,'Fresh W',key('W',True)),(7.8,'W release',key('W',False))];i=0;end_at=[8.5]
 while time.perf_counter()-start<end_at[0] or i<len(actions):
  now=time.perf_counter()-start
  while i<len(actions) and now>=actions[i][0]:
   at,label,fn=actions[i];fn();meta['events'].append(dict(planned=at,label=label,actual=time.perf_counter()-start,utc=datetime.now(timezone.utc).isoformat()));i+=1
  active.guard();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=box,all_screens=True)),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
  while encoded/30<now:writer.write(previous if previous is not None else frame);encoded+=1
  previous=frame;time.sleep(.01)
 now=time.perf_counter()-start
 while encoded/30<now:writer.write(previous);encoded+=1
 meta.update(completed=i==len(actions),after=cs['ClientA'].metrics(),captureSeconds=now,videoSeconds=encoded/30,endUTC=datetime.now(timezone.utc).isoformat());ImageGrab.grab(bbox=box,all_screens=True).save(out/'Final.png')
except Exception as e:meta['error']=str(e);raise
finally:
 if writer:writer.release()
 for c in cs.values():
  if c.ime:c.focus()
  c.finish()
 meta['externalInputMethodRestored']=all(not c.ime for c in cs.values());(out/'input.json').write_text(json.dumps(meta,indent=2))
print('Captured actual network controls; offline assertions required')
