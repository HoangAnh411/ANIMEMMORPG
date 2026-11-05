"""Ten continuous minutes of packaged Game-world input, menus and focus changes."""
import json,sys,time,subprocess
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from GInput import PackageClient,mouse,u
root=Path(__file__).resolve().parents[2];play=root/'Artifacts/U01/G/Play';folder=play/('LongPlay-'+datetime.now().strftime('%Y%m%d-%H%M%S'));folder.mkdir(exist_ok=False)
subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'Scripts/U01/StartGPackage.ps1'),'-Package',str(root/'Artifacts/U01/G/Package-20261105-153201-862-38caf5d5/Archive/Windows'),'-UserDir',str(play/'UserA'),'-Label','Long'],check=True)
r=json.loads((play/'UserA/Long.process.json').read_text(encoding='utf-8-sig'));c=PackageClient(r);events=[];completed=False;start=None
def utc():return datetime.now(timezone.utc).isoformat()
def mark(action,**kw):events.append(dict(action=action,utc=utc(),elapsed=time.perf_counter()-start if start else None,**kw))
def press(name,down):c.press(name,down);mark('key',key=name,down=down)
def schedule():
 return sorted([(3,'down','W'),(5,'down','Ctrl'),(7,'down','Space'),(7.6,'up','Space'),(8,'up','Ctrl'),(11,'up','W'),(14,'down','S'),(18,'up','S'),(20,'down','V'),(20.2,'up','V'),(22,'look',''),(24,'down','Escape'),(24.2,'up','Escape'),(25,'down','W'),(25.2,'down','Space'),(25.4,'down','Ctrl'),(26,'resume',''),(27,'up','W'),(27.1,'up','Space'),(27.2,'up','Ctrl'),(28,'down','W'),(30,'up','W'),(40,'focus',''),(48,'snapshot','')])
try:
 for _ in range(120):
  try:c.metrics();break
  except RuntimeError:time.sleep(.25)
 c.prepare();press('Escape',True);time.sleep(.1);press('Escape',False);time.sleep(.3);c.click_ui(640,245);time.sleep(.3);c.click_ui(640,459);time.sleep(.3);c.click_ui(640,482);time.sleep(.3);c.click_ui(640,505);time.sleep(.3);c.click_ui(640,205);time.sleep(.5)
 assert json.loads(c.metrics()['settings'])['bindings']['Forward']=='W'
 c.console('U01FixtureReset Runway');time.sleep(.5);start=time.perf_counter();started=utc();cycle=-1;pending=[]
 while time.perf_counter()-start<600:
  elapsed=time.perf_counter()-start;now=int(elapsed//60)
  if now!=cycle:
   if cycle>=0:c.console('U01FixtureReset Runway')
   cycle=now;pending=schedule();m=c.metrics();assert m['controlState']==0 and m['mappingContextCount']==1;mark('cycle',cycle=cycle,metrics=m);print('Long play minute',cycle+1,flush=True)
  c.guard();local=time.perf_counter()-start-cycle*60
  while pending and local>=pending[0][0]:
   nominal,action,name=pending.pop(0)
   if action in ('down','up'):press(name,action=='down')
   elif action=='look':mouse(1,80,-40);mark('mouse',dx=80,dy=-40)
   elif action=='resume':c.click_ui(640,205);mark('resume')
   elif action=='focus':
    c.release();mark('focus-start');u.ShowWindow(c.hwnd,6);time.sleep(1);c.prepare();mark('focus-return',metrics=c.metrics())
   elif action=='snapshot':ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(folder/f'minute-{cycle+1}.png');mark('snapshot',metrics=c.metrics())
  time.sleep(.003)
 completed=True;finished=utc();m=c.metrics();assert m['controlState']==0 and m['mappingContextCount']==1;mark('end',metrics=m)
finally:
 c.finish();(folder/'input.json').write_text(json.dumps({'completed':completed,'start':started if start else None,'end':utc(),'seconds':time.perf_counter()-start if start else None,'process':r,'events':events},indent=2),encoding='utf8',newline='\n')
if completed:
 c.press('Escape',True);time.sleep(.1);c.press('Escape',False);time.sleep(.3);c.click_ui(640,558)
print('Ten-minute packaged session complete:',completed,flush=True)
