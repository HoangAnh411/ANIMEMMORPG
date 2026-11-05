"""Sequential F60 study. Never runs build/Automation/package during measurements."""
import argparse,json,subprocess,time,hashlib
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--case',choices=('A','B','C','D','E','F3'),required=True);p.add_argument('--cap',type=int,choices=(30,60),default=30);a=p.parse_args()
folder=root/'Artifacts/U01/F/F60';folder.mkdir(exist_ok=True);out=folder/(a.case+'-'+datetime.now().strftime('%Y%m%d-%H%M%S'));out.mkdir();session=None;sampler=None
def utc():return datetime.now(timezone.utc).isoformat()
def ps(file,*args,**kwargs):return subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/file),*map(str,args)],creationflags=subprocess.CREATE_NO_WINDOW,**kwargs)
def progress(stage,**data):(out/'progress.json').write_text(json.dumps(dict(stage=stage,utc=utc(),**data),indent=2),encoding='utf8',newline='\n');print(stage,flush=True)
def native(path,marker):
 lines=path.read_text(encoding='utf-8-sig',errors='replace').splitlines()
 for line in reversed(lines):
  if marker in line:
   try:return json.loads(line.split(marker,1)[1])
   except json.JSONDecodeError:pass
 raise RuntimeError('No complete native '+marker+' in '+str(path))
count=1 if a.case in ('B','D') else 2;cap=60 if a.case in ('B','C','D') else a.cap if a.case=='F3' else 30;original=a.case=='D';buffered=a.case in ('E','F3')
try:
 progress('launch',case=a.case,clientCount=count,clientCap=cap,serverCap=30)
 args=['-ClientCount',count,'-ClientMaxFPS',cap,'-Diagnostics']
 if original:args+=['-OriginalQuality']
 if buffered:args+=['-BufferedDiagnostics']
 with (out/'launcher.log').open('w',encoding='utf8') as f:ps('Scripts/U01/ReviewF.ps1',*args,stdout=f,stderr=subprocess.STDOUT,check=True)
 session=Path((root/'Artifacts/U01/F/LatestReview.txt').read_text(encoding='utf-8-sig').strip());records=json.loads((session/'processes.json').read_text(encoding='utf-8-sig'))
 sampler=subprocess.Popen(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(root/'Scripts/U01/SampleF60Resources.ps1'),'-SessionPath',str(session)],stdout=(out/'sampler.log').open('w'),stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 progress('warmup',session=str(session),minimumSeconds=30)
 warm_start=utc();start=time.monotonic();ready=0
 while True:
  time.sleep(1);snapshots=[native(Path(r['log']),'U01F_NET ') for r in records]
  quiet=all(not s['asyncLoading'] and s.get('shaderJobs',-1)==0 and s.get('pipelinePrecompiles',-1)==0 for s in snapshots)
  ready=ready+1 if quiet else 0
  if time.monotonic()-start>=30 and ready>=3:break
  if time.monotonic()-start>240:raise RuntimeError('Assets/shaders did not become ready')
 configurations={}
 if sampler.poll() is not None or not (session/'resources.jsonl').exists():raise RuntimeError('Resource sampler failed; measurement cannot start')
 for record in records:
  if buffered:
   lines=(Path(record['userDir'])/'Frames.jsonl').read_text(encoding='utf8').splitlines()
   for line in reversed(lines):
    try:s=json.loads(line);break
    except json.JSONDecodeError:continue
  else:s=native(Path(record['log']),'U01F_PERF ')
  expected=30 if record['role']=='Server' else cap;assert s['t.MaxFPS']==expected
  if record['role']!='Server':
   assert s['r.ScreenPercentage']==(100 if original else 50)
   if not original:assert s['r.LumenScene.SurfaceCache.AtlasSize']==2048 and s['r.RenderTargetPoolMin']==128 and s['r.Streaming.PoolSize']==256
  configurations[record['role']]=s
 manifest={'case':a.case,'sourceSHA':records[0]['sourceSHA'],'packageSourceSHA':'0f02c77bc14fc4c727ba8694223f8cfc5a655c31','packageHashManifest':'Docs/U01/Evidence/F-Performance/PACKAGE.csv','session':str(session),'processes':records,'clientCount':count,'clientCap':cap,'serverCap':30,'originalQuality':original,'windowSize':[900,540],'internalResolution':100 if original else 50,'bufferedDiagnostics':buffered,'editorWindows':json.loads((session/'original-editor-windows.json').read_text(encoding='utf-8-sig')),'warmup':{'start':warm_start,'end':utc(),'seconds':time.monotonic()-start,'readySnapshots':snapshots},'runtime':configurations}
 (out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8',newline='\n')
 progress('measure',session=str(session),seconds=300 if a.case=='F3' else 120)
 subprocess.run(['python',str(root/'Scripts/U01/DriveF60.py'),'--session',str(session),'--seconds','300' if a.case=='F3' else '120'],cwd=root,check=True,stdout=(out/'input.log').open('w'),stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 time.sleep(2) # Last buffered frame batch must reach disk before stopping.
 manifest['input']=json.loads((session/'input.json').read_text());manifest['completed']=True;(out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8',newline='\n');progress('complete',session=str(session))
except Exception as e:progress('failed',error=repr(e),session=str(session));raise
finally:
 if session:
  (session/'stop-resources').touch()
  if sampler:
   try:sampler.wait(timeout=15)
   except subprocess.TimeoutExpired:raise RuntimeError('Resource sampler did not stop')
  with (out/'cleanup.log').open('w') as f:ps('Scripts/U01/StopFSession.ps1','-SessionPath',session,stdout=f,stderr=subprocess.STDOUT,check=True)
  if sampler and sampler.returncode:raise RuntimeError('Resource sampler exited with failure')
print(str(out),flush=True)
