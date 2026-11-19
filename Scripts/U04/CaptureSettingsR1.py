"""Physical settings conflict/rebind/slider/shoulder and Save/Quit/reopen integration."""
import argparse,json,time,threading,re,cv2,numpy as np
from pathlib import Path
from PIL import ImageGrab
from RegressionClientB import RegressionClientB,u
from F60Input import Input,Payload,Mouse,emit
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--expected',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
c=RegressionClientB(json.loads(a.record.read_text(encoding='utf-8-sig')));m=dict(completed=False,checks=[],process=c.record,stages=[]);stop=threading.Event();frames=0;start=time.perf_counter();cv2.setNumThreads(1)
video=cv2.VideoWriter(str(a.out/'Settings.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert video.isOpened()
def state():return c.metrics()
def prefs():return json.loads(state()['settings'])
def until(f):
 end=time.perf_counter()+6
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Settings condition timeout')
  time.sleep(.03)
def check(n,ok):m['checks'].append(dict(check=n,result='PASS' if ok else 'FAIL',metrics=state()));assert ok,n
def tap(k):c.press(k,True);time.sleep(.04);c.press(k,False);time.sleep(.15)
def button(label):
 until(lambda:label in state()['menuButtons']);b=state()['menuButtons'][label];c.click(round(b['x']),round(b['y']));time.sleep(.2)
def wheel():
 c.guard();l,t,_,_=c.bounds();u.SetCursorPos(l+650,t+420);emit(Input(type=0,payload=Payload(mouse=Mouse(data=(-240)&0xffffffff,flags=0x0800))));time.sleep(.18)
def find(label):
 for _ in range(20):
  if label in state()['menuButtons']:return
  wheel()
 raise RuntimeError('UI widget not visible '+label)
def controls():
 if state()['controlState']==0:tap('Escape')
 label=next(k for k in state()['menuButtons'] if '/ Controls' in k);button(label)
def main():
 find('Save');button('Save');button(next(k for k in state()['menuButtons'] if 'menu' in k))
def record():
 global frames
 while not stop.is_set():
  frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=c.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR)
  while frames/30<time.perf_counter()-start:video.write(frame);frames+=1
  time.sleep(.025)
worker=threading.Thread(target=record);worker.start()
try:
 c.focus();observed=c.probe_w()
 if observed!='W':c.toggle_ime();c.ime=True;assert c.probe_w()=='W'
 if a.expected:
  expected=json.loads(a.expected.read_text(encoding='utf-8'))
  check('Cold reopen restores exact saved key sensitivity and shoulder preferences',prefs()==expected)
  check('Cold reopen does not restore combat progress',state()['combat']['energy']==100 and state()['combat']['action']==0 and state()['combat']['eReady']==0 and state()['encounter']['monsterVital']['hp']==600)
 else:
  if state().get('encounter') and state()['combat']['vital']['hp']<1000:
   end=time.perf_counter()+22
   while not state()['encounter']['result']:
    assert time.perf_counter()<end;time.sleep(.03)
   button('Retry encounter')
   until(lambda:state()['combat']['vital']['hp']==1000)
  controls();original=prefs();button('S');until(lambda:state()['pendingRebind']==1);tap('W')
  check('Conflicting Backward=W rejected without swapping bindings',prefs()==original)
  tap('Escape');button('S');until(lambda:state()['pendingRebind']==1);c.press('H',True);until(lambda:prefs()['bindings']['Backward']=='H');main();button('Resume');time.sleep(.3)
  check('Held newly rebound movement key cannot move through Resume',state()['controlState']==0 and np.linalg.norm([float(v) for v in re.findall(r'[XYZ]=([-0-9.]+)',state()['velocityCmPerSec'])])<1)
  c.press('H',False);time.sleep(.05);c.press('H',True);time.sleep(.2);check('Release and repress of rebound key moves owned pawn',np.linalg.norm([float(v) for v in re.findall(r'[XYZ]=([-0-9.]+)',state()['velocityCmPerSec'])])>20);c.press('H',False)
  controls();find('U04Sensitivity');before=prefs();b=state()['menuButtons']['U04Sensitivity'];c.click(round(b['x']+b['width']*.2),round(b['y']));time.sleep(.25);check('Physical slider changes sensitivity',prefs()['sensitivity']!=before['sensitivity'])
  find('U04RightShoulder');button('U04RightShoulder');check('Physical checkbox changes default shoulder',prefs()['rightShoulder']!=before['rightShoulder']);main()
  (a.out/'expected-settings.json').write_text(json.dumps(prefs(),indent=2),encoding='utf-8')
 ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/'Saved.png');m['stages'].append(state());c.finish()
 if state()['controlState']==0:tap('Escape')
 button('Quit');m['completed']=True
except Exception as e:m['error']=repr(e);raise
finally:
 stop.set();worker.join();video.release();m['videoSeconds']=frames/30
 (a.out/'settings.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print('PASS settings',len(m['checks']))
