"""Physical Boot/lab cycles and preference save/Quit. Boot evidence uses map logs, never stale pawn metrics."""
import argparse,json,time,threading,cv2,numpy as np
from pathlib import Path
from PIL import ImageGrab
from DClient import DClient,u
from F60Input import Input,Payload,Mouse,emit
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--reopen',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
c=DClient(json.loads(a.record.read_text(encoding='utf-8-sig')));m=dict(completed=False,process=c.record,cycles=[],checks=[]);stop=threading.Event();writer=None;worker=None;encoded=0;start=time.perf_counter();cv2.setNumThreads(1)
def state():return c.metrics()
def until(f,timeout=15):
 end=time.perf_counter()+timeout
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Lifecycle timeout')
  time.sleep(.03)
def tap(k):c.press(k,True);time.sleep(.04);c.press(k,False)
def button(label):
 until(lambda:any(label in k and v['enabled'] for k,v in state().get('menuButtons',{}).items()))
 rows=[v for k,v in state()['menuButtons'].items() if label in k and v['enabled']];assert len(rows)==1,(label,state()['menuButtons']);v=rows[0];c.click(round(v['x']),round(v['y']));time.sleep(.2)
def wheel():
 l,t,_,_=c.bounds();u.SetCursorPos(l+650,t+420);emit(Input(type=0,payload=Payload(mouse=Mouse(data=(-240)&0xffffffff,flags=0x0800))));time.sleep(.15)
def record():
 global encoded
 previous=None
 while not stop.is_set():
  try:
   c.guard();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=c.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
   while encoded/30<now:writer.write(previous if previous is not None else frame);encoded+=1
   previous=frame
  except (AssertionError,RuntimeError,OSError,cv2.error):pass
  time.sleep(.015)
def log_after(offset):return c.log.read_bytes()[offset:].decode('utf-8-sig')
def boot():
 if state()['controlState']==0:tap('Escape');time.sleep(.15)
 offset=c.log.stat().st_size;button('Back to Boot');until(lambda:'LoadMap: /Game/AnimeMMORPG/Maps/L_Boot' in log_after(offset));time.sleep(.8)
def lab():
 offset=c.log.stat().st_size;old=state()['runID'];c.click(640,30)
 until(lambda:'LoadMap: /Game/AnimeMMORPG/Maps/L_CharacterCombatLab' in log_after(offset));until(lambda:state()['runID']!=old);time.sleep(.3)
try:
 c.focus();observed=c.probe_w()
 if observed!='W':c.toggle_ime();c.ime=True;assert c.probe_w()=='W'
 writer=cv2.VideoWriter(str(a.out/'Lifecycle-D.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert writer.isOpened();worker=threading.Thread(target=record);worker.start()
 if a.reopen:
  v=state();settings=json.loads(v['settings']);assert settings['bindings']['Target']=='T',settings
  assert v['encounter']['monsterVital']['hp']==600 and v['combat']['energy']==100 and v['combat']['qReady']==0 and v['combat']['eReady']==0
  m['checks'].append(dict(check='Quit/reopen retains binding without combat progress',result='PASS',metrics=v))
 else:
  boot();ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/'Boot.png')
  for i in range(5):
   lab();v=state()
   if v['controlState']!=0:button('Resume')
   time.sleep(.15);boot();m['cycles'].append(dict(index=i+1,ownedLab=v,bootLogVerified=True));ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/f'Boot-{i+1}.png')
  lab()
  if state()['controlState']==0:tap('Escape');time.sleep(.2)
  button('/ Controls')
  for _ in range(15):
   if 'Tab' in state().get('menuButtons',{}):break
   wheel()
  v=state()['menuButtons']['Tab'];c.click(round(v['x']),round(v['y']));until(lambda:state()['pendingRebind']==14);tap('T');until(lambda:json.loads(state()['settings'])['bindings']['Target']=='T')
  for _ in range(15):
   if 'Save' in state().get('menuButtons',{}):break
   wheel()
  button('Save');button('menu');m['checks'].append(dict(check='Actual binding saved before Quit',result='PASS',metrics=state()))
 if state()['controlState']==0:tap('Escape');time.sleep(.15)
 c.finish();button('Quit');m['completed']=True
except Exception as e:m['error']=repr(e);raise
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 m['encodedFPS']=30;m['videoSeconds']=encoded/30;(a.out/'lifecycle.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps(dict(completed=m['completed'],cycles=len(m['cycles']))))
