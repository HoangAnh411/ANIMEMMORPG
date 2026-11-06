import argparse,json,re,cv2
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);a=p.parse_args();cap=a.session/'Capture';m=json.loads((cap/'input.json').read_text());assert m['completed'] and m['externalInputMethodRestored'];start=datetime.fromisoformat(m['utc']);raw=(a.session/'Game.log').read_bytes();lines=raw[:raw.rfind(b'\n')+1].decode('utf-8-sig',errors='replace').splitlines();checks=list(m['checks']);samples=[];hits=[]
for l in lines:
 if 'Metrics {' in l:
  v=json.loads(l.split('Metrics ',1)[1]);t=(datetime.fromisoformat(v['utc'].replace('Z','+00:00'))-start).total_seconds()
  if 0<=t<=m['captureSeconds']:samples.append(v)
 if 'U02E_DAMAGE ' in l:
  x=re.search(r'timestamp=([^ ]+) source=([0-9A-F]+):(\d+) action=(\d+) target=([0-9A-F]+):(\d+) hurtbox=(\d+) raw=60 attack=([^ ]+) roll=([^ ]+) crit=(\d+) damage=(\d+) absorbed=(\d+) hpBefore=(\d+) hpAfter=(\d+) death=(\d+)',l)
  assert x,l
  hits.append(dict(timestamp=float(x[1]),source=x[2],life=int(x[3]),action=int(x[4]),target=x[5],targetLife=int(x[6]),hurtbox=int(x[7]),crit=bool(int(x[10])),damage=int(x[11]),absorbed=int(x[12]),hpBefore=int(x[13]),hpAfter=int(x[14]),death=bool(int(x[15])),line=l))
def check(name,v):checks.append(dict(check=name,result='PASS' if v else 'FAIL'))
check('Native source / actual owned Game standalone',bool(samples) and all(v['sourceSHA']==m['process']['sourceSHA'] and v['pid']==m['process']['pid'] and v['worldType']==1 and v['netMode']==0 and v['owner']==v['controller'] and v['localPlayers']==1 for v in samples))
ids=[(v['source'],v['life'],v['action'],v['target'],v['targetLife']) for v in hits];check('One damage per action/target life despite multi-hurtboxes',len(ids)==len(set(ids)))
check('Exactly one crit in controlled fixture',sum(v['crit'] for v in hits)==1 and any(v['damage']==90 for v in hits))
check('Death emitted exactly once per target life',len([(v['target'],v['targetLife']) for v in hits if v['death']])==len(set((v['target'],v['targetLife']) for v in hits if v['death'])) and sum(v['death'] for v in hits)==1)
check('Fixture crit setting explicitly diagnosed',any('mode=CRIT_OFF' in l for l in lines) and any('mode=CRIT_FORCED' in l for l in lines))
for stage in m['stages']:
 b=stage['after']['combat'];group=[h for h in hits if h['source']==b['pawnId'] and h['life']==b['life'] and h['action']==b['action']]
 check(stage['label']+' native result count',len(group)==stage['hits'])
 check(stage['label']+' damage timestamp in active',all(b['activeStart']<=h['timestamp']<b['activeEnd'] for h in group))
check('HP never negative',all(h['hpAfter']>=0 for h in hits))
check('No duplicate crit roll',m['finalMetrics']['combat']['critRolls']==len(hits))
check('Player remains HP1000',all(v['combat']['vital']['hp']==1000 for v in samples))
v=cv2.VideoCapture(str(cap/'Input-E.mp4'));duration=v.get(cv2.CAP_PROP_FRAME_COUNT)/v.get(cv2.CAP_PROP_FPS);v.release();check('Real-time duration from frame timestamps',abs(duration-m['captureSeconds'])<1/30+.01)
result=dict(sourceSHA=m['process']['sourceSHA'],automation=False,passed=sum(x['result']=='PASS' for x in checks),failed=sum(x['result']=='FAIL' for x in checks),checks=checks,damageEvents=len(hits),samples=len(samples),videoSeconds=duration,wallSeconds=m['captureSeconds'],capturedFrames=len(m['frames']),hits=hits)
(cap/'ASSERTIONS.json').write_text(json.dumps(result,indent=2));(cap/'DAMAGE-TRACE.log').write_text('\n'.join(h['line'] for h in hits));print(json.dumps(dict(passed=result['passed'],failed=result['failed'],damageEvents=len(hits),samples=len(samples))));assert result['failed']==0
