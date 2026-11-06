import argparse,json,time,re,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from FClient import FClient,key,VK
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);a=p.parse_args();out=a.session/'Disconnect';out.mkdir(exist_ok=True);records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));by={r['role']:r for r in records};m=dict(completed=False,utc=datetime.now(timezone.utc).isoformat(),processes=records)
def states(role):
 raw=Path(by[role]['log']).read_bytes();return [json.loads(l.split('U02F_STATE ',1)[1]) for l in raw[:raw.rfind(b'\n')+1].decode('utf-8-sig',errors='replace').splitlines() if 'U02F_STATE {' in l]
def latest(role):return states(role)[-1]
c=FClient(by['ClientA'])
try:
 c.prepare()
 if c.ime:c.toggle_ime();c.ime=False
 marker=str(time.time_ns())+' hit';(a.session/'command.txt').write_text(marker);time.sleep(1.5);old=c.metrics()['combat']['pawnId'];baseline=next(v for v in latest('Server')['pawns'] if v['id']==old)
 # The explicit server concurrent fixture consumed a command ID; drain any stale physical counter edges before this separate disconnect attempt.
 for attempt in range(4):
  c.attack(True);time.sleep(.04);c.attack(False);time.sleep(.06)
  current=next(v for v in latest('Server')['pawns'] if v['id']==old)
  if current['accepted']>baseline['accepted']:break
 for _ in range(80):
  s=latest('Server');own=next(v for v in s['pawns'] if v['id']==old)
  if own['accepted']>baseline['accepted']:break
  time.sleep(.005)
 assert own['accepted']>baseline['accepted'];assert s['time']<own['start']+.4,'Must request disconnect during accepted action'
 m.update(oldPawn=old,acceptedAtDisconnect=own,serverAtDisconnect=s,requestUTC=datetime.now(timezone.utc).isoformat());ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(out/'BeforeDisconnect.png')
 VK['F4']=0x73;c.guard();key('Alt',True);key('F4',True);time.sleep(.03);key('F4',False);key('Alt',False)
 for _ in range(600):
  s=latest('Server')
  if all(v['id']!=old for v in s['pawns']):break
  time.sleep(.1)
 assert all(v['id']!=old for v in s['pawns']),'Server did not remove disconnected pawn'
 m['serverAfterRemoval']=s;time.sleep(1);s=latest('Server');events=[]
 for l in Path(by['Server']['log']).read_text(encoding='utf-8-sig',errors='replace').splitlines():
  if 'U02B_EVENT {' in l:
   e=json.loads(l.split('U02B_EVENT ',1)[1])
   if e['pawnId']==old and e['detail']=='reason=5':events.append(e)
 assert events,'No authoritative removal boundary';removed=events[-1]['gameplaySeconds'];m['removalEvent']=events[-1]
 assert not any(r['source']==old and r['timestamp']>=removed for r in s['results']),'Damage after source removal'
 m['noDamageAfterRemoval']=True;c.finish()
 subprocess.run(['powershell','-NoProfile','-File',str(Path('Scripts/U02/ReconnectFClient.ps1').resolve()),'-SessionPath',str(a.session.resolve())],check=True)
 records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));by={r['role']:r for r in records};c=FClient(by['ClientA']);c.prepare();new=c.metrics()['combat']['pawnId'];assert new!=old
 marker=str(time.time_ns())+' hit';(a.session/'command.txt').write_text(marker);time.sleep(1.5);before=len(latest('Server')['results']);c.attack(True);time.sleep(.04);c.attack(False);time.sleep(1.5)
 for _ in range(120):
  ss={k:latest(k) for k in by}
  if all(v['results']==ss['Server']['results'] and len(v['pawns'])==2 for v in ss.values()):break
  time.sleep(.1)
 assert all(v['results']==ss['Server']['results'] and len(v['pawns'])==2 for v in ss.values());assert len(ss['Server']['results'])==before+2
 last=ss['Server']['results'][-2:];assert all(r['source']==new and r['action']==1 and r['sourceLife']==1 for r in last)
 m.update(newPawn=new,reconnectedProcesses=records,reconnectStates=ss,freshIdentityAndCommand=True,completed=True);ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(out/'AfterReconnect.png')
except Exception as e:m['error']=str(e);raise
finally:
 c.finish();m['externalInputMethodRestored']=not c.ime;(out/'ASSERTIONS.json').write_text(json.dumps(m,indent=2))
print('PASS actual Alt-F4 during accepted action, removal boundary, fresh reconnect and result agreement')
