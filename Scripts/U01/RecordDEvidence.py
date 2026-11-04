"""Record the completed D run without copying local config, tokens, caches or binaries into Git."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[2]
art=root/'Artifacts/U01/D'
out=root/'Docs/U01/Evidence'
source='715238443e33e1a2760ea3d89f4d1698f092e511'
base='868df83e096748991ccd861da3f98b64c409dcbd'
package=art/'Package-20261104-144914-755-2b8e3bc6'
archive=package/'Archive/Windows'
assert subprocess.check_output(['git','-C',str(art/'Source'),'rev-parse','HEAD'],text=True).strip()==source
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
files=sorted(p for p in archive.rglob('*') if p.is_file())
assert len(files)==48
with (out/'D-ARTIFACTS.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.writer(f);writer.writerow(['PathUnderWindows','Bytes','SHA256'])
    for path in files:writer.writerow([path.relative_to(archive).as_posix(),path.stat().st_size,digest(path)])
own=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'SHA256':digest(p)}
     for p in sorted((root/'Content/AnimeMMORPG/U01/Animation').glob('*.uasset'))]
assert len(own)==10
character=root/'Content/AnimeMMORPG/U01/Blueprints/BP_U01Character.uasset'
own.append({'path':character.relative_to(root).as_posix(),'bytes':character.stat().st_size,'SHA256':digest(character)})
shared_diff=subprocess.check_output(['git','diff',base,source,'--name-only','--','Content/Characters','Content/Variant_Combat','Content/Variant_Platforming','Content/Variant_SideScrolling'],text=True)
assert not shared_diff.strip()
asset_data={'sourceSHA':source,'ownedAssets':own,'sharedTemplateDiff':shared_diff,
            'authoringLog':'Authoring-20261104-142947/Editor.log','finalizeLog':'Finalize-20261104-144649/Editor.log',
            'rootPolicy':'Duplicate sequences: enable_root_motion=true, force_root_lock=true, AnimFirstFrame; AnimBP parent IgnoreRootMotion; source clips unchanged',
            'sourceAuthoredRootSpeedCmPerSec':{'walk':300.,'jog':600.340651},
            'samples':[{'speed':0,'clip':'A_U01_Idle','rate':1}, {'speed':300,'clip':'A_U01_Walk','rate':1},
                       {'speed':500,'clip':'A_U01_Jog','rate':500/600.340651},{'speed':700,'clip':'A_U01_Jog','rate':700/600.340651}],
            'playRateBounds':[.6,2.5], 'socket':{'skeleton':'SK_U01','name':'U01_Sword_R','bone':'hand_r','rotationPitchYawRoll':[0,0,90]},
            'sword':'Engine Cube components grip18x3x3cm, guard4x18x4cm, blade88x6x2.5cm; no collision/overlap/physics/navigation/damage',
            'artAnime':'DEFERRED'}
(out/'D-ASSETS.json').write_text(json.dumps(asset_data,ensure_ascii=False,indent=2),encoding='utf-8')
smoke=load(art/'SmokeB-20261104-145341/results.json')
assert len(smoke)==3 and all(s['passed'] and s['exitCode']==0 for s in smoke)
results=load(out/'D-RESULTS.json')
assert results['sourceSHA']==source and len(results['tests'])==14
video=art/'PlayCaptureFinal/Run1/Play-D.mp4'
meta=load(art/'PlayCaptureFinal/Run1/process.json')
assert meta['binarySHA256']==digest(archive/'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe')
manifest={'status':'READY_FOR_REVIEW','branch':'u01/d-animation','baseMainSHA':base,'sourceSHA':source,
          'engine':'5.8.4 CL58902052','compiler':'MSVC 14.51.36260, toolset folder14.51.36231','sdk':'10.0.26100.0',
          'clone':'Artifacts/U01/D/Source; GitHub no-checkout clone then fast-forward to pushed source; C LFS object cache seeded/fsck OK; no copied binaries or Intermediate',
          'build':'Build-20261104-144803-468-388ab013','nativeRebuild':'Build-20261104-144328-366-7006a6c3; final source changed only BlendSpace binary asset',
          'testRun':'MCPTests-20261104-144814','testsPass':14,'testResults':'D-RESULTS.json',
          'package':package.relative_to(art).as_posix()+'/Archive/Windows','packageFileCount':48,
          'artifactManifest':'D-ARTIFACTS.csv','artifactManifestSHA256':digest(out/'D-ARTIFACTS.csv'),
          'smokeRun':'SmokeB-20261104-145341','smoke':smoke,
          'video':video.relative_to(root).as_posix(),'reviewVideo':'Docs/U01/Evidence/D-PLAY.mp4','videoBytes':video.stat().st_size,'videoSHA256':digest(video),
          'capturePID':meta['pid'],'captureMethod':meta['method'],'captureSeconds':meta['wallSeconds'],
          'captureFrames':meta['frames'],'captureDuplicatedFrames':meta['duplicatedFrames'],'captureHz':10,
          'originalEditor':{'pid':19924,'project':'D:/Data/AnimeMMORPG/AnimeMMORPG.uproject','world':'/Game/AnimeMMORPG/Maps/L_Boot.L_Boot','actors':0,
                            'confirmedUtc':'2026-11-04T07:56:22.230Z','nativeB_CDLoaded':'NOT VERIFIED; no original restart/full build/Live Coding attempted in D'},
          'history':{'initialCompile':'Build-20261104-141726-881-2e394361: failed engine API adaptation',
                     'gameCompile':[],
                     'authoring':'Authoring-20261104-142401: transient FK binding mismatch, assets preserved separately',
                     'rejectedVisual':'PlayCapture/Run3: source07fbb3e, frozen locomotion; superseded, not accepted',
                     'regressionRed':'MCPTests-20261104-144514:12/14 pass, AssetPolicy and TransitionsAndAttachment fail on old asset',
                     'captureSetup':'PlayCapture Run1 BOM error before input; Run2 foreground refusal before input; Run3 succeeded but exposed locomotion fault'},
          'pending':['Reviewer foot sliding/motion quality assessment on video/package','No user acceptance of D yet','E/F/G not run; 30/60/120 render FPS unverified','Python/toolset issue from A remains for F/integration'],
          'artAnime':'DEFERRED'}
# Preserve real folder names rather than inventing a failed-build run ID.
def read_log(path):
    raw=path.read_bytes()
    return raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig')
failed_game=[p.parent.name for p in art.glob('Build-*/Game.log') if "'GetNumberOfBlendSamples'" in read_log(p)]
manifest['history']['gameCompile']=failed_game
(out/'D-MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'D-PLAY.mp4').write_bytes(video.read_bytes())
for name,frame in [('WALK','0040'),('SPRINT','0065'),('JUMP','0105'),('LAND','0210')]:
    (out/f'D-{name}.png').write_bytes((art/f'PlayCaptureFinal/Run1/frame-{frame}.png').read_bytes())
print(json.dumps({'sourceSHA':source,'files':len(files),'videoSHA256':digest(video),'smoke':[(s['map'],s['passed']) for s in smoke]}))
