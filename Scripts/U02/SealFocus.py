import argparse,json,hashlib,gzip,re,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--final',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[2];out=root/'Docs/U02/Evidence/Focus';out.mkdir(parents=True,exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(out/n).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*v):return subprocess.check_output(['git','-C',str(root),*v],text=True).strip()
source=load(root/'Docs/U02/Evidence/F/MANIFEST.json');assert not git('diff','--name-only','8580651','HEAD','--','Source','Content','Config','Plugins');assert sha(root/'Config/DefaultEngine.ini').upper()==(root/'Artifacts/U02/Focus/private-config-sha.txt').read_text(encoding='utf-8-sig').strip().upper()
sessions=[('Before',a.baseline.resolve(),'FocusBaseline'),('After',a.final.resolve(),'FocusAfter'),('MinimizedOnlyNotAccepted',root/'Artifacts/U02/F/Session-20261106-195720','FocusAfter'),('FirstLowRenderWindowCoverageIncomplete',root/'Artifacts/U02/F/Session-20261106-200158','FocusAfter'),('FinalNativeTailIncomplete',root/'Artifacts/U02/F/Session-20261106-200802','FocusAfter')]
for label in ['EditorVisible','EditorMinimized','OneClient','DiagnosticsReduced','LowRender']:
 sessions.append((label,Path((root/'Artifacts/U02/Focus'/(label+'-session.txt')).read_text(encoding='utf-8-sig').strip()),label))
summary=[];rawindex=[]
for label,session,folder in sessions:
 s=load(session/folder/'SUMMARY.json');assert s['completed'];summary.append(dict(label=label,session=str(session),**s));records=load(session/'processes.json');assert all(r['sourceSHA']==source['sourceSHA'] and r['moduleSHA256'].lower()==source['moduleSHA256'].lower() for r in records)
 for f in (session/folder).iterdir():
  if f.is_file():shutil.copyfile(f,out/(label+'-'+f.name))
 for f in ['processes.json','original-editor-windows.json','editor-minimized-verified.json','server-timer.json','resources.jsonl','STOP-VERIFIED.json']:
  if (session/f).exists():shutil.copyfile(session/f,out/(label+'-'+f))
 for r in records:
  for f in [Path(r['log']),Path(next(v.split('=',1)[1].strip(chr(34)) for v in r['arguments'] if v.startswith('-U01FPerfFile=')))]:
   data=f.read_bytes();txt=data.decode('utf-8-sig',errors='replace');assert not re.search(r'(?im)\bSecurityToken\s*=\s*[^\s\r\n]+',txt);name=label+'-'+r['role']+'-'+f.name+'.gz'
   with gzip.open(out/name,'wb') as z:z.write(data)
   rawindex.append(dict(file=name,rawSHA256=sha(f),sha256=sha(out/name)))
final=summary[1];assert len(final['trials'])>=10 and final['editorsAlwaysIconic'];assert load(a.final/'FocusAfter/INPUT-ASSERTIONS.json')['failed']==0;assert load(a.final/'FocusAfter/GATE.json')['failed']==0;assert all(v['restored'] and v['alive'] for v in load(a.final/'STOP-VERIFIED.json'))
write('COMPARISON.json',summary);write('RAW-LOGS.json',rawindex);history=[]
for f in (root/'Artifacts/U02/Focus').glob('*.log'):
 data=f.read_bytes();name='History-'+f.name+'.gz'
 with gzip.open(out/name,'wb') as z:z.write(data)
 history.append(dict(file=name,original=str(f),rawSHA256=sha(f)))

failed=root/'Artifacts/U02/Focus/Session-20261106-195207'
for f in failed.rglob('*.log'):
 name='FailedDiagnostics-'+f.parent.name+'-'+f.name+'.gz'
 with gzip.open(out/name,'wb') as z:z.write(f.read_bytes())
 history.append(dict(file=name,original=str(f),rawSHA256=sha(f),status='FAILED: native control telemetry disabled, guard refused input; not performance evidence'))
write('HISTORY.json',history);write('MANIFEST.json',dict(status='READY_FOR_REVIEW',utc=datetime.now(timezone.utc).isoformat(),runtimeSourceSHA=source['sourceSHA'],launcherSourceSHA=git('rev-parse','HEAD'),handoffParentSHA=git('rev-parse','HEAD'),moduleSHA256=source['moduleSHA256'],engineExeSHA256=source['engineExeSHA256'],baselineSession=str(a.baseline),afterSession=str(a.final),beforeTransfers=10,afterTransfers=10,followupSeconds=15,privateConfigByteUnchanged=True,runtimeSourceUnchanged=True,combatAcceptanceRetained=True,mainUnmerged=True,scope='Focus performance regression only; no U03 implementation'))
(out/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n');files=sorted(f for f in out.iterdir() if f.is_file() and f.name!='EVIDENCE-SHA256.json');write('EVIDENCE-SHA256.json',[dict(file=f.name,bytes=f.stat().st_size,sha256=sha(f)) for f in files]);print('Sealed focus evidence',len(files))
