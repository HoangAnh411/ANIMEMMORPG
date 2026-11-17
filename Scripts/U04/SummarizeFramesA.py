"""Describe measured frame intervals and actual cvars; never turn requested caps into FPS."""
import argparse,json,statistics
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--capture',type=Path,action='append',required=True);a=p.parse_args()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def utc(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
f=a.session/'all-processes.json';f=f if f.exists() else a.session/'processes.json'
records=read(f) if f.exists() else [read(a.session/'process.json')]
windows=[(utc(read(c/'command.json')['utc']),utc(read(c/'result.json')['completedUTC'])) for c in a.capture]
summaries=[]
for r in records:
 f=Path(r['log']).parent/'Frames.jsonl';rows=[]
 for line in f.read_text(encoding='utf-8-sig').splitlines():
  v=json.loads(line)
  if any(lo<=utc(v['utc'])<=hi for lo,hi in windows):rows.append(v)
 assert len(rows)>2, (r['role'],'no captured frame intervals')
 assert all(v['pid']==r['pid'] for v in rows)
 intervals=[y['wall']-x['wall'] for x,y in zip(rows,rows[1:])]
 assert all(t>0 for t in intervals) and all(y['frame']>x['frame'] for x,y in zip(rows,rows[1:]))
 def pct(q):return sorted(intervals)[round((len(intervals)-1)*q)]*1000
 keys=['t.MaxFPS','t.IdleWhenNotForeground','r.ScreenPercentage','r.LumenScene.SurfaceCache.AtlasSize','r.RenderTargetPoolMin','r.Streaming.PoolSize','r.Lumen.DiffuseIndirect.Allow','r.Lumen.Reflections.Allow','r.Shadow.Virtual.Enable','r.ShadowQuality']
 profile={k:sorted({v[k] for v in rows}) for k in keys}
 if r['role']!='Server':
  expected={'t.MaxFPS':60,'t.IdleWhenNotForeground':0,'r.ScreenPercentage':50,'r.LumenScene.SurfaceCache.AtlasSize':2048,'r.RenderTargetPoolMin':128,'r.Streaming.PoolSize':256,'r.Lumen.DiffuseIndirect.Allow':0,'r.Lumen.Reflections.Allow':0,'r.Shadow.Virtual.Enable':0,'r.ShadowQuality':2}
  assert all(profile[k]==[x] for k,x in expected.items()),profile
 else:assert profile['t.MaxFPS']==[30] and profile['t.IdleWhenNotForeground']==[0]
 summaries.append(dict(role=r['role'],pid=r['pid'],sourceSHA=r['sourceSHA'],frames=str(f),samples=len(rows),measuredFPS=1/statistics.mean(intervals),frameMsP50=pct(.5),frameMsP95=pct(.95),frameMsP99=pct(.99),maxMs=max(intervals)*1000,actualCvars=profile,scope='Captured active-gameplay interval; no U04-B or product FPS acceptance'))
out=a.session/'FRAME-SUMMARY.json';assert not out.exists();out.write_text(json.dumps(dict(completed=True,captures=[str(c) for c in a.capture],processes=summaries),indent=2),encoding='utf-8');print(out)
