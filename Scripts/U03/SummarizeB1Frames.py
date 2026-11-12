"""Measure wall-frame intervals, never mistake fixed simulation dt for measured FPS."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);s=p.parse_args().session.resolve();root=Path(__file__).resolve().parents[2];assert s.is_relative_to(root/'Artifacts/U03/B1')
out=[]
for path in s.glob('*/Frames.jsonl'):
 records=[json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines()];records=[v for v in records if v.get('frame',0)>100];wall=[]
 for before,after in zip(records,records[1:]):
  if after['wall']>before['wall']:wall.append((after['wall']-before['wall'])/max(1,after['frame']-before['frame']))
 if wall:out.append({'roleDirectory':path.parent.name,'samples':len(wall),'medianActualFrameMs':statistics.median(wall)*1000,'medianActualFPS':1/statistics.median(wall),'p95ActualFrameMs':sorted(wall)[int(.95*(len(wall)-1))]*1000,'maxActualFrameMs':max(wall)*1000,'editorThrottleValues':list(set(v.get('editorThrottle') for v in records)),'method':'FPlatformTime wall / GFrameCounter difference; whole session after first100 frames, includes setup/idle/reconnect; not U04 benchmark'})
(s/'wall-frame-summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))
