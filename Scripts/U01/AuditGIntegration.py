import json,shutil,hashlib
from pathlib import Path
from datetime import datetime
root=Path.cwd();play=root/'Artifacts/U01/G/Play';out=root/'Artifacts/U01/G/ClosureAudit';out.mkdir(exist_ok=True);source='5f8a6eabe103a8b31a894c82f32cffb0325474a9'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def utc(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,value):
    pass
    checks.append({'check':name,'result':'PASS' if value else 'REVIEW'})
logs={}
for user,label in [('UserA','Game'),('UserA','Reopen'),('FailureUser','Failure'),('CorruptUser','Corrupt')]:
    path=play/user/(label+'.log');lines=path.read_text(encoding='utf-8-sig').splitlines()
    samples=[json.loads(l.split('Metrics ',1)[1]) for l in lines if 'Metrics {' in l]
    check('Owned Game-world identity '+user+'/'+label,all(s['sourceSHA']==source and s['worldType']==1 and s['netMode']==0 and s['locallyControlled'] and s['owner']==s['controller'] and s['localPlayers']==1 for s in samples))
    check('One active mapping '+user+'/'+label,all(s['mappingContextCount']==1 for s in samples))
    check('Orderly exit '+user+'/'+label,any('LogExit: Exiting.' in l for l in lines))
    logs[label]=(lines,samples)
case_logs={'CaptureEdges':'Game','Rebind':'Game','MotionLocks':'Game','DefeatedRestore':'Game','Persist':'Reopen','LifecycleRetry':'Reopen','NetworkReturn':'Reopen','SaveFailure':'Failure','SaveRecovered':'Failure','Corrupt':'Corrupt'}
cases={}
for case,label in case_logs.items():
    directory=play/case;m=load(directory/'process.json');start=utc(m['utc'])
    check('Completed real input capture '+case,m['completed'] and m['externalInputMethodRestored'] and not m['staticCaptureRejected'])
    samples=[]
    for sample in logs[label][1]:
        t=(utc(sample['utc'])-start).total_seconds()
        if 0<=t<m['captureActiveSeconds']:
            assert sample['pid']==m['pid'];samples.append(dict(sample,captureTime=t))
    assert samples
    cases[case]={'metadata':m,'samples':samples}
    shutil.copyfile(directory/'Play-E.mp4',out/(case+'.mp4'))
    for path in directory.glob('*.png'):
        if not path.name.startswith('frame-') and path.name!='initial.png':shutil.copyfile(path,out/(case+'-'+path.name))
    (out/(case+'.json')).write_text(json.dumps(cases[case],ensure_ascii=False,indent=2),encoding='utf-8')
def window(case,a,b):
    samples=[s for s in cases[case]['samples'] if a<=s['captureTime']<b]
    assert samples,(case,a,b)
    return samples
def any_speed(case,a,b,speed):return any(abs(s['animationGroundSpeedCmPerSec']-speed)<1 for s in window(case,a,b))
def still(case,a,b):return all(s['animationGroundSpeedCmPerSec']<.1 and abs(s['animationVerticalSpeedCmPerSec'])<.1 for s in window(case,a,b))
def prefs(s):return json.loads(s['settings'])
R='Rebind';M='MotionLocks';D='DefeatedRestore'
check('Actual Ctrl chord leaves binding unchanged',all(prefs(s)['bindings']['Interact']=='N' and s['pendingRebind']==7 for s in window('CaptureEdges',1.35,1.7)))
check('Ctrl alone waits until key release',all(prefs(s)['bindings']['Interact']=='N' and s['pendingRebind']==7 for s in window('CaptureEdges',2.45,2.85)))
check('Plain Ctrl is bindable on release',all(prefs(s)['bindings']['Interact']=='LeftControl' and s['pendingRebind']==-1 for s in window('CaptureEdges',3.05,3.45)))
check('Actual wheel rejected without rebinding',all(prefs(s)['bindings']['Interact']=='N' and s['pendingRebind']==7 for s in window('CaptureEdges',4.8,5.15)))
check('Duplicate rejected without changing binding',all(prefs(s)['bindings']['Forward']=='W' and s['pendingRebind']==0 for s in window(R,.8,1.2)))
check('Reserved rejected without changing binding',all(prefs(s)['bindings']['Forward']=='W' and s['pendingRebind']==0 for s in window(R,1.5,1.9)))
check('Escape cancels capture',all(s['pendingRebind']==-1 and prefs(s)['bindings']['Forward']=='W' for s in window(R,2.2,2.6)))
expected=dict(zip(('Forward','Backward','Left','Right','Jump','Sprint','Shoulder','Interact'),('H','J','L','U','MiddleMouseButton','ThumbMouseButton','B','N')))
check('All eight bindings applied',all(prefs(s)['bindings']==expected for s in window(R,9.4,9.9)))
check('Slider applies while dragging',any(s['settingsDirty'] and 1<prefs(s)['sensitivity']<1.98 for s in window(R,10,10.6)))
check('Slider release saves',any(not s['settingsDirty'] and prefs(s)['sensitivity']>1.9 for s in window(R,10.7,11)))
check('Invert and default shoulder applied',all(prefs(s)['invertY'] and not prefs(s)['rightShoulder'] and s['shoulderOffsetCm']<-44 for s in window(R,12,13)))
check('Rebound move and sprint 500/700',any_speed(M,1.8,2.3,500) and any_speed(M,2.6,4,700))
check('Rebound mouse jump while sprinting',any(s['animationVerticalSpeedCmPerSec']>100 and s['animationGroundSpeedCmPerSec']>699 for s in window(M,2.8,3.5)))
check('Old W and Space inactive',still(M,5.1,5.8) and still(M,6,6.5))
check('Old Ctrl does not sprint',all(abs(s['animationGroundSpeedCmPerSec']-500)<1 for s in window(M,6.9,7.5)))
check('Each rebound direction moves',all(any_speed(M,a,b,500) for a,b in [(8.3,8.6),(9.3,9.6),(10.3,10.6)]))
check('Interacting blocks motor but retains gravity',all(s['motorLockMask']==2 and s['animationGroundSpeedCmPerSec']<.1 for s in window(M,11.8,13)) and any(s['animationVerticalSpeedCmPerSec']<-100 for s in window(M,11.8,13)))
check('Camera and shoulder continue under Interacting',len(set(s['aimYawPitchDegrees'] for s in window(M,11.8,13)))>1 and min(s['shoulderOffsetCm'] for s in window(M,12.2,13))<-40 and max(s['shoulderOffsetCm'] for s in window(M,12.2,13))>40)
check('Unlock still requires release',still(M,13.2,14) and any_speed(M,14.6,15,500))
check('Menu held movement/jump/sprint stay disarmed',still(M,16.3,17) and all(s['jumpCount']==0 and not s['bufferedJump'] for s in window(M,16.3,17)) and any_speed(M,18.1,18.5,700))
check('World gravity continues in menu',any(s['controlState']==1 and s['animationVerticalSpeedCmPerSec']<-100 for s in window(M,18.5,19.3)))
check('Actual Alt-Tab waits for Resume',cases[M]['metadata']['focusChecks'][0]['controlState']==2 and all(s['controlState']==2 for s in window(M,23.9,24.2)))
check('Held input after focus remains disarmed',still(M,24.8,25.5) and any_speed(M,26.3,27,500))
check('Defeated retains gravity and blocks motor',any(s['motorLockMask']==4 and s['animationVerticalSpeedCmPerSec']<-100 for s in window(D,2,2.5)) and still(D,2.7,3.5))
check('Defeated camera/menu still usable',len(set(s['aimYawPitchDegrees'] for s in window(D,2.7,3.5)))>1 and any(s['controlState']==1 and s['motorLockMask']&4 for s in window(D,4.1,4.5)))
check('Defeated unlock waits for release',still(D,5.1,5.6) and any_speed(D,6.3,6.8,500))
defaults=dict(zip(('Forward','Backward','Left','Right','Jump','Sprint','Shoulder','Interact'),('W','S','A','D','SpaceBar','LeftControl','V','G')))
check('Restore defaults applies immediately',all(prefs(s)['bindings']==defaults and prefs(s)['sensitivity']==1 and not prefs(s)['invertY'] and prefs(s)['rightShoulder'] for s in window(D,8.8,9.4)))
last=prefs(window(D,12.7,13.5)[-1]);first=prefs(logs['Reopen'][1][0])
check('Quit/reopen preserves binding and camera preferences',last==first and first['bindings']['Forward']=='H' and 1.5<first['sensitivity']<1.7 and first['invertY'] and not first['rightShoulder'])
# Reload persistence checked by observed preferences, later fixture intentionally restores defaults.
check('Other user directory starts with defaults',prefs(logs['Failure'][1][0])=={'version':1,'sensitivity':1,'invertY':False,'rightShoulder':True,'bindings':defaults})
check('Save failure visible and remains dirty',all(s['settingsDirty'] and s['settingsStatus'] and s['controlState']!=0 for s in window('SaveFailure',3.9,4.8)) and any('SettingsSaveFailed' in l for l in logs['Failure'][0]))
check('Save retry recovers without false success',any(not s['settingsDirty'] for s in window('SaveRecovered',1,1.4)) and any_speed('SaveRecovered',2.9,3.3,500))
check('Corrupt binary defaults with feedback, stays clean',all(prefs(s)['bindings']==defaults and s['settingsStatus'] and not s['settingsDirty'] for s in cases['Corrupt']['samples']))
check('Corrupt binary unchanged through load/Resume/Quit',digest(play/'CorruptUser/Saved/SaveGames/U01Controls_Player0.sav')==(play/'corrupt-hash-before.txt').read_text())
reopen=logs['Reopen'][0]
check('Five Boot/lab/Boot cycles',sum('LoadMap: /Game/AnimeMMORPG/Maps/L_Boot' in l for l in reopen)==6 and len(set(s['runID'] for s in logs['Reopen'][1]))==6)

(out/'TIMED-CHECKS.json').write_text(json.dumps(checks,indent=2));print(json.dumps([c for c in checks if c['result']!='PASS'],indent=2));print('Total',len(checks),'PASS',sum(c['result']=='PASS' for c in checks))
