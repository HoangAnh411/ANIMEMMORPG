"""B2 package: guarded physical defense input and wall-clock video; enemies only via fixture."""
import argparse,json,time,threading,re,cv2,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from B2Client import B2Client,u
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
c=B2Client(json.loads(a.record.read_text(encoding='utf-8-sig')));cv2.setNumThreads(1)
m={'completed':False,'checks':[],'stages':[],'events':[],'process':c.record};writer=None;worker=None;stop=threading.Event();start=0;encoded=0;last=0;previous=None
def check(n,v):
 m['checks'].append({'check':n,'result':'PASS' if v else 'FAIL'});assert v,n
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
def until(f,t=4):
 end=time.perf_counter()+t
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Physical condition timeout')
  time.sleep(.008)
def tap(key):c.press(key,True);wait(.035);c.press(key,False);m['events'].append({'wall':time.perf_counter()-start,'key':key})
def console(text):c.console(text);m['events'].append({'wall':time.perf_counter()-start,'fixture':text});wait(.15)
def reset():
 console('U03B2Fixture off');console('U01FixtureReset Runway');wait(.2)
def fixture(label):
 console('U03B2Fixture '+label)
 raw=c.log.read_text(encoding='utf-8-sig');hits=re.findall(r'U03B2_FIXTURE label='+label+r' start=([0-9.]+)',raw);assert hits
 line=[l for l in raw.splitlines() if 'U03B2_FIXTURE label='+label+' start=' in l][-1]
 global fixture_wall;fixture_wall=datetime.strptime(re.search(r'\[([0-9.:-]+)\]',line).group(1),'%Y.%m.%d-%H.%M.%S:%f').replace(tzinfo=timezone.utc).timestamp()
 return float(hits[-1])
def b():return c.metrics()['combat']
try:
 c.focus();w=c.probe_w()
 if w!='W':c.toggle_ime();c.ime=True;w=c.probe_w()
 assert w=='W'
 writer=cv2.VideoWriter(str(a.out/'Input-B2.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert writer.isOpened();start=time.perf_counter();worker=threading.Thread(target=record);worker.start()
 if c.metrics()['controlState']!=0:c.click(640,305);wait(.4)
 check('Actual Resume enters Playing',c.metrics()['controlState']==0)
 reset();c.press('RMB',True);until(lambda:b()['guard']);wait(.7);check('Held guard does not reopen parry',not b()['parryOpen']);c.press('RMB',False);until(lambda:not b()['guard']);check('Physical RMB release drops guard',not b()['guard'])
 reset();s=fixture('block');until(lambda:time.time()>=fixture_wall+1.10);c.press('RMB',True);until(lambda:b()['defenseResult']==2);check('Physical parry confirmed',b()['posture']==100);until(lambda:b()['defenseResult']==1);check('Same held input becomes ordinary block',b()['posture']==75);m['stages'].append({'stage':'ParryThenBlock','metrics':c.metrics()});c.press('RMB',False);console('U03B2Fixture off')
 reset();fixture('unparryable');c.press('RMB',True);until(lambda:b()['hardCC']==5,6);check('Four held blocks break guard',not b()['guard'] and b()['posture']==0);tap('X');until(lambda:b()['hardCC']==0);check('Physical X clears break and refills posture',b()['posture']==100 and b()['xReady']>c.metrics()['worldSeconds']+29);check('X grants immunity',b()['immuneEnd']>c.metrics()['worldSeconds']);m['stages'].append({'stage':'BreakX','metrics':c.metrics()});c.press('RMB',False);console('U03B2Fixture off')
 reset();fixture('grab');until(lambda:b()['hardCC']==4);tap('X');until(lambda:b()['hardCC']==0);check('Physical X clears labelled grab',b()['xReady']>c.metrics()['worldSeconds']);console('U03B2Fixture off')
 reset();c.press('RMB',True);until(lambda:b()['guard']);tap('Escape');wait(.3);check('Menu forcibly drops guard',not b()['guard']);c.click(640,305);wait(.3);check('Held RMB across Resume does not rearm',not b()['guard']);c.press('RMB',False);wait(.1);c.press('RMB',True);until(lambda:b()['guard']);c.press('RMB',False)
 c.press('RMB',True);until(lambda:b()['guard']);c.guard();u.ShowWindow(c.hwnd,6);wait(.6);c.focus();check('Focus requires Resume',c.metrics()['controlState']!=0);check('Focus drops guard',not b()['guard']);c.press('RMB',False);c.click(640,305);wait(.3);c.press('RMB',True);until(lambda:b()['guard']);check('Release after focus rearms guard',b()['guard']);c.press('RMB',False)
 reset();c.press('RMB',True);until(lambda:b()['guard']);c.press('W',True);wait(.4);c.press('Ctrl',True);tap('Space');wait(.2);v=c.metrics();speed=np.linalg.norm([float(x) for x in re.findall(r'[XY]=([-0-9.]+)',v['velocityCmPerSec'])]);check('Guard200 no sprint or jump with real keys',180<=speed<=201 and not v['sprinting'] and v['movementMode']==1 and not v['bufferedJump']);c.press('W',False);c.press('Ctrl',False);c.press('RMB',False)
 tap('Escape');wait(.2);c.click(640,346);wait(.2);c.click(785,451);tap('C');wait(.15);c.click(785,497);tap('Z');wait(.15)
 settings=json.loads(c.metrics()['settings']);check('Physical UI rebind Guard C and X Z',settings['bindings']['Guard']=='C' and settings['bindings']['EscapeCC']=='Z');c.click(640,705);wait(.15);c.click(640,305);wait(.3)
 tap('RMB');wait(.1);check('Old RMB binding no longer guards',not b()['guard']);c.press('C',True);until(lambda:b()['guard']);check('Rebound C guards',b()['guard']);c.press('C',False);fixture('grab');until(lambda:b()['hardCC']==4);tap('Z');until(lambda:b()['hardCC']==0);check('Rebound Z escapes',b()['xReady']>c.metrics()['worldSeconds']);console('U03B2Fixture off');m['stages'].append({'stage':'RealRebind','metrics':c.metrics()})
 tap('Escape');wait(.2);c.click(640,346);wait(.2);c.click(785,451);tap('RMB');wait(.15);c.click(785,497);tap('X');wait(.15);c.click(640,705);wait(.15);c.click(640,305);wait(.3)
 ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/'Final.png');m['completed']=True
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 if c.ime and c.metrics()['controlState']==0:tap('Escape');wait(.2)
 c.finish();m.update(captureSeconds=last,videoSeconds=encoded/30,encodedFPS=30,externalInputMethodRestored=not c.ime);(a.out/'input.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({'completed':m['completed'],'checks':len(m['checks'])}))
