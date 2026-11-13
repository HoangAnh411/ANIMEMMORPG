"""B2 package: guarded physical defense input and wall-clock video; enemies only via fixture."""
import argparse,json,time,threading,re,cv2,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from C1Client import C1Client,u
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
c=C1Client(json.loads(a.record.read_text(encoding='utf-8-sig')));cv2.setNumThreads(1)
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
 writer=cv2.VideoWriter(str(a.out/'Input-C1.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert writer.isOpened();start=time.perf_counter();worker=threading.Thread(target=record);worker.start()
 if c.metrics()['controlState']!=0:c.click(640,305);wait(.4)
 check('Actual Resume enters Playing',c.metrics()['controlState']==0)

 def skill(key,definition):
  tap(key);until(lambda:b()['definition']==definition and b()['phase']==1)
 def speed():return np.linalg.norm([float(x) for x in re.findall(r'[XY]=([-0-9.]+)',c.metrics()['velocityCmPerSec'])])
 reset();skill('Q',3);check('Q accepted spends20 and starts4s CD',b()['energy']==80 and 3.8<b()['qReady']-b()['serverSnapshotSeconds']<=4)
 tap('Q');until(lambda:b()['feintSequence']==1);check('New Q edge Feints current Q, no refund',not b()['locked'] and b()['energy']==80 and b()['feintAction']==b()['action']);m['stages'].append({'stage':'Feint','metrics':c.metrics()})
 tap('Space');c.press('W',True);c.press('Ctrl',True);wait(.08);check('Feint refuses jump and sprint',not c.metrics()['bufferedJump'] and not c.metrics()['sprinting']);wait(.4);check('Feint permits held walking after skill cutoff',speed()>400);c.press('W',False);c.press('Ctrl',False)
 reset();c.press('Q',True);until(lambda:b()['definition']==3 and b()['phase']==1);wait(.45);check('Held Q does not Feint or repeat',b()['feintSequence']==0 and b()['definition']==3 and b()['phase']==3);c.press('Q',False);wait(.5)
 reset();skill('E',4);check('E spends25 and starts6s CD',b()['energy']==75 and 5.8<b()['eReady']-b()['serverSnapshotSeconds']<=6);c.press('W',True);wait(.85);check('Held WASD resumes after E recovery',speed()>400);c.press('W',False)
 for combo in range(3):
  reset();c.attack(True);wait(.035);c.attack(False)
  for j in range(combo):
   until(lambda:b()['definition']==j and b()['phase']==3);c.attack(True);wait(.035);c.attack(False);until(lambda:b()['definition']==j+1)
  until(lambda:b()['definition']==combo and b()['phase']==3);old=b()['action'];tap('Q' if combo!=1 else 'E');until(lambda:b()['action']>old)
  check('Physical recovery chain attack'+str(combo+1),b()['definition']==(4 if combo==1 else 3));m['stages'].append({'stage':'Recovery'+str(combo+1),'metrics':c.metrics()});wait(.9)
 for key,replace in [('Q','Shift'),('E','RMB')]:
  reset();skill(key,3 if key=='Q' else 4);c.press(replace,True);wait(.08);check('Physical '+replace+' cancels '+key+' startup',b()['phase']==5 and (b()['guard'] if replace=='RMB' else b()['dodge']>0));c.press(replace,False);wait(.7)
 reset();c.press('RMB',True);until(lambda:b()['guard']);tap('Q');wait(.08);check('Guard requires voluntary release before Q',b()['guard'] and b()['energy']==100);c.press('RMB',False)
 reset();s=fixture('target-q');until(lambda:time.time()>=fixture_wall+.90);tap('E');wait(.6);raw=c.log.read_text(encoding='utf-8-sig');check('Real E collision Interrupts labelled Q startup','"interrupted":true' in raw);console('U03B2Fixture off')
 reset();fixture('incoming-e');until(lambda:time.time()>=fixture_wall+1.05);tap('Q');until(lambda:b()['interruptSequence']>0);check('Incoming real E Interrupt cancels player Q without refund',b()['energy']==80 and b()['hardCC']==0 and b()['phase']==5);console('U03B2Fixture off');m['stages'].append({'stage':'IncomingInterrupt','metrics':c.metrics()})
 reset();c.press('Q',True);until(lambda:b()['definition']==3);tap('Escape');wait(.2);check('Menu does not refund or cancel accepted Q',b()['qReady']>b()['serverSnapshotSeconds']);c.click(640,305);wait(.5);check('Held Q across Resume does not replay',b()['action']==1 and b()['feintSequence']==0);c.press('Q',False)
 c.guard();u.ShowWindow(c.hwnd,6);wait(.4);c.focus();check('Focus loss requires Resume',c.metrics()['controlState']!=0);c.click(640,305);wait(.3)
 ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/'Final.png');m['completed']=True
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 if c.ime and c.metrics()['controlState']==0:tap('Escape');wait(.2)
 c.finish();m.update(captureSeconds=last,videoSeconds=encoded/30,encodedFPS=30,externalInputMethodRestored=not c.ime);(a.out/'input.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({'completed':m['completed'],'checks':len(m['checks'])}))
