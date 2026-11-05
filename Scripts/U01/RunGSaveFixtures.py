import json,time,subprocess,hashlib
from pathlib import Path
from GInput import PackageClient
from ReplayGIntegration import capture
r=Path.cwd();p=r/'Artifacts/U01/G/Play';pkg=r/'Artifacts/U01/G/Package-20261105-153201-862-38caf5d5/Archive/Windows'
def launch(user,label):
 subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(r/'Scripts/U01/StartGPackage.ps1'),'-Package',str(pkg),'-UserDir',str(user),'-Label',label],check=True)
 rec=user/(label+'.process.json');v=json.loads(rec.read_text(encoding='utf-8-sig'));c=PackageClient(v)
 for _ in range(120):
  try:c.metrics();break
  except RuntimeError:time.sleep(.25)
 c.prepare();c.press('Escape',True);time.sleep(.1);c.press('Escape',False);time.sleep(.4);return rec,c
u=p/'FailureUser';(u/'Saved').mkdir(parents=True,exist_ok=False);block=u/'Saved/SaveGames';block.write_text('G isolated save-failure fixture')
rec,c=launch(u,'Failure');capture(rec,'SaveFailure',5,r/'Artifacts/U01/E/FinalPlay/SaveFailure.json');assert block.is_file();block.unlink();block.mkdir();capture(rec,'SaveRecovered',6,r/'Artifacts/U01/E/FinalPlay/SaveRecovered.json');time.sleep(2)
u=p/'CorruptUser';slot=u/'Saved/SaveGames/U01Controls_Player0.sav';slot.parent.mkdir(parents=True,exist_ok=False);slot.write_bytes(b'G invalid settings fixture');before=hashlib.sha256(slot.read_bytes()).hexdigest();rec,c=launch(u,'Corrupt');capture(rec,'Corrupt',4,r/'Artifacts/U01/E/FinalPlay/Corrupt.json');time.sleep(1);assert hashlib.sha256(slot.read_bytes()).hexdigest()==before;(p/'corrupt-hash-before.txt').write_text(before);print('Save failure/recovery/corruption captured',flush=True)
