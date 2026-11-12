"""Guarded Windows physical input; recording runs independently of admission timing."""
import argparse,json,time,threading,math,re,cv2,numpy as np
from pathlib import Path
from PIL import ImageGrab
from B1Client import B1Client,u
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
c=B1Client(json.loads(a.record.read_text(encoding='utf-8-sig')));cv2.setNumThreads(1)
m={'completed':False,'checks':[],'stages':[],'events':[],'process':c.record};writer=None;worker=None;stop=threading.Event();start=0;encoded=0;last=0;previous=None
def check(n,v):m['checks'].append({'check':n,'result':'PASS' if v else 'FAIL'});assert v,n
def vector(s):return np.array([float(x) for x in re.findall(r'[XYZ]=([-0-9.]+)',s)])
def record():
 global encoded,last,previous
 while not stop.is_set():
  try:
   c.guard();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=c.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
   while encoded/30<now:writer.write(previous if previous is not None else frame);encoded+=1
   previous=frame;last=now
  except (AssertionError,RuntimeError,cv2.error,OSError):m['skippedUnfocusedFrames']=m.get('skippedUnfocusedFrames',0)+1
  time.sleep(.008)
def wait(t):time.sleep(t)
def until(f,t=3):
 end=time.perf_counter()+t
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Physical condition timeout')
  time.sleep(.006)
def tap(key):c.press(key,True);wait(.035);c.press(key,False);m['events'].append({'wall':time.perf_counter()-start,'key':key})
def console(text):c.console(text);m['events'].append({'wall':time.perf_counter()-start,'fixture':text});wait(.35)
def reset(place='Runway'):
 console('U01FixtureReset '+place);wait(.3)
 if place=='Runway':
  # Spawn is only100cm from the runway's rear edge; walk to its open centre
  # before measuring a300cm backwards dodge. This is physical setup, not teleport.
  c.press('W',True);wait(1.4);c.press('W',False);wait(.25)
def elapsed():v=c.metrics();return v['worldSeconds']-v['combat']['dodgeStart']
try:
 c.focus();w=c.probe_w()
 if w!='W':c.toggle_ime();c.ime=True;w=c.probe_w()
 assert w=='W'
 writer=cv2.VideoWriter(str(a.out/'Input-B1-Terrain.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert writer.isOpened();start=time.perf_counter();worker=threading.Thread(target=record);worker.start()
 if c.metrics()['controlState']!=0:c.click(640,305);wait(.4)
 check('Actual Resume enters Playing',c.metrics()['controlState']==0)
 for place in ['Ledge','Slope30','Step40','Slope46','Corridor120']:
  reset(place)
  if place!='Corridor120':
   c.press('W',True);wait(.4 if place=='Ledge' else .25);c.press('W',False);wait(.25)
  before=c.metrics();c.press('W',True)
  if place=='Corridor120':c.press('D',True)
  wait(.03);tap('Shift');until(lambda:c.metrics()['combat']['dodge']>before['combat']['dodge']);c.press('W',False)
  if place=='Corridor120':c.press('D',False)
  wait(.5);v=c.metrics();position=vector(v['capsuleCenterWorldCm']);distance=np.linalg.norm((position-vector(v['combat']['dodgeOrigin']))[:2]);check(place+' consumes a charge',v['combat']['dodgeCharges']==1);check(place+' remains grounded',v['movementMode']==1)
  if place=='Ledge':check('Physical cliff cannot be crossed',position[0]<=401 and position[2]>390 and distance<295)
  if place=='Slope30':check('Physical walkable slope climbs',position[2]>150)
  if place=='Step40':check('Physical step40 climbs',position[2]>130)
  if place=='Slope46':check('Physical steep slope stops',position[2]<158 and distance<295)
  if place=='Corridor120':check('Physical corridor wall holds capsule',position[1]<13519)
  m['stages'].append({'stage':place,'before':before,'after':v,'distanceCm':float(distance)});ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/(place+'.png'))
 check('Recording thread complete',worker.is_alive());m['completed']=True
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 if c.ime and c.metrics()['controlState']==0:
  c.press('Escape',True);time.sleep(.035);c.press('Escape',False);time.sleep(.2)
 c.finish();m.update(captureSeconds=last,videoSeconds=encoded/30,encodedFPS=30,externalInputMethodRestored=not c.ime);(a.out/'input.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({'completed':m['completed'],'checks':len(m['checks'])}))
