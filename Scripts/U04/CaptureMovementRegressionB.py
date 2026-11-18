import os
"""Guarded Windows physical input; recording runs independently of admission timing."""
import argparse,json,time,threading,math,re,cv2,numpy as np
from pathlib import Path
from PIL import ImageGrab
from RegressionClientB import RegressionClientB,u,mouse
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
c=RegressionClientB(json.loads(a.record.read_text(encoding='utf-8-sig')));cv2.setNumThreads(1)
m={'completed':False,'checks':[],'stages':[],'events':[],'process':c.record};writer=None;worker=None;stop=threading.Event();start=0;encoded=0;last=0;previous=None
def check(n,v):m['checks'].append({'check':n,'result':'PASS' if v else 'FAIL','metrics':c.metrics()});assert v,n
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
def tap(key):
 if key=='LMB':c.attack(True);wait(.035);c.attack(False)
 else:c.press(key,True);wait(.035);c.press(key,False)
 m['events'].append({'wall':time.perf_counter()-start,'key':key})
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
 if c.metrics()['controlState']!=0:c.click(round(c.metrics()['menuButtons']['Resume']['x']),round(c.metrics()['menuButtons']['Resume']['y']));wait(.4)
 check('Actual Resume enters Playing',c.metrics()['controlState']==0)
 reset();c.press('W',True);wait(.4);walk=c.metrics();c.press('Ctrl',True);wait(.4);sprint=c.metrics();check('Physical walk and sprint use existing500/700 speeds',walk['maxSpeedCmPerSec']==500 and not walk['sprinting'] and sprint['maxSpeedCmPerSec']==700 and sprint['sprinting']);c.press('Ctrl',False);c.press('W',False)
 old=c.metrics()['shoulderOffsetCm'];tap('V');wait(.3);check('Physical shoulder swaps camera side',old*c.metrics()['shoulderOffsetCm']<0);tap('V');wait(.3)
 reset();tap('Space');until(lambda:c.metrics()['movementMode']==3);jump=c.metrics();check('Physical jump enters falling mode',jump['jumpCount']>0);wait(1)
 reset();console('U03B2Fixture stun');marker=[l for l in c.log.read_text(encoding='utf-8-sig').splitlines() if 'U03B2_FIXTURE label=stun start=' in l][-1];fixture_start=float(re.search(r'start=([0-9.]+)',marker)[1]);until(lambda:c.metrics()['worldSeconds']>=fixture_start+1.08);tap('Space');until(lambda:c.metrics()['combat']['hardCC']==1 and c.metrics()['movementMode']==3,6);before=c.metrics();wait(.10);locked=c.metrics();m['stages'].append(dict(stage='IncomingCCGravity',before=before,locked=locked));check('Combat lock from incoming CC during physical jump preserves gravity',locked['combat']['locked'] and locked['movementMode']==3 and locked['gravityCmPerSec2']<0 and vector(locked['velocityCmPerSec'])[2]<vector(before['velocityCmPerSec'])[2]);console('U03B2Fixture off');reset()
 c.press('W',True);wait(.15);tap('Escape');wait(.15);v=c.metrics();b=v['menuButtons']['Resume'];c.click(round(b['x']),round(b['y']));wait(.3);check('Held W through Escape and Resume remains quarantined',not c.metrics()['gateW']);c.press('W',False);c.press('W',True);wait(.1);check('Release and repress rearms W after Escape',c.metrics()['gateW']);c.press('W',False)
 c.press('W',True);wait(.1)
 # Only the game owns input at this point. Alt-Tab releases focus; no input is sent to the newly focused window.
 c.press('Alt',True);c.press('Tab',True);wait(.04)
 from F60Input import key
 key('Tab',False);key('Alt',False);wait(.4);c.focus();check('AltTab keeps controls awaiting Resume',c.metrics()['controlState']!=0);b=c.metrics()['menuButtons']['Resume'];c.click(round(b['x']),round(b['y']));wait(.25);check('Held W through AltTab and Resume does not replay',not c.metrics()['gateW']);c.press('W',False)
 m['stages'].append(dict(stage='MovementGravityFocus',walk=walk,sprint=sprint,falling=before,locked=locked))
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
  if place=='Corridor120':
   gain=1.
   for _ in range(12):
    yaw=float(re.search(r'Y=([-0-9.]+)',c.metrics()['aimYawPitchDegrees'])[1]);delta=(90-yaw+180)%360-180
    if abs(delta)<1:break
    dx=max(-4000,min(4000,round(delta/gain)));c.guard();mouse(1,dx,0);wait(.2);observed=float(re.search(r'Y=([-0-9.]+)',c.metrics()['aimYawPitchDegrees'])[1]);change=(observed-yaw+180)%360-180
    if dx and 0<change/dx<10:gain=change/dx
   wait(.25);v=c.metrics();check('Physical camera turn toward corridor wall produces safe sweep retraction',v['cameraHit'] and v['cameraPivotDistanceCm']<350)
  m['stages'].append({'stage':place,'before':before,'after':v,'distanceCm':float(distance)});ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/(place+'.png'))
 check('Recording thread complete',worker.is_alive());m['completed']=True
except Exception as e:m['error']=repr(e);m['errorMetrics']=c.metrics();raise
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 if c.ime and c.metrics()['controlState']==0:
  c.press('Escape',True);time.sleep(.035);c.press('Escape',False);time.sleep(.2)
 c.finish();m.update(captureSeconds=last,videoSeconds=encoded/30,encodedFPS=30,externalInputMethodRestored=not c.ime);(a.out/'input.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({'completed':m['completed'],'checks':len(m['checks'])}))
