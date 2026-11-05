import json,csv,hashlib,shutil
from pathlib import Path
r=Path.cwd();a=r/'Artifacts/U01/G';o=r/'Docs/U01/Evidence/G';o.mkdir(parents=True,exist_ok=True)
sha='5f8a6eabe103a8b31a894c82f32cffb0325474a9';package=a/'Package-20261105-153201-862-38caf5d5/Archive/Windows'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with (o/'PACKAGE.csv').open('w',newline='',encoding='utf8') as f:
 w=csv.writer(f);w.writerow(['PathUnderWindows','Bytes','SHA256'])
 for p in sorted(package.rglob('*')):
  if p.is_file():w.writerow([p.relative_to(package).as_posix(),p.stat().st_size,digest(p)])
long=load(a/'Play/LongPlay-20261105-172749/input.json');assert long['completed'] and long['seconds']>=600 and long['process']['sourceSHA']==sha
samples=[]
for line in (a/'Play/UserA/Long.log').read_text(encoding='utf-8-sig',errors='replace').splitlines():
 if 'Metrics {' in line:
  try:s=json.loads(line.split('Metrics ',1)[1])
  except ValueError:continue
  if long['start']<=s['utc']<=long['end']:samples.append(s)
assert samples and all(s['pid']==6424 and s['sourceSHA']==sha and s['worldType']==1 and s['netMode']==0 and s['mappingContextCount']==1 for s in samples)
focus=[e for e in long['events'] if e['action']=='focus-return'];assert len(focus)==10
summary={'sourceSHA':sha,'completed':True,'seconds':long['seconds'],'pid':6424,'realInputEvents':len(long['events']),'nativeGameSamples':len(samples),'focusReturnEvents':len(focus),'windowActiveSamples':sum(s['windowActive'] for s in samples),'windowInactiveSamples':sum(not s['windowActive'] for s in samples),'controlStates':sorted(set(s['controlState'] for s in samples)),'oneMappingThroughout':True,'history':{'path':'Artifacts/U01/G/Play/LongPlay/input.json','completed':False,'seconds':534.4294635,'reason':'Unexpected foreground change; input guard aborted; interrupted verification, not a ten-minute pass'}}
(o/'LONG-PLAY-SUMMARY.json').write_text(json.dumps(summary,indent=2));shutil.copyfile(a/'FPS/summary.json',o/'FPS-SUMMARY.json');shutil.copyfile(a/'FPS/trials.json',o/'FPS-TRIALS.json');shutil.copyfile(a/'Play/LongPlay-20261105-172749/input.json',o/'LONG-PLAY-INPUT.json');shutil.copyfile(a/'Play/LongPlay/input.json',o/'LONG-PLAY-INTERRUPTED.json')
for p in (a/'FPS').glob('cap-*.png'):shutil.copyfile(p,o/p.name)
for p in (a/'Play/LongPlay-20261105-172749').glob('minute-*.png'):shutil.copyfile(p,o/p.name)
(o/'MANIFEST.json').write_text(json.dumps({'status':'IN_PROGRESS','sourceSHA':sha,'packagePath':str(package.relative_to(r)),'packageIndexSHA256':digest(o/'PACKAGE.csv'),'gameExecutableSHA256':digest(package/'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'),'build':'Artifacts/U01/G/Build-20261105-152800-078-73c759e0','automation':'Artifacts/U01/G/MCPTests-20261105-153131','automationPassed':23,'smokePassed':3,'scope':'G not accepted/merged; remaining integrated checks pending','originalEditorObserved':{'pid':8676,'createdLocal':'2026-11-05T17:20:42','note':'Original project remains open. Earlier PID2068 no longer present; agent did not restart it. Do not claim uninterrupted PID lifetime.'}},indent=2))
(o/'.gitattributes').write_text('* -text\n');print(json.dumps(summary,indent=2))
