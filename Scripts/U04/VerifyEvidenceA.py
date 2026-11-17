"""Rehash a sealed raw/published manifest without modifying evidence."""
import argparse,json,hashlib,gzip
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('--published-only',action='store_true');a=p.parse_args();r=Path(__file__).resolve().parents[2];m=json.loads(a.manifest.read_text(encoding='utf-8'))
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(8388608),b''):h.update(b)
 return h.hexdigest()
for v in m['files']:
 f=r/v['published'];assert sha(f)==v['publishedSHA256'],v['published']
 if not a.published_only:
  raw=r/v['raw'];assert sha(raw)==v['rawSHA256'],v['raw']
  if 'redact' not in v['transformation']:
   data=gzip.decompress(f.read_bytes()) if 'gzip' in v['transformation'] else f.read_bytes()
   assert hashlib.sha256(data).hexdigest()==v['rawSHA256'],v['published']
print('PASS',len(m['files']),'raw/published evidence associations')
