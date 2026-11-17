"""Two real clients, sequential physical input, saved independent server/client state and reconnect."""
import argparse,json,time,threading,subprocess,cv2,numpy as np
from pathlib import Path
from PIL import ImageGrab
from DNetworkClient import DNetworkClient
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));clients=[DNetworkClient(next(r for r in records if r['role']==role)) for role in ['ClientA','ClientB']]
m=dict(completed=False,processes=records,inputScheduling='Sequential physical Windows input; not simultaneous human input',checks=[],stages=[],events=[]);stop=threading.Event();encoded=0;last=0;previous=None;start=time.perf_counter();cv2.setNumThreads(1)
m['loadedClientModules']=[c.processIdentity for c in clients]
writer=cv2.VideoWriter(str(a.out/'Network-D.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1800,540));assert writer.isOpened()
def until(f,timeout=7):
 end=time.perf_counter()+timeout
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Network condition timeout')
  time.sleep(.02)
def check(name,ok):m['checks'].append(dict(check=name,result='PASS' if ok else 'FAIL'));assert ok,name
def history(record,limit=16000000):
 with Path(record['log']).open('rb') as f:f.seek(0,2);end=f.tell();f.seek(max(0,end-limit));raw=f.read()
 if end>limit:raw=raw[raw.find(b'\n')+1:]
 rows=[json.loads(l.split('U02F_STATE ',1)[1]) for l in raw[:raw.rfind(b'\n')+1].decode('utf-8-sig').splitlines() if 'U02F_STATE {' in l]
 if not rows:raise RuntimeError('No complete network state')
 return rows
def state(record):return history(record,4000000)[-1]
def states():return [state(r) for r in records]
def button(c,label):
 until(lambda:label in c.metrics().get('menuButtons',{}) and c.metrics()['menuButtons'][label]['enabled']);b=c.metrics()['menuButtons'][label];assert b['enabled'];c.click(round(b['x']),round(b['y']));time.sleep(.18)
def tap(c,key):c.press(key,True);time.sleep(.035);c.press(key,False);m['events'].append(dict(wall=time.perf_counter()-start,client=c.record['role'],key=key))
def playing(c):
 c.focus()
 if c.metrics()['combat']['vital']['hp']<1000 and not c.metrics()['encounter']['result']:
  until(lambda:c.metrics()['encounter']['result']!=0,22)
 if c.metrics()['encounter']['result']:
  rev=c.metrics()['encounter']['revision'];button(c,'Retry encounter');until(lambda:c.metrics()['encounter']['revision']>rev)
 if c.metrics()['controlState']!=0:button(c,'Resume')
 until(lambda:c.metrics()['controlState']==0)
def coherent(name,identity):
 saved=None
 def ready():
  nonlocal saved
  rows=states();pairs=[]
  for row in rows:
   matches=[e for e in row['encounters'] if e['id']==identity]
   if len(matches)!=1:return False
   e=matches[0];actors={x['id']:x for x in row['pawns']}
   if e['player'] not in actors or e['monster'] not in actors:return False
   keys=['life','action','definition','definitionVersion','raw','start','qReady','eReady','dodge','dodgeCharges','hardCC','interruptSequence']
   values=[{k:actors[subject][k] for k in keys}|{'hp':actors[subject]['vital']['hp'],'vitalLife':actors[subject]['vital']['lifeGeneration']} for subject in [e['player'],e['monster']]]
   pairs.append(dict(encounter={k:e[k] for k in ['id','revision','result','ai','player','monster']},subjects=values))
  if pairs[0]!=pairs[1] or pairs[0]!=pairs[2]:return False
  saved=rows;return True
 until(ready);m['stages'].append(dict(stage=name,identity=identity,states=saved));check(name+' HP/action/AI/result/revision agree across actual processes',True)
def record():
 global encoded,last,previous
 while not stop.is_set():
  try:
   frame=np.hstack([cv2.cvtColor(np.array(ImageGrab.grab(bbox=c.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR) for c in clients]);last=time.perf_counter()-start
   while encoded/30<last:writer.write(previous if previous is not None else frame);encoded+=1
   previous=frame
  except (AssertionError,RuntimeError,OSError,cv2.error,ValueError):m['skippedFrames']=m.get('skippedFrames',0)+1
  time.sleep(.02)
worker=threading.Thread(target=record);worker.start()
try:
 for c in clients:
  c.focus();observed=c.probe_w()
  if observed!='W':c.toggle_ime();c.ime=True;observed=c.probe_w()
  assert observed=='W'
 ids=[c.metrics()['encounter']['id'] for c in clients];check('Two separate owner encounters',ids[0]!=ids[1])
 for i,c in enumerate(clients):
  playing(c);tap(c,'Tab');until(lambda:c.metrics()['informationTarget']['selected']);check(c.record['role']+' Target selects its own opponent',c.metrics()['informationTarget']['subject']==c.metrics()['encounter']['monsterCombat']['pawnId'])
  tap(c,'Tab');tap(c,'Shift');until(lambda:c.metrics()['combat']['dodgeCharges']==1);coherent(c.record['role']+' Dodge',ids[i]);time.sleep(.4)
  until(lambda:c.metrics()['encounter']['monsterCombat']['phase']==1 and c.metrics()['encounter']['monsterCombat']['serverSnapshotSeconds']<c.metrics()['encounter']['monsterCombat']['start']+.15)
  old=c.metrics()['encounter']['monsterCombat']['interruptSequence'];tap(c,'E');until(lambda:c.metrics()['encounter']['monsterCombat']['interruptSequence']>old)
  coherent(c.record['role']+' E Interrupt',ids[i]);m['stages'].append(dict(stage=c.record['role']+' input E',metrics=c.metrics()))
  def replicated_event():
   rows=states();events=[]
   for row in rows:
    e=next(x for x in row['encounters'] if x['id']==ids[i]);hits=[v for v in row['results'] if v.get('encounter')==ids[i] and v['source']==e['player'] and v['target']==e['monster'] and v['definition']==4]
    if not hits:return False
    events.append(hits[-1])
   if events[0]!=events[1] or events[0]!=events[2]:return False
   m['stages'].append(dict(stage=c.record['role']+' E results',identity=ids[i],states=rows,events=events));return True
  until(replicated_event);check(c.record['role']+' actual E damage/Interrupt history replicated',True)
 # Both stations continue running while focus moves. Let them reach stable terminal states.
 until(lambda:all(c.metrics()['encounter']['result']!=0 for c in clients),25)
 for i in range(2):coherent('Terminal'+str(i),ids[i])
 before=states();b=next(e for e in before[0]['encounters'] if e['id']==ids[1]);bp=next(x for x in before[0]['pawns'] if x['id']==b['player'])
 c=clients[0];c.focus();rev=c.metrics()['encounter']['revision'];button(c,'Retry encounter');until(lambda:c.metrics()['encounter']['revision']>rev);coherent('RetryA',ids[0]);after=states()
 for row in after:
  neighbor=next(e for e in row['encounters'] if e['id']==ids[1]);pawn=next(x for x in row['pawns'] if x['id']==b['player'])
  check('Retry A leaves B terminal/revision/HP/life/action unchanged',neighbor['revision']==b['revision'] and neighbor['result']==b['result'] and all(pawn[k]==bp[k] for k in ['life','action']) and pawn['vital']['hp']==bp['vital']['hp'])
 check('Retry leaves A AwaitingResume',c.metrics()['controlState']!=0)
 # Probe the product RPC using this controller, never a fixture reset RPC or target actor.
 playing(c);current=c.metrics()['encounter'];probe=100
 claims=[('unowned',ids[1],b['revision'],probe),('stale',ids[0],current['revision']-1,probe+1),('running',ids[0],current['revision'],probe+2),('duplicate',ids[0],current['revision'],probe+2)]
 for label,identity,revision,sequence in claims:
  c.console(f'U03C2RetryClaim {identity} {revision} {sequence}');time.sleep(.15)
  marker=f'claim={identity} revision={revision} sequence={sequence} accepted=0';server=next(r for r in records if r['role']=='Server')
  until(lambda:marker in Path(server['log']).read_text(encoding='utf-8-sig',errors='strict'))
  check(label+' actual owned-channel Retry claim rejected without revision change',c.metrics()['encounter']['revision']==current['revision']);m['events'].append(dict(probe=label,identity=identity,revision=revision,sequence=sequence,serverMarker=marker))
 # Create real pre-disconnect skill state, then restart only the recorded ClientA.
 playing(c);until(lambda:c.metrics()['combat']['serverSnapshotSeconds']>=c.metrics()['combat']['eReady']);tap(c,'E');until(lambda:c.metrics()['combat']['energy']<=75)
 old=c.metrics();m['stages'].append(dict(stage='BeforeDisconnect',metrics=old));c.finish()
 # A forced OS kill is detected only after the UDP connection timeout. Exercise
 # an explicit product disconnect, then wait for server Logout before reconnect.
 c.console('quit')
 server=next(r for r in records if r['role']=='Server')
 until(lambda:not any(e['id']==old['encounter']['id'] for e in state(server)['encounters']),15)
 m['stages'].append(dict(stage='AfterDisconnect server state',state=state(server)))
 check('Server Logout removes old encounter before reconnect',True)
 result=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(Path(__file__).with_name('ReconnectDClient.ps1')),'-SessionPath',str(a.session.resolve())],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
 (a.out/'reconnect-launcher.out').write_text(result.stdout);(a.out/'reconnect-launcher.err').write_text(result.stderr);assert result.returncode==0
 records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));m['reconnectProcesses']=records;clients[0]=DNetworkClient(next(r for r in records if r['role']=='ClientA'));c=clients[0];m['reconnectLoadedModule']=c.processIdentity;c.focus();new=c.metrics()
 observed=c.probe_w()
 if observed!='W':c.toggle_ime();c.ime=True;observed=c.probe_w()
 assert observed=='W'
 check('Reconnect gets new encounter and pawn identity',new['encounter']['id']!=old['encounter']['id'] and new['combat']['pawnId']!=old['combat']['pawnId'])
 check('Reconnect has fresh resources, cooldown and life',new['combat']['life']==1 and new['combat']['action']==0 and new['combat']['energy']==100 and new['combat']['eReady']==0 and new['combat']['dodgeCharges']==2)
 server=next(r for r in records if r['role']=='Server');initial=next(row for row in history(server) if any(e['id']==new['encounter']['id'] for e in row['encounters']));initial_e=next(e for e in initial['encounters'] if e['id']==new['encounter']['id']);initial_p=next(v for v in initial['pawns'] if v['id']==initial_e['player'])
 check('Server first reconnect snapshot has full HP at a fresh life',initial_p['vital']['hp']==1000 and initial_p['life']==1 and initial_e['revision']==1 and not any(e['id']==old['encounter']['id'] for e in initial['encounters']));m['stages'].append(dict(stage='Initial reconnect server state',state=initial))
 m['stages'].append(dict(stage='AfterReconnect',metrics=new));coherent('Reconnect fresh identity',new['encounter']['id'])
 # Old encounter claims are rejected on the new owned controller as well.
 if c.metrics()['controlState']!=0:button(c,'Resume')
 newrev=c.metrics()['encounter']['revision'];c.console(f'U03C2RetryClaim {old["encounter"]["id"]} {old["encounter"]["revision"]} 1');time.sleep(.2)
 marker=f'claim={old["encounter"]["id"]} revision={old["encounter"]["revision"]} sequence=1 accepted=0';until(lambda:marker in Path(server['log']).read_text(encoding='utf-8-sig',errors='strict'));m['events'].append(dict(probe='old encounter on reconnect',serverMarker=marker))
 check('Old encounter identity cannot reset reconnect',c.metrics()['encounter']['revision']==newrev)
 m['completed']=True
except Exception as error:
 m['error']=repr(error);raise
finally:
 stop.set();worker.join();writer.release()
 for c in clients:
  try:
   c.focus()
   if c.ime and c.metrics()['controlState']==0:tap(c,'Escape');time.sleep(.15)
   c.finish()
  except Exception as error:m.setdefault('cleanupErrors',[]).append(repr(error))
 m['externalInputMethodRestored']=all(not c.ime for c in clients)
 m.update(captureSeconds=last,videoSeconds=encoded/30,encodedFPS=30);(a.out/'network.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(completed=m['completed'],checks=len(m['checks']))))
