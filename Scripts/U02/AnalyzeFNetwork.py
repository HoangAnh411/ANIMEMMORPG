import argparse,json,re,statistics,math
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);a=p.parse_args();checks=[]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def epoch(v):return datetime.fromisoformat(v.replace('Z','+00:00')).timestamp()
def lines(p):
 raw=p.read_bytes();return raw[:raw.rfind(b'\n')+1].decode('utf-8-sig',errors='replace').splitlines()
def parsed(p,tag):return [json.loads(l.split(tag,1)[1]) for l in lines(p) if tag+'{' in l]
def check(n,v):checks.append(dict(check=n,result='PASS' if v else 'FAIL'))
primary=load(a.session/'Capture/input.json');control=load(a.session/'Controls/input.json');disconnect=load(a.session/'Disconnect/ASSERTIONS.json');source=primary['processes'][0]['sourceSHA'];check('Primary complete and IME restored',primary['completed'] and primary['externalInputMethodRestored'] and primary['failed']==0);check('Controls complete and IME restored',control['completed'] and control['externalInputMethodRestored']);check('Actual disconnect/reconnect proof complete',disconnect['completed'] and disconnect['noDamageAfterRemoval'] and disconnect['freshIdentityAndCommand']);check('Different connection identity',disconnect['oldPawn']!=disconnect['newPawn']);check('Initial life1 then fixture life2',disconnect['initialReconnectSubject']['life']==1 and disconnect['postFixtureLife']==2)
records={r['role']:r for r in control['processes']};start=epoch(control['utc']);end=start+control['captureSeconds'];metrics={};states={}
for k,r in records.items():
 metrics[k]=[q for q in parsed(Path(r['log']),'Metrics ') if start<=epoch(q['utc'])<=end]
 states[k]=parsed(Path(r['log']),'U02F_STATE ')
check('Source/PID/native worlds correct',all(q['sourceSHA']==source and q['pid']==records[k]['pid'] and q['worldType']==1 and q['netMode']==(1 if k=='Server' else 3) for k,ss in states.items() for q in ss));rows=metrics['ClientA'];check('Owned runtime samples present',len(rows)>100 and all(q['locallyControlled'] and q['owner']==q['controller'] and q['localPlayers']==1 for q in rows))
for q in rows:q['t']=epoch(q['utc'])-start
events={e['label']:e['actual'] for e in control['events']};speed=lambda q:q['animationGroundSpeedCmPerSec'];lock=[q for q in rows if q['combat']['locked']];check('Observed combat lock stops horizontal movement',bool(lock) and all(speed(q)<.1 for q in lock));check('Held WASD resumes after recovery',any(speed(q)>490 for q in rows if events['Attack']+.55<q['t']<events['W up']-.05));check('Sprint returns accepted U01 speed',any(speed(q)>699 and q['maxSpeedCmPerSec']==700 and q['sprinting'] for q in rows if events['Sprint Ctrl']+.3<q['t']<events['Ctrl up']));check('Gravity continues under menu',any(q['controlState']!=0 and q['animationVerticalSpeedCmPerSec']<-50 for q in rows));check('Resume clicks do not create attack',control['after']['combat']['accepted']==control['before']['combat']['accepted']+1);check('Fresh W after focus/Resume works',any(speed(q)>490 for q in rows if events['Fresh W']+.25<q['t']<events['W release']));check('Focus requires AwaitingResume',any(q['controlState']==2 for q in rows if events['Focus B']<q['t']<events['Focus A Resume']));check('Settings remain unchanged',json.loads(control['before']['settings'])==json.loads(control['after']['settings']));check('Actual U02 graph loaded, root motion ignored',bool(rows) and all('/ABP_U02.' in q['animClass'] and q['rootMotionMode']==1 for q in rows));check('Actual montage runs then returns',any(q['attackPresented'] for q in rows) and not control['after']['attackPresented']);y=[q for q in rows if q['combat']['yawLocked'] and q['combat']['locked']];check('Actual body locked to confirmed aim',bool(y) and all(abs((q['bodyYawDegrees']-q['combat']['aimYaw']+180)%360-180)<.1 for q in y));check('Camera moves independently during locked phase',len({round(float(q['aimYawPitchDegrees'].split('Y=')[1].split()[0]),1) for q in y})>1)
server=states['Server'];check('Server advances while client menu/focus',server[-1]['time']>server[0]['time']+5);all_results=server[-1]['results'];keys=[(r['source'],r['sourceLife'],r['action'],r['target'],r['targetLife']) for r in all_results];check('One confirmed event per source action target life',len(keys)==len(set(keys)));check('Serials monotonic and unique',all_results and [r['serial'] for r in all_results]==sorted(set(r['serial'] for r in all_results)));be=parsed(Path(records['Server']['log']),'U02B_EVENT ');check('Actual server rejects nonfinite aim at correct stage',any(q['event']=='Rejected' and 'reason=2 ' in q['detail'] for q in be));check('Actual server rejects stale life',any(q['event']=='RejectedLife' for q in be));check('Actual server rejects duplicate command',any(q['event']=='Rejected' and 'reason=3 ' in q['detail'] for q in be))
stage={q['label']:epoch(q['utc']) for q in primary['stages']}
check('NaN rejection tied to its actual wire probe',any(q['event']=='Rejected' and 'reason=2 ' in q['detail'] and stage['ConcurrentLethal']<=epoch(q['utc'])<=stage['NonfiniteAim'] for q in be))
check('Duplicate rejection tied to its actual wire probe',any(q['event']=='Rejected' and 'reason=3 ' in q['detail'] and stage['HitMulti']<=epoch(q['utc'])<=stage['Duplicate'] for q in be))
check('One RNG roll per valid network hit',all(p['critRolls']==len(all_results) for p in server[-1]['pawns']))
newrows=states['ClientA'];newid=disconnect['newPawn'];initialserver=next(q for q in server if any(p['id']==newid and p['life']==1 for p in q['pawns']))
def currenttargets(q):return sorted((t['id'],t['lifeGeneration'],t['hp'],t['shield'],t['dead']) for t in q['targets'])
oldhistorysafe=any(currenttargets(q)==currenttargets(initialserver) and any(p['local'] and p['life']==1 for p in q['pawns']) and any(any(t['id']==r['target'] and t['lifeGeneration']>r['targetLife'] and t['hp']!=r['hp'] for t in q['targets']) for r in q['results']) for q in newrows)
check('Reconnect old result history cannot overwrite current-life HP',oldhistorysafe)
# Presentation on each client for the same authoritative action identity, including remote proxies.
present={}
for k in ['ClientA','ClientB']:
 ss=parsed(Path(next(r for r in primary['processes'] if r['role']==k)['log']),'U02F_STATE ');shown={(p['id'],p['life'],p['action']) for q in ss for p in q['pawns'] if p['montage']};present[k]=shown
 for role in ['local','proxy']:check(k+' montage on '+role,any(p['montage'] and p['local']==(role=='local') for q in ss for p in q['pawns']))
check('Same action montage observed by both clients',bool(present['ClientA']&present['ClientB']))
profiles={}
for k,r in records.items():
 frame=Path(next(v.split('=',1)[1].strip(chr(34)) for v in r['arguments'] if v.startswith('-U01FPerfFile=')));fs=[]
 if frame.exists():
  for l in lines(frame):
   try:q=json.loads(l)
   except ValueError:continue
   if q['pid']==r['pid'] and start<=epoch(q['utc'])<=end and q.get('dt',q.get('frameDt',0))>0:fs.append(q)
 values=[q.get('dt',q.get('frameDt')) for q in fs];profiles[k]=dict(n=len(values),medianDt=statistics.median(values) if values else None,p95Dt=sorted(values)[int((len(values)-1)*.95)] if values else None)
for label,m in [('Network',primary),('Controls',control)]:check(label+' video matches wall duration',abs(m['videoSeconds']-m['captureSeconds'])<=1/30+.005)
result=dict(sourceSHA=source,automation=False,method='independent per-process logs and actual Windows input postprocessing',passed=sum(q['result']=='PASS' for q in checks),failed=sum(q['result']=='FAIL' for q in checks),primaryInputPassed=primary['passed'],controlSamples=len(rows),checks=checks,frameProfiles=profiles,sharedMontageActions=[list(v) for v in sorted(present['ClientA']&present['ClientB'])]);(a.session/'ASSERTIONS-F.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:result[k] for k in ['sourceSHA','passed','failed','controlSamples','frameProfiles']}));print('\n'.join(q['check'] for q in checks if q['result']=='FAIL'));assert result['failed']==0
