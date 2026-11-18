"""Seal fresh build artifacts, receipts and logs; never infer identity from metadata alone."""
import argparse,json,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--clone',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--source',required=True);a=p.parse_args()
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
assert not subprocess.check_output(['git','-C',str(a.clone),'diff',a.source,'--','Source','Content','Config','Plugins','AnimeMMORPG.uproject'])
assert not subprocess.check_output(['git','-C',str(a.clone),'status','--porcelain','--untracked-files=no'])
for step in ['Generate','Editor','Game','Package']:assert json.loads((a.build/(step+'.result.json')).read_text(encoding='utf-8-sig'))['exitCode']==0
package=a.build/'Archive/Windows';exe=package/'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe';engine=Path('D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe')
receipts=[dict(path=str(f),sha256=sha(f),content=json.loads(f.read_text(encoding='utf-8-sig'))) for f in (a.clone/'Binaries/Win64').glob('*.target')]
m=dict(toolSHA=subprocess.check_output(['git','-C',str(a.clone),'rev-parse','HEAD'],text=True).strip(),sourceSHA=a.source,utc=datetime.now(timezone.utc).isoformat(),clone=str(a.clone.resolve()),build=str(a.build.resolve()),engineExecutable=str(engine),engineSHA256=sha(engine),moduleSHA256=sha(a.clone/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll'),gameSHA256=sha(exe),receipts=receipts,package=[dict(path=f.relative_to(package).as_posix(),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(package.rglob('*')) if f.is_file()])
m['builtGameSHA256']=sha(a.clone/'Binaries/Win64/AnimeMMORPG.exe')
assert m['builtGameSHA256']==m['gameSHA256'], 'Staged Game differs from built Game'
m['engineCommandletSHA256']=sha(engine.with_name('UnrealEditor-Cmd.exe'))
m['engineVersion']=json.loads((engine.parents[2]/'Build/Build.version').read_text())
m['gitTree']=subprocess.check_output(['git','-C',str(a.clone),'ls-tree','-r','HEAD','Source','Content','Config','Plugins','AnimeMMORPG.uproject'],text=True)
m['buildEvidence']=[dict(path=f.name,sha256=sha(f)) for f in sorted(a.build.glob('*')) if f.is_file()]
out=a.build/'BUILD-IDENTITY.json';assert not out.exists();out.write_text(json.dumps(m,indent=2),encoding='utf-8');print(out)
