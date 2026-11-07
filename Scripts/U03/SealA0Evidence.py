"""Seal U03-A0 evidence only; never read private workspace config contents."""
from pathlib import Path
import hashlib,json,gzip,re,subprocess
root=Path(__file__).resolve().parents[2]
runs=root/'Artifacts/U03/A0/Runs'; dest=root/'Docs/U03/Evidence/A0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(root),*a],text=True).strip()
def write(p,obj):p.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def decode_source(data):
 if data.startswith(b'\xff\xfe'): return data.decode('utf-16'), 'utf-16-le-bom'
 if data.startswith(b'\xfe\xff'): return data.decode('utf-16'), 'utf-16-be-bom'
 if data.startswith(b'\xef\xbb\xbf'): return data.decode('utf-8-sig'), 'utf-8-bom'
 # PowerShell may write UTF-16 without a BOM. Detect the ASCII structural bytes.
 if len(data)>4 and data[1::2].count(0)>len(data[1::2])//3:
  return data.decode('utf-16-le'), 'utf-16-le'
 return data.decode('utf-8'), 'utf-8'
dest.mkdir(parents=True,exist_ok=True)
entries=[];warnings=[];traces=[]
for p in sorted(runs.rglob('*')):
 if not p.is_file() or p.suffix not in ('.log','.json'):continue
 data=p.read_bytes()
 # Clone logs may carry credentials; retain raw privately, sanitize published copies.
 text,encoding=decode_source(data)
 clean,n=re.subn(r'(?im)(SecurityToken\s*[=:]\s*|Authorization\s*:\s*Bearer\s+)[^\s,\"}]+',r'\1[REDACTED]',text)
 rel=p.relative_to(runs);out=dest/rel;out.parent.mkdir(parents=True,exist_ok=True)
 if p.suffix=='.log':out=out.with_suffix('.log.gz');out.write_bytes(gzip.compress(clean.encode(),mtime=0))
 else:out.write_bytes(clean.encode('utf-8'))
 entries.append(dict(path=str(out.relative_to(dest)),rawSHA256=sha(p),publishedSHA256=sha(out),sourceEncoding=encoding,publishedEncoding='utf-8',redactions=n))
 for line in clean.splitlines():
  if re.search(r'warning |Warning:|error C\d|Error:',line):warnings.append(dict(run=str(rel),line=line))
  if 'U03A0_TRACE' in line or 'Test Completed.' in line or 'Automation Test Queue Empty' in line:traces.append(line)
clone=root/'Artifacts/U03/A0/Source'
binaries=[]
for name in ['UnrealEditor-AnimeMMORPG.dll','AnimeMMORPG.exe']:
 p=clone/'Binaries/Win64'/name
 if p.exists():binaries.append(dict(path=str(p),sha256=sha(p)))
source=git('-C',str(clone),'rev-parse','HEAD')
manifest=dict(base='f8434d23e4f27a649dde4ea21f47dd296c0fc9ba',source=source,branch=git('branch','--show-current'),binaries=binaries,files=entries,
 sourceFiles=[dict(path=p,gitBlob=git('rev-parse',source+':'+p)) for p in git('diff','--name-only','f8434d2',source,'--','Source').splitlines()],
 privateConfigUnchanged=sha(root/'Config/DefaultEngine.ini').upper()==(root/'Artifacts/U03-config-before.sha256').read_text().strip(),
 runtimePathsUnchanged=not git('diff','--name-only','f8434d2',source,'--','Source/AnimeMMORPG/U01','Source/AnimeMMORPG/U02','Content','Config','Plugins','AnimeMMORPG.uproject'),
 scope='A0 pure models and fresh existing Automation regression; no new input/network/package evidence')
write(dest/'MANIFEST.json',manifest);write(dest/'WARNINGS.json',warnings)
(dest/'TIMELINE.log').write_text('\n'.join(traces),encoding='utf-8')
print('Sealed',len(entries),'artifacts; runtime unchanged:',manifest['runtimePathsUnchanged'],'private config unchanged:',manifest['privateConfigUnchanged'])
