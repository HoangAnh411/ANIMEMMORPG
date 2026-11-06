import argparse,json,re,statistics
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--label',default='Baseline');a=p.parse_args();inp=json.loads((a.session/a.label/'input.json').read_text());records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'))
def t(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def stats(v):
 if not v:return None
 v=sorted(v);return {'n':len(v),'median':statistics.median(v),'p95':v[int((len(v)-1)*.95)],'max':max(v)}
frames={};metrics={};presses={};profiles={}
for r in records:
 fs=[]
 framepath=Path(next(v.split('=',1)[1].strip(chr(34)) for v in r['arguments'] if v.startswith('-U01FPerfFile=')))
 for l in framepath.read_text().splitlines():
  try:f=json.loads(l);f['time']=t(f['utc']);fs.append(f)
  except ValueError:pass
 frames[r['pid']]=fs;ms=[];ps=[]
 for l in Path(r['log']).read_text(encoding='utf-8-sig',errors='replace').splitlines():
  if 'Metrics {' in l:
   try:m=json.loads(l.split('Metrics ',1)[1]);m['time']=t(m['utc']);ms.append(m)
   except ValueError:pass
  if 'PhysicalPress key=W ' in l:
   match=re.match(r'\[(\d{4})\.(\d\d)\.(\d\d)-(\d\d)\.(\d\d)\.(\d\d):(\d+)\]',l)
   if match:
    yy,mo,dd,hh,mi,ss,frac=match.groups();ps.append({'time':t(f'{yy}-{mo}-{dd}T{hh}:{mi}:{ss}.{frac}+00:00'),'line':l})
 metrics[r['pid']]=ms;presses[r['pid']]=ps
 keys=('t.MaxFPS','t.IdleWhenNotForeground','r.ScreenPercentage','editorThrottle','r.LumenScene.SurfaceCache.AtlasSize','r.RenderTargetPoolMin','r.Streaming.PoolSize','pktLag','pktLoss')
 profiles[r['role']]={k:sorted(set(f.get(k) for f in fs[-100:]),key=str) for k in keys}
rows=[]
for q in inp['trials']:
 if 'endUTC' not in q:continue
 target=next(r for r in records if r['role']==q['to']);pid=target['pid'];foc=t(q['focusUTC']);key=t(q['keyUTC']) if 'keyUTC'in q else foc;fs=frames[pid];localid=next((p['id'] for f in fs if f['time']>=foc for p in f['pawns'] if p['local']),None)
 def movement(role):
  record=next(r for r in records if r['role']==role)
  return next((f['time'] for f in frames[record['pid']] if key-.05<=f['time']<=key+2 for v in f['pawns'] if v['id']==localid and v['speed']>1),None)
 first=next((v for v in presses[pid] if key-.1<=v['time']<=key+1),None)
 bins={}
 for lo,hi in ((-5,0),(0,.5),(.5,2),(2,5),(5,15)):
  ff=[f for f in fs if foc+lo<=f['time']<foc+hi];wall=[(b['wall']-a['wall'])*1000 for a,b in zip(fs,fs[1:]) if foc+lo<=b['time']<foc+hi]
  bins[f'{lo}:{hi}']={'gameMs':stats([f.get('gameMs',0) for f in ff]),'renderMs':stats([f.get('renderMs',0) for f in ff]),'gpuMs':stats([f.get('gpuMs',0) for f in ff]),'allRoles':{r['role']:{'dtMs':stats([v['dt']*1000 for v in frames[r['pid']] if foc+lo<=v['time']<foc+hi]),'wallMs':stats([(bb['wall']-aa['wall'])*1000 for aa,bb in zip(frames[r['pid']],frames[r['pid']][1:]) if foc+lo<=bb['time']<foc+hi])} for r in records},'dtMs':stats([v['dt']*1000 for v in ff]),'wallMs':stats(wall),'focusSamples':sum(v['focus'] for v in ff),'frames':len(ff)}
 local=movement(q['to']);server=movement('Server');other=movement(q['from']);rows.append({'index':q['index'],'direction':q['from']+'->'+q['to'],'focusUTC':q['focusUTC'],'activatedUTC':q.get('activatedUTC'),'focusCallMs':(t(q['activatedUTC'])-foc)*1000,'activationFrameMs':next(((b['wall']-aa['wall'])*1000 for aa,b in zip(fs,fs[1:]) if b['time']>=foc),None),'resumeToKeyMs':(key-t(q.get('resumeUTC',q['focusUTC'])))*1000,'keyToNativePressMs':(first['time']-key)*1000 if first else None,'pressLine':first['line'] if first else None,'keyToOwnedTransformMs':(local-key)*1000 if local else None,'keyToServerTransformMs':(server-key)*1000 if server else None,'keyToPeerTransformMs':(other-key)*1000 if other else None,'bins':bins,'controlSamples':[m for m in metrics[pid] if foc-5<=m['time']<=foc+15]})
out={'completed':inp['completed'],'profiles':profiles,'trials':rows,'limitations':'Per-frame game-thread transforms, not display latency. Native controls sampled5Hz. UTC millisecond quantization. Input timestamp recorded just after SendInput; small negative samples possible.'};(a.session/a.label/'analysis.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(completed=inp['completed'],trials=len(rows),targetMaxMs=[max(b['wallMs']['max'] for k,b in r['bins'].items() if k!='-5:0' and b['wallMs']) for r in rows],lateP95=[r['bins']['5:15']['wallMs']['p95'] for r in rows])))
