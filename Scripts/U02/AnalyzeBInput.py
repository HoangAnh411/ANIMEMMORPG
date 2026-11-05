"""Postprocess real native samples against the recorded input timeline; no synthetic input PASS."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);a=p.parse_args()
    meta=json.loads((a.capture/'input.json').read_text(encoding='utf-8-sig'))
    record=meta['process'];start=datetime.fromisoformat(meta['utc'])
    raw=Path(record['log']).read_bytes();lines=raw[:raw.rfind(b'\n')+1].decode('utf-8-sig',errors='replace').splitlines()
    def relative(v):return (datetime.fromisoformat(v['utc'].replace('Z','+00:00'))-start).total_seconds()
    samples=[json.loads(l.split('Metrics ',1)[1]) for l in lines if 'Metrics {' in l]
    samples=[dict(s,t=relative(s)) for s in samples if 0<=relative(s)<=meta['captureSeconds']]
    events=[json.loads(l.split('U02B_EVENT ',1)[1]) for l in lines if 'U02B_EVENT {' in l]
    events=[dict(e,t=relative(e)) for e in events if 0<=relative(e)<=meta['captureSeconds']]
    checks=[]
    def check(name,value):
        checks.append(dict(check=name,result='PASS' if value else 'FAIL'))
    def window(lo,hi):
        values=[s for s in samples if lo<=s['t']<hi]
        assert values,(lo,hi)
        return values
    def speed(s):return s.get('animationGroundSpeedCmPerSec',0)
    def yaw(s):return float(re.search(r'Y=([-\d.]+)',s['aimYawPitchDegrees'])[1])
    check('Completed guarded real-input capture and restored IME',meta['completed'] and meta['externalInputMethodRestored'])
    check('Native Game world/standalone/owner/source identity',bool(samples) and all(s['pid']==record['pid'] and s['sourceSHA']==record['sourceSHA'] and s['worldType']==1 and s['netMode']==0 and s['owner']==s['controller'] and s['locallyControlled'] and s['localPlayers']==1 for s in samples))
    accepted=[e for e in events if e['event']=='Accepted'];rejected=[e for e in events if e['event']=='Rejected']
    check('Seven intended edges accepted; no Resume/menu/focus phantom attack',len(accepted)==7)
    check('Holding LMB does not repeat',len([e for e in accepted if 1.6<e['t']<2.9])==1)
    check('Busy, Interacting and airborne rejection reasons present',all(any(e['lastReject']==reason for e in rejected) for reason in (8,6,5)))
    locked=[s for s in samples if s['combat']['locked']]
    check('Combat authority bit present throughout locked samples',bool(locked) and all(s['motorLockMask']&8 for s in locked))
    check('Locked samples stop XY and sprint',bool(locked) and all(speed(s)<.1 and not s['sprinting'] for s in locked))
    check('Sprint was running before attack',any(speed(s)>699 for s in window(1.3,1.65)))
    check('Held WASD/Ctrl resumes after recovery without physical release',any(speed(s)>699 for s in window(2.3,2.7)))
    check('Busy jump never buffered/took off',all(s['jumpCount']==0 and not s['bufferedJump'] for s in window(1.8,2.6)))
    phase_samples=[s for s in window(1.7,2.2) if s['combat']['phase'] in (2,3)]
    check('Active/recovery yaw fixed while camera turns',len(phase_samples)>2 and max(s['bodyYawDegrees'] for s in phase_samples)-min(s['bodyYawDegrees'] for s in phase_samples)<.05 and max(yaw(s) for s in phase_samples)-min(yaw(s) for s in phase_samples)>5)
    menu=window(4.4,5.1)
    check('Menu during action keeps world/action clock progressing to finish',all(s['controlState']==1 for s in menu) and any(s['combat']['phase']==3 for s in menu) and any(s['combat']['phase']==4 for s in menu))
    check('Resume click did not attack',all(s['controlState']==0 and s['combat']['accepted']==3 for s in window(5.5,6.0)))
    check('Focus away enters AwaitingResume; accepted action finishes',any(s['controlState']==2 and not s['windowActive'] for s in window(7.2,7.9)) and any(s['controlState']==2 and s['combat']['phase']==4 for s in window(7.6,7.9)))
    check('Focus return alone remains AwaitingResume',any(s['controlState']==2 and s['windowActive'] for s in window(8.05,8.28)))
    # Assert observed movement, not an internal gate bit: Win32 injected-key state
    # can be reset by focus/input-mode transitions. Gate policy is covered separately
    # by U01/A/B tests; this capture cannot prove a physical key stayed down in hardware.
    check('Menu/Resume does not replay queued movement after combat finish',all(speed(s)<.1 for s in window(5.5,5.9)))
    check('Focus Resume does not auto-move; a fresh W edge works',all(speed(s)<.1 for s in window(8.6,8.95)) and any(speed(s)>490 for s in window(9.45,9.65)))
    check('Interacting rejected attack without action',any(s['motorLockMask']&2 and s['combat']['accepted']==5 for s in window(10.3,10.65)))
    check('Gravity remains under menu lock',any(s['controlState']==1 and s['animationVerticalSpeedCmPerSec']<-50 for s in window(11.9,12.25)))
    for action in accepted:
        seq=action['action'];first=action['start']
        for name,offset in [('Active',.16),('Recovery',.22),('Finished',.4)]:
            matching=[e for e in events if e['event']==name and e['action']==seq]
            check(f'Action {seq} exact {name} gameplay timestamp',len(matching)==1 and abs(matching[0]['gameplaySeconds']-(first+offset))<1e-8)
    result=dict(sourceSHA=record['sourceSHA'],pid=record['pid'],automation=False,method='postprocessed real Windows input/native runtime samples',samples=len(samples),accepted=len(accepted),rejected=len(rejected),checks=checks,passed=sum(c['result']=='PASS' for c in checks),failed=sum(c['result']=='FAIL' for c in checks),events=events,sampleWindow=[samples[0]['t'],samples[-1]['t']])
    (a.capture/'ASSERTIONS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','events')}))
    for c in checks:
        if c['result']=='FAIL':print('FAIL:',c['check'])
    assert result['failed']==0

if __name__=='__main__':main()
