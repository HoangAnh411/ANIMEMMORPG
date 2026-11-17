import subprocess,json,time
from pathlib import Path
def verify(record):
 script=f"Get-CimInstance Win32_Process -Filter 'ProcessId={int(record['pid'])}' | Select-Object ExecutablePath,CommandLine,@{{n='creationUTC';e={{$_.CreationDate.ToUniversalTime().ToString('o')}}}},@{{n='modules';e={{@(Get-Process -Id {int(record['pid'])} -Module | Where-Object {{$_.ModuleName -like '*AnimeMMORPG*'}} | Select-Object ModuleName,FileName)}}}} | ConvertTo-Json -Depth 5"
 deadline=time.monotonic()+90
 while True:
  raw=subprocess.check_output(['powershell','-NoProfile','-Command',script],text=True,creationflags=subprocess.CREATE_NO_WINDOW)
  live=json.loads(raw);assert Path(live['ExecutablePath']).resolve()==Path(record['executable']).resolve()
  modules=live.get('modules') or []
  if isinstance(modules,dict):modules=[modules] if modules else []
  if record['role'] not in ('ClientA','ClientB','Server'):break
  expected=Path(record['project']).parent/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll'
  if any(v.get('FileName') and Path(v['FileName']).resolve()==expected.resolve() for v in modules):break
  assert time.monotonic()<deadline, 'Expected clone native module was not loaded before timeout'
  time.sleep(.25)
 cmd=live['CommandLine'].replace('\\','/').lower()
 assert str(record['userDir']).replace('\\','/').lower() in cmd and str(record['log']).replace('\\','/').lower() in cmd
 assert '-u02sourcesha='+record['sourceSHA'].lower() in cmd
 if record.get('creationUTC'):assert live['creationUTC']==record['creationUTC']
 if record['role'] in ('ClientA','ClientB','Server'):
  expected=Path(record['project']).parent/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll'
  assert any(v.get('FileName') and Path(v['FileName']).resolve()==expected.resolve() for v in modules), 'Loaded native module differs from clone artifact'
 return dict(executable=live['ExecutablePath'],creationUTC=live['creationUTC'],modules=modules)
