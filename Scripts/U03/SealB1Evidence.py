"""Publish strict decoded/redacted B1 evidence, retaining all raw runs locally."""
from pathlib import Path
import hashlib,json,gzip,re,subprocess,shutil
root=Path(__file__).resolve().parents[2];base=root/'Artifacts/U03/B1';dest=root/'Docs/U03/Evidence/B1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(root),*a],text=True).strip()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def decode(b):
 if b.startswith((b'\xff\xfe',b'\xfe\xff')):return b.decode('utf-16'),'utf-16-bom'
 if b.startswith(b'\xef\xbb\xbf'):return b.decode('utf-8-sig'),'utf-8-bom'
 if len(b)>4 and b[1::2].count(0)>len(b[1::2])//3:return b.decode('utf-16-le'),'utf-16-le'
 return b.decode('utf-8'),'utf-8'
manifest=json.loads((dest/'MANIFEST.json').read_text(encoding='utf-8'));files=[];warnings=[];traces=[]
for p in sorted(base.rglob('*')):
 if not p.is_file() or 'Source' in p.relative_to(base).parts or 'Archive' in p.relative_to(base).parts:continue
 if p.suffix.lower() not in ('.log','.json','.jsonl','.sha256','.mp4','.png'):continue
 rel=p.relative_to(base);out=dest/'Runs'/rel;out.parent.mkdir(parents=True,exist_ok=True);enc='binary';n=0
 if p.suffix.lower() in ('.mp4','.png'):shutil.copyfile(p,out)
 else:
  text,enc=decode(p.read_bytes());clean,n=re.subn(r'(?im)(SecurityToken\s*[=:]\s*|Authorization\s*:\s*Bearer\s+)[^\s,\"}]+',r'\1[REDACTED]',text)
  out=out.with_suffix(out.suffix+'.gz');out.write_bytes(gzip.compress(clean.encode('utf-8'),mtime=0));assert gzip.decompress(out.read_bytes()).decode('utf-8')==clean
  if p.suffix=='.log':
   for line in clean.splitlines():
    if re.search(r'Warning:|warning [A-Z]|Error:|error C\d',line):warnings.append({'run':str(rel),'line':line})
    if any(x in line for x in ['Test Completed.','Automation Test Queue Empty','U03B1_TRACE','U03A0_TRACE']):traces.append({'run':str(rel),'line':line})
 files.append({'path':str(out.relative_to(dest)),'rawPath':str(p.relative_to(root)),'rawSHA256':sha(p),'publishedSHA256':sha(out),'sourceEncoding':enc,'redactions':n,'verifiedDecodedContent':enc!='binary'})
manifest.update(status='READY_FOR_REVIEW',files=files,privateConfigUnchanged=sha(root/'Config/DefaultEngine.ini').upper()==(base/'Audit/CONFIG-BEFORE.sha256').read_text().strip().upper(),sourceFiles=[{'path':p,'gitBlob':git('rev-parse',manifest['source']+':'+p)} for p in git('diff','--name-only',manifest['base'],manifest['source'],'--','Source','Content','Config').splitlines()])
for p in files:assert sha(dest/p['path'])==p['publishedSHA256']
write(dest/'MANIFEST.json',manifest);write(dest/'WARNINGS.json',warnings);write(dest/'TEST-TRACES.json',traces);write(dest/'ENCODING-VERIFICATION.json',{'files':len(files),'strictDecode':True,'roundTripVerified':True,'rawFilesPreserved':True})
print(json.dumps({'files':len(files),'privateConfigUnchanged':manifest['privateConfigUnchanged'],'warnings':len(warnings)}))
