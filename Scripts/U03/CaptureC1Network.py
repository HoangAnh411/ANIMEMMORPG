"""Physical Dodge across two clients, compare authority state/position and negative probes."""
import argparse,json,time,threading,re,cv2,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from C1NetworkClient import C1NetworkClient
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));clients=[C1NetworkClient(r) for r in records if r['role']!='Server'];cv2.setNumThreads(1)
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
 active=clients[0];active.prepare();writer=cv2.VideoWriter(str(a.out/'Network-C1.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1800,540));assert writer.isOpened();start=time.perf_counter();worker=threading.Thread(target=record);worker.start()

 for ix,c in enumerate(clients):
  if ix:active.finish()
  active=c;c.prepare();reset();identity=c.metrics()['combat']['pawnId']
  def combat():return c.metrics()['combat']
  tap('Q');until(lambda:combat()['definition']==3 and combat()['phase']==1);tap('Q');until(lambda:combat()['feintSequence']==1)
  compare(identity,'Client'+str(ix)+'Feint');ps=owned(identity)
  keys=['action','definition','qReady','eReady','feintSequence','feintAction','feintLockEnd','feintLastSuccess']
  check('Three-process Q/Feint identity and deadlines',all(all(p[k]==ps[0][k] for k in keys) for p in ps));check('Feint spends only cast energy',all(80<=p['energy']<84 for p in ps))
  reset();tap('E');until(lambda:combat()['definition']==4);compare(identity,'Client'+str(ix)+'E');ps=owned(identity)
  check('Three-process E definition/raw/cooldown',all(p['definition']==4 and p['raw']==80 and p['eReady']==ps[0]['eReady'] and 75<=p['energy']<79 for p in ps))
  time.sleep(.5);base=owned(identity)[0];before=(base['qReady'],base['eReady'],base['action'],base['feintSequence'])
  for probe in ['duplicate','stale','nan','other']:c.console('U02NetProbe '+probe);time.sleep(.2)
  after=owned(identity)[0];check('Rejected RPCs do not replay skills/resources',before==(after['qReady'],after['eReady'],after['action'],after['feintSequence']))
  reset();command('b2-incoming-e')
  server=Path(records[0]['log']).read_text(encoding='utf-8-sig');line=[l for l in server.splitlines() if 'U03B2_FIXTURE label=incoming-e start=' in l][-1];wall=datetime.strptime(re.search(r'\[([0-9.:-]+)\]',line).group(1),'%Y.%m.%d-%H.%M.%S:%f').replace(tzinfo=timezone.utc).timestamp()
  until(lambda:time.time()>=wall+1.05);tap('Q');until(lambda:combat()['interruptSequence']>0);command('b2-off');compare(identity,'Client'+str(ix)+'IncomingInterrupt');ps=owned(identity)
  keys=['action','life','interruptSequence','interruptedAction','interruptTime','qReady','hardCC']
  check('Three-process incoming E Interrupt matches life/action',all(all(p[k]==ps[0][k] for k in keys) for p in ps) and ps[0]['hardCC']==0)
  vs=states();last=[next(r for r in reversed(v['results']) if r['target']==identity and r['interrupted']) for v in vs]
  check('Damage/Interrupt history agrees across three processes',last[0]==last[1]==last[2]);m['stages'].append({'stage':'InterruptedResults'+str(ix),'states':vs})
  oldlife=ps[0]['life'];reset();ps=owned(identity);check('New life resets skill/Feint/Interrupt without replay',all(p['life']>oldlife and p['action']==0 and p['energy']==100 and p['qReady']==p['eReady']==p['feintSequence']==p['interruptSequence']==0 for p in ps))
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
