"""Check real body measurements and recorded wall-time video, independently of model tests."""
import argparse,csv,json,math,re,cv2
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--before',action='store_true');a=p.parse_args()
m=json.loads((a.session/'Capture/input.json').read_text(encoding='utf-8-sig'));start=datetime.fromisoformat(m['utc'])
def rel(v):return (datetime.fromisoformat(v['utc'].replace('Z','+00:00'))-start).total_seconds()
lines=(a.session/'Game.log').read_text(encoding='utf-8-sig',errors='replace').splitlines()
ss=[];events=[]
for line in lines:
    try:
        if 'Metrics {' in line:
            v=json.loads(line.split('Metrics ',1)[1]);t=rel(v)
            if 0<=t<=m['captureSeconds']:ss.append(dict(v,t=t))
        if 'U02B_EVENT {' in line:
            v=json.loads(line.split('U02B_EVENT ',1)[1]);t=rel(v)
            if 0<=t<=m['captureSeconds']:events.append(dict(v,t=t))
    except (ValueError,KeyError):continue
def delta(x,y):
    d=(y-x+180)%360-180
    return 180 if d==-180 else d
checks=[]
def check(n,v):checks.append(dict(check=n,result='PASS' if v else 'FAIL'))
accepted=[v for v in events if v['event']=='Accepted'];locked=[v for v in ss if v['combat']['locked']]
check('Guarded input completed and IME restored',m['completed'] and m['externalInputMethodRestored'])
check('Actual owned source/world identity',bool(ss) and all(v['sourceSHA']==m['process']['sourceSHA'] and v['pid']==m['process']['pid'] and v['worldType']==1 and v['netMode']==0 and v['owner']==v['controller'] for v in ss))
check('Seven intended attacks, no Resume phantom',len(accepted)==7 and m['finalMetrics']['combat']['accepted']==7)
video=cv2.VideoCapture(str(a.session/'Capture/Input-C.mp4'));duration=video.get(cv2.CAP_PROP_FRAME_COUNT)/video.get(cv2.CAP_PROP_FPS);video.release()
check('Video duration matches wall time within one output frame',abs(duration-m['captureSeconds'])<1/30+.005)
check('Root motion still ignored',all(v['rootMotionMode']==1 for v in ss))
check('Motor lock retains stop during all attack phases',bool(locked) and all(v['motorLockMask']&8 and v['animationGroundSpeedCmPerSec']<.1 for v in locked))
check('All attacks return from montage',all(any(v['combat']['action']==seq and v['combat']['phase']==4 and not v['attackPresented'] for v in ss) for seq in range(1,8)))
check('AwaitingResume after real AltTab',any(v['controlState']==2 and not v['windowActive'] for v in ss))
check('Menu does not cancel accepted action',any(v['controlState']==1 and v['combat']['phase'] in (1,2,3) for v in ss))
check('Held W continues after recovery',any(6.<v['t']<6.2 and v['animationGroundSpeedCmPerSec']>0 for v in ss))
if not a.before:
    first=accepted[0];start_yaw=first['gameplayBodyYaw'];target=first['aimYaw']
    check('Back-facing setup exceeds 170 degrees',abs(delta(start_yaw,target))>170)
    check('Attack acceptance does not snap actual body',abs(delta(start_yaw,target))>170 and abs(delta(start_yaw,first['turnFromYaw']))<.01)
    startup=[v for v in ss if v['combat']['action']==1 and v['combat']['phase']==1]
    check('Measured startup includes intermediate actual body yaw',any(5<abs(delta(start_yaw,v['bodyYawDegrees']))<170 for v in startup))
    errors=[]
    for v in ss:
        b=v['combat']
        if not b['locked']:continue
        elapsed=v['worldSeconds'];deadline=b['activeStart'];seg=b['turnStart']
        alpha=max(0,min(1,(elapsed-seg)/(deadline-seg))) if deadline>seg else 1
        expected=b['turnFromYaw']+delta(b['turnFromYaw'],b['aimYaw'])*alpha*alpha*(3-2*alpha)
        errors.append(abs(delta(expected,v['bodyYawDegrees'])))
    check('Measured actual body follows timestamp trajectory',bool(errors) and max(errors)<.05)
    check('Active and recovery actual body equals locked gameplay aim',all(abs(delta(v['bodyYawDegrees'],v['combat']['aimYaw']))<.01 for v in locked if v['combat']['phase'] in (2,3)))
    check('Body and mesh diagnostics are real transform measurements',all(abs(delta(v['bodyYawDegrees'],v['combat']['gameplayBodyYaw']))<.001 and math.isfinite(v['combat']['meshWorldYaw']) for v in ss))
    for seq in (1,2):
        active=[v for v in ss if v['combat']['action']==seq and v['combat']['phase']==2]
        check('Fixed aim action '+str(seq)+' reaches yaw at active',bool(active) and all(abs(delta(v['bodyYawDegrees'],v['combat']['aimYaw']))<.01 for v in active))
    report=dict(maxMeasuredTrajectoryErrorDegrees=max(errors),startBodyYaw=start_yaw,firstAimYaw=target)
else:report=dict(note='Historical before package; new trajectory assertions do not apply')
result=dict(sourceSHA=m['process']['sourceSHA'],passed=sum(v['result']=='PASS' for v in checks),failed=sum(v['result']=='FAIL' for v in checks),checks=checks,videoSeconds=duration,wallSeconds=m['captureSeconds'],samples=len(ss),report=report)
(a.session/'Capture/TURN-ASSERTIONS.json').write_text(json.dumps(result,indent=2))
with (a.session/'Capture/YAW-TRACE.csv').open('w',newline='') as f:
    out=csv.writer(f);out.writerow(['utc','wallRelativeSeconds','worldSeconds','action','phase','actualBodyYaw','actualMeshWorldYaw','aimYaw','actionSeconds','turnFromYaw','segmentStart'])
    for v in ss:
        b=v['combat'];out.writerow([v['utc'],v['t'],v['worldSeconds'],b['action'],b['phase'],v['bodyYawDegrees'],b.get('meshWorldYaw'),b['yaw'],v['worldSeconds']-b['start'],b.get('turnFromYaw'),b.get('turnStart')])
print(json.dumps(result,indent=2));assert result['failed']==0
