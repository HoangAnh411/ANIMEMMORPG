"""Labelled regression fixtures, guarded real input/video; no product encounter runs alongside them."""
import argparse,json,time,threading,re,cv2,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from DClient import DClient,u
from F60Input import Input,Payload,Mouse,emit
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
c=DClient(json.loads(a.record.read_text(encoding='utf-8-sig')));cv2.setNumThreads(1)
m=dict(completed=False,process=c.record,checks=[],stages=[],events=[]);stop=threading.Event();writer=None;worker=None;start=time.perf_counter();encoded=0;previous=None
def state():return c.metrics()
def b():return state()['combat']
def until(f,timeout=6):
 end=time.perf_counter()+timeout
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Condition timeout: '+str(state()))
  time.sleep(.01)
def check(n,ok):m['checks'].append(dict(check=n,result='PASS' if ok else 'FAIL',metrics=state()));assert ok,n
def tap(k):
 if k=='LMB':c.attack(True);time.sleep(.035);c.attack(False)
 else:c.press(k,True);time.sleep(.035);c.press(k,False)
 m['events'].append(dict(key=k,wall=time.perf_counter()-start))
def button(label):
 until(lambda:any(label in k and v['enabled'] for k,v in state().get('menuButtons',{}).items()))
 matches=[(k,v) for k,v in state()['menuButtons'].items() if label in k and v['enabled']];assert len(matches)==1,(label,matches)
 name,v=matches[0];c.click(round(v['x']),round(v['y']));time.sleep(.2);m['events'].append(dict(button=name,wall=time.perf_counter()-start))
def resume():
 if state()['controlState']!=0:button('Resume')
 until(lambda:state()['controlState']==0)
def console(s):c.console(s);time.sleep(.16);m['events'].append(dict(fixture=s,wall=time.perf_counter()-start))
def reset():console('U03B2Fixture off');console('U01FixtureReset Runway');time.sleep(.25)
def fixture(label):
 console('U03B2Fixture '+label);text=c.log.read_text(encoding='utf-8-sig');line=[x for x in text.splitlines() if 'U03B2_FIXTURE label='+label+' start=' in x][-1]
 return datetime.strptime(re.search(r'\[([0-9.:-]+)\]',line).group(1),'%Y.%m.%d-%H.%M.%S:%f').replace(tzinfo=timezone.utc).timestamp()
def snap(name):ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/(name+'.png'));m['stages'].append(dict(stage=name,metrics=state()))
def wheel(delta):
 c.guard();l,t,_,_=c.bounds();u.SetCursorPos(l+650,t+420);emit(Input(type=0,payload=Payload(mouse=Mouse(data=delta&0xffffffff,flags=0x0800))));time.sleep(.15)
def bind(index,old,new):
 if state()['controlState']==0:tap('Escape');time.sleep(.15)
 button('/ Controls')
 for _ in range(15):
  if old in state().get('menuButtons',{}):break
  wheel(-240)
 v=state()['menuButtons'][old];c.click(round(v['x']),round(v['y']));until(lambda:state()['pendingRebind']==index);tap(new);time.sleep(.15)
 for _ in range(15):
  if 'Save' in state().get('menuButtons',{}):break
  wheel(-240)
 button('Save');button('menu');resume()
def record():
 global encoded,previous
 while not stop.is_set():
  try:
   c.guard();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=c.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
   while encoded/30<now:writer.write(previous if previous is not None else frame);encoded+=1
   previous=frame
  except (AssertionError,RuntimeError,OSError,cv2.error):m['skippedFrames']=m.get('skippedFrames',0)+1
  time.sleep(.012)
try:
 c.focus();observed=c.probe_w()
 if observed!='W':c.toggle_ime();c.ime=True;assert c.probe_w()=='W'
 writer=cv2.VideoWriter(str(a.out/'Regression-D.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert writer.isOpened();worker=threading.Thread(target=record);worker.start();resume()
 check('Regression run has no product encounter',not state().get('encounter'))
 reset();tap('Q');until(lambda:b()['definition']==3 and b()['phase']==1);tap('Q');until(lambda:b()['feintSequence']==1);snap('Feint');check('Physical Q edge Feints without refund',b()['energy']==80);time.sleep(1.3)
 reset();tap('LMB');until(lambda:b()['phase']==1);until(lambda:b()['phase']==3);tap('LMB');until(lambda:b()['definition']==1);until(lambda:b()['phase']==3);tap('LMB');until(lambda:b()['definition']==2);time.sleep(.65);snap('ComboMiss')
 reset();tap('Shift');until(lambda:b()['dodge']>0);snap('Dodge');time.sleep(.4)
 reset();wall=fixture('block');until(lambda:time.time()>=wall+1.10);c.press('RMB',True);until(lambda:b()['defenseResult']==2);snap('Parry');until(lambda:b()['defenseResult']==1);snap('Block');check('Parry then held block confirmed',b()['posture']==75);c.press('RMB',False);console('U03B2Fixture off')
 reset();fixture('unparryable');c.press('RMB',True);until(lambda:b()['hardCC']==5,8);snap('Break');check('Guard breaks after four blocks',b()['posture']==0 and not b()['guard']);tap('X');until(lambda:b()['hardCC']==0);snap('X');check('X clears break and restores posture',b()['posture']==100);c.press('RMB',False);console('U03B2Fixture off')
 for label,kind in [('stun',1),('knockdown',2),('launch',3),('grab',4)]:
  reset();fixture(label);until(lambda:b()['hardCC']==kind);snap('CC-'+label);tap('X');until(lambda:b()['hardCC']==0);check('X clears labelled '+label,b()['xReady']>state()['worldSeconds']);console('U03B2Fixture off')
 reset();wall=fixture('target-q');until(lambda:time.time()>=wall+.90);tap('E');until(lambda:b()['definition']==4);cast=b()['start'];time.sleep(.5);snap('Interrupt')
 events=[json.loads(x.split('U02B_EVENT ',1)[1]) for x in c.log.read_text(encoding='utf-8-sig').splitlines() if 'U02B_EVENT {' in x]
 check('Real E Interrupts fixture startup',any(x['pawnId']!=b()['pawnId'] and x['interruptTime']>=cast and x['interruptedAction']>0 for x in events));console('U03B2Fixture off')
 reset();c.press('RMB',True);until(lambda:b()['guard']);tap('Escape');time.sleep(.2);resume();check('Held guard does not rearm through menu',not b()['guard']);c.press('RMB',False)
 c.press('Q',True);until(lambda:b()['definition']==3);tap('Escape');time.sleep(.2);resume();time.sleep(.9);check('Held Q does not replay through Resume',b()['action']==1 and b()['feintSequence']==0);c.press('Q',False)
 c.guard();u.ShowWindow(c.hwnd,6);time.sleep(.4);c.focus();check('Focus loss requires explicit Resume',state()['controlState']!=0);resume()
 bind(9,'Right Mouse Button','C');check('Guard rebound through UI',json.loads(state()['settings'])['bindings']['Guard']=='C');tap('RMB');check('Old guard binding inactive',not b()['guard']);c.press('C',True);until(lambda:b()['guard']);c.press('C',False);bind(9,'C','RMB')
 snap('Final');m['completed']=True
except Exception as e:m['error']=repr(e);raise
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 c.finish();m['videoSeconds']=encoded/30;m['encodedFPS']=30;(a.out/'regression.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps(dict(completed=m['completed'],checks=len(m['checks']))))
