"""Seal separately from historical D. Does not build, save assets or accept U03."""
import argparse,csv,gzip,hashlib,json,re,shutil,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--prepare-index',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[2];base=root/'Artifacts/U03/D';run=base/'R1';dest=root/'Evidence/D-R1';clone=base/'Source'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=subprocess.check_output(['git','-C',str(clone),'rev-parse','HEAD'],text=True).strip()
plan=read(run/'FINAL-RUNS.json');assert source==plan['source']
subprocess.run(['git','diff','--exit-code',source,'--','Source','Content'],check=True,stdout=subprocess.DEVNULL)
package=root/plan['package']/'Archive/Windows';module=clone/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll';engine=Path('D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe')
checkpoint=run/'Binaries'/source/module.name;checkpoint.parent.mkdir(parents=True,exist_ok=True)
if not checkpoint.exists():shutil.copyfile(module,checkpoint)
assert sha(checkpoint)==sha(module)
write(run/'BinaryCheckpoint.json',dict(source=source,path=checkpoint.relative_to(root).as_posix(),sha256=sha(checkpoint),bytes=checkpoint.stat().st_size))
dest.mkdir(parents=True,exist_ok=True)
index=[dict(path=f.relative_to(package).as_posix(),sha256=sha(f),bytes=f.stat().st_size) for f in sorted(package.rglob('*')) if f.is_file()]
with (dest/'PACKAGE.csv').open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=['path','sha256','bytes']);w.writeheader();w.writerows(index)
manifest=dict(status='IN_PROGRESS',revision='D-R1',source=source,binarySource=source,base='bc3a9955a8c0ecc1cb7f0d43dce13300c9664ac9',branch='u03/d-integration',packageRelativePath=package.relative_to(root).as_posix(),packageFiles=len(index),packageIndexSHA256=sha(dest/'PACKAGE.csv'),engineExeSHA256=sha(engine),engine=read(Path('D:/Software/UE_5.8/Engine/Build/Build.version')),toolchain=dict(compiler='MSVC14.51.36260',sdk='10.0.26100.0',python=sys.version),binaries=[dict(path=str(module),sha256=sha(module)),dict(path=str(package/'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'),sha256=sha(package/'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'))])
if a.prepare_index:write(dest/'MANIFEST.json',manifest);print('Prepared R1 index; technical sealing still pending');raise SystemExit()
gates={}
build=root/plan['build']
for kind in ['Generate','Editor','Game']:assert read(build/(kind+'.command.json'))['sourceSHA']==source and read(build/(kind+'.result.json'))['ExitCode']==0
gates['build']=dict(status='PASS',run=build.relative_to(root).as_posix())
scope=read(run/'GameplayPreservation.json');assert scope['completed'] and scope['source']==source
gates['gameplayPreservation']=dict(status='PASS',unchangedBlobs=len(scope['unchanged']),run='Artifacts/U03/D/R1/GameplayPreservation.json')
auto=root/plan['automation'];tests=read(auto/'result.json');assert tests['sourceSHA']==source and tests['executed']==140 and tests['failed']==0
assert read(auto/'process.json')['moduleSHA256'].lower()==sha(module)
gates['automation']=dict(status='PASS',run=auto.relative_to(root).as_posix(),executed=140,failed=0,tests=tests['tests'])
pr=root/plan['package'];assert read(pr/'Package.command.json')['sourceSHA']==source and read(pr/'Package.result.json')['ExitCode']==0
gates['package']=dict(status='PASS',run=pr.relative_to(root).as_posix())
smoke=read(root/plan['smoke']/'results.json');assert len(smoke)==3 and all(v['passed'] and v['sourceSHA']==source for v in smoke)
gates['smoke']=dict(status='PASS',run=plan['smoke'],maps=3)
assets=read(root/plan['assets']/'result.json');assert assets['completed'] and len(assets['blueprints'])==16 and not assets['missing']
gates['assets']=dict(status='PASS',run=plan['assets'],blueprints=16)
vis=read(root/plan['visibility']/'visibility.json');assert vis['completed'] and len(vis['checks'])==20 and all(v['result']=='PASS' for v in vis['checks']) and all(v['sourceSHA']==source for v in vis['processes'])
gates['visibility']=dict(status='PASS',run=plan['visibility'],checks=20,loopbackWarnings=vis['warnings'])
for label,name,count in [('combat','input.json',24),('target','input.json',15),('regression','regression.json',15)]:
 folder=root/plan[label];v=read(folder/name);assert v['completed'] and v['process']['sourceSHA']==source and len(v['checks'])==count and all(c['result']=='PASS' for c in v['checks']),label
 gates[label]=dict(status='PASS',run=plan[label],checks=count)
 if label in ['combat','regression']:
  sound=read(folder/'audio.json');assert sound['inputExitCode']==0 and sound['isLoopback'] and sound['parry660'] and sound['parry990After660'];gates[label]['loopbackWarnings']=sound['warnings']
net=root/plan['network'];n=read(net/'network.json');assert n['completed'] and len(n['checks'])==26 and all(c['result']=='PASS' for c in n['checks'])
ind=read(net/'network-independent.json');assert ind['completed'] and len(ind['checks'])==41
profile=read(net/'profile.json');assert profile['completed'] and all(p['source']==source for p in profile['processes'])
audit=read(net/'feedback-r1-audit.json');assert audit['completed'] and all(c['result']=='PASS' for c in audit['checks'])
assert (root/plan['networkSession']/'editor-restored-verified.json').exists()
gates['network']=dict(status='PASS',run=net.relative_to(root).as_posix(),checks=26,independentComparisons=41,feedbackChecks=len(audit['checks']),profile=profile)
guards=read(run/'LAUNCH-GUARDS.json');assert guards['completed'] and guards['manifestRestoredByteForByte'] and guards['packageIndexRestoredByteForByte']
launchers=read(run/'LauncherRuntime.json');assert launchers['completed'] and launchers['sourceSHA']==source
assert launchers['sdkLogPreservation']['completed'] and read(run/'SDKGuardTests.json')['completed']
assert read(run/'ConcurrentSolo.json')['completed'] and read(run/'OccupiedPort.json')['completed']
assert read(root/plan['regression']/'frequency-bands.json')['completed']
gates['launchers']=dict(status='PASS',guards=guards,runtime=launchers)
history=read(run/'InheritedEvidenceAudit.json');assert all(not history[k]['mismatches'] for k in ['raw','published','package'])
protected=read(run/'Preservation.json');assert all(sha(root/p['path']).lower()==p['sha256'].lower() for p in protected['files'])
extensions={'.log','.json','.jsonl','.mp4','.wav','.png','.py','.ps1','.csv'}
raws=[f for f in run.rglob('*') if f.is_file() and f.suffix.lower() in extensions]
folders=[f for f in (base/'Runs').iterdir() if f.is_dir() and ((f.name.startswith('Build-20261116-') and f.name>='Build-20261116-132059') or (f.name.startswith('Package-20261116-') and f.name>='Package-20261116-132637'))]
for folder in folders:
 raws += [f for f in folder.rglob('*') if f.is_file() and 'Archive' not in f.parts and f.suffix.lower() in extensions]
for session in launchers['sessions']:
 raws += [f for f in (root/session).rglob('*') if f.is_file() and f.suffix.lower() in extensions]
files=[];warnings=[]
for f in sorted(set(raws)):
 out=dest/'Runs'/f.relative_to(base);out.parent.mkdir(parents=True,exist_ok=True);redactions=0;encoding='binary'
 if f.suffix.lower() in {'.mp4','.wav','.png'}:shutil.copyfile(f,out)
 else:
  raw=f.read_bytes();encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig';text=raw.decode(encoding,errors='strict')
  text,redactions=re.subn(r'''(?im)(security[ _-]*token["']?\s*[:=]\s*["']?|Authorization\s*:\s*Bearer\s+|-AUTH_PASSWORD=)[^\s,"'}]+''',r'\1[REDACTED]',text)
  matches=[l for l in text.splitlines() if re.search(r'Warning:|Error:|warning C|error C|Traceback|RuntimeWarning',l)]
  if matches:warnings.append(dict(raw=f.relative_to(root).as_posix(),count=len(matches),examples=list(dict.fromkeys(matches))[:30]))
  out=out.with_suffix(out.suffix+'.gz');out.write_bytes(gzip.compress(text.encode('utf-8'),mtime=0))
 files.append(dict(raw=f.relative_to(root).as_posix(),rawSHA256=sha(f),published=out.relative_to(root).as_posix(),publishedSHA256=sha(out),encoding=encoding,redactions=redactions))
write(dest/'WARNINGS.json',warnings)
manifest.update(status='READY_FOR_REVIEW',gates=gates,files=files,warnings='Evidence/D-R1/WARNINGS.json',protectedFiles=protected,history=history,inherited=dict(D='Evidence/D/MANIFEST.json',DStatus='NOT ACCEPTED at f6d0f68; historical technical evidence only',C2='Docs/U03/Evidence/C2/MANIFEST.json'),failedRuns=['Build-20261116-132059: fixture replication compile error','Visibility-01: attached camera rotated with pawn','Visibility-02: chased target/strafe overshoot invalid partial-wall setup','Visibility-03: harness incorrectly required a log for an event consumed before scope/clock readiness'],limits=['READY_FOR_REVIEW only; no ACCEPTED/merge/U03 closure/U04','Blockout/mannequin art; separate user visual/feel gate','Review resolution/pools/render profile preserved, not graphics/performance acceptance','Loopback discontinuity warnings retained; no sample-exact audio timing claim','No arbitrary packet injection; native duplicate/late/life tests plus real reconnect','Original mutable clone DLL was rebuilt; historical D hash is not a claim that the clone still contains that DLL; old published/raw/package evidence remains verified'])
manifest['failedRuns'] += ['Regression-01: harness pressed in early recovery before the existing 150ms buffer could reach action end','Visibility-05: fresh visible feedback consumed ahead of clock; presentation defect fixed by clock eligibility in final source','Build-20261116-140355: ambiguous precision assertion overload; fixed in final source']
manifest['failedRuns'].append('LauncherAttempt01: invalid helper setup pressed disabled Resume after authority Lost; retried via actual Retry/Resume without source change')
manifest['failedRuns'].append('SDKRestoreAttempt01: new log-preservation guard initially refused restoration; final guard checks live OS process identity; focused stale-CIM/idempotency checks and real restoration pass')
manifest['binaryCheckpoint']=read(run/'BinaryCheckpoint.json')
write(dest/'MANIFEST.json',manifest);print(json.dumps(dict(status=manifest['status'],source=source,files=len(files),packageFiles=len(index))))
