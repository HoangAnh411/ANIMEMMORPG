"""Dedicated server + two real Windows clients; input and independent per-process consensus."""
import argparse,json,time,cv2,numpy as np
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from FClient import FClient,u
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);a=p.parse_args();out=a.session/'Capture';out.mkdir(exist_ok=True)
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));by={r['role']:r for r in records};clients={k:FClient(by[k]) for k in ['ClientA','ClientB']};active=None;writer=None;meta=dict(completed=False,utc=datetime.now(timezone.utc).isoformat(),processes=records,stages=[],checks=[])
def state(role):
 data=Path(by[role]['log']).read_bytes();lines=data[:data.rfind(b'\n')+1].decode('utf-8-sig',errors='replace').splitlines();rows=[json.loads(l.split('U02F_STATE ',1)[1]) for l in lines if 'U02F_STATE {' in l];assert rows;return rows[-1]
def check(name,value):
 meta['checks'].append(dict(check=name,result='PASS' if value else 'FAIL'));assert value,name
def consensus(label,expected=None):
 for _ in range(150):
  states={k:state(k) for k in by};s=states['Server'];
  def core(x):return sorted((t['id'],t['lifeGeneration'],t['hp'],t['shield'],t['dead'],t['deathCount'],t['identityLife']) for t in x['targets']),x['results'],x['critMode']
  if all(core(v)==core(s) for v in states.values()) and all(len(v['pawns'])==len(s['pawns']) for v in states.values()):break
  wait(.1)
 else:raise AssertionError('Consensus timeout '+label)
 check(label+' result/HP/shield/life agreement',True);check(label+' dedicated no LocalPlayer',s['netMode']==1 and s['localPlayers']==0)
 for k in clients:check(label+' owned pawn '+k,states[k]['netMode']==3 and states[k]['localPlayers']==1 and sum(p['local'] for p in states[k]['pawns'])==1 and all(p['role']==(2 if p['local'] else 1) for p in states[k]['pawns']))
 check(label+' distinct ownership',len({next(p['id'] for p in states[k]['pawns'] if p['local']) for k in clients})==2)
 check(label+' profile30/60/60',s['t.MaxFPS']==30 and all(states[k]['t.MaxFPS']==60 and states[k]['r.ScreenPercentage']==50 for k in clients))
 if expected is not None:check(label+' event delta',len(s['results'])-meta['stages'][-1]['resultCount']==expected)
 meta['stages'].append(dict(label=label,utc=datetime.now(timezone.utc).isoformat(),resultCount=len(s['results']),states=states));grab();ImageGrab.grab(bbox=bounds,all_screens=True).save(out/(label+'.png'));return s

def grab():
 global encoded,previous
 active.guard();assert active.bounds() in window_bounds
 frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=bounds,all_screens=True)),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
 while encoded/30<now:writer.write(previous if previous is not None else frame);encoded+=1
 previous=frame

def wait(seconds):
 end=time.perf_counter()+seconds
 while time.perf_counter()<end:grab();time.sleep(.02)
def focus(k):
 global active
 active=clients[k];active.prepare();wait(.4)
def setup(mode):
 marker=str(time.time_ns())+' '+mode;(a.session/'command.txt').write_text(marker)
 for _ in range(120):
  if 'U02F_FIXTURE '+marker in Path(by['Server']['log']).read_text(encoding='utf-8-sig',errors='replace'):break
  wait(.1)
 else:raise AssertionError('Fixture ack timeout '+mode)
 wait(1)
def attack():
 active.attack(True);time.sleep(.04);active.attack(False);wait(1)
try:
 for c in clients.values():c.prepare()
 active=clients['ClientB'];window_bounds=[c.bounds() for c in clients.values()];bounds=(min(v[0] for v in window_bounds),min(v[1] for v in window_bounds),max(v[2] for v in window_bounds),max(v[3] for v in window_bounds));cv2.setNumThreads(1);writer=cv2.VideoWriter(str(out/'Network-F.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(bounds[2]-bounds[0],bounds[3]-bounds[1]));assert writer.isOpened();start=time.perf_counter();encoded=0;previous=None
 setup('hit');focus('ClientA');consensus('Baseline');attack();s=consensus('HitMulti',2);check('Two target HP540',sum(t['hp']==540 for t in s['targets'])==2)
 active.console('U02NetProbe duplicate');wait(1);consensus('Duplicate',0)
 active.console('U02NetProbe stale');wait(1);consensus('StaleLife',0)
 before={p['id']:(p['accepted'],p['rejected']) for p in state('Server')['pawns']};active.console('U02NetProbe other');wait(1);s=consensus('WrongOwnership',0);check('Foreign RPC never reaches server admission',before=={p['id']:(p['accepted'],p['rejected']) for p in s['pawns']})
 setup('miss');attack();consensus('Miss',0)
 setup('wall');attack();consensus('Wall',0)
 setup('partial');attack();s=consensus('PartialHead',1);check('Head-only hurtbox',s['results'][-1]['hurtbox']==2)
 setup('crit');attack();s=consensus('Crit',1);check('Crit90 server/client agree',s['results'][-1]['crit'] and s['results'][-1]['damage']==90)
 setup('shield');consensus('ShieldGranted',0);attack();s=consensus('ShieldHit',1);check('Shield absorbs40',s['results'][-1]['absorbed']==40)
 setup('reset');s=consensus('ResetGeneration',0);check('Reset restores600',all(t['hp']==600 and t['shield']==0 for t in s['targets']))
 focus('ClientB');attack();consensus('ClientBRealAttack',1);focus('ClientA')
 # An accepted attack continues while its client enters menu and the peer resumes.
 active.attack(True);time.sleep(.04);active.attack(False);active.press('Escape',True);time.sleep(.03);active.press('Escape',False);wait(.5);focus('ClientB');consensus('MenuFocusDoesNotPause',1)
 setup('lethal');consensus('LethalPrepared',0);before={p['id']:p['accepted'] for p in state('Server')['pawns']};setup('concurrent');wait(1);s=consensus('ConcurrentLethal',2);check('Both concurrent fixture sources accepted',all(p['accepted']==before[p['id']]+1 for p in s['pawns']));check('Death once per target',sum(t['dead'] and t['deathCount']==1 for t in s['targets'])==2);check('Sorted lethal only first source per target',len({r['source'] for r in s['results'][-2:]})==1)
 active.console('U02NetProbe nan');wait(1);consensus('NonfiniteAim',0)
 # Production API has no client-supplied HP/damage fields; native reflected-schema test verifies this.
 active.console('U02NetProbe damage');wait(.5);consensus('NoDamagePayloadAPI',0)
 meta['completed']=True;meta['captureSeconds']=time.perf_counter()-start;meta['videoSeconds']=encoded/30;meta['timestampPolicy']='CFR30 previous image held to wall timestamp; no acceleration'
except Exception as error:meta['error']=str(error);raise
finally:
 if writer:writer.release()
 for k,c in clients.items():
  if c.ime:c.focus()
  c.finish()
 meta['externalInputMethodRestored']=all(not c.ime for c in clients.values());meta['passed']=sum(c['result']=='PASS' for c in meta['checks']);meta['failed']=sum(c['result']=='FAIL' for c in meta['checks']);(out/'input.json').write_text(json.dumps(meta,indent=2))
print(json.dumps({k:meta[k] for k in ['completed','passed','failed','captureSeconds','videoSeconds']}))
