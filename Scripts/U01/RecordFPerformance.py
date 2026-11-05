"""Seal F performance revision; keep earlier F evidence unchanged."""
from pathlib import Path
import csv,hashlib,json,shutil,subprocess,sys
import cv2
import numpy as np
cv2.setNumThreads(1)
root=Path(__file__).resolve().parents[2];art=root/'Artifacts/U01/F';study=art/'PerfInvestigation';final=art/'Reviews/Session-20261105-132938';out=root/'Docs/U01/Evidence/F-Performance';out.mkdir(exist_ok=True)
source='0f02c77bc14fc4c727ba8694223f8cfc5a655c31'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8',newline='\n')
assert subprocess.check_output(['git','-C',str(art/'Source'),'rev-parse','HEAD'],text=True).strip()==source
subprocess.run([sys.executable,str(root/'Scripts/U01/AnalyzeFPerformance.py'),'--artifacts',str(study),'--out',str(out),'--final-session',str(final)],check=True,capture_output=True)
results=load(out/'RESULTS.json');cases={c['case']:c for c in results['cases']}
for name in ('FinalA','FinalB','RepeatA','RepeatB'):
 for role,v in cases[name]['roles'].items():
  assert v['identity']['sourceSHA']==source and v['identity']['worldType']==1
  assert v['fps']>29 and v['wallFrameMs']['max']<100
  for setting in ('pktLag','pktLagMin','pktLagMax','pktLoss','pktOrder','pktDup','incomingLagMin','incomingLagMax','incomingLoss'):assert v['settings'][setting]==[0]
  assert v['settings']['t.MaxFPS']==[30] and v['settings']['t.IdleWhenNotForeground']==[0] and v['settings']['editorThrottle']==[False]
  assert len(v['updateSettings'])==1 and v['updateSettings'][0][:3]==[100,2,2] and abs(v['updateSettings'][0][3]-.1)<1e-6
  assert v['focus']==[role==cases[name]['owner']]
 write(name+'-capture.json',load(final/name/'process.json'))
# Retain complete physical input metadata for before/after; no fabricated frames.
videos={}
for r,name in [(study/'Session-20261105-130458','BaselineAEnglish'),(study/'Session-20261105-130458','BaselineBEnglish'),(final,'RepeatA'),(final,'RepeatB')]:
 m=load(r/name/'process.json');assert m['completed'] and not m['staticCaptureRejected'];src=r/name/'Play-F.mp4';dst=out/(name+'.mp4');cap=cv2.VideoCapture(str(src));fps=cap.get(cv2.CAP_PROP_FPS);count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));assert int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))==1840 and int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))==540
 writer=cv2.VideoWriter(str(dst),cv2.VideoWriter_fourcc(*'mp4v'),fps,(1800,540));assert writer.isOpened();n=0
 while True:
  ok,frame=cap.read()
  if not ok:break
  writer.write(np.concatenate((frame[:,:900],frame[:,-900:]),axis=1));n+=1
 writer.release();cap.release();assert n==count
 videos[name]={'rawSHA256':sha(src),'exportSHA256':sha(dst),'frames':n,'encodedHz':fps,'uniqueCaptureHz':m['uniqueCaptureHz'],'distinctImageHz':m['distinctImageHz'],'edit':'Only desktop gap removed. Both native 900x540 clients, in-game warnings, all frame order and duplicate timing frames retained; no interpolation or speed change.'}
 write(name+'-capture.json',m)
write('VIDEOS.json',videos);write('PROCESSES.json',load(final/'processes.json'));write('SERVER-TIMER.json',load(final/'server-timer.json'));write('TIMER-ABA.json',load(study/'TimerABA.json'))
for name in ('BudgetMemory.json','MinimizedMemory.json','MinimizedGPUCounters.json','FinalMemoryGPU.json'):
 write(name,load(study/name))
for name in ('FinalGPU.csv','GPU.csv'):
 # Preserve complete rows; continuous nvidia-smi was stopped during last row.
 lines=(study/name).read_text(encoding='utf-8-sig').splitlines();width=lines[0].count(',');complete=[s for s in lines if s.count(',')==width]
 (out/name).write_text('\n'.join(complete)+'\n',encoding='utf8',newline='\n')
tests=study/'MCPTests-20261105-132523';lines=(tests/'Editor.log').read_text(encoding='utf-8-sig').splitlines();done=[s for s in lines if 'Test Completed. Result=' in s];assert len(done)==23 and all('Result={Success}' in s for s in done) and any('23 tests performed' in s for s in lines)
write('AUTOMATION.json',{'sourceSHA':source,'process':load(tests/'process.json'),'tests':done,'measurements':[s for s in lines if 'U01C_MEASURE ' in s or 'U01D_MEASURE ' in s]})
smoke=load(study/'SmokeB-20261105-132746/results.json');assert len(smoke)==3 and all(s['passed'] and s['exitCode']==0 for s in smoke);write('SMOKE.json',smoke)
events={}
for role in ('Server','ClientA','ClientB'):
 lines=(final/role/(role+'.log')).read_text(encoding='utf-8-sig').splitlines();assert not any('AttributeError:' in s or 'Blueprint Runtime Error' in s or 'Accessed None' in s for s in lines)
 events[role]=[s for s in lines if any(k in s for k in ('t.MaxFPS =','t.IdleWhenNotForeground =','AtlasSize =','PoolMin =','PoolSize =','ScreenPercentage =','FixtureReset','Join succeeded'))]
write('RUNTIME-CONFIG.json',events)
package=study/'Package-20261105-132600-709-df14ddc7/Archive/Windows'
with (out/'PACKAGE.csv').open('w',encoding='utf8',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['PathUnderWindows','Bytes','SHA256'])
 for p in sorted(package.rglob('*')):
  if p.is_file():w.writerow([p.relative_to(package).as_posix(),p.stat().st_size,sha(p)])
write('MANIFEST.json',{'status':'READY_FOR_REVIEW','sourceSHA':source,'baseAcceptedMain':'99363222895b0069b3afdab2b103bfc81c68af6b','engine':'UE5.8.4 CL58902052','toolchain':'MSVC14.51.36260 / toolset14.51.36231 / SDK10.0.26100.0','build':'Artifacts/U01/F/Build-20261105-130401-709-c1d0b747','tests':str(tests.relative_to(root)),'automation':23,'smoke':str((study/'SmokeB-20261105-132746').relative_to(root)),'package':str(package.relative_to(root)),'finalSession':str(final.relative_to(root)),'moduleSHA256':sha(art/'Source/Binaries/Win64/UnrealEditor-AnimeMMORPG.dll'),'engineExeSHA256':sha(Path('D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe')),'reviewProfile':{'scope':'Per-process local 4GiB two-client review; original product settings unchanged','DX12_SM6_Lumen':True,'LumenAtlasSize':2048,'RenderTargetPoolMinimumMiB':128,'StreamingPoolMiB':256,'ScreenPercentage':50,'WindowSize':[900,540],'originalEditor':'Kept open; windows minimized and placement saved for cleanup restore','server':'Honor existing timer-resolution request on dedicated process only','maxFPS':30,'replicationOrSmoothingChanged':False},'limits':['Original graphics profile remains insufficient under the same simultaneous workload; do not claim product performance fixed','Game-thread packet/mesh onset measurement, not GPU scanout latency','No integrated G FPS/10min or 60/120FPS acceptance','No F acceptance/merge; no packaged Server acceptance; anime art/combat DEFERRED']})
print('Sealed F performance evidence; 23 tests, 3 smoke maps, 4 measured final runs')
