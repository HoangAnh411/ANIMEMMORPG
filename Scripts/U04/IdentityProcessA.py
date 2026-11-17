import subprocess,json
from pathlib import Path
def verify(record):
 script=f"Get-CimInstance Win32_Process -Filter 'ProcessId={int(record['pid'])}' | Select-Object ExecutablePath,CommandLine,@{{n='creationUTC';e={{$_.CreationDate.ToUniversalTime().ToString('o')}}}} | ConvertTo-Json"
 raw=subprocess.check_output(['powershell','-NoProfile','-Command',script],text=True,creationflags=subprocess.CREATE_NO_WINDOW)
 live=json.loads(raw);assert Path(live['ExecutablePath']).resolve()==Path(record['executable']).resolve()
 cmd=live['CommandLine'].replace('\\','/').lower()
 assert str(record['userDir']).replace('\\','/').lower() in cmd and str(record['log']).replace('\\','/').lower() in cmd
 assert '-u02sourcesha='+record['sourceSHA'].lower() in cmd
 if record.get('creationUTC'):assert live['creationUTC']==record['creationUTC']
 return live['creationUTC']
