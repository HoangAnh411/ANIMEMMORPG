"""Publish immutable review evidence with explicit raw/published SHA256 associations."""
import argparse,json,hashlib,gzip,re,shutil
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--gates',type=Path,required=True);p.add_argument('--publish',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[2]
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(8388608),b''):h.update(b)
 return h.hexdigest()
gates=json.loads(a.gates.read_text(encoding='utf-8'));assert gates['completed'] and gates['status']=='READY_FOR_REVIEW'
assert not a.publish.exists();a.publish.mkdir(parents=True)
records=[]
for f in sorted((root/'Artifacts/U04/A/Runs').rglob('*')):
 if not f.is_file():continue
 rel=f.relative_to(root/'Artifacts/U04/A/Runs')
 if 'Archive' in rel.parts or any(x.lower()=='settings' for x in rel.parts):continue
 dest=a.publish/'Runs'/rel;dest.parent.mkdir(parents=True,exist_ok=True)
 raw=sha(f);transform='identity'
 if f.suffix.lower() in ('.mp4','.png'):
  assert f.stat().st_size<95*1024*1024, ('Media requires separate publication packaging',f)
  shutil.copyfile(f,dest)
 else:
  data=f.read_bytes()
  if f.suffix.lower() in ('.json','.log','.txt','.csv'):
   enc='utf-16' if data[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig'
   try:
    text=data.decode(enc)
    clean=re.sub(r'(?i)(SecurityToken\s*[=:]\s*|AUTH_PASSWORD=)([^\s";]+)',r'\1[REDACTED]',text)
    if clean!=text:data=clean.encode(enc);transform='redact-secrets'
   except UnicodeDecodeError:pass
  dest=dest.with_name(dest.name+'.gz');dest.write_bytes(gzip.compress(data,compresslevel=6,mtime=0));transform+=';gzip'
 records.append(dict(raw=f.relative_to(root).as_posix(),rawSHA256=raw,rawBytes=f.stat().st_size,published=dest.relative_to(root).as_posix(),publishedSHA256=sha(dest),publishedBytes=dest.stat().st_size,transformation=transform))
for rel in ['Scripts/U01/F60Input.py','Scripts/U01/FReviewHost.ps1','Scripts/U02/EnsureEditorMinimized.ps1']:
 f=root/rel;dest=a.publish/'SharedHarness'/f.name;dest.parent.mkdir(exist_ok=True);shutil.copyfile(f,dest)
 records.append(dict(raw=rel,rawSHA256=sha(f),published=dest.relative_to(root).as_posix(),publishedSHA256=sha(dest),transformation='identity'))
manifest=dict(schema=1,status='READY_FOR_REVIEW',createdUTC=datetime.now(timezone.utc).isoformat(),sourceSHA=gates['sourceSHA'],mainBaseline=gates['mainBaseline'],gates=gates,files=records,warnings=['Packaged Server not passed; installed engine has no advertised Win64 Server platform/receipt and project has no Server target.','Review resolution/internal50% and measured intervals describe this host only; no U04-B or product60FPS/1080p acceptance.','All failed/invalid/intermediate/historical runs are retained and explicitly excluded from passing gates.','Automation actual schema exposes no XML export; raw log and exact expected/discovered/executed JSON are provided.'])
out=a.publish/'MANIFEST.json';out.write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(out,sha(out))
