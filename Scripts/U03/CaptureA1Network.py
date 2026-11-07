"""Owned physical network combo, replicated result comparison and negative RPC probes."""
import argparse,json,time,cv2,numpy as np,threading
from pathlib import Path
from PIL import ImageGrab
from A1NetworkClient import A1NetworkClient
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));clients=[A1NetworkClient(r) for r in records if r['role']!='Server'];cv2.setNumThreads(1)
m={'completed':False,'checks':[],'stages':[],'processes':records};active=None;writer=None;start=0;encoded=0;prev=None;last=0
def check(n,v):m['checks'].append({'check':n,'result':'PASS' if v else 'FAIL'});assert v,n
def capture():
 global encoded,prev,last
 now=time.perf_counter()-start
 if now-last<1/30:return
 active.guard();bounds=[c.bounds() for c in clients];left=min(x[0] for x in bounds);top=min(x[1] for x in bounds);right=max(x[2] for x in bounds);bottom=max(x[3] for x in bounds);screen=np.array(ImageGrab.grab(bbox=(left,top,right,bottom),all_screens=True));frames=[screen[t-top:b-top,l-left:r-left] for l,t,r,b in bounds];f=cv2.cvtColor(np.concatenate(frames,axis=1),cv2.COLOR_RGB2BGR)
 while encoded/30<now:writer.write(prev if prev is not None else f);encoded+=1
 prev=f;last=now
def grab():pass
stop=threading.Event();worker=None
def recording():
 while not stop.is_set():
  try:capture()
  except AssertionError:pass
  time.sleep(.004)
def wait(s):
 end=time.perf_counter()+s
 while time.perf_counter()<end:grab();time.sleep(.003)
def states():
 result=[]
 for r in records:
  with Path(r['log']).open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-500000));raw=f.read()
  lines=raw[:raw.rfind(b'\n')+1].decode('utf-8-sig').splitlines();v=[json.loads(l.split('U02F_STATE ',1)[1]) for l in lines if 'U02F_STATE {' in l][-1];assert v['pid']==r['pid'] and v['sourceSHA']==r['sourceSHA'];result.append(v)
 return result
try:
 for c in clients:
  c.focus();active=c;c.prepare()
 active=clients[0];active.focus();active.prepare();writer=cv2.VideoWriter(str(a.out/'Network-A1.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1800,540));assert writer.isOpened();start=time.perf_counter();worker=threading.Thread(target=recording);worker.start()
 for ix,c in enumerate(clients):
  if ix:active.finish()
  active=c;c.focus();c.prepare();(a.session/'command.txt').write_text(str(time.time_ns())+' hit',encoding='utf-8');wait(.7)
  base=c.metrics()['combat']['action'];seen={};sent=set();c.attack(True);wait(.025);c.attack(False);deadline=time.perf_counter()+5
  while time.perf_counter()<deadline:
   grab();v=c.metrics();b=v['combat'];i=b['action']-base
   if 1<=i<=3:
    seen.setdefault(i,{'definition':b['definition'],'start':b['start'],'action':b['action'],'life':b['life']})
    # Repeated physical edges replace the single slot; snapshot replication is
    # intentionally slower than the 150ms buffer. Do not compare client clock.
    if i<3 and b['locked'] and b['actionSeconds']>=.20 and time.perf_counter()-getattr(c,'lastTap',0)>.045:c.attack(True);wait(.025);c.attack(False);c.lastTap=time.perf_counter();sent.add(i)
    if i==3 and not b['locked']:break
   time.sleep(.003)
  m['stages'].append({'stage':'Observed'+str(ix),'base':base,'actions':seen,'last':c.metrics()})
  check('Client '+str(ix)+' physical definitions 1/2/3',[v['definition'] for v in seen.values()]==[0,1,2]);wait(.65);s=states();local=c.metrics()['pawnId'] if 'pawnId' in c.metrics() else c.metrics()['combat']['pawnId']
  results=[[x for x in v['results'] if x['source']==local and x['sourceLife']==seen[1]['life'] and x['action']>=seen[1]['action']] for v in s]
  check('Client '+str(ix)+' all three processes agree results',results[0]==results[1]==results[2]);check('Client '+str(ix)+' real contacts for every definition',set(x['definition'] for x in results[0])=={0,1,2})
  check('Client '+str(ix)+' immutable raw payload',all(x['raw']==[60,70,90][x['definition']] for x in results[0]));check('Client '+str(ix)+' no friendly fire',all(p['vital']['hp']==1000 for v in s for p in v['pawns']))
  for i in (2,3):check('Client '+str(ix)+' exact successor '+str(i),abs(seen[i]['start']-seen[i-1]['start']-[.40,.45,.60][seen[i-1]['definition']])<1e-9)
  m['stages'].append({'stage':'Client'+str(ix)+'Combo','actions':seen,'states':s});cv2.imwrite(str(a.out/('Client'+str(ix)+'Combo.png')),prev)
 before=states();accepted=[p['accepted'] for p in before[0]['pawns']];hp=[t['hp'] for t in before[0]['targets']]
 for probe in ['duplicate','stale','nan','other']:active.console('U02NetProbe '+probe);wait(.3)
 after=states();check('Negative probes cannot accept an action',[p['accepted'] for p in after[0]['pawns']]==accepted);check('Negative probes cannot damage',[t['hp'] for t in after[0]['targets']]==hp);m['stages'].append({'stage':'NegativeProbes','before':before,'after':after})
 expected={'t.MaxFPS':60,'r.ScreenPercentage':50,'r.Streaming.PoolSize':256,'r.LumenScene.SurfaceCache.AtlasSize':2048,'r.RenderTargetPoolMin':128,'t.IdleWhenNotForeground':0,'r.Lumen.DiffuseIndirect.Allow':0,'r.Lumen.Reflections.Allow':0,'r.Shadow.Virtual.Enable':0,'r.ShadowQuality':2}
 for i,v in enumerate(after[1:]):check('Client '+str(i)+' actual review cvars',all(v[k]==x for k,x in expected.items()))
 check('Server actual cap30 and idle0',after[0]['t.MaxFPS']==30 and after[0]['t.IdleWhenNotForeground']==0);m['completed']=True
finally:
 stop.set()
 if worker:worker.join()
 if writer:writer.release()
 for c in clients:
  if c.ime:c.focus()
  c.finish()
 m['videoSeconds']=encoded/30;m['captureSeconds']=last;m['encodedFPS']=30;(a.out/'network.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps({'completed':m['completed'],'checks':len(m['checks'])}))
