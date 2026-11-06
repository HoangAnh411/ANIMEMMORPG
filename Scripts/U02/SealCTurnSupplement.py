"""Preserve comparison footage, failed setup logs, and actual transform traces."""
import argparse,json,hashlib,gzip,shutil,re
from pathlib import Path
p=argparse.ArgumentParser()
for name in ['before','after','evidence','frames']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2];out=a.evidence.resolve();assert out.is_relative_to(root/'Docs/U02/Evidence');out.mkdir(exist_ok=True,parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
items=[]
for label,session in [('Before',a.before),('After',a.after)]:
 for name in ['Input-C.mp4','input.json','TURN-ASSERTIONS.json','YAW-TRACE.csv']:
  source=session/'Capture'/name;target=out/(label+'-'+name);shutil.copyfile(source,target);items.append(dict(file=target.name,sha256=sha(target),original=str(source)))
 target=out/(label+'-Turn-Game.log.gz')
 with gzip.open(target,'wb') as f:f.write((session/'Game.log').read_bytes())
 items.append(dict(file=target.name,sha256=sha(target),rawSHA256=sha(session/'Game.log')))
for p in a.frames.iterdir():
 if p.is_file():shutil.copyfile(p,out/p.name)
for name in ['Before-Historical-Realtime.mp4','Before-Historical-Realtime.json']:
 shutil.copyfile(root/'Artifacts/U02/C'/name,out/name)
history=[]
for source in sorted((root/'Artifacts/U02/C').glob('turn-*.log')):
 raw=source.read_bytes();s=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig',errors='replace');assert not re.search(r'(?im)\bSecurityToken\s*=\s*[^\s\r\n]+',s)
 target=out/('History-'+source.name+'.gz')
 with gzip.open(target,'wb') as f:f.write(raw)
 history.append(dict(file=target.name,rawSHA256=sha(source),original=str(source)))
for source in sorted((root/'Artifacts/U02/C').glob('Author-*/Editor.log')):
 target=out/(source.parent.name+'-Editor.log.gz')
 with gzip.open(target,'wb') as f:f.write(source.read_bytes())
 history.append(dict(file=target.name,rawSHA256=sha(source),original=str(source)))
for path in [root/'Artifacts/U02/C/Turn-Before-61be83b/INVALID.txt',root/'Artifacts/U02/C/SmokeB-20261106-102717/INVALID.txt']:
 shutil.copyfile(path,out/(path.parent.name+'-INVALID.txt'))
for session_name in ['Turn-Before-61be83b','Play-Turn-2e166a2','Turn-After-2e166a2']:
 session=root/'Artifacts/U02/C'/session_name
 source=session/'Game.log';target=out/('History-'+session_name+'-Game.log.gz')
 with gzip.open(target,'wb') as f:f.write(source.read_bytes())
 history.append(dict(file=target.name,rawSHA256=sha(source),original=str(source)))
 for name in ['input.json','ASSERTIONS.json','TURN-ASSERTIONS.json']:
  source=session/'Capture'/name
  if source.exists():shutil.copyfile(source,out/('History-'+session_name+'-'+name))
for source in (root/'Artifacts/U02/C/SmokeB-20261106-102717').glob('*/Game.log'):
 target=out/('Invalid-Source-Stamp-'+source.parent.name+'-Game.log.gz')
 with gzip.open(target,'wb') as f:f.write(source.read_bytes())
 history.append(dict(file=target.name,rawSHA256=sha(source),original=str(source)))
(out/'COMPARISON.json').write_text(json.dumps(items,indent=2))
(out/'REVISION-HISTORY.json').write_text(json.dumps(history,indent=2))
(out/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n')
(out/'ASSETS.json').write_text(json.dumps([dict(path=p.relative_to(root).as_posix(),sha256=sha(p),bytes=p.stat().st_size,provenance='project-authored technical blockout; accepted U01 skeleton/socket/grip unchanged') for p in (root/'Content/AnimeMMORPG/U02/Animation').glob('*.uasset')],indent=2))
files=sorted(p for p in out.iterdir() if p.is_file() and p.name!='EVIDENCE-SHA256.json')
(out/'EVIDENCE-SHA256.json').write_text(json.dumps([dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in files],indent=2))
