"""Guarded physical Windows input; product Retry/Target only, no combat fixture resets."""
import argparse,json,time,threading,re,math,cv2,numpy as np
from pathlib import Path
from PIL import ImageGrab
from C2Client import C2Client,u,mouse
from F60Input import Input,Payload,Mouse,emit
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=['inspect','combat','target'],default='combat');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
c=C2Client(json.loads(a.record.read_text(encoding='utf-8-sig')));cv2.setNumThreads(1)
m=dict(completed=False,mode=a.mode,checks=[],stages=[],events=[],process=c.record);stop=threading.Event();writer=None;worker=None;start=0;encoded=0;last=0;previous=None
def state():return c.metrics()
def encounter():return state()['encounter']
def combat():return state()['combat']
def target():return state()['informationTarget']
def vec(s):return np.array([float(v) for v in re.findall(r'[XYZ]=([-0-9.]+)',s)])
def distance():return np.linalg.norm(vec(state()['capsuleCenterWorldCm'])-vec(encounter()['monsterPosition']))
def check(name,ok):m['checks'].append(dict(check=name,result='PASS' if ok else 'FAIL',metrics=state()));assert ok,name
def until(predicate,timeout=5):
 end=time.perf_counter()+timeout
 while not predicate():
  if time.perf_counter()>end:raise RuntimeError('Physical condition timeout')
  time.sleep(.01)
def tap(key):
 if key=='LMB':c.attack(True);time.sleep(.035);c.attack(False)
 else:c.press(key,True);time.sleep(.035);c.press(key,False)
 m['events'].append(dict(wall=time.perf_counter()-start,key=key))
def button(label):
 until(lambda:any(label in k for k in state().get('menuButtons',{})))
 names=[k for k in state()['menuButtons'] if label in k];assert len(names)==1,(label,names)
 v=state()['menuButtons'][names[0]];assert v['enabled'];c.click(round(v['x']),round(v['y']));time.sleep(.18)
 m['events'].append(dict(wall=time.perf_counter()-start,button=names[0],geometry=v))
def resume():
 if state()['controlState']!=0:button('Resume')
 until(lambda:state()['controlState']==0)
def retry():
 old=encounter()['revision'];button('Retry encounter');until(lambda:encounter()['revision']>old)
 check('Retry publishes fresh Running state',encounter()['result']==0 and encounter()['monsterVital']['hp']==600 and combat()['energy']==100 and combat()['dodgeCharges']==2 and combat()['eReady']==0)
 check('Retry never auto-Resumes or attacks',state()['controlState']!=0 and combat()['action']==0)
def approach():
 c.press('W',True)
 try:until(lambda:distance()<160,5)
 finally:c.press('W',False)
def winding():
 until(lambda:encounter()['monsterCombat']['phase']==1 and encounter()['monsterCombat']['serverSnapshotSeconds']<encounter()['monsterCombat']['start']+.40,5)
def turn(yaw):
 for _ in range(5):
  current=float(re.search(r'Y=([-0-9.]+)',state()['aimYawPitchDegrees']).group(1));delta=(yaw-current+180)%360-180
  if abs(delta)<1:return
  sensitivity=json.loads(state()['settings'])['sensitivity'];c.guard();mouse(1,round(delta/sensitivity),0);time.sleep(.16)
 raise RuntimeError('Physical camera yaw did not converge')
def wheel(delta):
 c.guard();left,top,_,_=c.bounds();u.SetCursorPos(left+650,top+420);emit(Input(type=0,payload=Payload(mouse=Mouse(data=delta&0xffffffff,flags=0x0800))));time.sleep(.15)
def rebind(old,new):
 if state()['controlState']==0:tap('Escape');time.sleep(.15)
 button('/ Controls')
 for _ in range(12):
  if old in state().get('menuButtons',{}):break
  wheel(-240)
 button(old);until(lambda:state()['pendingRebind']==14);tap(new);until(lambda:json.loads(state()['settings'])['bindings']['Target']==new)
 for _ in range(12):
  if 'Save' in state().get('menuButtons',{}):break
  wheel(-240)
 button('Save');button('Về menu');resume()
def record():
 global encoded,last,previous
 while not stop.is_set():
  try:
   c.guard();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=c.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR);last=time.perf_counter()-start
   while encoded/30<last:writer.write(previous if previous is not None else frame);encoded+=1
   previous=frame
  except (AssertionError,RuntimeError,cv2.error,OSError):m['skippedUnfocusedFrames']=m.get('skippedUnfocusedFrames',0)+1
  time.sleep(.008)
try:
 c.focus();ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/'Initial.png');m['initial']=state()
 if a.mode=='inspect':m['completed']=True
 else:
  observed=c.probe_w()
  if observed!='W':c.toggle_ime();c.ime=True;observed=c.probe_w()
  assert observed=='W'
  writer=cv2.VideoWriter(str(a.out/('Input-C2-'+a.mode+'.mp4')),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert writer.isOpened();start=time.perf_counter();worker=threading.Thread(target=record);worker.start()
  if a.mode=='combat' and encounter()['result']:retry()
  resume();before=state();c.press('Tab',True);time.sleep(.45);c.press('Tab',False)
  check('Physical Target edge selects and hold never toggles',target()['selected'] and target()['visible'])
  check('Target leaves camera and facing alone',state()['aimYawPitchDegrees']==before['aimYawPitchDegrees'] and state()['bodyYawDegrees']==before['bodyYawDegrees'])
  tap('Tab');check('Second Target edge toggles off',not target()['selected'])
  if a.mode=='combat':
   winding();tap('Shift');until(lambda:combat()['dodgeCharges']==1);check('Physical dodge uses one charge',combat()['dodge']>0);time.sleep(.4);approach()
   winding();old=combat()['parryFeedbackSequence'];until(lambda:encounter()['monsterCombat']['serverSnapshotSeconds']>=encounter()['monsterCombat']['start']+.515)
   c.press('RMB',True);until(lambda:combat()['parryFeedbackSequence']>old,2);c.press('RMB',False);check('Physical parry resolves monster hit',combat()['hardCC']==0)
   winding();old=encounter()['monsterCombat']['interruptSequence'];tap('E');until(lambda:encounter()['monsterCombat']['interruptSequence']>old,2)
   check('Real E Interrupts Monster startup without stun',encounter()['monsterCombat']['hardCC']==0);time.sleep(.55)
   until(lambda:not combat()['locked']);old=encounter()['monsterCombat']['interruptSequence'];tap('Q');until(lambda:combat()['definition']==3);time.sleep(.45);check('Real Q does not Interrupt Monster',encounter()['monsterCombat']['interruptSequence']==old)
   until(lambda:not combat()['locked']);end=time.perf_counter()+12
   while encounter()['result']==0 and time.perf_counter()<end:tap('LMB');time.sleep(.42)
   until(lambda:encounter()['result']!=0);check('Player wins through physical attacks and server result',encounter()['result']==1);m['stages'].append(dict(stage='Won',metrics=state()))
   c.press('W',True);c.press('Q',True);retry();button('Resume');time.sleep(.4)
   check('Held W/Q across Retry and Resume do not replay',not state()['gateW'] and combat()['action']==0 and combat()['energy']==100)
   c.press('W',False);c.press('Q',False);c.press('W',True);time.sleep(.12);c.press('W',False);check('Physical release and repress rearms movement',state()['gateW'])
   until(lambda:encounter()['result']==2,22);check('Standing player loses by server decision',encounter()['result']==2);m['stages'].append(dict(stage='Lost',metrics=state()));retry()
   u.ShowWindow(c.hwnd,6);time.sleep(.3);c.focus();check('Focus return still requires Resume',state()['controlState']!=0)
  else:
   tap('Tab');check('Coincident candidates use stable subject ID',target()['subject'].endswith('00000001'))
   turn(180);time.sleep(1.15);check('Offscreen alone retains selection and hides information',target()['selected'] and not target()['visible']);turn(0);until(lambda:target()['visible'])
   tap('Tab');rebind('Tab','T');tap('Tab');check('Old Target key no longer selects',not target()['selected']);tap('T');check('Rebound Target selects',target()['selected']);tap('T');rebind('T','Tab')
   tap('Tab');point=np.array([15500.,45.,78.15]);dist=lambda:np.linalg.norm(vec(state()['capsuleCenterWorldCm'])-point)
   c.press('S',True);until(lambda:dist()>2900,7);check('Selected target retained below30m',target()['selected']);until(lambda:dist()>3020,2);c.press('S',False);until(lambda:not target()['selected']);check('Selection clears beyond30m',not target()['selected'])
   c.press('W',True);until(lambda:dist()<2050,4);c.press('W',False);tap('Tab');check('Selection refuses beyond20m',not target()['selected'])
   c.press('W',True);until(lambda:dist()<1950,2);c.press('W',False);tap('Tab');check('Selection accepts inside20m',target()['selected'])
  ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/'Final.png');m['completed']=True
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 c.finish();m.update(captureSeconds=last,videoSeconds=encoded/30,encodedFPS=30,externalInputMethodRestored=not c.ime);(a.out/'input.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(completed=m['completed'],checks=len(m['checks']))))
