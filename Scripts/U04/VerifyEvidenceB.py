"""Verify published evidence and, on the capture host, raw/published associations."""
import argparse,gzip,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('manifest',type=Path);p.add_argument('--published-only',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[2];m=json.loads(a.manifest.read_text(encoding='utf-8'))
def sha(f):
    h=hashlib.sha256()
    with f.open('rb') as s:
        for chunk in iter(lambda:s.read(8388608),b''):h.update(chunk)
    return h.hexdigest()
if not a.published_only:assert sha(Path(m['gatesRawPath']))==m['gatesRawSHA256'], 'Raw final gates changed'
for r in m['files']:
    f=root/r['published'];assert sha(f)==r['publishedSHA256'],f
    if not a.published_only:
        raw=Path(m['rawRoot'])/r['raw'];assert sha(raw)==r['rawSHA256'],raw
    if 'redact' not in r['transformation']:
        data=gzip.decompress(f.read_bytes()) if 'gzip' in r['transformation'] else f.read_bytes()
        assert hashlib.sha256(data).hexdigest()==r['rawSHA256'],f
print('PASS',len(m['files']),'evidence associations')
