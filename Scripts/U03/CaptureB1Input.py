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
  except AssertionError:pass
  time.sleep(.008)
def wait(t):time.sleep(t)
def until(f,t=3):
 end=time.perf_counter()+t
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Physical condition timeout')
  time.sleep(.006)
def tap(key):c.press(key,True);wait(.035);c.press(key,False);m['events'].append({'wall':time.perf_counter()-start,'key':key})
def console(text):c.console(text);m['events'].append({'wall':time.perf_counter()-start,'fixture':text});wait(.35)
def reset(place='Runway'):console('U01FixtureReset '+place);wait(.3)
def elapsed():v=c.metrics();return v['worldSeconds']-v['combat']['dodgeStart']
try:
 c.focus();w=c.probe_w()
 if w!='W':c.toggle_ime();c.ime=True;w=c.probe_w()
 assert w=='W'
 writer=cv2.VideoWriter(str(a.out/'Input-B1.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert writer.isOpened();start=time.perf_counter();worker=threading.Thread(target=record);worker.start()
 if c.metrics()['controlState']!=0:c.click(640,305);wait(.4)
 check('Actual Resume enters Playing',c.metrics()['controlState']==0)
 for keys,expected in [(['W'],[1,0,0]),(['S'],[-1,0,0]),(['A'],[0,-1,0]),(['D'],[0,1,0]),(['W','D'],[math.sqrt(.5),math.sqrt(.5),0]),([],[-1,0,0])]:
  reset();before=c.metrics()
  for key in keys:c.press(key,True)
  wait(.04);tap('Shift');until(lambda:c.metrics()['combat']['dodge']>before['combat']['dodge'])
  for key in keys:c.press(key,False)
  until(lambda:elapsed()>=.27);v=c.metrics();b=v['combat'];distance=np.linalg.norm((vector(v['capsuleCenterWorldCm'])-vector(b['dodgeOrigin']))[:2]);direction=vector(b['dodgeDirection'])
  check('Direction '+str(keys),np.linalg.norm(direction-np.array(expected))<.01);check('300cm +/-5 '+str(keys),abs(distance-300)<5);check('No energy cost '+str(keys),b['energy']==100);m['stages'].append({'stage':'Direction'+str(keys),'metrics':v,'distanceCm':float(distance)});wait(.2)
 reset();base=c.metrics()['combat']['dodge'];c.press('Shift',True);wait(1.2);c.press('Shift',False);check('Held Shift does not repeat',c.metrics()['combat']['dodge']==base+1)
 reset();tap('Shift');until(lambda:elapsed()>=.50);tap('Shift');until(lambda:c.metrics()['combat']['dodge']==2);v=c.metrics();check('Buffered second start exactly .60',abs(v['combat']['dodgeStart']-(v['combat']['dodgeRestoreAt']-2+.60))<1.e-9);check('Two charges consumed',v['combat']['dodgeCharges']==0);tap('Shift');wait(.1);check('No charge cannot buffer',c.metrics()['combat']['pendingCommand']==0);check('No third action',c.metrics()['combat']['dodge']==2)
 first=v['combat']['dodgeRestoreAt']-2;until(lambda:c.metrics()['worldSeconds']>=first+2.1);v2=c.metrics();check('Sequential first charge',v2['combat']['dodgeCharges']==1);check('Next restore is original start+4',abs(v2['combat']['dodgeRestoreAt']-(first+4))<1.e-9);until(lambda:c.metrics()['worldSeconds']>=first+4.1,4);check('Sequential full charges',c.metrics()['combat']['dodgeCharges']==2);m['stages'].append({'stage':'Charges','second':v,'firstRestored':v2,'full':c.metrics()})
 reset();c.attack(True);wait(.035);c.attack(False);wait(.035);tap('Shift');wait(.4);v=c.metrics();check('Physical startup cancellation admits dodge',v['combat']['dodge']==1);check('Cancelled sword presentation stops',not v['attackPresented']);m['stages'].append({'stage':'StartupCancel','metrics':v})
 reset();tap('Shift');tap('Space');wait(.5);check('Dodge does not replay jump',c.metrics()['movementMode']==1 and not c.metrics()['bufferedJump'])
 reset();tap('Shift');wait(.025);tap('Escape');wait(.4);v=c.metrics();check('Menu locks control',v['controlState']!=0);check('Menu preserves accepted dodge movement',np.linalg.norm((vector(v['capsuleCenterWorldCm'])-vector(v['combat']['dodgeOrigin']))[:2])>295);c.click(640,305);wait(.4);check('Menu Resume',c.metrics()['controlState']==0)
 reset();tap('Shift');wait(.025);c.guard();u.ShowWindow(c.hwnd,6);m['events'].append({'wall':time.perf_counter()-start,'focusGap':'minimized .6s; video repeats last visible frame'});wait(.6);c.focus();v=c.metrics();check('Actual focus loss requires Resume',v['controlState']!=0);check('Focus preserves accepted dodge',np.linalg.norm((vector(v['capsuleCenterWorldCm'])-vector(v['combat']['dodgeOrigin']))[:2])>295);c.click(640,305);wait(.4);check('Focus Resume',c.metrics()['controlState']==0)
 reset('CombatD2');tap('Shift');wait(.5);m['stages'].append({'stage':'WallAreaBackwardDodge','metrics':c.metrics()})
 ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/'Final.png');m['completed']=True
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 c.finish();m.update(captureSeconds=last,videoSeconds=encoded/30,encodedFPS=30,externalInputMethodRestored=not c.ime);(a.out/'input.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({'completed':m['completed'],'checks':len(m['checks'])}))
