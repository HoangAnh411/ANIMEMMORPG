"""Ten guarded focus transfers, no gameplay/smoothing modifications."""
import argparse,json,time
from pathlib import Path
from datetime import datetime,timezone
from F60Input import Client,mouse
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--label',default='Baseline');a=p.parse_args();out=a.session/a.label;out.mkdir(exist_ok=False)
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));clients=[Client(r,stage='G') for r in records if r['role']!='Server'];events=[];trials=[];done=False

def utc():return datetime.now(timezone.utc).isoformat()
def event(action,**kw):events.append(dict(utc=utc(),wall=time.perf_counter(),action=action,**kw))
def save():(out/'input.json').write_text(json.dumps({'completed':done,'trials':trials,'events':events,'method':'Real SendInput; raw native per-frame and 5Hz control metrics retained in session; no added wait for FPS after activation'},indent=2))
active=None
try:
 for c in clients:
  active=c;c.prepare();c.console('U01NetFixture reset');c.release()
 active=clients[0];active.prepare();time.sleep(30)
 for index in range(10):
  source=clients[index%2];target=clients[(index+1)%2];assert active is source
  event('pre-window',index=index,role=source.record['role']);time.sleep(4)
  source.press('W',True);event('source-key-down',index=index,pid=source.pid);time.sleep(.8)
  event('focus-request',index=index,source=source.pid,target=target.pid);t={'index':index,'from':source.record['role'],'to':target.record['role'],'focusUTC':utc(),'beforeTarget':target.metrics()};trials.append(t);save()
  source.release();active=target;target.focus();event('focus-return',index=index,pid=target.pid,metrics=target.metrics());t['activatedUTC']=utc()
  # Preserve AwaitingResume; a real explicit Resume click is required.
  target.click(450,241);event('resume-clicked',index=index,pid=target.pid);t['resumeUTC']=utc()
  time.sleep(.05);target.press('W',True);t['keyUTC']=utc();event('target-key-down',index=index,pid=target.pid)
  time.sleep(1.2);target.press('W',False);event('target-key-up',index=index,pid=target.pid)
  time.sleep(.35);target.press('S',True);event('target-second-down',index=index,pid=target.pid);time.sleep(1.2);target.press('S',False)
  remaining=5-(datetime.now(timezone.utc)-datetime.fromisoformat(t['focusUTC'])).total_seconds()
  if remaining>0:time.sleep(remaining)
  t['endUTC']=utc();t['afterTarget']=target.metrics();event('post-window',index=index,pid=target.pid);save();print(a.label,index+1,'complete',flush=True)
 done=True
finally:
 if active:active.finish()
 save()
