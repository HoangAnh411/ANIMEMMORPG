"""Physical Dodge across two clients, compare authority state/position and negative probes."""
import argparse,json,time,threading,re,cv2,numpy as np
from pathlib import Path
from PIL import ImageGrab
from B1NetworkClient import B1NetworkClient
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));clients=[B1NetworkClient(r) for r in records if r['role']!='Server'];cv2.setNumThreads(1)
m={'completed':False,'checks':[],'stages':[],'processes':records};active=None;writer=None;start=0;encoded=0;prev=None;last=0;stop=threading.Event();worker=None
def check(n,v):m['checks'].append({'check':n,'result':'PASS' if v else 'FAIL'});assert v,n
def vec(s):return np.array([float(x) for x in re.findall(r'[XYZ]=([-0-9.]+)',s)])
def record():
 global encoded,prev,last
 while not stop.is_set():
  try:
   active.guard();bs=[c.bounds() for c in clients];l=min(x[0] for x in bs);t=min(x[1] for x in bs);r=max(x[2] for x in bs);b=max(x[3] for x in bs);screen=np.array(ImageGrab.grab(bbox=(l,t,r,b),all_screens=True));frame=cv2.cvtColor(np.concatenate([screen[y-t:yy-t,x-l:xx-l] for x,y,xx,yy in bs],axis=1),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
   while encoded/30<now:writer.write(prev if prev is not None else frame);encoded+=1
   prev=frame;last=now
  except AssertionError:pass
  time.sleep(.008)
def states():
 out=[]
 for r in records:
  with Path(r['log']).open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-500000));raw=f.read()
  lines=raw[:raw.rfind(b'\n')+1].decode('utf-8-sig').splitlines();v=[json.loads(l.split('U02F_STATE ',1)[1]) for l in lines if 'U02F_STATE {' in l][-1];assert v['pid']==r['pid'] and v['sourceSHA']==r['sourceSHA'];out.append(v)
 return out
def tap():active.press('Shift',True);time.sleep(.035);active.press('Shift',False)
def until(f,t=3):
 end=time.perf_counter()+t
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Network physical condition timeout')
  time.sleep(.006)
try:
 for c in clients:active=c;c.prepare()
 active=clients[0];active.prepare();writer=cv2.VideoWriter(str(a.out/'Network-B1.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1800,540));assert writer.isOpened();start=time.perf_counter();worker=threading.Thread(target=record);worker.start()
 for ix,c in enumerate(clients):
  if ix:active.finish()
  active=c;c.prepare();(a.session/'command.txt').write_text(str(time.time_ns())+' hit',encoding='utf-8');time.sleep(.8)
  # Default no-WASD direction is backwards, away from technical dummy lanes.
  before=c.metrics();tap();until(lambda:c.metrics()['combat']['dodge']>before['combat']['dodge']);first=c.metrics();time.sleep(.65);s=states();identity=c.metrics()['combat']['pawnId'];pawns=[next(p for p in v['pawns'] if p['id']==identity) for v in s]
  check('Client'+str(ix)+' server accepted physical Dodge',pawns[0]['dodge']==1);check('Client'+str(ix)+' two peers agree sequence/charges',all(p['dodge']==1 and p['dodgeCharges']==1 for p in pawns));check('Client'+str(ix)+' authority swept distance',abs(np.linalg.norm((vec(pawns[0]['position'])-vec(pawns[0]['dodgeOrigin']))[:2])-300)<5)
  check('Client'+str(ix)+' peers converge to authority position',all(np.linalg.norm(vec(p['position'])-vec(pawns[0]['position']))<5 for p in pawns));check('Client'+str(ix)+' energy unchanged/no damage immunity invented',all(p['energy']==100 and p['vital']['hp']==1000 for p in pawns));m['stages'].append({'stage':'Client'+str(ix)+'Dodge','first':first,'states':s});cv2.imwrite(str(a.out/('Client'+str(ix)+'Dodge.png')),prev)
  tap();time.sleep(.7);s2=states();p2=[next(p for p in v['pawns'] if p['id']==identity) for v in s2];check('Client'+str(ix)+' second consumes final charge',all(p['dodge']==2 and p['dodgeCharges']==0 for p in p2));check('Client'+str(ix)+' second preserves original restore',all(p['dodgeRestoreAt']==pawns[0]['dodgeRestoreAt'] for p in p2));tap();time.sleep(.2);s3=states();check('Client'+str(ix)+' exhausted edge cannot create third',all(next(p for p in v['pawns'] if p['id']==identity)['dodge']==2 for v in s3));m['stages'].append({'stage':'Client'+str(ix)+'Second','states':s2,'exhausted':s3})
 before=states();base=[(p['id'],p['dodge'],p['action']) for p in before[0]['pawns']]
 for probe in ['dodgeduplicate','dodgestale','dodgenan','dodgeother']:active.console('U02NetProbe '+probe);time.sleep(.3)
 after=states();check('Negative Dodge probes cannot create actions',[(p['id'],p['dodge'],p['action']) for p in after[0]['pawns']]==base);m['stages'].append({'stage':'NegativeProbes','before':before,'after':after})
 expected={'t.MaxFPS':60,'r.ScreenPercentage':50,'r.Streaming.PoolSize':256,'r.LumenScene.SurfaceCache.AtlasSize':2048,'r.RenderTargetPoolMin':128,'t.IdleWhenNotForeground':0,'r.Lumen.DiffuseIndirect.Allow':0,'r.Lumen.Reflections.Allow':0,'r.Shadow.Virtual.Enable':0,'r.ShadowQuality':2}
 for i,v in enumerate(after[1:]):check('Client'+str(i)+' actual cvars',all(v[k]==x for k,x in expected.items()))
 check('Server cap30/idle0',after[0]['t.MaxFPS']==30 and after[0]['t.IdleWhenNotForeground']==0);m['completed']=True
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 for c in clients:
  if c.ime:c.focus()
  c.finish()
 m.update(videoSeconds=encoded/30,captureSeconds=last,encodedFPS=30);(a.out/'network.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({'completed':m['completed'],'checks':len(m['checks'])}))
