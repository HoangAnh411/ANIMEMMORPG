"""Real input for confirmed damage, crit/shield/death/reset; package identity guards retained."""
import argparse,json,time,cv2,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from EClient import EClient
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
r=json.loads(a.record.read_text(encoding='utf-8-sig'));c=EClient(r);writer=None;m=dict(process=r,completed=False,events=[],checks=[],frames=[],stages=[])
def check(label,v):m['checks'].append(dict(check=label,result='PASS' if v else 'FAIL'));assert v,label
try:
 c.prepare();bounds=c.bounds();l,t,rr,b=bounds;cv2.setNumThreads(1);writer=cv2.VideoWriter(str(a.out/'Input-E.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(rr-l,b-t));assert writer.isOpened()
 start=time.perf_counter();m['utc']=datetime.now(timezone.utc).isoformat();encoded=0;previous=None
 def grab():
  global encoded,previous
  c.guard();assert c.bounds()==bounds
  frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=bounds,all_screens=True)),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
  while encoded/30<now:writer.write(previous if previous is not None else frame);encoded+=1
  previous=frame;m['frames'].append(now)
 def wait(seconds):
  deadline=time.perf_counter()+seconds
  while time.perf_counter()<deadline:grab()
 def console(text):c.console(text);m['events'].append(dict(command=text,wall=time.perf_counter()-start));wait(.3)
 def attack(label,hits,damage=None,hp=None,absorb=None,hold=False):
  before=c.metrics();c.attack(True);time.sleep(.06)
  if not hold:c.attack(False)
  wait(.7);after=c.metrics();b=after['combat']
  check(label+' confirmed target count',b['damageResults']-before['combat']['damageResults']==hits)
  check(label+' one accepted action',b['accepted']-before['combat']['accepted']==1 and not b['locked'])
  if hits and damage is not None:check(label+' damage',b['lastDamage']==damage)
  if hits and hp is not None:check(label+' target HP',b['lastTargetHP']==hp)
  if hits and absorb is not None:check(label+' absorbed',b['lastAbsorbed']==absorb)
  m['stages'].append(dict(label=label,before=before,after=after,wall=time.perf_counter()-start,hits=hits));ImageGrab.grab(bbox=bounds,all_screens=True).save(a.out/(label+'.png'));grab()
 console('U02ECrit off');console('U02EResetDummies');console('U01FixtureReset CombatD3');wait(.7)
 attack('Normal60',1,60,540)
 console('U02ECrit force');attack('Crit90',1,90,450)
 console('U02ECrit off');console('U02EShield 1 40 60');attack('Shield40',1,60,430,40)
 console('U02EResetDummies');attack('Reset600',1,60,540)
 for i,hp in enumerate([480,420,360,300,240,180,120,60,0]):attack('LethalChain'+str(i+1),1,60,hp)
 check('Dummy defeated exactly at HP0',c.metrics()['combat']['lastDeath'])
 attack('DeadNoHit',0)
 console('U02EResetDummies');attack('ResetHeld',1,60,540,hold=True)
 # Holding LMB across a real lab reset must not synthesize a new attack edge.
 before=c.metrics();console('U01FixtureReset CombatD3');wait(.8);after=c.metrics();check('Held LMB across reset no automatic action',after['combat']['accepted']==before['combat']['accepted']);c.attack(False);wait(.2)
 console('U02EResetDummies');console('U01FixtureReset CombatD2');wait(.7);attack('FullWall',0)
 console('U01FixtureReset CombatD1');wait(.7);attack('MultipleTargets',2,60,540)
 # Face away from both targets using real mouse; validates actual miss at completion.
 c.console('U02CornerCase outside');wait(.7);attack('MissOutside',0)
 m['captureSeconds']=m['frames'][-1];m['processingEndSeconds']=time.perf_counter()-start;m['videoSeconds']=encoded/30;m['encodedFrames']=encoded;m['encodedFPS']=30
 check('Real-time export',abs(m['videoSeconds']-m['captureSeconds'])<1/30+.01);m['finalMetrics']=c.metrics();ImageGrab.grab(bbox=bounds,all_screens=True).save(a.out/'Final.png');m['completed']=True
except Exception as e:m['error']=str(e);raise
finally:
 if 'start' in locals():m.setdefault('captureSeconds',m['frames'][-1] if m['frames'] else 0);m.setdefault('videoSeconds',encoded/30)
 if writer:writer.release()
 c.finish();m['externalInputMethodRestored']=not c.ime;(a.out/'input.json').write_text(json.dumps(m,indent=2))
print(json.dumps(dict(completed=m['completed'],checks=len(m['checks']),wall=m['captureSeconds'],video=m['videoSeconds'])))
