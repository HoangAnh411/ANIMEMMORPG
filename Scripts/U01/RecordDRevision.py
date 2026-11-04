"""Seal D1/D2/D3 evidence from the accepted source snapshot, with runtime-input checks."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import cv2
import numpy as np

root=Path(__file__).resolve().parents[2]
art=root/'Artifacts/U01/D/Revision'
out=root/'Docs/U01/Evidence/D-Revision'
out.mkdir(exist_ok=True)
source='819fbd041b8bc1f8463d6a075a4c6c29215b1f9c'
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def utc(text):return datetime.fromisoformat(text.replace('Z','+00:00'))
def git(*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
assert git('-C',str(root/'Artifacts/U01/D/Source'),'rev-parse','HEAD')==source
tests=art/'MCPTests-20261104-183218'
lines=(tests/'Editor.log').read_text(encoding='utf-8-sig').splitlines()
success=[x for x in lines if 'Test Completed. Result={Success}' in x]
assert len(success)==16 and any('16 tests performed' in x for x in lines)
assert not any('Test Completed. Result={Fail}' in x for x in lines)
measurements=[x for x in lines if 'U01D_MEASURE ' in x]
assert len(measurements)==9 and all('sourceSHA='+source in x for x in measurements)
datasets={}
capture_paths={'Before':('BeforeScreenVerified/CaptureAdaptive','BeforeScreenVerified/Game.log','715238443e33e1a2760ea3d89f4d1698f092e511'),
               'After':('AfterScreenVerified/Compare','AfterScreenVerified/Game.log',source),
               'Coverage':('AfterScreenVerified/Coverage','AfterScreenVerified/Game.log',source)}
for name,(folder,log,expected) in capture_paths.items():
    meta=load(art/folder/'process.json')
    assert meta['completed'] and meta['uniqueCaptureHz']>15 and meta['externalInputMethodRestored']
    assert meta['distinctImageCount']>50 and not meta['staticCaptureRejected']
    assert meta['inputValidation']
    if name!='Coverage':assert {x['key'] for x in meta['inputValidation']}=={'W','Ctrl'}
    start=utc(meta['utc'])
    samples=[]
    for line in (art/log).read_text(encoding='utf-8-sig').splitlines():
        if 'Metrics {' not in line:continue
        s=json.loads(line.split('Metrics ',1)[1]);relative=(utc(s['utc'])-start).total_seconds()
        if 0<=relative< (25 if name=='Coverage' else 11):
            assert s['pid']==meta['pid'] and s['sourceSHA']==expected and s['worldType']==1 and s['netMode']==0
            assert s['locallyControlled'] and s['owner']==s['controller']
            samples.append(dict(s,captureTimeSeconds=relative))
    assert samples
    destination=out/(name+'.mp4');shutil.copyfile(art/folder/'Play-D.mp4',destination)
    datasets[name]={'meta':meta,'videoSHA256':sha(destination),'sourceSHA':expected,'samples':samples}
before=datasets['Before']['samples'];after=datasets['After']['samples'];coverage=datasets['Coverage']['samples']
bad=[s for s in before if s['animationPoseIndex']==4 and s['animationGroundSpeedCmPerSec']>3]
assert any(abs(s['animationGroundSpeedCmPerSec']-500)<1 for s in bad)
assert any(abs(s['animationGroundSpeedCmPerSec']-700)<1 for s in bad)
assert not any(s['animationPoseIndex']==4 and s['animationGroundSpeedCmPerSec']>3 for s in after+coverage)
assert any(s['animationGroundSpeedCmPerSec']>490 for s in after)
assert any(s['animationGroundSpeedCmPerSec']>690 for s in after)
ledge=[s for s in coverage if 17<s['captureTimeSeconds']<20]
assert any(s['animationPoseIndex']==3 and s['animationVerticalSpeedCmPerSec']<0 for s in ledge)
assert any(s['animationPoseIndex']==1 and s['movementMode']==1 for s in ledge)
assert not any(s['animationPoseIndex']==2 for s in ledge)
assert any(s['animationPoseIndex']==4 and s['animationGroundSpeedCmPerSec']<=3 for s in coverage)
datasets['comparison']={'oldMovingLandingSamples':bad,'newMovingLandingSamples':[],
                       'runtimeVerifiedMovement':True,'ledgeFallThenLocomotion':True,
                       'deadlineProof':'LandingTransitions Automation checks compiled blend times, partial weights before deadline and full target after .100s + sampling tolerance; video is for review of feel',
                       'bufferVideoLimit':'Timed real-input repeated jumps are recorded; exact coyote/buffer edges and event priority are established by Game-world Automation, not 5Hz trace sampling'}
results={'sourceSHA':source,'tests':success,'measurements':measurements,'captures':datasets}
(out/'RESULTS.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for side,folder in [('Before','HandBeforeVerified'),('After','HandCandidateVerified')]:
    dest=out/'Hands'/side;dest.mkdir(parents=True,exist_ok=True)
    for path in (art/folder).glob('*.png'):shutil.copyfile(path,dest/path.name)
    shutil.copyfile(art/folder/'Hand.json',dest/'Hand.json')
    shutil.copyfile(art/folder/'process.json',dest/'process.json')
for name in ('Before','After'):
    video=cv2.VideoCapture(str(out/(name+'.mp4')))
    for second in (3.6,7.65):
        video.set(cv2.CAP_PROP_POS_MSEC,second*1000);ok,frame=video.read();assert ok
        cv2.imwrite(str(out/(name+'-'+str(second)+'s.png')),frame)
    video.release()
archive=art/'Package-20261104-183402-258-c983dd92/Archive/Windows'
package_files=sorted(p for p in archive.rglob('*') if p.is_file());assert len(package_files)==48
with (out/'PACKAGE.csv').open('w',encoding='utf-8',newline='') as file:
    writer=csv.writer(file);writer.writerow(['PathUnderWindows','Bytes','SHA256'])
    for path in package_files:writer.writerow([path.relative_to(archive).as_posix(),path.stat().st_size,sha(path)])
smoke=load(art/'SmokeB-20261104-184708/results.json');assert len(smoke)==3 and all(s['passed'] for s in smoke)
protected=['Source/AnimeMMORPG/U01/U01Character.cpp','Source/AnimeMMORPG/U01/U01Character.h','Source/AnimeMMORPG/U01/U01MotorPolicy.h',
           'Source/AnimeMMORPG/U01/U01PlayerController.cpp','Source/AnimeMMORPG/U01/U01PlayerController.h','Content/AnimeMMORPG/U01/Input','Content/Characters','Content/AnimeMMORPG/Maps']
assert not git('diff','941bc3d',source,'--name-only','--',*protected)
assets=[{'path':p.relative_to(root).as_posix(),'SHA256':sha(p),'bytes':p.stat().st_size} for p in sorted((root/'Content/AnimeMMORPG/U01/Animation').glob('*.uasset'))]
assert len(assets)==11
manifest={'status':'READY_FOR_REVIEW','branch':'u01/d-animation','revisionBase':'941bc3d3b7216355557053078c89b35a2b0a6477','sourceSHA':source,
          'mainUnchanged':'868df83e096748991ccd861da3f98b64c409dcbd','engine':'5.8.4 CL58902052','compiler':'MSVC14.51.36260 / toolset14.51.36231','sdk':'10.0.26100.0',
          'nativeBuild':'Build-20261104-182743-101-c6712605','sourceBuild':'Build-20261104-183208-319-cbeba78e','testRun':tests.name,'testsPassed':16,
          'testPID':load(tests/'process.json')['pid'],'package':archive.relative_to(root).as_posix(),'packageFiles':48,'smokeRun':'SmokeB-20261104-184708','smoke':smoke,
          'gripConfig':load(root/'Scripts/U01/DGrip.json'),'assets':assets,'protectedMotorInputTemplateMapDiff':[],
          'blend':'Every selector pose stores explicit .100s in AnimBP; moving >3cm/s cancels hold; stationary hold maximum .250s',
          'handDiagnosis':{'before':'941 legacy ABP/SK bytes verified against D-ASSETS.json; current native editor preview tool. No gameplay metrics inferred.',
                           'after':'Calibrated assets identical to819fbd0; preview native42e9ad4; render proxy recreated per pose to avoid stale GPU skinning',
                           'angles':'Front/Side/Top in actor world axes, plus Palm/ThumbSide/FingerEnd in hand axes; transient preview fill light only; some direct views naturally occluded by arm/blade',
                           'fingers':'Single own PoseAsset after selector, branch filters at five right finger01 bones; no wrist/arm/metacarpal modification',
                           'landingPreview':'Early stationary-landing transition sampled by diagnostic tool; gameplay transition separately captured and tested'},
          'inputMethod':'Real Win32 SendInput, exact foreground HWND/PID/exe verified. W probed safely in locked menu; UniKey Ctrl+Shift only if conversion observed, restored if changed; runtime logs verify movement. Product input unchanged.',
          'captureStatistics':{n:{k:d['meta'].get(k) for k in ['uniqueCaptureHz','distinctImageCount','distinctImageHz','uniqueFrameGapP95Seconds','uniqueFrameGapMaxSeconds','frames','duplicatedFrames','captureActiveSeconds','menuWProbeBefore','menuWProbeAfter','externalInputMethodRestored']} for n,d in datasets.items() if n in capture_paths},
          'originalEditor':{'pid':20412,'project':'D:/Data/AnimeMMORPG/AnimeMMORPG.uproject','world':'/Game/AnimeMMORPG/Maps/L_Boot.L_Boot','actors':0,'confirmedUtc':'2026-11-04T12:09:56.665Z','nativeDLoaded':'NOT VERIFIED; AI did not close/restart original'},
          'history':['GitHub500 delayed pushes; independent builds used local Git object fetch and were not called pushed-source proof. Source819fbd0 eventually pushed, full-built and cold-tested.',
                     'Private pose helper / missing exported GetPoseNames / editor-only GetPoseNameByIndex compile/link failures retained in RevisionBuildConsole3-6 logs; final builds pass.',
                     'HandBefore/HandBeforeLit/HandCandidate1 multi-pose GPU cache diagnosis: superseded by render-proxy refresh and verified before/after captures.',
                     'Earlier Before/Capture and After/Compare/CompareFinal/CoverageFinal did not confirm W movement (UniKey emitted key=None); not accepted locomotion evidence.',
                     'After/Compare captured below1Hz readback; rejected. Window-client-DC variants could cache a stale menu despite high readback rate; excluded after visual inspection. Only BeforeScreenVerified/CaptureAdaptive and AfterScreenVerified/Compare/Coverage are handoff videos, with image diversity and runtime movement checks.'],
          'reviewPending':['Subjective smoothness of100ms blend and grip appearance on final package','D user acceptance; no merge or E yet'],'artAnime':'DEFERRED'}
(out/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with (out/'EVIDENCE.csv').open('w',encoding='utf-8',newline='') as file:
    writer=csv.writer(file);writer.writerow(['RelativeEvidence','Bytes','SHA256'])
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.name!='EVIDENCE.csv':writer.writerow([path.relative_to(out).as_posix(),path.stat().st_size,sha(path)])
print(json.dumps({'tests':len(success),'oldMovingLandSamples':len(bad),'newMovingLandSamples':0,'captures':manifest['captureStatistics']}))
