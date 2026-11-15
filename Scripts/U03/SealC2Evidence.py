"""Validate final C2 gates and publish hashed/redacted evidence; preserve every raw run."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,os,re,shutil,subprocess
p=argparse.ArgumentParser()
for n in ['source','build','automation','package','smoke','combat','route','target','network','session']:p.add_argument('--'+n,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2];base=root/'Artifacts/U03/C2';dest=root/'Docs/U03/Evidence/C2';clone=base/'Source'
def read(f):return json.loads(Path(f).read_text(encoding='utf-8-sig'))
def write(f,v):Path(f).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as s:
  for block in iter(lambda:s.read(1048576),b''):h.update(block)
 return h.hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
source=git('rev-parse',a.source);assert subprocess.check_output(['git','-C',str(clone),'rev-parse','HEAD'],text=True).strip()==source
assert not git('diff','--name-only',source,'HEAD','--','Source','Content','Config')
assert not git('diff','--name-only','--','Source','Content')
assert not subprocess.check_output(['git','-C',str(clone),'status','--porcelain','--untracked-files=no'],text=True).strip()
for n in ['build','automation','package','smoke','combat','route','target','network','session']:
 f=Path(getattr(a,n)).resolve();assert f.is_relative_to(base.resolve());setattr(a,n,f)
gates={}
for kind in ['Generate','Editor','Game']:
 assert read(a.build/(kind+'.command.json'))['sourceSHA']==source and read(a.build/(kind+'.result.json'))['ExitCode']==0
gates['build']=str(a.build.relative_to(root))
auto=read(a.automation/'result.json');process=read(a.automation/'process.json')
assert auto['sourceSHA']==source and auto['failed']==0 and process['moduleSHA256'].lower()==sha(clone/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll')
expected=set()
for f in (clone/'Source/AnimeMMORPG/Tests').glob('*.cpp'):expected.update(re.findall(r'IMPLEMENT_SIMPLE_AUTOMATION_TEST\(\s*\w+\s*,\s*"(AnimeMMORPG\.[^"]+)"',f.read_text(encoding='utf-8-sig')))
assert set(auto['tests'])==expected and auto['executed']==len(expected)
gates['automation']=dict(run=str(a.automation.relative_to(root)),executed=auto['executed'],failed=0,c2=len([x for x in expected if x.startswith('AnimeMMORPG.U03.C2.')]))
pkg_run=a.package.parent.parent;assert read(pkg_run/'Package.command.json')['sourceSHA']==source and read(pkg_run/'Package.result.json')['ExitCode']==0
gates['package']=str(pkg_run.relative_to(root));smoke=read(a.smoke/'results.json');assert len(smoke)==3 and all(x['passed'] and x['sourceSHA']==source for x in smoke);gates['smoke']=str(a.smoke.relative_to(root))
for kind,folder,name in [('combat',a.combat,'input.json'),('route',a.route,'input.json'),('target',a.target,'input.json'),('network',a.network,'network.json')]:
 data=read(folder/name);assert data['completed'] and read(folder/'process-result.json')['exitCode']==0 and all(x['result']=='PASS' for x in data['checks'])
 records=data.get('processes',[data.get('process')]);assert all(r['sourceSHA']==source for r in records)
 assert data.get('externalInputMethodRestored',True)
 command=read(folder/'command.json');assert sha(folder/'harness'/Path(command['arguments'][2]).name).lower()==command['scriptSHA256'].lower()
 gates[kind]=dict(run=str(folder.relative_to(root)),checks=len(data['checks']))
 if kind!='network':
  session=Path(data['process']['userDir']);assert (session/'editor-minimized-verified.json').exists() and (session/'editor-restored-verified.json').exists()
independent=read(a.network/'network-independent.json');assert independent['completed'] and independent['sourceSHA']==source and all(x['result']=='PASS' for x in independent['checks']);gates['network']['independentComparisons']=len(independent['checks'])
assert (a.session/'editor-minimized-verified.json').exists() and (a.session/'editor-restored-verified.json').exists()
guards=read(base/'Audit/LAUNCH-GUARDS.json');assert guards['completed'] and guards['manifestRestoredByteForByte'] and guards['packageIndexRestoredByteForByte'] and all(x['result']=='PASS' for x in guards['checks']);gates['launcherGuards']=dict(checks=len(guards['checks']),run='Artifacts/U03/C2/Audit/LAUNCH-GUARDS.json')
before=read(base/'Preflight/RESULT.json');assert sha(root/'Config/DefaultEngine.ini').lower()==before['privateConfigSHA256'].lower()
dest.mkdir(parents=True,exist_ok=True);package=[]
for f in sorted(a.package.rglob('*')):
 if f.is_file():package.append(dict(path=f.relative_to(a.package).as_posix(),sha256=sha(f),bytes=f.stat().st_size))
with (dest/'PACKAGE.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['path','sha256','bytes']);w.writeheader();w.writerows(package)
def decode(b):
 if b.startswith((b'\xff\xfe',b'\xfe\xff')):return b.decode('utf-16'),'utf-16-bom'
 if b.startswith(b'\xef\xbb\xbf'):return b.decode('utf-8-sig'),'utf-8-bom'
 if len(b)>4 and b[1::2].count(0)>len(b[1::2])//3:return b.decode('utf-16-le'),'utf-16-le'
 return b.decode('utf-8'),'utf-8'
files=[];warnings=[];traces=[]
def publish(f,relative):
 out=dest/'Runs'/relative;out.parent.mkdir(parents=True,exist_ok=True);encoding='binary';redactions=0
 if f.suffix.lower() in ['.mp4','.png','.wav']:shutil.copyfile(f,out)
 else:
  text,encoding=decode(f.read_bytes());text,redactions=re.subn(r'''(?im)(security[ _-]*token["']?\s*[:=]\s*["']?|Authorization\s*:\s*Bearer\s+)[^\s,"'}]+''',r'\1[REDACTED]',text)
  out=out.with_suffix(out.suffix+'.gz');out.write_bytes(gzip.compress(text.encode('utf-8'),mtime=0));assert gzip.decompress(out.read_bytes()).decode('utf-8')==text
  if f.suffix.lower()=='.log':
   for line in text.splitlines():
    if re.search(r'Warning:|warning [A-Z]|Error:|error C\d',line):warnings.append(dict(run=relative.as_posix(),line=line))
    if any(x in line for x in ['Test Completed.','Automation Test Queue Empty','C2_LOS','U03C2_RETRY','Live coding succeeded','Failed to compile']):traces.append(dict(run=relative.as_posix(),line=line))
 files.append(dict(path=out.relative_to(dest).as_posix(),rawPath=f.relative_to(root).as_posix(),rawSHA256=sha(f),publishedSHA256=sha(out),sourceEncoding=encoding,redactions=redactions))
for current,dirs,names in os.walk(base):
 dirs[:]=[n for n in dirs if n not in ['Source','Archive']]
 for name in sorted(names):
  f=Path(current)/name
  if f.suffix.lower() in ['.log','.json','.jsonl','.sha256','.txt','.mp4','.png','.csv','.md','.py','.ps1']:publish(f,f.relative_to(base))
for entry in before['launchers']:
 for value in entry['files']:
  f=root/value['path'];assert sha(f)==value['sha256'];publish(f,Path('Prerequisite')/entry['stage']/f.relative_to(root/'Artifacts/U03'/entry['stage']))
cleanup=root/'Docs/Maintenance/Cleanup-20261114-114536'
for name in ['AFTER.json','REPORT.md','VERIFY.log','MANIFEST-CROSSCHECK.json']:publish(cleanup/name,Path('Prerequisite/Cleanup')/name)
binaries=[dict(path=f.relative_to(root).as_posix(),sha256=sha(f)) for f in [clone/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll',clone/'Binaries/Win64/AnimeMMORPG.exe']]
assets=[dict(path=f.relative_to(root).as_posix(),sha256=sha(f)) for f in [root/'Content/AnimeMMORPG/Maps/L_CharacterCombatLab.umap',root/'Content/AnimeMMORPG/Maps/L_NetworkLab.umap']]
manifest=dict(status='READY_FOR_REVIEW',base='8d1d2c37bc6259a58dd110a63f4fc1d3963b058f',source=source,packageRelativePath=a.package.relative_to(root).as_posix(),packageFiles=len(package),engineExeSHA256=sha('D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'),binaries=binaries,assets=assets,gates=gates,privateConfigUnchanged=True,files=files,feelAcceptance='PENDING USER REVIEW; B2/C1 not user-playtested',noAcceptanceOrMerge=True,sourceFiles=[dict(path=f,gitBlob=git('rev-parse',source+':'+f)) for f in git('diff','--name-only','8d1d2c3',source,'--','Source','Content','Config').splitlines()])
write(dest/'MANIFEST.json',manifest);write(dest/'WARNINGS.json',warnings);write(dest/'TEST-TRACES.json',traces);write(dest/'ENCODING-VERIFICATION.json',dict(files=len(files),strictDecode=True,roundTripVerified=True,rawPreserved=True));print(json.dumps(dict(files=len(files),packageFiles=len(package),gates=gates)))
