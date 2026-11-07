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
 bounds=c.bounds();l,t,rr,b=bounds;writer=cv2.VideoWriter(str(a.out/'Input-A1.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(rr-l,b-t));assert writer.isOpened();start=time.perf_counter()
 if c.metrics()['controlState']!=0:resume()
 console('U02ECrit off');console('U02EResetDummies');console('U01FixtureReset CombatD3');wait(.6)
 before,after=combo(9)
 check('Three combos confirm9 hits',after['combat']['damageResults']-before['combat']['damageResults']==9)
 check('Dummy600 dies on hit9',after['combat']['lastTargetHP']==0 and after['combat']['lastDeath'])
 check('Hit9 definition3 raw90',after['combat']['definition']==2 and after['combat']['lastDamage']==90)
 ImageGrab.grab(bbox=bounds,all_screens=True).save(a.out/'NineHits.png')
 console('U02EResetDummies');console('U01FixtureReset CombatD3');wait(.5)
 b=c.metrics();c.attack(True);wait(1.0);c.attack(False);wait(.25);v=c.metrics()
 check('Held Attack never loops',v['combat']['action']==b['combat']['action']+1)
 # A valid queued edge is removed by an actual menu transition.
 console('U01FixtureReset CombatD3');wait(.4);tap()
 while c.metrics()['worldSeconds']-c.metrics()['combat']['start']<.26:grab()
 tap();v=c.metrics();m['stages'].append({'stage':'MenuBefore','metrics':v});check('Menu precondition pending normal action',v['combat']['pendingCommand']!=0 and v['combat']['locked']);c.press('Escape',True);wait(.025);c.press('Escape',False);wait(.8)
 check('Menu enters control lock',c.metrics()['controlState']!=0)
 check('Menu clears pending successor',c.metrics()['combat']['action']==v['combat']['action'])
 resume();wait(.3)
 # Actual Windows minimization produces focus loss; no input is injected while unfocused.
 console('U01FixtureReset CombatD3');wait(.4);tap()
 while c.metrics()['worldSeconds']-c.metrics()['combat']['start']<.252:grab()
 # Do not spend the remaining buffer window in screenshot work before OS deactivation.
 c.attack(True);m['inputEvents'].append({'wall':time.perf_counter()-start,'edge':'FocusQueueDown'});time.sleep(.006);c.attack(False)
 deadline=time.perf_counter()+.06
 while time.perf_counter()<deadline:
  focus_before=c.metrics()
  if focus_before['combat']['pendingCommand']!=0:break
  time.sleep(.001)
 m['stages'].append({'stage':'FocusBefore','metrics':focus_before})
 check('Focus precondition pending normal action',focus_before['combat']['pendingCommand']!=0 and focus_before['combat']['locked'])
 check('Focus scheduled before late recovery edge',focus_before['worldSeconds']-focus_before['combat']['start']<.325)
 gap_start=time.perf_counter()-start
 u.ShowWindow(c.hwnd,6);time.sleep(.7)
 now=time.perf_counter()-start
 while encoded/30<now:writer.write(previous);encoded+=1
 m.setdefault('unfocusedVideoIntervals',[]).append({'begin':gap_start,'end':now,'presentation':'last visible game frame held while HWND minimized; no input injection'})
 c.focus();wait(.25);focus_after=c.metrics()
 check('Actual focus loss requires Resume',focus_after['controlState']!=0)
 check('Focus loss clears pending without cancelling accepted action',focus_after['combat']['action']==focus_before['combat']['action'] and not focus_after['combat']['locked'])
 m['stages'].append({'stage':'Focus','before':focus_before,'after':focus_after})
 resume();wait(.3)
 # Real held movement resumes on the open runway, not against the partial-wall fixture.
 console('U01FixtureReset Runway');wait(.4);tap();c.press('W',True);wait(.25)
 locked=c.metrics();check('Movement still locked during action',locked['combat']['locked'] and speed(locked)<1.)
 wait(.35);moving=c.metrics();c.press('W',False);check('Held W resumes after recovery',speed(moving)>400)
 m['stages'].append({'stage':'HeldW','locked':locked,'moving':moving})
 # Geometry wall fixture uses physical Attack, not an RPC hit.
 console('U02EResetDummies');console('U01FixtureReset CombatD2');wait(.5);b=c.metrics();tap();wait(.7)
 check('Wall prevents physical attack damage',c.metrics()['combat']['damageResults']==b['combat']['damageResults'])
 ImageGrab.grab(bbox=bounds,all_screens=True).save(a.out/'Final.png')
 m['completed']=True
finally:
 if start is not None:
  m['captureSeconds']=m['frames'][-1] if m['frames'] else 0;m['videoSeconds']=encoded/30;m['encodedFrames']=encoded;m['encodedFPS']=30
 if writer:writer.release()
 c.finish();m['externalInputMethodRestored']=not c.ime
 (a.out/'input.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({'completed':m['completed'],'checks':len(m['checks']),'seconds':m.get('captureSeconds')}))
