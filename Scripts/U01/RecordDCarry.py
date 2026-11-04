"""Seal carry revision evidence; accepted socket/grip and motor/input stay byte-identical."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import cv2

root=Path(__file__).resolve().parents[2]
art=root/'Artifacts/U01/D/Carry'
out=root/'Docs/U01/Evidence/D-Carry'
out.mkdir(exist_ok=True)
source='6ef6ec3125ed455e3963a687df481eb138629df6'
base='4c8de13a1d2dca986e683bf63c0bca86397a3d22'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
def utc(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
assert git('-C',str(root/'Artifacts/U01/D/Source'),'rev-parse','HEAD')==source
protected=['Content/Characters','Content/AnimeMMORPG/Maps','Content/AnimeMMORPG/U01/Input',
           'Source/AnimeMMORPG/U01/U01Character.cpp','Source/AnimeMMORPG/U01/U01Character.h',
           'Source/AnimeMMORPG/U01/U01MotorPolicy.h','Source/AnimeMMORPG/U01/U01PlayerController.cpp',
           'Source/AnimeMMORPG/U01/U01PlayerController.h','Source/AnimeMMORPG/U01/U01AnimInstance.cpp']
assert not git('diff',base,source,'--name-only','--',*protected)
accepted=load(root/'Docs/U01/Evidence/D-Revision/MANIFEST.json')
accepted_hashes={a['path']:a['SHA256'] for a in accepted['assets']}
unchanged={}
for name in ('SK_U01','PA_U01_RightGrip','SKM_U01','A_U01_Idle','A_U01_Walk','A_U01_Jog','A_U01_Jump','A_U01_Fall','A_U01_Land','BS_U01_Locomotion'):
    path='Content/AnimeMMORPG/U01/Animation/'+name+'.uasset'
    assert digest(root/path)==accepted_hashes[path]
    unchanged[path]=digest(root/path)
tests=art/'MCPTests-20261104-215718'
log=(tests/'Editor.log').read_text(encoding='utf-8-sig').splitlines()
success=[l for l in log if 'Test Completed. Result={Success}' in l]
assert len(success)==17 and any('17 tests performed' in l for l in log)
assert not any('Test Completed. Result={Fail}' in l for l in log)
measurements=[l for l in log if 'U01D_MEASURE ' in l]
assert len(measurements)==10 and all('sourceSHA='+source in l for l in measurements)
assert any('minBodyProxyClearanceCm=21.742434' in l for l in measurements)
captures={}
raw=(art/'Play/Game.log').read_text(encoding='utf-8-sig').splitlines()
for name,folder,duration in [('Transitions','Transitions3',24),('Front','FrontVerified',15)]:
    path=art/'Play'/folder
    meta=load(path/'process.json')
    assert meta['completed'] and meta['distinctImageCount']>200 and not meta['staticCaptureRejected']
    assert meta['uniqueCaptureHz']>15 and meta['externalInputMethodRestored']
    assert any(c['key']=='Ctrl' and c['speed']>650 for c in meta['inputValidation'])
    samples=[]
    for line in raw:
        if 'Metrics {' not in line:continue
        sample=json.loads(line.split('Metrics ',1)[1])
        relative=(utc(sample['utc'])-utc(meta['utc'])).total_seconds()
        if 0<=relative<duration:
            assert sample['pid']==11332 and sample['sourceSHA']==source and sample['worldType']==1 and sample['netMode']==0
            assert sample['locallyControlled'] and sample['owner']==sample['controller']
            samples.append(dict(sample,captureTimeSeconds=relative))
    assert set(s['animationPoseIndex'] for s in samples)=={0,1,2,3,4}
    assert any(abs(s['animationGroundSpeedCmPerSec']-500)<1 for s in samples)
    assert any(abs(s['animationGroundSpeedCmPerSec']-700)<1 for s in samples)
    assert any(s['animationPoseIndex']==2 and s['animationGroundSpeedCmPerSec']>690 for s in samples)
    assert any(s['animationPoseIndex']==3 and s['animationGroundSpeedCmPerSec']>690 for s in samples)
    assert not any(s['animationPoseIndex']==4 and s['animationGroundSpeedCmPerSec']>3 for s in samples)
    if name=='Front':assert any('Y=179.970001' in s['aimYawPitchDegrees'] for s in samples)
    shutil.copyfile(path/'Play-D.mp4',out/(name+'.mp4'))
    events=meta['events'];assert {e.get('key') for e in events if e['action']=='down'}>={'Ctrl','Space','D','S'}
    captures[name]={'metadata':meta,'samples':samples,'videoSHA256':digest(out/(name+'.mp4'))}
    video=cv2.VideoCapture(str(out/(name+'.mp4')))
    for second in ([4.9,5.6,6.5,8.8,12.6] if name=='Front' else [4.0,5.0,6.4,8.9]):
        video.set(cv2.CAP_PROP_POS_MSEC,second*1000);ok,frame=video.read();assert ok
        cv2.imwrite(str(out/(name+'-'+str(second)+'s.png')),frame)
    video.release()
preview=out/'Preview';preview.mkdir(exist_ok=True)
for side,folder in [('Before','Before'),('After','Candidate1')]:
    dest=preview/side;dest.mkdir(exist_ok=True)
    for pattern in ('*-Body*.png','Hand.json','process.json'):
        for path in (art/folder).glob(pattern):shutil.copyfile(path,dest/path.name)
    # Hand-axis closeup cameras can be inside the arm after wrist reorientation;
    # deliberately omit those views, rather than treating occluded images as grip evidence.
package=art/'Package-20261104-215800-485-e6e047e7/Archive/Windows'
files=sorted(p for p in package.rglob('*') if p.is_file());assert len(files)==48
with (out/'PACKAGE.csv').open('w',encoding='utf-8',newline='') as file:
    writer=csv.writer(file);writer.writerow(['PathUnderWindows','Bytes','SHA256'])
    for path in files:writer.writerow([path.relative_to(package).as_posix(),path.stat().st_size,digest(path)])
smoke=load(art/'SmokeB-20261104-220617/results.json');assert len(smoke)==3 and all(s['passed'] and s['exitCode']==0 for s in smoke)
results={'sourceSHA':source,'tests':success,'physicsMeasurements':measurements,'captures':captures}
(out/'RESULTS.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
manifest={'status':'READY_FOR_REVIEW','branch':'u01/d-animation','baseSHA':base,'sourceSHA':source,
          'userAcceptance':'Grip accepted by user after4c8de13; arm/sword trajectory still required correction; D overall NOT accepted',
          'mainUnchanged':'868df83e096748991ccd861da3f98b64c409dcbd',
          'engine':'5.8.4 CL58902052','toolchain':'MSVC14.51.36260/toolset14.51.36231; SDK10.0.26100.0',
          'clone':'Artifacts/U01/D/Source; fast-forward to pushed source, independent disk builds; original Editor kept open',
          'build':'Build-20261104-215608-771-521adf60','testRun':tests.name,'testPID':load(tests/'process.json')['pid'],'testsPassed':17,
          'package':package.relative_to(root).as_posix(),'packageFiles':48,'smokeRun':'SmokeB-20261104-220617','smoke':smoke,
          'carryConfig':load(root/'Scripts/U01/DCarry.json'),
          'carryLayer':'Own PA_U01_RightCarry, clavicle_r branch, mesh-space rotation blend weight1, between locomotion selector and accepted finger grip layer. Deliberately suppresses unarmed arm swing; small shoulder/spine translation remains.',
          'authoring':'Analytic two-link geometry used only to author static pose in editor; no runtime IK, collision response or new animation framework',
          'acceptedAssetsUnchangedSHA256':unchanged,'protectedMotorInputTemplateMapDiff':[],
          'trajectoryFixture':'1270 samples in real Game world at1/120s through idle/walk/sprint/ascent/fall/moving and stationary land and four direction changes; blade segment radius3.25cm against moving bone capsules torso/head/thighs. Proxy clearance, not triangle-perfect mesh intersection or network proof.',
          'newAssetSHA256':digest(root/'Content/AnimeMMORPG/U01/Animation/PA_U01_RightCarry.uasset'),
          'animBPSHA256':digest(root/'Content/AnimeMMORPG/U01/Animation/ABP_U01.uasset'),
          'captureStatistics':{n:{k:v['metadata'].get(k) for k in ['pid','uniqueCaptureHz','distinctImageHz','distinctImageCount','uniqueFrameGapP95Seconds','uniqueFrameGapMaxSeconds','frames','duplicatedFrames','externalInputMethodRestored']} for n,v in captures.items()},
          'originalEditor':{'pid':21452,'project':'D:/Data/AnimeMMORPG/AnimeMMORPG.uproject','world':'/Game/AnimeMMORPG/Maps/L_Boot.L_Boot','actors':0,'confirmedUtc':'2026-11-04T15:06:26.814Z','nativeDLoaded':'NOT VERIFIED; AI did not close/restart original'},
          'history':['Transitions/Transitions2 refused foreground before input. Transitions3 recorded with strict focus guard after startup queue coordination.',
                     'Front first attempt moved camera only12.6deg and was excluded as frontal evidence; FrontVerified uses observed mapping .07deg/pixel to reach179.97deg, confirmed in runtime log.',
                     'Candidate1 hand-axis closeups became occluded by forearm; excluded. Whole-body previews and final game videos used; accepted grip/socket hashes unchanged.',
                     'Old unarmed hand-cycle expectations removed from TransitionsAndAttachment because carry intentionally suppresses right arm swing; foot-cycle assertions and all movement/root tests retained.'],
          'pending':['Review right-arm/sword trajectory through transitions and direction changes in final package','No D acceptance/merge or E work yet'],'artAnime':'DEFERRED'}
(out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with (out/'EVIDENCE.csv').open('w',encoding='utf-8',newline='') as file:
    writer=csv.writer(file);writer.writerow(['RelativeEvidence','Bytes','SHA256'])
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.name!='EVIDENCE.csv':writer.writerow([path.relative_to(out).as_posix(),path.stat().st_size,digest(path)])
print(json.dumps({'tests':len(success),'sourceSHA':source,'captureHz':{n:v['metadata']['uniqueCaptureHz'] for n,v in captures.items()},'gripAssetsUnchanged':True}))
