"""Validate and seal E package evidence; Automation count remains 21."""
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

root=Path(__file__).resolve().parents[2]
art=root/'Artifacts/U01/E'
play=art/'Play-c8df4ff'
out=root/'Docs/U01/Evidence/E'
source='c8df4ff2182c0006c11f65466ecec4b9223be5a3'
base='e867af97c53bbf11ea141fe5f8f21efc1e31200a'
package=art/'Package-20261104-232646-531-8bba7fa6/Archive/Windows'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
assert git('-C',str(art/'Source'),'rev-parse','HEAD')==source
assert not git('diff',base,source,'--name-only','--','Content/Characters','Content/AnimeMMORPG/U01/Animation','Source/AnimeMMORPG/U01/U01MotorPolicy.h','Source/AnimeMMORPG/U01/U01AnimInstance.cpp')
checks=[]
def check(name,value):
    if not value:raise AssertionError(name)
    checks.append({'check':name,'result':'PASS'})
logs={}
for user,label in [('UserA','Game'),('UserA','Reopen'),('UserB','Failure'),('CorruptUser','Corrupt')]:
    path=play/user/(label+'.log');lines=path.read_text(encoding='utf-8-sig').splitlines()
    samples=[json.loads(l.split('Metrics ',1)[1]) for l in lines if 'Metrics {' in l]
    check('Owned Game-world identity '+user+'/'+label,all(s['sourceSHA']==source and s['worldType']==1 and s['netMode']==0 and s['locallyControlled'] and s['owner']==s['controller'] and s['localPlayers']==1 for s in samples))
    check('One active mapping '+user+'/'+label,all(s['mappingContextCount']==1 for s in samples))
    check('Orderly exit '+user+'/'+label,any('LogExit: Exiting.' in l for l in lines))
    logs[label]=(lines,samples)
case_logs={'CaptureEdges':'Game','Rebind':'Game','MotionLocks':'Game','DefeatedRestore':'Game','Persist':'Reopen','Lifecycle':'Reopen','NetworkReturn':'Reopen','SaveFailure':'Failure','SaveRecovered':'Failure','Corrupt':'Corrupt'}
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
check('No write simply from reload/Resume',digest(play/'UserA/Saved/SaveGames/U01Controls_Player0.sav')==(play/'persist-hash-before.txt').read_text())
check('Other user directory starts with defaults',prefs(logs['Failure'][1][0])=={'version':1,'sensitivity':1,'invertY':False,'rightShoulder':True,'bindings':defaults})
check('Save failure visible and remains dirty',all(s['settingsDirty'] and s['settingsStatus'] and s['controlState']!=0 for s in window('SaveFailure',3.9,4.8)) and any('SettingsSaveFailed' in l for l in logs['Failure'][0]))
check('Save retry recovers without false success',any(not s['settingsDirty'] for s in window('SaveRecovered',1,1.4)) and any_speed('SaveRecovered',2.9,3.3,500))
check('Corrupt binary defaults with feedback, stays clean',all(prefs(s)['bindings']==defaults and s['settingsStatus'] and not s['settingsDirty'] for s in cases['Corrupt']['samples']))
check('Corrupt binary unchanged through load/Resume/Quit',digest(play/'CorruptUser/Saved/SaveGames/U01Controls_Player0.sav')==(play/'corrupt-hash-before.txt').read_text())
reopen=logs['Reopen'][0]
check('Five Boot/lab/Boot cycles',sum('LoadMap: /Game/AnimeMMORPG/Maps/L_Boot' in l for l in reopen)==6 and len(set(s['runID'] for s in logs['Reopen'][1]))==6)
# Runtime input logs only, never startup config/authentication output.
for label,(lines,_) in logs.items():
    chosen=[l for l in lines if 'LogU01Control:' in l and 'Metrics {' not in l]
    (out/(label+'-input.log')).write_text('\n'.join(chosen)+'\n',encoding='utf-8')
smoke=load(art/'SmokeB-20261104-232759/results.json');check('Final package smoke three maps',len(smoke)==3 and all(s['passed'] and s['exitCode']==0 for s in smoke))
(out/'SMOKE.json').write_text(json.dumps(smoke,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'CHECKS.json').write_text(json.dumps({'sourceSHA':source,'method':'Postprocessing actual guarded Win32 input / owned packaged Game-world metrics; these are not additional Automation tests','checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
files=sorted(p for p in package.rglob('*') if p.is_file())
with (out/'PACKAGE.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.writer(f);writer.writerow(['PathUnderWindows','Bytes','SHA256'])
    for p in files:writer.writerow([p.relative_to(package).as_posix(),p.stat().st_size,digest(p)])
manifest={'status':'READY_FOR_REVIEW','branch':'u01/e-settings','baseSHA':base,'sourceSHA':source,'engine':'UE 5.8.4 CL58902052','toolchain':'MSVC14.51.36260 / toolset14.51.36231 / SDK10.0.26100.0',
 'build':'Artifacts/U01/E/Build-20261104-232437-531-46c7d54a','mcpTests':'Artifacts/U01/E/MCPTests-20261104-232558','automationTests':21,'packageRelativePath':package.relative_to(root).as_posix(),'packageFiles':len(files),'smoke':'Artifacts/U01/E/SmokeB-20261104-232759','physicalInputChecks':len(checks),
 'captures':{name:{'pid':case['metadata']['pid'],'uniqueCaptureHz':case['metadata']['uniqueCaptureHz'],'method':case['metadata']['method'],'seconds':case['metadata']['captureActiveSeconds']} for name,case in cases.items()},
 'originalEditor':{'pid':21452,'project':'D:/Data/AnimeMMORPG/AnimeMMORPG.uproject','level':'/Game/AnimeMMORPG/Maps/L_Boot.L_Boot','actors':0,'nativeELoaded':'NOT VERIFIED; kept open, no restart'},
 'ctrlChordRegression':{'beforeSource':'b8bda5842e8fdc66e44112f2a659e517e51f44f8','beforeEvidence':'History/CtrlBefore-b8bda58.mp4','beforeObservedBinding':'LeftControl after Ctrl+T','afterSource':source,'afterEvidence':'CaptureEdges.mp4','afterResult':'Ctrl+T rejected; plain Ctrl commits on release; wheel rejected'},
 'art':'Anime art and combat animation DEFERRED; accepted temporary D blockout carry unchanged','F_G':'NOT RUN; no network/server acceptance claimed',
 'preliminaryHistory':{'source':'1cca45f1f59ec209357e19cd035c7913bac5ea39','builds':'Artifacts/U01/E/Build-* before final build','tests':'Artifacts/U01/E/MCPTests-20261104-225138','package':'Artifacts/U01/E/Package-20261104-225239-671-b3874bf5','captures':'Artifacts/U01/E/Play','note':'Initial movement hit spawn obstacle; corrected to runway fixture. Final captures and tests above supersede preliminary results. Early compiler failures retained in Artifacts.'}}
(out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Sealed',len(checks),'tool checks,',len(files),'package files; Automation remains 21')
