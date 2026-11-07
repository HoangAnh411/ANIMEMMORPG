"""A1 physical input + wall-clock video. Every input is guarded to the owned game HWND."""
import argparse,json,time,re,math,cv2,numpy as np
from pathlib import Path
from PIL import ImageGrab
from A1Client import A1Client,u
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--resume-y',type=int,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
r=json.loads(a.record.read_text(encoding='utf-8-sig'));c=A1Client(r);cv2.setNumThreads(1)
m={'process':r,'completed':False,'checks':[],'stages':[],'frames':[],'inputEvents':[]};writer=None;start=None;encoded=0;previous=None

def check(name,value):
 m['checks'].append({'check':name,'result':'PASS' if value else 'FAIL'});assert value,name

def speed(v):
 values=[float(x) for x in re.findall(r'[XYZ]=([-0-9.]+)',v['velocityCmPerSec'])];return math.hypot(values[0],values[1])

def grab():
 global previous,encoded
 if m['frames'] and time.perf_counter()-start-m['frames'][-1]<1./30:return
 c.guard();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=bounds,all_screens=True)),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
 while encoded/30<now:writer.write(previous if previous is not None else frame);encoded+=1
 previous=frame;m['frames'].append(now)

def wait(seconds):
 until=time.perf_counter()+seconds
 while time.perf_counter()<until:grab();time.sleep(.004)

def tap():
 c.attack(True);m['inputEvents'].append({'wall':time.perf_counter()-start,'edge':'AttackDown'});wait(.025);c.attack(False);m['inputEvents'].append({'wall':time.perf_counter()-start,'edge':'AttackUp'})

def console(text):
 before=c.metrics()['combat']['command'];c.console(text);m['inputEvents'].append({'wall':time.perf_counter()-start,'consoleFixture':text});wait(.35)
 check('Console consumes binding keys: '+text,c.metrics()['combat']['command']==before)

def resume():
 c.click(640,a.resume_y);wait(.4);check('Physical Resume enters Playing',c.metrics()['controlState']==0)

def combo(actions=3):
 before=c.metrics();base=int(before['combat']['action']);tap();seen={};sent=set();deadline=time.perf_counter()+10
 while time.perf_counter()<deadline:
  grab();v=c.metrics();b=v['combat'];seq=int(b['action']);index=seq-base
  if 1<=index<=actions:
   seen.setdefault(index,{'definition':int(b['definition']),'start':b['start'],'life':b['life'],'action':seq})
   if index<actions and index not in sent and b['locked']:
    elapsed=v['worldSeconds']-b['start'];threshold=.27 if b['definition']==0 else .32 if b['definition']==1 else .47
    if elapsed>=threshold:tap();sent.add(index)
   if index==actions and not b['locked']:break
  time.sleep(.004)
 else:raise RuntimeError('Combo completion timeout')
 after=c.metrics();check('Physical combo action count',int(after['combat']['action'])-base==actions)
 check('All action definitions observed',len(seen)==actions)
 for i,x in sorted(seen.items()):check('Definition for action '+str(i),x['definition']==(i-1)%3)
 m['stages'].append({'stage':'ComboTiming','actions':seen,'wall':time.perf_counter()-start})
 # Queued successors must use exact definition duration, independent of wall-clock capture FPS.
 for i in range(2,actions+1):
  delta=seen[i]['start']-seen[i-1]['start'];expect=(.40,.45,.60)[seen[i-1]['definition']]
  check('Queued action starts at predecessor end '+str(i),abs(delta-expect)<1.e-9)
 m['stages'].append({'stage':'Combo'+str(actions),'before':before,'after':after,'actions':seen,'wall':time.perf_counter()-start})
 return before,after

try:
 c.focus();observed=c.probe_w()
 if observed!='W':c.toggle_ime();c.ime=True;observed=c.probe_w()
 assert observed=='W'
 bounds=c.bounds();l,t,rr,b=bounds;writer=cv2.VideoWriter(str(a.out/'Input-A1-Turn.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(rr-l,b-t));assert writer.isOpened();start=time.perf_counter()
 if c.metrics()['controlState']!=0:resume()
 console('U01FixtureReset Runway');wait(.5);base=int(c.metrics()['combat']['action']);tap()
 def elapsed():
  v=c.metrics();return v['worldSeconds']-v['combat']['start']
 def until(predicate,seconds=2):
  end=time.perf_counter()+seconds
  while not predicate():
   if time.perf_counter()>end:raise RuntimeError('Physical turn boundary timeout')
   grab();time.sleep(.002)
 screens={}
 for i,(active,recovery,duration,delta) in enumerate([(.16,.22,.40,8),(.18,.25,.45,-8),(.26,.36,.60,8)]):
  until(lambda:int(c.metrics()['combat']['action'])==base+i+1)
  v0=c.metrics();wait(.025);c.guard()
  from A1Client import mouse
  mouse(1,delta,0);m['inputEvents'].append({'wall':time.perf_counter()-start,'mouseStartupDelta':delta,'definition':i})
  until(lambda:elapsed()>=active+.012);v1=c.metrics()
  check('Definition'+str(i+1)+' uses its own startup deadline',v1['combat']['definition']==i and v1['combat']['yawLocked'])
  check('Definition'+str(i+1)+' montage presented',v1['attackPresented'])
  check('Definition'+str(i+1)+' startup physical mouse changes body',abs(v1['bodyYawDegrees']-v0['bodyYawDegrees'])>.1)
  screens[i]=previous.copy()
  c.guard();mouse(1,int(-delta*.75),0);m['inputEvents'].append({'wall':time.perf_counter()-start,'mouseActiveDelta':-delta*.75,'definition':i})
  wait(.05);until(lambda:elapsed()>=recovery+.02);v2=c.metrics()
  m['stages'].append({'stage':'TurnBeforeAssertions'+str(i+1),'startup':v0,'active':v1,'recovery':v2})
  check('Definition'+str(i+1)+' active/recovery body locked',abs(v2['bodyYawDegrees']-v1['bodyYawDegrees'])<.05)
  check('Definition'+str(i+1)+' camera remains free',v2['aimYawPitchDegrees']!=v1['aimYawPitchDegrees'])
  m['stages'].append({'stage':'Turn'+str(i+1),'startup':v0,'active':v1,'recovery':v2})
  if i<2:
   until(lambda:elapsed()>=(.27 if i==0 else .32));tap()
  else:until(lambda:not c.metrics()['combat']['locked'])
 for i,frame in screens.items():cv2.imwrite(str(a.out/('Attack'+str(i+1)+'.png')),frame)
 m['completed']=True
finally:
 if start is not None:m['captureSeconds']=m['frames'][-1] if m['frames'] else 0;m['videoSeconds']=encoded/30;m['encodedFrames']=encoded;m['encodedFPS']=30
 if writer:writer.release()
 c.finish();m['externalInputMethodRestored']=not c.ime;(a.out/'input.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({'completed':m['completed'],'checks':len(m['checks']),'seconds':m.get('captureSeconds')}))
