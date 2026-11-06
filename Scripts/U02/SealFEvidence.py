"""Seal full-build cold MCP tests and actual dedicated/two-client evidence; reject private tokens."""
import argparse,json,hashlib,gzip,re,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser()
for n in ['build','tests','session','evidence']:p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.session=a.session.resolve();root=Path(__file__).resolve().parents[2];out=a.evidence.resolve();assert out.is_relative_to(root/'Docs/U02/Evidence');out.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,d):(out/n).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*v):return subprocess.check_output(['git','-C',str(root),*v],text=True).strip()
final=load(a.tests/'result.json');proc=load(a.tests/'process.json');source=final['sourceSHA'];assert final['failed']==0 and final['executed']>0 and source==proc['sourceSHA'] and not (a.tests/'INVALID.txt').exists();mcp=load(a.tests/'mcp-results.json');logs=json.loads(mcp['content'][0]['text'])['returnValue'];completed=[dict(result=m[1],name=m[2]) for l in logs if (m:=re.search(r'Test Completed\. Result=\{([^}]+)\}.*Path=\{([^}]+)\}',l))];assert len(completed)==final['executed'] and all(t['result']=='Success' for t in completed) and {t['name'] for t in completed}==set(final['tests']);assert any('Automation Test Queue Empty '+str(final['executed'])+' tests performed' in l for l in logs)
module=Path(proc['module']);assert sha(module)==proc['moduleSHA256'].lower();assert not git('diff','--name-only',source,'HEAD','--','Source','Content','Config','Plugins','AnimeMMORPG.uproject');assert sha(root/'Config/DefaultEngine.ini')==load(root/'Artifacts/U02/F/private-config-before.json')['sha256'];assert b'SecurityToken=' not in subprocess.check_output(['git','-C',str(root),'show','HEAD:Config/DefaultEngine.ini'])
primary=load(a.session/'Capture/input.json');controls=load(a.session/'Controls/input.json');audit=load(a.session/'ASSERTIONS-F.json');disconnect=load(a.session/'Disconnect/ASSERTIONS.json');assert primary['completed'] and primary['failed']==0 and audit['failed']==0 and audit['sourceSHA']==source and controls['completed'] and disconnect['completed'];records=load(a.session/'all-processes.json');assert len(records)==4 and all(r['sourceSHA']==source and r['moduleSHA256'].lower()==sha(module) for r in records);restored=load(a.session/'EDITOR-RESTORED.json');assert restored and all(r['alive'] and r['restored'] for r in restored)
build={n:dict(result=load(a.build/(n+'.result.json')),command=load(a.build/(n+'.command.json'))) for n in ['Generate','Editor','Game']};assert all(v['result']['ExitCode']==0 for v in build.values());write('BUILD-RESULTS.json',build);write('AUTOMATION-RESULTS.json',dict(**final,perTest=completed));write('MCP-PROCESS.json',proc);shutil.copyfile(a.tests/'mcp-results.json',out/'MCP-RESULTS.json');write('PROCESS-MANIFEST.json',records);write('RUNTIME-ASSERTIONS.json',audit)
for name in ['processes.json','all-processes.json','server-timer.json','original-editor-windows.json','EDITOR-RESTORED.json']:shutil.copyfile(a.session/name,out/name)
for label,folder in [('Network',a.session/'Capture'),('Controls',a.session/'Controls'),('Disconnect',a.session/'Disconnect'),('Controls-Failed-Schedule',a.session/'Controls-Failed-Schedule')]:
 for f in folder.iterdir():
  if f.is_file():shutil.copyfile(f,out/(label+'-'+f.name))
for f in a.session.glob('ASSERTIONS-F-Failed-*.json'):shutil.copyfile(f,out/f.name)
history=[];warnings={};raws=[]
paths=list((root/'Artifacts/U02/F').glob('Build-*/*.log'))+list((root/'Artifacts/U02/F').glob('MCPTests-*/Editor.log'))+list((root/'Artifacts/U02/F').glob('*.log'))
for run in sorted((root/'Artifacts/U02/F').glob('Session-*')):
 for f in run.rglob('*'):
  if f.is_file() and f.name.endswith(('.log','.jsonl')):paths.append(f)
 if run==a.session:continue
 for folder in ['Capture','Disconnect','Controls']:
  q=run/folder
  if q.exists():
   for f in q.iterdir():
    if f.is_file():shutil.copyfile(f,out/('History-'+run.name+'-'+folder+'-'+f.name))
for d in sorted((root/'Artifacts/U02/F').glob('MCPTests-*')):
 item=dict(run=d.name,invalid=(d/'INVALID.txt').read_text(encoding='utf-8-sig') if (d/'INVALID.txt').exists() else None,result=load(d/'result.json') if (d/'result.json').exists() else None);history.append(item)
for f in sorted(set(paths)):
 raw=f.read_bytes();txt=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig',errors='replace');assert not re.search(r'(?im)\bSecurityToken\s*=\s*[^\s\r\n]+|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----',txt),f
 name='Raw-'+str(f.relative_to(root/'Artifacts/U02/F')).replace('\\','-').replace('/','-')+'.gz'
 with gzip.open(out/name,'wb') as stream:stream.write(raw)
 raws.append(dict(file=name,original=str(f),rawSHA256=sha(f),sha256=sha(out/name)))
 w=[l for l in txt.splitlines() if re.search(r': Warning:|warning C\d+|Error:|error C\d+|not a preferred|newer than latest preferred',l)]
 if w:warnings[str(f)]=w
write('RAW-LOGS.json',raws);write('RUN-HISTORY.json',history);write('WARNINGS.json',warnings)
write('MANIFEST.json',dict(status='READY_FOR_REVIEW',branch='u02/f-dedicated-two-clients',sourceSHA=source,baseSHA=git('rev-parse','main'),utc=datetime.now(timezone.utc).isoformat(),moduleSHA256=sha(module),engineExeSHA256=proc['exeSHA256'].lower(),gameBuildExeSHA256=sha(module.parent/'AnimeMMORPG.exe'),buildRun=a.build.name,testRun=a.tests.name,sessionRun=a.session.name,automationExecuted=final['executed'],networkInputAssertions=primary['passed'],supplementalAssertions=audit['passed'],sourceEqualsHandoffRuntime=True,privateConfigByteUnchanged=True,originalEditorRestored=True,serverPackaged=False,networkBadConditionsAccepted=False,reviewAccepted=False,cloneRelativePath='Artifacts/U02/F/Source',scope='Dedicated Editor server and two rendered Editor-game clients; E Windows package accepted separately, no packaged Server/U05/U03'))
(out/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n');files=sorted(f for f in out.iterdir() if f.is_file() and f.name!='EVIDENCE-SHA256.json');write('EVIDENCE-SHA256.json',[dict(file=f.name,bytes=f.stat().st_size,sha256=sha(f)) for f in files]);print(json.dumps(dict(sourceSHA=source,automation=final['executed'],network=primary['passed'],supplemental=audit['passed'],evidenceFiles=len(files))))
