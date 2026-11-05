"""Actual packaged 1080p frame/motor/camera trials, with no quality reductions."""
import json,sys,time,subprocess
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from GInput import PackageClient,mouse
root=Path(__file__).resolve().parents[2];folder=root/'Artifacts/U01/G/FPS';folder.mkdir(exist_ok=False)
subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'Scripts/U01/StartGPackage.ps1'),'-Package',str(root/'Artifacts/U01/G/Package-20261105-153201-862-38caf5d5/Archive/Windows'),'-UserDir',str(folder),'-Label','FPS','-Measure','-Width','1920','-Height','1080','-Fullscreen','-MaxFPS','30'],check=True)
r=json.loads((folder/'FPS.process.json').read_text(encoding='utf-8-sig'));c=PackageClient(r);assert(c.width,c.height)==(1920,1080);trials=[];active=None
def utc():return datetime.now(timezone.utc).isoformat()
def save():(folder/'trials.json').write_text(json.dumps({'process':r,'geometry':[c.width,c.height],'quality':'Unchanged project renderer/scalability defaults; internal100%; stat unit; opt-in diagnostic fixture floor far from runway','trials':trials},indent=2),encoding='utf8',newline='\n')
try:
 time.sleep(30);c.prepare()
 for cap in (30,60,120):
  c.console('t.MaxFPS '+str(cap));c.console('U01FixtureReset Runway');time.sleep(5)
  trial={'cap':cap,'start':utc(),'events':[],'completed':False};trials.append(trial);save();start=time.perf_counter();pending=[(2,'down','W'),(14,'up','W'),(16,'reset',''),(17.8,'down','Ctrl'),(18,'down','W'),(30,'up','W'),(30.2,'up','Ctrl'),(34,'reset',''),(36,'down','Space'),(36.6,'up','Space'),(42,'look',''),(45,'down','V'),(45.2,'up','V'),(48,'down','Escape'),(48.2,'up','Escape'),(50,'resume',''),(52,'down','W'),(55,'up','W'),(57,'snapshot','')]
  while time.perf_counter()-start<60:
   c.guard();elapsed=time.perf_counter()-start
   while pending and elapsed>=pending[0][0]:
    nominal,action,key=pending.pop(0)
    if action in ('down','up'):c.press(key,action=='down')
    elif action=='reset':c.console('U01FixtureReset Runway')
    elif action=='look':mouse(1,120,-80)
    elif action=='resume':c.click_ui(640,205)
    elif action=='snapshot':ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(folder/f'cap-{cap}.png')
    trial['events'].append({'nominal':nominal,'action':action,'key':key,'elapsed':time.perf_counter()-start,'utc':utc()})
   time.sleep(.002)
  trial['completed']=True;trial['end']=utc();save();print('Packaged cap',cap,'complete',flush=True)
 time.sleep(2)
finally:
 c.finish();save()
c.press('Escape',True);time.sleep(.1);c.press('Escape',False);time.sleep(.3);c.click_ui(640,558)
