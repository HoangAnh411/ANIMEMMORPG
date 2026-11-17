"""Measured frame statistics during authority-observed combat; model step rates are not render FPS."""
import argparse,json,re
from pathlib import Path
from datetime import datetime
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);a=p.parse_args()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def stamp(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
records=read(a.session/'all-processes.json') if (a.session/'all-processes.json').exists() else read(a.session/'processes.json')
rows=[]
for process in records:
 path=Path(process['log']).parent/'Frames.jsonl'
 if not path.exists():continue
 states=[]
 for line in Path(process['log']).read_text(encoding='utf-8-sig').splitlines():
  if 'U02F_STATE {' not in line:continue
  value=json.loads(line.split('U02F_STATE ',1)[1])
  if any(x.get('action',0)>0 and x.get('locked',False) for x in value.get('pawns',[])):states.append(stamp(value['utc']))
 frames=[json.loads(x) for x in path.read_text(encoding='utf-8-sig').splitlines() if x.strip()];cap=30 if process['role']=='Server' else 60
 for previous,current in zip(frames,frames[1:]):current['measuredFrameSeconds']=current['wall']-previous['wall']
 selected=[x for x in frames if x['t.MaxFPS']==cap and len(x.get('pawns',[]))>=4 and x['dt']>0 and any(abs(stamp(x['utc'])-s)<=.12 for s in states)]
 assert selected,(process['role'],'No measured runtime combat frames')
 dt=np.array([x['measuredFrameSeconds'] for x in selected if x.get('measuredFrameSeconds',0)>0]);entry=dict(role=process['role'],pid=process['pid'],source=process['sourceSHA'],framesFile=str(path),allFrames=len(frames),combatFrames=len(selected),requestedCap=cap,measuredFPS=float(1/np.mean(dt)),frameMsP50=float(np.percentile(dt,50)*1000),frameMsP95=float(np.percentile(dt,95)*1000),frameMsP99=float(np.percentile(dt,99)*1000),maxFrameMs=float(max(dt)*1000),focusedFrames=sum(bool(x['focus']) for x in selected),worldStepMsP95=float(np.percentile([x['dt'] for x in selected],95)*1000))
 for k in ['gameMs','renderMs','gpuMs']:
  values=[x[k] for x in selected if x.get(k,0)>0]
  if values:entry[k+'P95']=float(np.percentile(values,95))
 entry['profiles']={k:sorted(set(x[k] for x in selected)) for k in ['t.MaxFPS','t.IdleWhenNotForeground','r.ScreenPercentage','r.LumenScene.SurfaceCache.AtlasSize','r.RenderTargetPoolMin','r.Streaming.PoolSize','editorThrottle']}
 entry['smoothing']=sorted(set((v['smoothMode'],v['smoothSeconds'],v['updatesHz'],v['minUpdatesHz']) for x in selected for v in x.get('pawns',[])))
 assert entry['profiles']['t.MaxFPS']==[cap] and entry['profiles']['t.IdleWhenNotForeground']==[0]
 rows.append(entry)
assert {'Server','ClientA','ClientB'}.issubset({x['role'] for x in rows})
result=dict(completed=True,selection='actual authority action active within120ms of frame timestamp; cap applied; two encounter pairs present; all raw frames retained',measurement='FPS/frame percentiles use successive monotonic wall timestamps sampled every game/render frame; world dt retained separately; GPU stat is separate',note='Review profile only; actual FPS is not guaranteed by cap60/server30 and is not U04 acceptance',processes=rows)
(a.capture/'profile.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps([dict(role=x['role'],pid=x['pid'],fps=x['measuredFPS'],p99=x['frameMsP99']) for x in rows]))
