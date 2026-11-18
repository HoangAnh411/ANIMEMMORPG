"""Recompute every original assertion from retained raw data, including FAIL/INVALID attempts."""
import argparse,hashlib,json
from pathlib import Path
from AnalyzeB import analyze
p=argparse.ArgumentParser();p.add_argument('--runs',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
assert not a.out.exists();results=[]
for f in sorted(a.runs.glob('FPS*/Capture/*/ASSERTIONS.json')):
    expected=json.loads(f.read_text(encoding='utf-8'));raw=f.parents[2]/'Raw'/(expected['trial']+'.jsonl')
    actual=analyze(raw,expected['target'],expected['case'])
    keys=['status','gameplay','cadence','reason','rawSHA256','case','target','version']
    differences=[k for k in keys if actual.get(k)!=expected.get(k)]
    results.append(dict(assertion=str(f.resolve()),raw=str(raw.resolve()),status=expected['status'],matches=not differences,differences=differences))
out=dict(completed=bool(results) and all(r['matches'] for r in results),analyzerSHA256=hashlib.sha256(Path(__file__).with_name('AnalyzeB.py').read_bytes()).hexdigest(),attempts=results)
a.out.write_text(json.dumps(out,indent=2),encoding='utf-8');assert out['completed'],str(a.out)
print('PASS recomputed',len(results),'original assertions, preserving all status labels')
