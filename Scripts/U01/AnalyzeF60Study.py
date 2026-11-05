"""F60 observed capacity and transform latency; wall time is separate from GPU time."""
import argparse,csv,gzip,json,math,collections
from datetime import datetime
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,default=Path('Artifacts/U01/F/F60'));p.add_argument('--out',type=Path,default=Path('Docs/U01/Evidence/F60'));a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def t(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def stats(v):
 if not len(v):return {'n':0,'unavailable':'chưa đo được'}
 return dict(zip(('n','mean','median','p95','p99','max'),[len(v),*map(float,[np.mean(v),*np.percentile(v,[50,95,99,100])])]))
def write(name,x):(a.out/name).write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf8',newline='\n')
def readframes(record,buffered):
 path=Path(record['userDir'])/'Frames.jsonl' if buffered else Path(record['log']);frames=[];identity=None
 if buffered:
  for line in path.read_text(encoding='utf-8-sig').splitlines():
   try:frames.append(json.loads(line))
   except json.JSONDecodeError:pass
 lines=Path(record['log']).read_text(encoding='utf-8-sig').splitlines()
 for line in lines:
  if 'U01F_NET {' in line and identity is None:identity=json.loads(line.split('U01F_NET ',1)[1])
  if not buffered and 'U01F_PERF {' in line:
   try:frames.append(json.loads(line.split('U01F_PERF ',1)[1]))
   except json.JSONDecodeError:pass
 assert identity['worldType']==1 and identity['pid']==record['pid'] and identity['netMode']==(1 if record['role']=='Server' else 3)
 for f in frames:f['time']=t(f['utc'])
 return frames,{k:identity[k] for k in ('sourceSHA','pid','world','worldType','netMode','context','localPlayers')}
allruns=[]
for case in ('A','B','C','D','E','F3'):
 candidates=[]
 for path in sorted(a.artifacts.glob(case+'-*/MANIFEST.json')):
  m=load(path)
  if m.get('completed') and m.get('protocolValid',True) and m['input']['completed']:candidates.append((path,m))
 if not candidates:continue
 path,m=candidates[-1];start=t(m['input']['start']);duration=m['input']['requestedSeconds'];end=start+duration;samples={};run={'case':case,'manifest':str(path),'session':m['session'],'seconds':duration,'clientCap':m['clientCap'],'clientCount':m['clientCount'],'bufferedDiagnostics':m['bufferedDiagnostics'],'roles':{},'trials':[]}
 with gzip.open(a.out/(case+'-frames.csv.gz'),'wt',encoding='utf8',newline='') as out:
  w=csv.writer(out,lineterminator='\n');w.writerow(['role','utc','caseSeconds','frame','wall','simulationDt','foreground','gameMs','renderMs','rhiMs','gpuMs','pawnID','local','capsuleX','packetX','meshX','speed'])
  for record in m['processes']:
   role=record['role'];ss,identity=readframes(record,m['bufferedDiagnostics']);ss=[s for s in ss if start<=s['time']<end];assert len(ss)>2;samples[role]=ss
   assert all(y['frame']-x['frame']==1 for x,y in zip(ss,ss[1:])),('Missing/duplicate frame samples',case,role)
   intervals=[(y['wall']-x['wall'])*1000 for x,y in zip(ss,ss[1:])];focus={}
   for flag in (False,True):
    ds=[(y['wall']-x['wall'])*1000 for x,y in zip(ss,ss[1:]) if x['focus']==y['focus']==flag]
    focus['foreground' if flag else 'background']={'seconds':sum(ds)/1000,'fps':1000*len(ds)/sum(ds) if ds else None,'frameMs':stats(ds)}
   over=[{'utc':ss[i+1]['utc'],'caseSeconds':ss[i+1]['time']-start,'ms':dt,'focusTransition':ss[i]['focus']!=ss[i+1]['focus']} for i,dt in enumerate(intervals) if dt>100]
   streak=longest=0
   for dt in intervals:streak=streak+1 if dt>100 else 0;longest=max(longest,streak)
   states={k:sorted({s[k] for s in ss}) for k in ('t.MaxFPS','t.IdleWhenNotForeground','editorThrottle','r.VSync','r.ScreenPercentage','r.LumenScene.SurfaceCache.AtlasSize','r.RenderTargetPoolMin','r.Streaming.PoolSize','pktLag','pktLagMin','pktLagMax','pktLagVariance','pktJitter','pktLoss','incomingLagMin','incomingLagMax','incomingLoss','pktBufferBloatMs','incomingBufferBloatMs')}
   assert states['t.MaxFPS']==[30 if role=='Server' else m['clientCap']]
   row={'identity':identity,'fps':1000*len(intervals)/sum(intervals),'frames':len(ss),'frameMs':stats(intervals),'focus':focus,'runtime':states,'cpuGpuMs':{k:stats([s[k] for s in ss if s.get(k,0)>0]) for k in ('gameMs','renderMs','rhiMs','gpuMs')},'over100ms':over,'longestOver100msStreak':longest,'focusEvents':[{'utc':y['utc'],'foreground':y['focus']} for x,y in zip(ss,ss[1:]) if x['focus']!=y['focus']],'pingMs':stats([v['pingMs'] for s in ss for v in s['pawns'] if v['local']]),'updateSettings':sorted({(v['updatesHz'],v['minUpdatesHz'],v['smoothMode'],v['smoothSeconds']) for s in ss for v in s['pawns']})}
   assert len(row['updateSettings'])==1 and row['updateSettings'][0][:3]==(100,2,2) and abs(row['updateSettings'][0][3]-.1)<1e-6
   for s in ss:
    for v in s['pawns']:w.writerow([role,s['utc'],s['time']-start,s['frame'],s['wall'],s['dt'],s['focus'],*[s.get(k,'') for k in ('gameMs','renderMs','rhiMs','gpuMs')],v['id'],v['local'],v['x'],v['repX'],v['meshX'],v['speed']])
   run['roles'][role]=row
 # Ten forward starts AND stops per foreground direction in 120s; return strokes retained in input.
 for event in m['input']['events']:
  if event['action']!='key' or event.get('key')!='W':continue
  owner=event['role'];id=next(v['id'] for s in samples[owner] for v in s['pawns'] if v['local']);peer=next((r for r in samples if r not in ('Server',owner)),None);at=t(event['utc']);down=event['down'];trial={'role':owner,'kind':'start' if down else 'stop','inputUTC':event['utc'],'phase':event['phase'],'pawn':id};chain={}
  for label,role,field in [('owner',owner,'x'),('server','Server','x'),('peerPacket',peer,'repX'),('peerMesh',peer,'meshX')]:
   if role is None:continue
   before=[v for s in samples[role] if s['time']<=at for v in s['pawns'] if v['id']==id]
   if not before:chain[label]=None;continue
   base=before[-1][field];found=None;previous=None;stable=[]
   for s in samples[role]:
    v=next((v for v in s['pawns'] if v['id']==id),None)
    if v is None:continue
    if not at<=s['time']<=at+(1.8 if down else .79):previous=(s,v);continue
    stopped=v['speed']<3
    if not down and label=='peerMesh':
     stopped=stopped and previous is not None and abs(v['meshX']-previous[1]['meshX'])/(s['wall']-previous[0]['wall'])<3
     stable=stable+[s['time']] if stopped else []
     if len(stable)>=3:found=stable[0];break
    elif (v[field]>base+1) if down else stopped:found=s['time'];break
    previous=(s,v)
   chain[label]=found
  trial['valid']=all(v is not None for v in chain.values());trial['onsetsUTCSeconds']=chain
  trial['stagesMs']={x+'->'+y:(chain[y]-chain[x])*1000 if chain.get(y) is not None and chain.get(x) is not None else None for x,y in [('owner','server'),('server','peerPacket'),('peerPacket','peerMesh')] if x in chain and y in chain}
  trial['inputToServerMs']=(chain['server']-at)*1000 if chain.get('server') is not None else None
  trial['inputToPeerMeshMs']=(chain['peerMesh']-at)*1000 if chain.get('peerMesh') is not None else None
  run['trials'].append(trial)
 run['latency']={}
 for owner in ('ClientA','ClientB'):
  if owner not in samples:continue
  run['latency'][owner]={}
  for kind in ('start','stop'):
   ts=[x for x in run['trials'] if x['role']==owner and x['kind']==kind];valid=[x for x in ts if x['valid']]
   run['latency'][owner][kind]={'attempted':len(ts),'valid':len(valid),'invalid':len(ts)-len(valid),'inputToServerMs':stats([x['inputToServerMs'] for x in valid]),'inputToPeerMeshMs':stats([x['inputToPeerMeshMs'] for x in valid if x['inputToPeerMeshMs'] is not None])}
 resources=[]
 for line in (Path(m['session'])/'resources.jsonl').read_text(encoding='utf-8-sig').splitlines():
  if not line:continue
  try:r=json.loads(line)
  except json.JSONDecodeError:continue
  if start<=t(r['utc'])<end:resources.append(r)
 write(case+'-resources.json',resources);write(case+'-manifest.json',m)
 run['resources']={'n':len(resources),'gpuMemoryUsedMiB':stats([float(r['gpuCsv'].split(',')[1]) for r in resources]),'gpuUtilPercent':stats([float(r['gpuCsv'].split(',')[2]) for r in resources]),'sharedMemoryBytes':{r['role']:stats([sum(v['value'] for v in s['counters'] if 'pid_'+str(r['pid'])+'_' in v['instance'] and v['path'].lower().endswith('shared usage')) for s in resources]) for r in m['processes']}}
 write(case+'-results.json',run);allruns.append(run)
result={'method':'Continuous wall intervals 120/300 s; percentiles numpy linear. Every-frame timestamps; transform timings are game-thread observations, not scanout. Last-drawn-frame raw stat-unit CPU/GPU time; no GPU time inferred from cap. Buffered control removes per-frame log I/O, not JSON collection cost.','runs':allruns}
by={r['case']:r for r in allruns}
if 'C' in by:
 c=by['C'];fps_ok=all(c['roles'][r]['fps']>=57 and c['roles'][r]['frameMs']['p95']<=20 for r in ('ClientA','ClientB')) and c['roles']['Server']['fps']>=28.5
 no_chain=all(v['longestOver100msStreak']<3 and v['frameMs']['max']<500 for v in c['roles'].values());valid=all(c['latency'][r]['start']['valid']>=10 and c['latency'][r]['stop']['valid']>=10 for r in ('ClientA','ClientB'));flags=[]
 if 'A' in by:
  for role in ('ClientA','ClientB'):
   for kind in ('start','stop'):
    new=c['latency'][role][kind]['inputToPeerMeshMs'];old=by['A']['latency'][role][kind]['inputToPeerMeshMs']
    if new['n'] and old['n'] and (new['median']-old['median']>20 or new['p95']-old['p95']>33):flags.append(role+'/'+kind)
 # Explain the observed stop tail using actual offsets, not a speculative network fix.
 # UE CharacterMovementComponent.cpp:8470-8474 uses offset *= 1-dt/(0.5*SmoothTime)
 # when velocity is exactly zero. Keep that implementation/settings unchanged.
 fits={};decomposition={}
 if 'A' in by:
  for label in ('A','C'):
   groups=collections.defaultdict(list)
   with gzip.open(a.out/(label+'-frames.csv.gz'),'rt',encoding='utf8') as f:
    for row in csv.DictReader(f):
     if row['role']!='Server' and row['local']=='False':groups[(row['role'],row['pawnID'])].append(row)
   observed=[];expected=[];errors=[]
   for rows in groups.values():
    for x,y in zip(rows,rows[1:]):
     dx=float(x['meshX'])-float(x['capsuleX']);dy=float(y['meshX'])-float(y['capsuleX']);dt=float(y['simulationDt'])
     if float(x['speed'])==float(y['speed'])==0 and abs(float(x['capsuleX'])-float(y['capsuleX']))<1e-6 and abs(dx)>.02 and abs(dy)>.02 and 0<dt<.05:
      observed.append(dy/dx);expected.append(1-dt/.05);errors.append(abs(dy/dx-(1-dt/.05)))
   fits[label]={'observedRatio':stats(observed),'predictedRatio':stats(expected),'absoluteError':stats(errors)}
  for role in ('ClientA','ClientB'):
   means={}
   for label in ('A','C'):
    ts=[v for v in by[label]['trials'] if v['role']==role and v['kind']=='stop' and v['valid']]
    means[label]={'inputToServerMs':float(np.mean([v['inputToServerMs'] for v in ts])),'serverToPeerPacketMs':float(np.mean([v['stagesMs']['server->peerPacket'] for v in ts])),'peerPacketToMeshSettledMs':float(np.mean([v['stagesMs']['peerPacket->peerMesh'] for v in ts])),'inputToMeshSettledMs':float(np.mean([v['inputToPeerMeshMs'] for v in ts]))}
   decomposition[role]={'means':means,'CminusA':{k:means['C'][k]-means['A'][k] for k in means['A']}}
 formula_proven=bool(fits) and all(v['absoluteError']['n']>=20 and v['absoluteError']['p95']<1e-5 for v in fits.values())
 explained=bool(flags) and all(f.endswith('/stop') for f in flags) and formula_proven and all(v['CminusA']['serverToPeerPacketMs']<=0 and v['CminusA']['peerPacketToMeshSettledMs']>0 for v in decomposition.values())
 result['latencyExplanation']={'engineSource':'UE5.8 Engine/Private/Components/CharacterMovementComponent.cpp:8470-8474','unchangedSmoothing':'Exponential / NetworkSimulatedSmoothLocationTime=0.1s; at zero velocity time=0.05s','offsetDecayFits':fits,'stopMeanDecomposition':decomposition,'explainsFlaggedStopIncrease':explained,'interpretation':'Fully-settled mesh threshold includes physical braking and discrete exponential smoothing, not merely transport delay. At 30Hz factor is ~1/3, at 60Hz ~2/3. No engine or smoothing changes made.'}
 result['selection']={'defaultClientMaxFPS':60 if fps_ok and no_chain and valid and (not flags or explained) else 30,'fpsCriteriaMet':fps_ok,'noLongStutterChain':no_chain,'tenValidStartsStopsPerDirection':valid,'latencyIncreaseFlags':flags,'stopIncreaseExplainedByMeasuredDecay':explained,'latencyFlagRule':'Review if median increases >20ms or p95 >33ms versus A; not a gameplay rule','stutterRule':'Reject repeated 3x >100ms or an isolated >500ms; report every >100ms regardless'}
write('RESULTS.json',result)
for r in allruns:print(r['case'],[(k,round(v['fps'],2),round(v['frameMs']['p95'],2),round(v['frameMs']['p99'],2),round(v['frameMs']['max'],2)) for k,v in r['roles'].items()],'valid trials',{role:{kind:v['valid'] for kind,v in values.items()} for role,values in r['latency'].items()})
if 'selection' in result:print('SELECTION',result['selection'])
