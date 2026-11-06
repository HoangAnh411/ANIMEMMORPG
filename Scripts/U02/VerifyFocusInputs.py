import argparse,json,math,re
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--label',required=True);a=p.parse_args();d=a.session/a.label;m=json.loads((d/'input.json').read_text());records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));checks=[]
def check(n,v):checks.append(dict(check=n,result='PASS' if v else 'FAIL'))
def epoch(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
metrics={};frames={}
for r in records:
 raw=Path(r['log']).read_bytes();ls=raw[:raw.rfind(b'\n')+1].decode('utf-8-sig',errors='replace').splitlines();metrics[r['role']]=[json.loads(l.split('Metrics ',1)[1]) for l in ls if 'Metrics {' in l];fp=Path(next(s.split('=',1)[1].strip(chr(34)) for s in r['arguments'] if s.startswith('-U01FPerfFile=')));frames[r['role']]=[json.loads(l) for l in fp.read_text().splitlines()]
check('Ten completed transfers with15s followup',m['completed'] and len(m['trials'])>=10 and all(epoch(t['endUTC'])-epoch(t['focusUTC'])>=15 for t in m['trials']))
for t in m['trials']:
 idx=t['index'];foc=epoch(t['focusUTC']);resume=epoch(t['resumeUTC']);key=epoch(t['keyUTC']);end=epoch(t['endUTC']);rows=[s for s in metrics[t['to']] if foc<=epoch(s['utc'])<=end];check(str(idx)+' Resume no attack',rows and all(s['combat']['accepted']==t['beforeTarget']['combat']['accepted'] for s in rows));check(str(idx)+' Playing after actual Resume',t['afterTarget']['controlState']==0);check(str(idx)+' Key injected promptly after click',.04<=key-resume<.15)
 ev=[e for e in m['events'] if e.get('index')==idx];up=epoch(next(e['utc'] for e in ev if e['action']=='target-key-up'));second=epoch(next(e['utc'] for e in ev if e['action']=='target-second-down'));up2=epoch(next(e['utc'] for e in ev if e['action']=='post-window'));check(str(idx)+' First W moves',any(s['animationGroundSpeedCmPerSec']>400 for s in rows if key+.1<=epoch(s['utc'])<up));check(str(idx)+' Release then second S edge moves',any(s['animationGroundSpeedCmPerSec']>400 for s in rows if second+.1<=epoch(s['utc'])<second+1.2));check(str(idx)+' Release stops',t['afterTarget']['animationGroundSpeedCmPerSec']<.1);check(str(idx)+' No artificial packet loss',all(s.get('pktLoss',0)==0 and s.get('incomingLoss',0)==0 for ff in frames.values() for s in ff if foc<=epoch(s['utc'])<=end))
res=dict(passed=sum(c['result']=='PASS' for c in checks),failed=sum(c['result']=='FAIL' for c in checks),checks=checks);(d/'INPUT-ASSERTIONS.json').write_text(json.dumps(res,indent=2));print(json.dumps({k:res[k] for k in ['passed','failed']}));print('\n'.join(c['check'] for c in checks if c['result']=='FAIL'));assert not res['failed']
