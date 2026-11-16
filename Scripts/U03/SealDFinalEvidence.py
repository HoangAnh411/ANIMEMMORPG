"""Validate final D gates and seal evidence. Never builds, changes gameplay or asserts acceptance."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,re,shutil,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--network',type=Path,required=True);p.add_argument('--session',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];base=root/'Artifacts/U03/D';dest=root/'Evidence/D';clone=base/'Source'
a.network=a.network.resolve();a.session=a.session.resolve()
assert a.network.is_relative_to(base.resolve()) and a.session.is_relative_to(base.resolve())
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=subprocess.check_output(['git','-C',str(clone),'rev-parse','HEAD'],text=True).strip()
assert source=='9da1b43aa8ed49bd83226f76fe2b816db0d64f24'
subprocess.run(['git','-C',str(root),'diff','--exit-code',source,'--','Source','Content'],check=True,stdout=subprocess.DEVNULL)
build=base/'Runs/Build-20261115-220654';auto=base/'Runs/MCPTests-20261115-221026';package_run=base/'Runs/Package-20261115-221157';package=package_run/'Archive/Windows'
gates={}
for kind in ['Generate','Editor','Game']:
 assert read(build/(kind+'.command.json'))['sourceSHA']==source and read(build/(kind+'.result.json'))['ExitCode']==0
gates['build']=dict(status='PASS',run=str(build.relative_to(root)))
tests=read(auto/'result.json');assert tests['sourceSHA']==source and tests['failed']==0 and tests['executed']==137
module=clone/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll';engine=Path('D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe')
proc=read(auto/'process.json');assert proc['moduleSHA256'].lower()==sha(module) and proc['exeSHA256'].lower()==sha(engine)
gates['automation']=dict(status='PASS',run=str(auto.relative_to(root)),executed=137,failed=0,tests=tests['tests'])
assert read(package_run/'Package.command.json')['sourceSHA']==source and read(package_run/'Package.result.json')['ExitCode']==0
gates['package']=dict(status='PASS',run=str(package_run.relative_to(root)))
smoke=base/'Runs/Smoke-20261115-221300';s=read(smoke/'results.json');assert len(s)==3 and all(x['passed'] and x['sourceSHA']==source for x in s)
gates['smoke']=dict(status='PASS',run=str(smoke.relative_to(root)),maps=3)
assets=base/'Runs/Assets-20261115-221349';assert read(assets/'process.json')['sourceSHA']==source and read(assets/'result.json')['completed']
gates['assets']=dict(status='PASS',run=str(assets.relative_to(root)),blueprints=len(read(assets/'result.json')['blueprints']))
for label,folder,name in [('combat','FinalCombat-20261115-221500','input.json'),('route','FinalRoute-20261115-221600','input.json'),('lifecycle','FinalLifecycle-20261115-222100','lifecycle.json'),('reopen','FinalReopen-20261116-115900','lifecycle.json'),('target','FinalTarget-20261116-120000','input.json'),('regression','FinalRegression-20261116-120100','regression.json')]:
 run=base/'Runs'/folder;value=read(run/name);assert value['completed'] and value['process']['sourceSHA']==source,(label,'incomplete/wrong source')
 assert all(x['result']=='PASS' for x in value.get('checks',[])),label
 gates[label]=dict(status='PASS',run=str(run.relative_to(root)),checks=len(value.get('checks',[])))
 if label=='lifecycle':assert len(value['cycles'])==5;gates[label]['cycles']=5
 if label in ['combat','regression']:
  audio=read(run/'audio.json');assert audio['inputExitCode']==0 and audio['isLoopback'] and audio['parry660'] and audio['parry990After660']
  gates[label]['loopbackWarnings']=len(audio.get('warnings',[]))
 if label=='regression':assert value['onScreenDebugMessagesDisabled']
net=read(a.network/'network.json');assert net['completed'] and all(x['result']=='PASS' for x in net['checks']) and all(x['sourceSHA']==source for x in net['processes'])
ind=read(a.network/'network-independent.json');assert ind['completed'] and ind['sourceSHA']==source
assert read(a.network/'profile.json')['completed']
assert read(a.network/'feedback-audit.json')['completed']
assert (a.session/'editor-restored-verified.json').exists()
gates['network']=dict(status='PASS',run=str(a.network.relative_to(root)),checks=len(net['checks']),independentComparisons=len(ind['checks']),session=str(a.session.relative_to(root)),profile=str((a.network/'profile.json').relative_to(root)))
guards=read(base/'Audit/LAUNCH-GUARDS.json');assert guards['completed'] and guards['manifestRestoredByteForByte'] and guards['packageIndexRestoredByteForByte']
gates['launchers']=dict(status='PASS',checks=len(guards['checks']),run=str((base/'Audit/LAUNCH-GUARDS.json').relative_to(root)))
saved=read(base/'Runs/LauncherSave-20261116-121900/lifecycle.json');reopened=read(base/'Runs/LauncherReopen-20261116-122000/lifecycle.json')
assert saved['completed'] and reopened['completed'] and reopened['defaultsRestoredByUI']
assert saved['process']['userDir']==reopened['process']['userDir'] and 'UserSettings' in saved['process']['userDir']
assert read(base/'Audit/CONCURRENT-SOLO.json')['passed'] and read(base/'Audit/OCCUPIED-PORT.json')['passed']
net_records=read(a.session/'all-processes.json');old_a,new_a=[x for x in net_records if x['role']=='ClientA'];b=next(x for x in net_records if x['role']=='ClientB')
assert old_a['userDir']==new_a['userDir'] and old_a['userDir']!=b['userDir'] and old_a['log']!=new_a['log']
gates['launchers'].update(stablePreferences=True,reconnectRetainsPreferenceDirectory=True,concurrentSoloRefused=True,occupiedPortRefused=True,soloSaveRun='Artifacts/U03/D/Runs/LauncherSave-20261116-121900',soloReopenRun='Artifacts/U03/D/Runs/LauncherReopen-20261116-122000')
dest.mkdir(parents=True,exist_ok=True);index=[]
for f in sorted(package.rglob('*')):
 if f.is_file():index.append(dict(path=f.relative_to(package).as_posix(),sha256=sha(f),bytes=f.stat().st_size))
with (dest/'PACKAGE.csv').open('w',encoding='utf-8',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=['path','sha256','bytes']);writer.writeheader();writer.writerows(index)
files=[];warnings=[]
roots=[x for x in base.iterdir() if x.is_dir() and x.name!='Source']
raws=[x for folder in roots for x in folder.rglob('*') if x.is_file() and 'Archive' not in x.parts and x.suffix.lower() in {'.log','.json','.jsonl','.mp4','.wav','.png','.py','.ps1','.csv'}]
raws += list(base.glob('*.log'))
for f in sorted(set(raws)):
 relative=f.relative_to(base);out=dest/'Runs'/relative;out.parent.mkdir(parents=True,exist_ok=True);redactions=0;encoding='binary'
 if f.suffix.lower() in {'.mp4','.wav','.png'}:shutil.copyfile(f,out)
 else:
  raw=f.read_bytes();encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig';text=raw.decode(encoding,errors='strict')
  text,n=re.subn(r'''(?im)(security[ _-]*token["']?\s*[:=]\s*["']?|Authorization\s*:\s*Bearer\s+|-AUTH_PASSWORD=)[^\s,"'}]+''',r'\1[REDACTED]',text);redactions+=n
  matches=[line for line in text.splitlines() if re.search(r'Warning:|Error:|warning C|error C|Traceback|RuntimeWarning',line)]
  if matches:warnings.append(dict(raw=str(f.relative_to(root)),count=len(matches),examples=list(dict.fromkeys(matches))[:40]))
  out=out.with_suffix(out.suffix+'.gz');encoded=text.encode('utf-8');out.write_bytes(gzip.compress(encoded,mtime=0));assert gzip.decompress(out.read_bytes())==encoded
 files.append(dict(raw=str(f.relative_to(root)),rawSHA256=sha(f),published=str(out.relative_to(root)),publishedSHA256=sha(out),encoding=encoding,redactions=redactions))
write(dest/'WARNINGS.json',warnings)
assets_list=[]
for f in sorted((root/'Content/AnimeMMORPG/U03/Animation').rglob('*.uasset')):assets_list.append(dict(path=str(f.relative_to(root)),sha256=sha(f),provenance='D original procedural pose' if '/D/' in f.as_posix() else 'extended existing graph' if f.name=='ABP_U03.uasset' else 'inherited unchanged clip/montage'))
for path in ['U01/Animation/SK_U01.uasset','U01/Animation/PA_U01_RightCarry.uasset','U01/Animation/PA_U01_RightGrip.uasset','U02/Animation/A_U02_Attack1.uasset','U02/Animation/AM_U02_Attack1.uasset']:
 f=root/'Content/AnimeMMORPG'/path;assert f.exists();assets_list.append(dict(path=str(f.relative_to(root)),sha256=sha(f),provenance='inherited unchanged'))
manifest=dict(status='READY_FOR_REVIEW',source=source,binarySource=source,base='bc3a9955a8c0ecc1cb7f0d43dce13300c9664ac9',branch='u03/d-integration',packageRelativePath=str(package.relative_to(root)),packageFiles=len(index),packageIndexSHA256=sha(dest/'PACKAGE.csv'),engineExeSHA256=sha(engine),engine=read(Path('D:/Software/UE_5.8/Engine/Build/Build.version')),toolchain=dict(compiler='MSVC14.51.36260',sdk='10.0.26100.0',python=sys.version),binaries=[dict(path=str(module),sha256=sha(module)),dict(path=str(package/'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'),sha256=sha(package/'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'))],gates=gates,files=files,assets=assets_list,warnings='Evidence/D/WARNINGS.json',inherited=dict(c2='Docs/U03/Evidence/C2/MANIFEST.json',initialD='Evidence/D/Checkpoints/INITIAL-MANIFEST.json',note='Inherited results are not final D runs; all listed final gates use source above'),protectedFiles={str(f.relative_to(root)):sha(f) for f in [root/'Config/DefaultEngine.ini',root/'AnimeMMORPG.uproject']},limits=['Blockout/mannequin; product anime art deferred','Technical review separate from user feel/closure permission','Dedicated Editor only; no packaged Server','Review rendering profile is not U04 performance/graphics acceptance','30/60/120 model/world steps are not measured render FPS','Loopback/capture warnings and all failed/pre-final runs retained'])
manifest['audioProvenance']=dict(source='Source/AnimeMMORPG/U03/U03Presentation.cpp',sourceSHA256=sha(root/'Source/AnimeMMORPG/U03/U03Presentation.cpp'),type='original synthetic PCM blockout; existing parry expression reused',sampleRate=24000,channels=1,bits=16,durationSeconds=.24,frequencies=dict(hit=440,block=220,parry=[660,990],miss=160,feint='880 downward chirp',interrupt='330 upward chirp',guardBreak=110,escape=1320),note='Evidence WAV is 48kHz stereo output-loopback, not microphone or asset input')
write(dest/'MANIFEST.json',manifest);print(json.dumps(dict(status=manifest['status'],source=source,files=len(files),packageFiles=len(index),gates=len(gates))))
