import argparse,json,hashlib,gzip,shutil,re,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--damage',type=Path,required=True);p.add_argument('--controls',type=Path,required=True);p.add_argument('--boot',type=Path,required=True);p.add_argument('--reopen',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[2];out=a.evidence.resolve();assert out.is_relative_to(root/'Docs/U02/Evidence');out.mkdir(exist_ok=True,parents=True)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=load(out/'MANIFEST.json');source=manifest['sourceSHA'];controls=load(a.controls/'Capture/ASSERTIONS.json');assert controls['sourceSHA']==source and controls['failed']==0
for name in ['input.json','ASSERTIONS.json','Controls-E.mp4','Final.png']:
 shutil.copyfile(a.controls/'Capture'/name,out/('Controls-'+name))
for p in (a.damage/'Capture').glob('*.png'):shutil.copyfile(p,out/p.name)
shutil.copyfile(a.damage/'Capture/DAMAGE-TRACE.log',out/'DAMAGE-TRACE.log')
roundtrip=[]
for label,session in [('Boot',a.boot),('Reopen',a.reopen)]:
 m=load(session/'Capture/input.json');assert m['completed'] and m['externalInputMethodRestored'] and m['process']['sourceSHA']==source and m['exitCode']==0 and m['windowClosed']
 if label=='Boot':assert m['bootMapVerified']
 for p in (session/'Capture').iterdir():
  if p.is_file():shutil.copyfile(p,out/(label+'-'+p.name))
 roundtrip.append(dict(label=label,pid=m['process']['pid'],binarySHA256=m['process']['binarySHA256'],sourceSHA=m['process']['sourceSHA'],exitCode=0,bootVerified=m.get('bootMapVerified',False),method='actual input Back to Boot or menu Quit; native map load and original process handle signalled exit0'))
assert roundtrip[0]['pid']!=roundtrip[1]['pid'] and roundtrip[0]['binarySHA256']==roundtrip[1]['binarySHA256'];(out/'BOOT-QUIT-REOPEN.json').write_text(json.dumps(roundtrip,indent=2))
history=[]
paths=list((root/'Artifacts/U02/E').glob('*.log'))+[a.controls/'Game.log',a.boot/'Game.log',a.reopen/'Game.log']
paths+=list((root/'Artifacts/U02/E').glob('Play-BootQuit*/Game.log'))
for src in paths:
 if not src.exists():continue
 raw=src.read_bytes();txt=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig',errors='replace');assert not re.search(r'(?im)\bSecurityToken\s*=\s*[^\s\r\n]+',txt)
 name='History-'+src.parent.name+'-'+src.name+'.gz'
 with gzip.open(out/name,'wb') as f:f.write(raw)
 history.append(dict(file=name,rawSHA256=sha(src),original=str(src)))
for session in ['Play-Damage','Play-Controls','Play-BootQuit']:
 src=root/'Artifacts/U02/E'/session
 for f in [src/'Capture/input.json',src/'Capture/ASSERTIONS.json',src/'INVALID.txt']:
  if f.exists():shutil.copyfile(f,out/('History-'+session+'-'+f.name))
(out/'HISTORY.json').write_text(json.dumps(history,indent=2));(out/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n')
manifest.update(controlsRuntimeAssertions=controls['passed'],damageRuntimeAssertions=manifest['runtimeAssertions'],bootQuitReopen=True,reviewAccepted=False,networkAgreementAccepted=False,damageSession=str(a.damage),controlsSession=str(a.controls));(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2))
files=sorted(p for p in out.iterdir() if p.is_file() and p.name!='EVIDENCE-SHA256.json');(out/'EVIDENCE-SHA256.json').write_text(json.dumps([dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in files],indent=2))
