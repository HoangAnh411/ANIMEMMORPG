"""Seal completed F60 study without replacing previous F evidence or rebuilding package."""
import csv,hashlib,json,shutil,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'Docs/U01/Evidence/F60';art=root/'Artifacts/U01/F/F60'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8',newline='\n')
subprocess.run([sys.executable,str(root/'Scripts/U01/AnalyzeF60Study.py')],cwd=root,check=True)
r=load(out/'RESULTS.json');by={v['case']:v for v in r['runs']};assert set(by)=={'A','B','C','D','E','F3'}
assert r['selection']['defaultClientMaxFPS'] in (30,60)
selected=r['selection']['defaultClientMaxFPS'];long=by['F3'];assert long['seconds']==300 and long['clientCap']==selected
assert all(v['frameMs']['max']<500 and v['longestOver100msStreak']<3 for v in long['roles'].values())
assert long['roles']['Server']['fps']>=28.5
if selected==60:assert all(long['roles'][v]['fps']>=57 and long['roles'][v]['frameMs']['p95']<=20 for v in ('ClientA','ClientB'))
source=load(out/'C-manifest.json')['sourceSHA'];videos={};raw={};warnings={};runtime={}
for case,run in by.items():
 m=load(out/(case+'-manifest.json'));assert m['warmup']['seconds']>=30 and m['sourceSHA']==source
 for s in m['warmup']['readySnapshots']:assert not s['asyncLoading'] and s['shaderJobs']==s['pipelinePrecompiles']==0
 session=Path(m['session']);raw[case]={'manifest':run['manifest'],'manifestSHA256':digest(Path(run['manifest'])),'inputSHA256':digest(session/'input.json'),'resourcesSHA256':digest(session/'resources.jsonl'),'frames':{}}
 runtime[case]={}
 for rec in m['processes']:
  path=Path(rec['userDir'])/'Frames.jsonl' if m['bufferedDiagnostics'] else Path(rec['log']);raw[case]['frames'][rec['role']]={'path':str(path),'SHA256':digest(path)}
  lines=Path(rec['log']).read_text(encoding='utf-8-sig').splitlines()
  assert not any('AttributeError:' in l or 'Accessed None' in l or 'Blueprint Runtime Error' in l or 'Cannot flush buffered performance file' in l for l in lines)
  if m['bufferedDiagnostics']:assert not any('U01F_PERF {' in l for l in lines)
  runtime[case][rec['role']]=[l for l in lines if any(k in l for k in ('t.MaxFPS =','t.IdleWhenNotForeground =','ScreenPercentage =','AtlasSize =','PoolMin =','PoolSize ='))]
  warnings[case+'/'+rec['role']]=[l for l in lines if ': Warning:' in l or ': Error:' in l]
  if rec['role']!='Server':
   assert run['roles'][rec['role']]['runtime']['r.ScreenPercentage']==[100 if case=='D' else 50]
  for k in ('pktLag','pktLagMin','pktLagMax','pktLagVariance','pktJitter','pktLoss','incomingLagMin','incomingLagMax','incomingLoss','pktBufferBloatMs','incomingBufferBloatMs'):assert run['roles'][rec['role']]['runtime'][k]==[0]
 # Focused comparison excerpts; dual-client images already omit the desktop gap.
 if case in ('A','C','D','F3'):
  phases=(0,1) if m['clientCount']==2 else (0,)
  for phase in phases:
   src=session/f'Phase{phase}.mp4';dst=out/f'{case}-Phase{phase}.mp4';shutil.copyfile(src,dst)
   meta=m['input']['videos'][str(phase)];times=meta['wallTimes'];videos[dst.name]={'SHA256':digest(dst),'encodedHz':30,'uniqueCaptures':len(times),'actualCaptureHz':(len(times)-1)/(times[-1]-times[0]) if len(times)>1 else None,'encodedFrames':meta['frames'],'duplicateFrames':meta['duplicates'],'firstCaseSecond':times[0] if times else None,'lastCaseSecond':times[-1] if times else None,'edit':'Original guarded client rectangles only, timing duplicates retained; no interpolation. Frame data establishes 60 FPS, not this 30Hz-encoded excerpt.'}
write('RAW-ARTIFACTS.json',raw);write('VIDEOS.json',videos);write('RUNTIME-CVARS.json',runtime);write('WARNINGS.json',warnings)
tests=root/'Artifacts/U01/F/MCPTests-20261105-140807';lines=(tests/'Editor.log').read_text(encoding='utf-8-sig').splitlines();done=[l for l in lines if 'Test Completed. Result=' in l];assert len(done)==23 and all('Result={Success}' in l for l in done) and any('23 tests performed' in l for l in lines)
write('AUTOMATION.json',{'sourceSHA':source,'process':load(tests/'process.json'),'tests':done,'measurements':[l for l in lines if 'U01C_MEASURE ' in l or 'U01D_MEASURE ' in l]})
build=root/'Artifacts/U01/F/F60-Build-20261105-140722';assert load(build/'result.json')['exitCode']==0;write('BUILD.json',load(build/'result.json'))
package=root/'Artifacts/U01/F/PerfInvestigation/Package-20261105-132600-709-df14ddc7/Archive/Windows';hashes=root/'Docs/U01/Evidence/F-Performance/PACKAGE.csv'
for row in csv.DictReader(hashes.open(encoding='utf8')):assert digest(package/row['PathUnderWindows'])==row['SHA256']
shutil.copyfile(hashes,out/'PACKAGE.csv')
history=[]
for p in sorted(art.glob('*/progress.json')):
 v=load(p)
 if v['stage']=='failed':history.append({'path':str(p),'progress':v,'inputLog':(p.parent/'input.log').read_text(encoding='utf8',errors='replace') if (p.parent/'input.log').exists() else ''})
for p in sorted(art.glob('*/MANIFEST.json')):
 v=load(p)
 if v.get('protocolValid') is False:history.append({'path':str(p),'issue':v.get('protocolIssue'),'accepted':False,'samplerLog':(p.parent/'sampler.log').read_text(encoding='utf8',errors='replace') if (p.parent/'sampler.log').exists() else ''})
write('HISTORY.json',history)
scripts={p.name:digest(p) for p in (root/'Scripts/U01').glob('*F60*') if p.is_file()}
for name in ('StartFSession.ps1','ReviewF.ps1','FReviewHost.ps1','StopFSession.ps1','StopLatestFReview.ps1'):scripts[name]=digest(root/'Scripts/U01'/name)
write('MANIFEST.json',{'status':'READY_FOR_REVIEW','branch':'u01/f-network','baseSHA':'412bc7b6623c4afb8af8c6fe07d7f419dedcbc5b','sourceSHA':source,'packageSourceSHA':'0f02c77bc14fc4c727ba8694223f8cfc5a655c31','package':str(package.relative_to(root)),'packageReused':True,'build':str(build.relative_to(root)),'tests':str(tests.relative_to(root)),'automation':23,'engine':'UE5.8.4 CL58902052','toolchain':'MSVC14.51.36260 / SDK10.0.26100.0','editorModuleSHA256':digest(root/'Artifacts/U01/F/Source/Binaries/Win64/UnrealEditor-AnimeMMORPG.dll'),'engineExeSHA256':digest(Path('D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe')),'defaultClientMaxFPS':selected,'serverMaxFPS':30,'selection':r['selection'],'profile':{'clients':2,'window':[900,540],'screenPercentage':50,'LumenAtlasSize':2048,'RenderTargetPoolMinimumMiB':128,'StreamingPoolMiB':256,'originalEditor':'Kept open, minimized during every run; placement restored by each cleanup','server':'Dedicated Editor / NullRHI; process-local existing timer request honored; no GPU/window/render dimensions apply'},'nativeGameplayChanged':False,'replicationOrSmoothingChanged':False,'testsOrBuildsDuringMeasurements':False,'inputProtocol':'Continuous 120 seconds per A-D/E, alternating 60s foreground blocks; continuous 300 seconds F3 including all focus/menu transitions; 10 forward starts+stops per block, backward return strokes retained','scriptsAtSeal':scripts,'limits':['Not an uncapped maximum-FPS measurement','D is one client at 900x540 internal100%, not target-resolution product benchmark','No packaged Server acceptance, latency/loss tests or G acceptance','All transform timings are game-thread estimates, not scanout latency','F remains pending user confirmation; no merge or G work']})
print('Sealed F60; selected client cap',selected,'server 30; full 300s validation complete')
