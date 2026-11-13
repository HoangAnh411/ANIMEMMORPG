"""Validate gates and publish strict decoded/redacted C1 evidence; raw runs remain untouched."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,re,shutil,subprocess
p=argparse.ArgumentParser()
for name in ['source','package','build','automation','input','network','dodge','session','smoke']:p.add_argument('--'+name,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2];base=root/'Artifacts/U03/C1';dest=root/'Docs/U03/Evidence/C1'
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
source=git('rev-parse',a.source);clone=base/'Source';assert subprocess.check_output(['git','-C',str(clone),'rev-parse','HEAD'],text=True).strip()==source
assert not git('diff','--name-only',source,'HEAD','--','Source','Content','Config'),'Unverified committed native/content/config changes'
for name in ['package','build','automation','input','network','dodge','session','smoke']:
 value=Path(getattr(a,name)).resolve();assert value.is_relative_to(base.resolve());setattr(a,name,value)
gates={}
for name in ['Generate','Editor','Game']:
 assert read(a.build/(name+'.result.json'))['ExitCode']==0
 assert read(a.build/(name+'.command.json'))['sourceSHA']==source
gates['build']=str(a.build.relative_to(root))
tests=read(a.automation/'result.json');assert tests['sourceSHA']==source and tests['executed']>0 and tests['failed']==0
expected=set()
for f in (clone/'Source/AnimeMMORPG/Tests').glob('*.cpp'):expected.update(re.findall(r'IMPLEMENT_SIMPLE_AUTOMATION_TEST\(\s*\w+\s*,\s*"(AnimeMMORPG\.[^"]+)"',f.read_text(encoding='utf-8-sig')))
assert set(tests['tests'])==expected and tests['executed']==len(expected);gates['automation']={'run':str(a.automation.relative_to(root)),'executed':tests['executed'],'failed':0}
smoke=read(a.smoke/'results.json');assert len(smoke)==3 and all(v['passed'] and v['sourceSHA']==source for v in smoke);gates['smoke']=str(a.smoke.relative_to(root))
for kind,folder,file in [('input',a.input,'input.json'),('network',a.network,'network.json'),('dodgeNetworkRegression',a.dodge,'network.json')]:
 data=read(folder/file);assert data['completed']
 assert all(v.get('result')=='PASS' or v.get('passed') is True for v in data['checks'])
 records=data.get('processes',[data.get('process')]);assert all(v['sourceSHA']==source for v in records)
 gates[kind]={'run':str(folder.relative_to(root)),'checks':len(data['checks'])}


reconnect=read(a.session/'reconnect-result.json');before=read(a.session/'reconnect-before.json')
assert reconnect['completed'] and before['metrics']['combat']['eReady']>0 and reconnect['metrics']['combat']['eReady']==0
assert before['metrics']['combat']['pawnId']!=reconnect['metrics']['combat']['pawnId']
assert reconnect['process']['sourceSHA']==source;gates['reconnect']={'session':str(a.session.relative_to(root)),'checks':len(reconnect['checks'])}
assert (a.session/'editor-restored-verified.json').exists()
assert (a.session/'editor-minimized-verified.json').exists()
solo=Path(read(a.input/'input.json')['process']['userDir']);assert (solo/'editor-restored-verified.json').exists() and (solo/'editor-minimized-verified.json').exists()
assert sha(root/'Config/DefaultEngine.ini').upper()==(base/'Audit/CONFIG-BEFORE.sha256').read_text().strip().upper()
dest.mkdir(parents=True,exist_ok=True)
package_files=[]
for file in sorted(a.package.rglob('*')):
 if file.is_file():package_files.append({'path':file.relative_to(a.package).as_posix(),'sha256':sha(file),'bytes':file.stat().st_size})
assert any(v['path'].endswith('Binaries/Win64/AnimeMMORPG.exe') for v in package_files)
with (dest/'PACKAGE.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['path','sha256','bytes']);w.writeheader();w.writerows(package_files)
def decode(b):
 if b.startswith((b'\xff\xfe',b'\xfe\xff')):return b.decode('utf-16'),'utf-16-bom'
 if b.startswith(b'\xef\xbb\xbf'):return b.decode('utf-8-sig'),'utf-8-bom'
 if len(b)>4 and b[1::2].count(0)>len(b[1::2])//3:return b.decode('utf-16-le'),'utf-16-le'
 return b.decode('utf-8'),'utf-8'
files=[];warnings=[];traces=[]
for file in sorted(base.rglob('*')):
 if not file.is_file() or any(x in file.relative_to(base).parts for x in ['Source','Archive']):continue
 if file.suffix.lower() not in ['.log','.json','.jsonl','.sha256','.mp4','.png','.wav','.txt']:continue
 rel=file.relative_to(base);out=dest/'Runs'/rel;out.parent.mkdir(parents=True,exist_ok=True);enc='binary';redactions=0
 if file.suffix.lower() in ['.mp4','.png','.wav']:shutil.copyfile(file,out)
 else:
  text,enc=decode(file.read_bytes())
  clean,redactions=re.subn(r'''(?im)(security[ _-]*token["']?\s*[:=]\s*["']?|Authorization\s*:\s*Bearer\s+)[^\s,"'}]+''',r'\1[REDACTED]',text)
  out=out.with_suffix(out.suffix+'.gz');out.write_bytes(gzip.compress(clean.encode('utf-8'),mtime=0));assert gzip.decompress(out.read_bytes()).decode('utf-8')==clean
  if file.suffix=='.log':
   for line in clean.splitlines():
    if re.search(r'Warning:|warning [A-Z]|Error:|error C\d',line):warnings.append({'run':str(rel),'line':line})
    if any(v in line for v in ['Test Completed.','Automation Test Queue Empty','U03C1_','U03B1_R1_']):traces.append({'run':str(rel),'line':line})
 files.append({'path':out.relative_to(dest).as_posix(),'rawPath':file.relative_to(root).as_posix(),'rawSHA256':sha(file),'publishedSHA256':sha(out),'sourceEncoding':enc,'redactions':redactions,'verifiedDecodedContent':enc!='binary'})
binaries=[{'path':str(file.relative_to(root)),'sha256':sha(file)} for file in [clone/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll',clone/'Binaries/Win64/AnimeMMORPG.exe']]
manifest={'status':'READY_FOR_REVIEW','base':'f826371b9409c39453e5bd2ed8f8414749f1d34b','source':source,'packageRelativePath':a.package.relative_to(root).as_posix(),'packageFiles':len(package_files),'engineExeSHA256':sha('D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'),'binaries':binaries,'gates':gates,'privateConfigUnchanged':True,'files':files,'sourceFiles':[{'path':file,'gitBlob':git('rev-parse',source+':'+file)} for file in git('diff','--name-only','f826371',source,'--','Source','Content','Config').splitlines()]}
for file in files:assert sha(dest/file['path'])==file['publishedSHA256']
write(dest/'MANIFEST.json',manifest);write(dest/'WARNINGS.json',warnings);write(dest/'TEST-TRACES.json',traces);write(dest/'ENCODING-VERIFICATION.json',{'files':len(files),'strictDecode':True,'roundTripVerified':True,'rawFilesPreserved':True})
print(json.dumps({'files':len(files),'packageFiles':len(package_files),'privateConfigUnchanged':True,'gates':gates}))
