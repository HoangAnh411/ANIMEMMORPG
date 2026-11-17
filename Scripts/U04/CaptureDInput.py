"""Guarded physical Windows input; product Retry/Target only, no combat fixture resets."""
import argparse,json,time,threading,re,math,cv2,numpy as np
from pathlib import Path
from PIL import ImageGrab
from datetime import datetime
from DClient import DClient,u,mouse
from F60Input import Input,Payload,Mouse,emit
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=['inspect','combat','target','route'],default='combat');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
c=DClient(json.loads(a.record.read_text(encoding='utf-8-sig')));cv2.setNumThreads(1)
m=dict(completed=False,mode=a.mode,checks=[],stages=[],events=[],process=c.record);stop=threading.Event();writer=None;worker=None;start=0;encoded=0;last=0;previous=None
def state():return c.metrics()
def encounter():return state()['encounter']
def combat():return state()['combat']
def target():return state()['informationTarget']
def current_world_estimate():
 v=state();utc=datetime.fromisoformat(v['utc'].replace('Z','+00:00')).timestamp()
 return v['worldSeconds']+max(0,time.time()-utc)
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
 until(lambda:any(label in k and v['enabled'] for k,v in state().get('menuButtons',{}).items()))
 names=[k for k in state()['menuButtons'] if label in k];assert len(names)==1,(label,names)
 v=state()['menuButtons'][names[0]];assert v['enabled'];c.click(round(v['x']),round(v['y']));time.sleep(.18)
 m['events'].append(dict(wall=time.perf_counter()-start,button=names[0],geometry=v))
def resume():
 if state()['controlState']!=0:button('Resume')
 until(lambda:state()['controlState']==0)
def retry():
 old=encounter()['revision'];m['events'].append(dict(retrySelectionBefore=target()));button('Retry encounter');until(lambda:encounter()['revision']>old)
 check('Retry publishes fresh Running state',encounter()['result']==0 and encounter()['monsterVital']['hp']==600 and combat()['energy']==100 and combat()['dodgeCharges']==2 and combat()['eReady']==0)
 check('Retry never auto-Resumes or attacks',state()['controlState']!=0 and combat()['action']==0)
 until(lambda:not target()['selected']);check('New encounter revision clears selection without replacement',not target()['selected'])
def approach():
 c.press('W',True)
 try:until(lambda:distance()<160,5)
 finally:c.press('W',False)
def move_until(key,predicate,timeout=7):
 c.press(key,True)
 try:until(predicate,timeout)
 finally:c.press(key,False)
def winding():
 until(lambda:encounter()['monsterCombat']['phase']==1 and encounter()['monsterCombat']['serverSnapshotSeconds']<encounter()['monsterCombat']['start']+.40,5)
def turn(yaw):
 gain=1.
 for _ in range(12):
  current=float(re.search(r'Y=([-0-9.]+)',state()['aimYawPitchDegrees']).group(1));delta=(yaw-current+180)%360-180
  if abs(delta)<1:return
  dx=max(-4000,min(4000,round(delta/gain)));c.guard();mouse(1,dx,0);time.sleep(.2)
  observed=float(re.search(r'Y=([-0-9.]+)',state()['aimYawPitchDegrees']).group(1));change=(observed-current+180)%360-180
  if dx and 0<change/dx<10:gain=change/dx
  m['events'].append(dict(mouseDx=dx,beforeYaw=current,afterYaw=observed,observedGain=gain))
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
  writer=cv2.VideoWriter(str(a.out/('Input-D-'+a.mode+'.mp4')),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert writer.isOpened();start=time.perf_counter();worker=threading.Thread(target=record);worker.start()
  if a.mode in ('combat','route'):
   # Gameplay continues in the menu. Setup may have consumed most of this life;
   # start measured cases at a fresh product Retry rather than racing terminal UI.
   if combat()['vital']['hp']<1000 and not encounter()['result']:until(lambda:encounter()['result']!=0,22)
   if encounter()['result']:retry()
  resume();before=state();c.press('Tab',True);time.sleep(.45);c.press('Tab',False)
  check('Physical Target edge selects and hold never toggles',target()['selected'] and target()['visible'])
  check('Target leaves camera and facing alone',state()['aimYawPitchDegrees']==before['aimYawPitchDegrees'] and state()['bodyYawDegrees']==before['bodyYawDegrees'])
  tap('Tab');check('Second Target edge toggles off',not target()['selected'])
  if a.mode=='combat':
   winding();tap('Shift');until(lambda:combat()['dodgeCharges']==1);check('Physical dodge uses one charge',combat()['dodge']>0);time.sleep(.4);approach()
   old=combat()['parryFeedbackSequence'];m['parryAttempts']=[]
   for attempt in range(3):
    winding();deadline=encounter()['monsterCombat']['start']+.60
    until(lambda:current_world_estimate()>=deadline-.145)
    c.press('RMB',True);end=time.perf_counter()+.45
    while combat()['parryFeedbackSequence']==old and time.perf_counter()<end:time.sleep(.01)
    sample=combat();m['parryAttempts'].append(dict(deadline=deadline,guardStart=sample['parryStart'],guardEnd=sample['parryEnd'],parry=sample['parryFeedbackSequence']>old))
    c.press('RMB',False)
    if sample['parryFeedbackSequence']>old:break
    until(lambda:current_world_estimate()>=sample['parryReady'])
   check('Physical parry resolves monster hit',combat()['parryFeedbackSequence']>old and combat()['hardCC']==0)
   winding();old=encounter()['monsterCombat']['interruptSequence'];tap('E');until(lambda:encounter()['monsterCombat']['interruptSequence']>old,2)
   check('Real E Interrupts Monster startup without stun',encounter()['monsterCombat']['hardCC']==0);time.sleep(.55)
   until(lambda:not combat()['locked']);old=encounter()['monsterCombat']['interruptSequence'];tap('Q');until(lambda:combat()['definition']==3);time.sleep(.45);check('Real Q does not Interrupt Monster',encounter()['monsterCombat']['interruptSequence']==old)
   until(lambda:not combat()['locked']);tap('Tab');check('Opponent selected before lethal damage',target()['selected']);end=time.perf_counter()+12
   while encounter()['result']==0 and time.perf_counter()<end:tap('LMB');time.sleep(.42)
   until(lambda:encounter()['result']!=0);check('Player wins through physical attacks and server result',encounter()['result']==1);until(lambda:not target()['selected']);check('Target death clears information without replacement',not target()['selected']);m['stages'].append(dict(stage='Won',metrics=state()))
   c.press('W',True);c.press('Q',True);retry();button('Resume');time.sleep(.4)
   check('Held W/Q across Retry and Resume do not replay',not state()['gateW'] and combat()['action']==0 and combat()['energy']==100)
   c.press('W',False);c.press('Q',False);c.press('W',True);time.sleep(.12);c.press('W',False);check('Physical release and repress rearms movement',state()['gateW']);tap('Tab');check('Living opponent selected before Lost and Retry',target()['selected'])
   until(lambda:encounter()['result']==2,22);check('Standing player loses by server decision',encounter()['result']==2);m['stages'].append(dict(stage='Lost',metrics=state()));retry()
   u.ShowWindow(c.hwnd,6);time.sleep(.3);c.focus();check('Focus return still requires Resume',state()['controlState']!=0)
  elif a.mode=='route':
   approach();winding();tap('E');until(lambda:encounter()['monsterVital']['hp']<600);until(lambda:not combat()['locked'])
   oldlife=encounter()['monsterVital']['lifeGeneration'];path=[]
   def sample():
    v=state();e=v['encounter'];point=dict(time=v['worldSeconds'],position=vec(e['monsterPosition']).tolist(),life=e['monsterVital']['lifeGeneration'],ai=e['ai'],hp=e['monsterVital']['hp'])
    if not path or point['time']>path[-1]['time']:path.append(point)
   def measured(predicate):sample();return predicate()
   def walk(key,predicate,timeout):
    c.press(key,True)
    try:until(lambda:measured(predicate),timeout)
    finally:c.press(key,False)
   walk('D',lambda:vec(state()['capsuleCenterWorldCm'])[1]>900,4)
   walk('W',lambda:vec(state()['capsuleCenterWorldCm'])[0]>16200,4)
   until(lambda:measured(lambda:vec(encounter()['monsterPosition'])[0]>16000),6)
   walk('A',lambda:vec(state()['capsuleCenterWorldCm'])[1]<0,4)
   walk('S',lambda:vec(state()['capsuleCenterWorldCm'])[0]<15400,4)
   until(lambda:measured(lambda:encounter()['monsterVital']['lifeGeneration']>oldlife),8)
   returns=[v for v in path if v['ai']==3 and v['life']==oldlife];check('Physical route causes server Return behind the obstacle',bool(returns))
   check('Return cannot rechase before reset',all(v['ai']==3 for v in path if returns[0]['time']<=v['time'] and v['life']==oldlife))
   check('Return completes inside50cm and heals',np.linalg.norm(vec(encounter()['monsterPosition'])-np.array([15500.,0.,98.15]))<=50 and encounter()['monsterVital']['hp']==600)
   speeds=[np.linalg.norm(np.array(v['position'])-np.array(u['position']))/(v['time']-u['time']) for u,v in zip(path,path[1:]) if v['time']>u['time']]
   check('Recorded chase/return stays continuous at300cm/s (0.2cm/s text-quantization allowance)',bool(speeds) and max(speeds)<=300.2)
   life=encounter()['monsterVital']['lifeGeneration'];time.sleep(.6);check('Return reset occurs exactly once',encounter()['monsterVital']['lifeGeneration']==life);m['stages'].append(dict(stage='Navigation route',path=path,speeds=speeds,metrics=state()))
  else:
   tap('Tab');check('Coincident candidates use stable subject ID',target()['subject'].endswith('00000001'))
   turn(180);time.sleep(1.15);check('Offscreen alone retains selection and hides information',target()['selected'] and not target()['visible']);turn(0);until(lambda:target()['visible'])
   tap('Tab');rebind('Tab','T');tap('Tab');check('Old Target key no longer selects',not target()['selected']);tap('T');check('Rebound Target selects',target()['selected']);tap('T');rebind('T','Tab')
   tap('Tab');point=np.array([15500.,45.,78.15]);dist=lambda:np.linalg.norm(vec(state()['capsuleCenterWorldCm'])-point)
   c.press('S',True);c.press('A',True);until(lambda:dist()>2900,7);check('Selected target retained below30m',target()['selected']);until(lambda:dist()>3020,2);c.press('S',False);c.press('A',False);until(lambda:not target()['selected']);check('Selection clears beyond30m',not target()['selected'])
   c.press('W',True);c.press('D',True);until(lambda:dist()<2050,4);c.press('W',False);c.press('D',False);tap('Tab');check('Selection refuses beyond20m',not target()['selected'])
   c.press('W',True);c.press('D',True);until(lambda:dist()<1950,2);c.press('W',False);c.press('D',False);tap('Tab');check('Selection accepts inside20m',target()['selected'])
   move_until('W',lambda:vec(state()['capsuleCenterWorldCm'])[0]>16200)
   turn(180);move_until('A',lambda:vec(state()['capsuleCenterWorldCm'])[1]>260)
   check('Occlusion hides information immediately before timeout',target()['selected'] and not target()['visible'])
   move_until('D',lambda:vec(state()['capsuleCenterWorldCm'])[1]<50)
   until(lambda:target()['visible']);check('Seeing the target again resets continuous occlusion',target()['selected'])
   move_until('A',lambda:vec(state()['capsuleCenterWorldCm'])[1]>300)
   until(lambda:not target()['visible']);time.sleep(.6);check('New occlusion receives its own one-second interval',target()['selected']);time.sleep(.5);until(lambda:not target()['selected']);check('Continuous wall occlusion clears without replacement',not target()['selected'])
  ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/'Final.png');m['completed']=True
except Exception as error:
 m['error']=repr(error);m['errorMetrics']=state();raise
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 c.finish();m.update(captureSeconds=last,videoSeconds=encoded/30,encodedFPS=30,externalInputMethodRestored=not c.ime);(a.out/'input.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(completed=m['completed'],checks=len(m['checks']))))
