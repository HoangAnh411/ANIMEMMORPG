"""Re-run accepted E physical-input regressions against the new G package."""
import json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];play=root/'Artifacts/U01/G/Play';actions=play/'Actions';actions.mkdir(exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def capture(record,name,seconds,source=None):
 if source:
  if 'Evidence' in str(source):events=load(source)['metadata']['events'];events=[{k:v for k,v in e.items() if k not in ('actualTime','utc')} for e in events]
  else:events=load(source)
  (actions/(name+'.json')).write_text(json.dumps(events),encoding='utf8')
 r=load(record)
 args=[sys.executable,str(root/'Scripts/U01/CaptureEPlay.py'),'--pid',str(r['pid']),'--exe',r['executable'],'--out',str(play/name),'--actions',str(actions/(name+'.json')),'--duration',str(seconds),'--hz','30','--virtual-keys','--no-movement-probe','--us-layout']
 # Boot intentionally has no U01 pawn/input observer; never treat its last lab sample as current.
 if not name.startswith('Lifecycle'):args+=['--game-log',r['log'],'--ime-toggle-ctrl-shift']
 subprocess.run(args,check=True,cwd=root)
def launch(label):
 subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'Scripts/U01/StartGPackage.ps1'),'-Package',str(root/'Artifacts/U01/G/Package-20261105-153201-862-38caf5d5/Archive/Windows'),'-UserDir',str(play/'UserA'),'-Map','L_CharacterCombatLab','-Label',label],check=True)
 p=play/'UserA'/(label+'.process.json')
 for _ in range(240):
  time.sleep(.25)
  r=load(p)
  if Path(r['log']).exists() and 'LogU01Control: Display: Metrics {' in Path(r['log']).read_text(encoding='utf-8-sig',errors='replace'):break
 return p
if __name__=='__main__':
 record=play/'UserA/Game.process.json'
 capture(record,'CaptureEdges',6.3,root/'Docs/U01/Evidence/E/CaptureEdges.json')
 capture(record,'DefeatedRestore',14,root/'Artifacts/U01/E/FinalPlay/DefeatedRestore.json')
 time.sleep(3);record=launch('Reopen')
 capture(record,'Persist',7.5,root/'Artifacts/U01/E/FinalPlay/Persist.json')
 capture(record,'Lifecycle',20,root/'Artifacts/U01/E/FinalPlay/Lifecycle.json')
 capture(record,'NetworkReturn',6,root/'Artifacts/U01/E/FinalPlay/NetworkReturn.json')
 print('Packaged rebind/locks/persistence and five Boot cycles captured',flush=True)
