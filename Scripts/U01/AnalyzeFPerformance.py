"""Analyze opt-in F frame logs. Uses host UTC, not clamped game DeltaSeconds.

Game-thread mesh samples describe presentation transforms, not GPU scanout.
Packet observations are bounded by the receiving client's frame interval.
"""
import argparse,csv,json,statistics
from pathlib import Path
from datetime import datetime

p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--final-session',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def stamp(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
def quant(v,q):return sorted(v)[min(len(v)-1,int((len(v)-1)*q))] if v else None
def distribution(v):return {'n':len(v),'median':statistics.median(v) if v else None,'p95':quant(v,.95),'max':max(v) if v else None}
result={'method':'Every Game-world frame, shared localhost UTC; measured wall intervals, not clamped simulation DeltaSeconds. Mesh is game-thread presentation, not photon/scanout latency. No packet injection or smoothing tuning.','cases':[]}
spec=[('Session-20261105-130458',['BaselineAEnglish','BaselineBEnglish','HalfMotionA','HalfMotionB']),('Session-20261105-131333',['BudgetA','BudgetB','BudgetHalfMotionA','BudgetHalfMotionB','MinimizedMotionA','MinimizedMotionB','OriginalMinimizedA','OriginalMinimizedB'])]
if a.final_session:spec.append((str(a.final_session.resolve()),['FinalA','FinalB','RepeatA','RepeatB']))
for session,names in spec:
 r=a.artifacts/session;logs={};identities={}
 for role in ('Server','ClientA','ClientB'):
  logs[role]=[]
  lines=(r/role/(role+'.log')).read_text(encoding='utf-8-sig').splitlines()
  identities[role]=next(json.loads(line.split('U01F_NET ',1)[1]) for line in lines if 'U01F_NET {' in line)
  assert identities[role]['worldType']==1 and identities[role]['netMode']==(1 if role=='Server' else 3)
  for line in lines:
   if 'U01F_PERF {' not in line:continue
   try:s=json.loads(line.split('U01F_PERF ',1)[1])
   except json.JSONDecodeError:continue # Live log may end in a partial write.
   s['time']=stamp(s['utc']);logs[role].append(s)
 for name in names:
  meta_path=r/name/'process.json'
  if not meta_path.exists():continue
  m=load(meta_path);start=stamp(m['utc']);end=start+m['captureActiveSeconds']
  owner='ClientB' if name.endswith('B') or name=='BaselineBEnglish' else 'ClientA';peer='ClientB' if owner=='ClientA' else 'ClientA'
  samples={role:[s for s in ss if start<=s['time']<=end] for role,ss in logs.items()};id=next(v['id'] for s in samples[owner] for v in s['pawns'] if v['local']);case={'case':name,'session':session,'owner':owner,'pawn':id,'roles':{}}
  assert m['completed'] and m.get('menuWProbeAfter',m.get('menuWProbeBefore'))=='W'
  rows=[]
  for role,ss in samples.items():
   intervals=[(y['time']-x['time'])*1000 for x,y in zip(ss,ss[1:])]
   settings={k:sorted({s[k] for s in ss}) for k in ['t.MaxFPS','t.IdleWhenNotForeground','editorThrottle','r.VSync','r.ScreenPercentage','pktLag','pktLagMin','pktLagMax','pktLoss','pktOrder','pktDup','incomingLagMin','incomingLagMax','incomingLoss']}
   identity={k:identities[role][k] for k in ['sourceSHA','pid','world','worldType','netMode','context','localPlayers']}
   state={'identity':identity,'fps':(len(ss)-1)/(ss[-1]['time']-ss[0]['time']),'wallFrameMs':distribution(intervals),'focus':sorted({s['focus'] for s in ss}),'settings':settings,'pingMs':distribution([v['pingMs'] for s in ss for v in s['pawns'] if v['local'] or role=='Server']),'connectionAvgLagMs':distribution([c['avgLagSeconds']*1000 for s in ss for c in s['connections']]),'updateSettings':sorted({(v['updatesHz'],v['minUpdatesHz'],v['smoothMode'],v['smoothSeconds']) for s in ss for v in s['pawns']})}
   for s in ss:
    for v in s['pawns']:
     if v['id']==id:rows.append([role,s['utc'],s['time']-start,s['dt'],s['focus'],v['x'],v['repX'],v['meshX'],v['speed']])
   case['roles'][role]=state
  origin=next(v['x'] for s in samples[owner] for v in s['pawns'] if v['id']==id)
  times={}
  for label,role,field in [('ownerSimulation',owner,'x'),('serverSimulation','Server','x'),('peerPacketObserved',peer,'repX'),('peerMeshPresentation',peer,'meshX')]:
   times[label]=next((s['time']-start for s in samples[role] for v in s['pawns'] if v['id']==id and v[field]>origin+1),None)
  times['physicalW']=next(e['actualTime'] for e in m['events'] if e.get('key')=='W' and e['action']=='down')
  case['onsetSecondsFromRunStart']=times
  chain=['physicalW','ownerSimulation','serverSimulation','peerPacketObserved','peerMeshPresentation'];case['onsetStageMs']={x+' -> '+y:(times[y]-times[x])*1000 if times[y] is not None and times[x] is not None else None for x,y in zip(chain,chain[1:])}
  arrivals=[];last=None
  for s in samples[peer]:
   for v in s['pawns']:
    if v['id']==id and v['repX']!=last:
     if last is not None and start+1.5<=s['time']<=start+10:arrivals.append(s['time'])
     last=v['repX']
  case['peerChangedPacketIntervalsMs']=distribution([(y-x)*1000 for x,y in zip(arrivals,arrivals[1:])]);case['peerChangedPacketCount']=len(arrivals)
  active=[];down=None
  for event in m['events']:
   if event.get('key')=='W':
    if event['action']=='down':down=start+event['actualTime']
    elif down is not None:active.append((down,start+event['actualTime']));down=None
  case['intentWindowsUTCSeconds']=active
  case['peerMovingPacketIntervalsMs']=distribution([(y-x)*1000 for x,y in zip(arrivals,arrivals[1:]) if any(lo<=x<y<=hi for lo,hi in active)])
  case['packetCadenceCaveat']='All changed-position intervals retain the deliberate two-second stop. Moving intervals require both endpoints in the same actual W-held window; stationary actor positions do not imply packet loss.'
  case['peerMeshCapsuleOffsetCm']=distribution([abs(v['x']-v['meshX']) for s in samples[peer] for v in s['pawns'] if v['id']==id and v['speed']>100])
  case['peerMeshOffsetTimeEquivalentMs']=distribution([abs(v['x']-v['meshX'])/v['speed']*1000 for s in samples[peer] for v in s['pawns'] if v['id']==id and v['speed']>100])
  case['displayCaveat']='Onset at mesh and packet can share a frame; this does not imply zero ongoing smoothing. Offset is relative to extrapolated proxy capsule, not server-to-photon latency.'
  with (a.out/(name+'.csv')).open('w',encoding='utf8',newline='') as f:
   w=csv.writer(f,lineterminator='\n');w.writerow(['role','utc','caseSeconds','simulationDt','foreground','capsuleX','packetX','meshX','speed']);w.writerows(rows)
  result['cases'].append(case)
timer=a.artifacts/'TimerABA.json'
if timer.exists():
 phases=load(timer);ss=[]
 for line in (a.artifacts/'Session-20261105-131333/Server/Server.log').read_text(encoding='utf-8-sig').splitlines():
  if 'U01F_PERF {' in line:
   try:ss.append(json.loads(line.split('U01F_PERF ',1)[1]))
   except json.JSONDecodeError:pass
 result['serverTimerABA']=[]
 for phase in phases:
  frames=[s for s in ss if stamp(phase['start'])<=stamp(s['utc'])<=stamp(phase['end'])]
  result['serverTimerABA'].append(dict(phase,fps=(len(frames)-1)/(frames[-1]['wall']-frames[0]['wall']),wallFrameMs=distribution([(y['wall']-x['wall'])*1000 for x,y in zip(frames,frames[1:])])))
(a.out/'RESULTS.json').write_text(json.dumps(result,indent=2),encoding='utf8',newline='\n')
for c in result['cases']:
 print(c['case'],[(r,round(s['fps'],2),round(s['wallFrameMs']['p95'],1),round(s['wallFrameMs']['max'],1)) for r,s in c['roles'].items()],c['onsetStageMs'])
