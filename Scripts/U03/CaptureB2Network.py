"""Physical Dodge across two clients, compare authority state/position and negative probes."""
import argparse,json,time,threading,re,cv2,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from B2NetworkClient import B2NetworkClient
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));clients=[B2NetworkClient(r) for r in records if r['role']!='Server'];cv2.setNumThreads(1)
m={'completed':False,'checks':[],'stages':[],'processes':records};active=None;writer=None;start=0;encoded=0;prev=None;last=0;stop=threading.Event();worker=None;screens={}
def check(n,v):m['checks'].append({'check':n,'result':'PASS' if v else 'FAIL'});assert v,n
def vec(s):return np.array([float(x) for x in re.findall(r'[XYZ]=([-0-9.]+)',s)])
def record():
 global encoded,prev,last
 while not stop.is_set():
  try:
   active.guard();bs=[c.bounds() for c in clients];l=min(x[0] for x in bs);t=min(x[1] for x in bs);r=max(x[2] for x in bs);b=max(x[3] for x in bs);screen=np.array(ImageGrab.grab(bbox=(l,t,r,b),all_screens=True));frame=cv2.cvtColor(np.concatenate([screen[y-t:yy-t,x-l:xx-l] for x,y,xx,yy in bs],axis=1),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
   while encoded/30<now:writer.write(prev if prev is not None else frame);encoded+=1
   prev=frame;last=now
  except (AssertionError,RuntimeError):m['skippedUnfocusedFrames']=m.get('skippedUnfocusedFrames',0)+1
  time.sleep(.008)
def states():
 out=[]
 for r in records:
  with Path(r['log']).open('rb') as f:f.seek(0,2);end=f.tell();f.seek(max(0,end-500000));raw=f.read()
  if end>500000:raw=raw[raw.find(b'\n')+1:]
  lines=raw[:raw.rfind(b'\n')+1].decode('utf-8-sig').splitlines();v=[json.loads(l.split('U02F_STATE ',1)[1]) for l in lines if 'U02F_STATE {' in l][-1];assert v['pid']==r['pid'] and v['sourceSHA']==r['sourceSHA'];out.append(v)
 return out
def histories():
 out=[]
 for r in records:
  with Path(r['log']).open('rb') as f:f.seek(0,2);end=f.tell();f.seek(max(0,end-15000000));raw=f.read()
  if end>15000000:raw=raw[raw.find(b'\n')+1:]
  lines=raw[:raw.rfind(b'\n')+1].decode('utf-8-sig').splitlines();out.append([json.loads(l.split('U02F_STATE ',1)[1]) for l in lines if 'U02F_STATE {' in l])
 return out
def tap(key):active.press(key,True);time.sleep(.035);active.press(key,False)
def until(f,t=3):
 end=time.perf_counter()+t
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Network physical condition timeout')
  time.sleep(.006)
def command(label):
 (a.session/'command.txt').write_text(str(time.time_ns())+' '+label,encoding='utf-8');time.sleep(.2)
def owned(identity):
 return [next(p for p in v['pawns'] if p['id']==identity) for v in states()]
def compare(identity,label):
 time.sleep(.4);ps=owned(identity);keys=['life','guardSequence','guard','posture','hardCC','hardEnd','xReady','parryReady','defenseResult','defenseEvent']
 check(label+' identity/state agreement across server and both clients',all(all(p[k]==ps[0][k] for k in keys) and p['vital']['hp']==ps[0]['vital']['hp'] for p in ps));m['stages'].append({'stage':label,'states':states(),'samples':ps})
def reset():command('b2-off');command('hit');time.sleep(.3)
try:
 for c in clients:active=c;c.prepare()
 active=clients[0];active.prepare();writer=cv2.VideoWriter(str(a.out/'Network-B2.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1800,540));assert writer.isOpened();start=time.perf_counter();worker=threading.Thread(target=record);worker.start()
 for ix,c in enumerate(clients):
  if ix:active.finish()
  active=c;c.prepare();reset();identity=c.metrics()['combat']['pawnId'];c.press('RMB',True);command('b2-block');until(lambda:c.metrics()['combat']['posture']==75,4);command('b2-off');c.press('RMB',False);compare(identity,'Client'+str(ix)+'Block')
  ps=owned(identity);check('Block damage18 and posture75',all(p['vital']['hp']==982 and p['posture']==75 for p in ps))
  reset();command('b2-block');server=Path(records[0]['log']).read_text(encoding='utf-8-sig');s=float(re.findall(r'U03B2_FIXTURE label=block start=([0-9.]+)',server)[-1]);line=[l for l in server.splitlines() if 'U03B2_FIXTURE label=block start=' in l][-1];wall=datetime.strptime(re.search(r'\[([0-9.:-]+)\]',line).group(1),'%Y.%m.%d-%H.%M.%S:%f').replace(tzinfo=timezone.utc).timestamp();until(lambda:time.time()>=wall+1.10);c.press('RMB',True);until(lambda:c.metrics()['combat']['defenseResult']==2);command('b2-off');c.press('RMB',False);compare(identity,'Client'+str(ix)+'Parry');check('Parry leaves HP and posture intact',all(p['vital']['hp']==1000 and p['posture']==100 for p in owned(identity)))
  reset();command('b2-unparryable');c.press('RMB',True);until(lambda:c.metrics()['combat']['hardCC']==5,6);check('Physical network break',c.metrics()['combat']['posture']==0);tap('X');until(lambda:c.metrics()['combat']['xReady']>c.metrics()['combat']['serverSnapshotSeconds']+28);command('b2-off');c.press('RMB',False);compare(identity,'Client'+str(ix)+'BreakX');check('X release agrees',all(p['hardCC']==0 and p['posture']==100 and p['xReady']>p['serverSnapshotSeconds'] for p in owned(identity)))
  base=owned(identity)[0];before=(base['xReady'],base['parryReady'],base['action'])
  for probe in ['duplicate','stale','nan','other']:c.console('U02NetProbe '+probe);time.sleep(.2)
  after=owned(identity)[0];check('Duplicate stale malformed and unowned do not replay defense/X',before==(after['xReady'],after['parryReady'],after['action']));m['stages'].append({'stage':'Negative'+str(ix),'states':states()})
  oldlife=after['life'];reset();ps=owned(identity);check('Reset increments life and clears defense/CC/X',all(p['life']>oldlife and not p['guard'] and p['posture']==100 and p['hardCC']==0 and p['xReady']==0 and p['slow']==0 for p in ps));m['stages'].append({'stage':'Reset'+str(ix),'states':states()})
 expected={'t.MaxFPS':60,'r.ScreenPercentage':50,'t.IdleWhenNotForeground':0}
 for i,v in enumerate(states()[1:]):check('Client'+str(i)+' client60 profile',all(v[k]==x for k,x in expected.items()))
 check('Dedicated server30',states()[0]['t.MaxFPS']==30);m['completed']=True
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 command('b2-off')
 for c in clients:
  if c.ime:c.focus()
  if c.ime and c.metrics()['controlState']==0:c.press('Escape',True);time.sleep(.035);c.press('Escape',False);time.sleep(.2)
  c.finish()
 m.update(videoSeconds=encoded/30,captureSeconds=last,encodedFPS=30);(a.out/'network.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({'completed':m['completed'],'checks':len(m['checks'])}))
