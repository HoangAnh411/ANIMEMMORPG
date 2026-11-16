"""Scoped real Windows input, two GPU viewports, output loopback; no microphone."""
import argparse,json,time,threading,wave,warnings,re
from pathlib import Path
import cv2,numpy as np,soundcard as sc
from PIL import ImageGrab
from DNetworkClient import DNetworkClient
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));clients=[DNetworkClient(next(r for r in records if r['role']==s)) for s in ['ClientA','ClientB']]
m=dict(completed=False,processes=records,checks=[],stages=[],samples=[],warnings=[],input='Sequential physical Windows keys in guarded HWNDs',debugOverlay=False)
warnings.showwarning=lambda message,category,filename,lineno,*args,**kwargs:m['warnings'].append(str(message))
stop=threading.Event();frames=0;start=time.perf_counter();blocks=[];cv2.setNumThreads(1)
video=cv2.VideoWriter(str(a.out/'Visibility.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1800,540));assert video.isOpened()
speaker=sc.default_speaker();loop=sc.get_microphone(speaker.name,include_loopback=True);assert loop.isloopback
def record():
 global frames
 previous=None
 while not stop.is_set():
  try:
   frame=np.hstack([cv2.cvtColor(np.array(ImageGrab.grab(bbox=c.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR) for c in clients])
   while frames/30<time.perf_counter()-start:video.write(previous if previous is not None else frame);frames+=1
   previous=frame
  except Exception as e:m.setdefault('captureErrors',[]).append(repr(e))
  time.sleep(.02)
def audio():
 with loop.recorder(samplerate=48000,channels=2) as r:
  while not stop.is_set():blocks.append(r.record(numframes=4800))
def until(f,timeout=7):
 end=time.perf_counter()+timeout
 while True:
  v=f()
  if v:return v
  if time.perf_counter()>end:raise RuntimeError('Condition timeout')
  time.sleep(.012)
def check(name,ok):m['checks'].append(dict(name=name,result='PASS' if ok else 'FAIL'));assert ok,name
def snap(c,name):
 v=c.metrics();m['stages'].append(dict(name=name,wall=time.perf_counter()-start,metrics=v));ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/(name+'.png'));return v
def button(c,label):
 b=until(lambda:c.metrics().get('menuButtons',{}).get(label));assert b['enabled'];c.click(round(b['x']),round(b['y']));time.sleep(.1)
def tap(c,key):c.press(key,True);time.sleep(.035);c.press(key,False)
def playing(c):
 if c.metrics()['encounter']['result']:
  rev=c.metrics()['encounter']['revision'];button(c,'Retry encounter');until(lambda:c.metrics()['encounter']['revision']>rev)
 if c.metrics()['controlState']!=0:button(c,'Resume')
 until(lambda:c.metrics()['controlState']==0)
def target(c):return c.metrics()['encounter']['monsterCombat']['pawnId']
def actor(c):return next((r for r in c.metrics()['presentation']['actors'] if r['subject']==target(c)),None)
def event(c):return next((r for r in c.metrics()['presentation']['events'] if r['subject']==target(c) and r['kind']==0),None)
workers=[threading.Thread(target=record),threading.Thread(target=audio)]
for t in workers:t.start()
try:
 for c in clients:
  c.focus();observed=c.probe_w()
  if observed!='W':c.toggle_ime();c.ime=True;observed=c.probe_w()
  assert observed=='W'
  c.console('stat unit');c.console('DisableAllScreenMessages');c.console('U03R1Scene');playing(c)
  until(lambda:actor(c) and not actor(c)['visible']);snap(c,c.record['role']+'-full-wall')
  check(c.record['role']+' environment hides opponent labels',not actor(c)['subjectClear'] and not actor(c)['visible'])
  until(lambda:c.metrics()['encounter']['monsterCombat']['phase']==1 and c.metrics()['encounter']['monsterCombat']['serverSnapshotSeconds']<c.metrics()['encounter']['monsterCombat']['start']+.15)
  tap(c,'E');hidden=until(lambda:event(c));serial=hidden['serial'];check(c.record['role']+' hidden fresh contact silent',not hidden['visible'] and not hidden['audio']);snap(c,c.record['role']+'-hidden-event')
  c.press('D',True)
  try:revealed=until(lambda:(v if (v:=event(c)) and v['serial']==serial and v['visible'] else None),1)
  finally:c.press('D',False)
  snap(c,c.record['role']+'-reveal-remainder');check(c.record['role']+' reveal in original window without sound replay',revealed['remaining']>0 and not revealed['new'] and not revealed['audio'])
  until(lambda:not any(r['serial']==serial for r in c.metrics()['presentation']['events']),2)
  snap(c,c.record['role']+'-expired');check(c.record['role']+' expired event removed',not any(r['serial']==serial for r in c.metrics()['presentation']['events']))
  # Return to the station centre with physical input; never move/teleport a pawn in fixture code.
  station=c.metrics()['encounter']['station'];centre=station*5000
  c.press('A',True)
  try:until(lambda:float(re.search(r'Y=([-\d.]+)',c.metrics()['capsuleCenterWorldCm'])[1])<=centre+2,2)
  finally:c.press('A',False)
  c.console('U03R1Partial');playing(c)
  partial=until(lambda:(r if (r:=actor(c)) and r['visible'] and r['worldDepthSegments']==15 and r['blockedSegmentMidpoints']>0 and r['clearSegmentMidpoints']>0 else None),8)
  snap(c,c.record['role']+'-partial-depth');check(c.record['role']+' visible anchor with both occluded and exposed world geometry',partial['canvasTelegraphSegments']==0 if 'canvasTelegraphSegments' in partial else c.metrics()['presentation']['canvasTelegraphSegments']==0)
  check(c.record['role']+' old serial cannot return after hide/reveal',not any(r['serial']==serial for r in c.metrics()['presentation']['events']))
  # Freeze controls via the actual menu while the other physical window is exercised.
  if c.metrics()['controlState']==0:tap(c,'Escape')
 m['completed']=True
except Exception as e:m['error']=repr(e);raise
finally:
 stop.set()
 for t in workers:t.join()
 video.release();pcm=(np.clip(np.concatenate(blocks) if blocks else np.zeros((0,2)),-1,1)*32767).astype('<i2')
 with wave.open(str(a.out/'Output-Loopback.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);w.writeframes(pcm.tobytes())
 for c in clients:
  try:c.focus();c.finish()
  except Exception as e:m.setdefault('cleanupErrors',[]).append(repr(e))
 m.update(videoSeconds=frames/30,loopbackDevice=loop.name,audioSeconds=len(pcm)/48000)
 (a.out/'visibility.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps(dict(completed=m['completed'],checks=len(m['checks']))))
