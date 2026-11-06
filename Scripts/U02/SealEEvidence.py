"""Verify and seal E source -> binary/package -> MCP/runtime evidence. No gameplay inference from trigger."""
import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

p=argparse.ArgumentParser()
for name in ('build','tests','package','smoke','capture'):p.add_argument('--'+name,type=Path,required=True)
p.add_argument('--evidence',type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2];out=a.evidence.resolve();assert out.is_relative_to(root/'Docs/U02/Evidence');out.mkdir(parents=True,exist_ok=True)
for name in ('build','tests','package','smoke','capture'):setattr(a,name,getattr(a,name).resolve())
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(name,data):(out/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def text(path):
    raw=path.read_bytes();return raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig',errors='replace')

test=load(a.tests/'result.json');process=load(a.tests/'process.json');source=test['sourceSHA']
assert source==process['sourceSHA'] and test['executed']>0 and test['failed']==0
mcp=load(a.tests/'mcp-results.json');lines=json.loads(mcp['content'][0]['text'])['returnValue']
completed=[dict(result=m[1],name=m[2]) for l in lines if (m:=re.search(r'Test Completed\. Result=\{([^}]+)\}.*Path=\{([^}]+)\}',l))]
assert len(completed)==test['executed'] and {t['name'] for t in completed}==set(test['tests']) and all(t['result']=='Success' for t in completed)
assert any(re.search(r'Automation Test Queue Empty\s+'+str(len(completed))+r' tests performed',l) for l in lines)
assert sha(Path(process['module']))==process['moduleSHA256'].lower()
assert not git('diff','--name-only',source,'HEAD','--','Source','Content','Config','Plugins','AnimeMMORPG.uproject')
private=load(root/'Artifacts/U02/E/private-config-before.json')
assert sha(root/'Config/DefaultEngine.ini')==private['sha256']
assert b'SecurityToken=' not in subprocess.check_output(['git','-C',str(root),'show','HEAD:Config/DefaultEngine.ini'])
build={n:load(a.build/(n+'.result.json')) for n in ('Generate','Editor','Game')}
assert all(v['ExitCode']==0 for v in build.values())
for n in build:build[n]['command']=load(a.build/(n+'.command.json'))
assert load(a.package/'Package.result.json')['ExitCode']==0
smoke=load(a.smoke/'results.json');assert len(smoke)==3 and all(s['passed'] for s in smoke)
for s in smoke:
    for m in s['metrics']:assert m['sourceSHA']==source
capture=load(a.capture/'input.json');assert capture['process']['sourceSHA']==source and capture['completed'] and capture['externalInputMethodRestored']
assertions=load(a.capture/'ASSERTIONS.json');assert assertions['failed']==0 and assertions['sourceSHA']==source
write('BUILD-RESULTS.json',build);write('AUTOMATION-RESULTS.json',dict(**test,perTest=completed));write('PROCESS.json',process)
write('PACKAGE-RESULT.json',load(a.package/'Package.result.json'));write('SMOKE.json',smoke)
write('INPUT.json',capture);write('RUNTIME-ASSERTIONS.json',assertions)
shutil.copyfile(a.tests/'mcp-results.json',out/'MCP-RESULTS.json')
shutil.copyfile(a.capture/'Input-E.mp4',out/'Input-E.mp4');shutil.copyfile(a.capture/'Final.png',out/'Final.png')
(out/'TIMELINE.log').write_text('\n'.join(l for l in lines if 'U02B_ASSERT' in l or 'U02B_EVENT' in l)+'\n',encoding='utf-8')

package=a.package/'Archive/Windows';files=sorted(p for p in package.rglob('*') if p.is_file())
with (out/'PACKAGE.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);writer.writeheader()
    for path in files:writer.writerow(dict(path=path.relative_to(package).as_posix(),bytes=path.stat().st_size,sha256=sha(path)))
game=package/'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
assert sha(game).upper()==capture['process']['binarySHA256'].upper()

logs=[];warnings={};history=[]
paths=list((root/'Artifacts/U02/E').glob('Build-*/*.log'))+list((root/'Artifacts/U02/E').glob('MCPTests-*/Editor.log'))
paths += [a.package/'Package.log',Path(capture['process']['log'])]+[Path(s['log']) for s in smoke]
for path in paths:
    name=(path.parent.parent.name+'-' if path.parent.name in ('L_Boot','L_CharacterCombatLab','L_NetworkLab') else '')+path.parent.name+'-'+path.name+'.gz'
    target=out/name
    with gzip.open(target,'wb') as f:f.write(path.read_bytes())
    logs.append(dict(original=str(path),rawSHA256=sha(path),file=name,sha256=sha(target)))
    s=text(path)
    # Never print or stage a generated token/private key from a raw log.
    assert not re.search(r'(?im)\bSecurityToken\s*=\s*[^\s\r\n]+|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----',s),path
    found=[l for l in s.splitlines() if re.search(r': Warning:|warning [A-Z]+\d+|Error:|error C\d+|not a preferred|newer than latest preferred',l)]
    if found:warnings[str(path)]=found
for directory in sorted((root/'Artifacts/U02/E').glob('MCPTests-*')):
    if (directory/'result.json').exists():history.append(dict(run=directory.name,**load(directory/'result.json')))
write('LOGS.json',logs);write('WARNINGS.json',warnings);write('RUN-HISTORY.json',history)
write('MANIFEST.json',dict(status='READY_FOR_REVIEW',remoteDelivery='source verified; handoff verification recorded separately',utc=datetime.now(timezone.utc).isoformat(),branch='u02/e-vitals-damage-death',
    baseSHA=git('rev-parse','main'),sourceSHA=source,moduleSHA256=sha(Path(process['module'])),
    gameExeSHA256=sha(game),engineExeSHA256=process['exeSHA256'],packageRelativePath=package.relative_to(root).as_posix(),packageFiles=len(files),
    buildRun=a.build.name,testRun=a.tests.name,packageRun=a.package.name,smokeRun=a.smoke.name,captureRun=a.capture.name,
    automationExecuted=len(completed),runtimeAssertions=assertions['passed'],privateConfigByteUnchanged=True,
    mainSHA=git('rev-parse','main'),sourceEqualsHandoffRuntime=True,
    scope='E authoritative HP/damage/crit/shield/death on Windows; no F dedicated agreement',
    sourceGitBlobs={s:git('rev-parse',source+':'+s) for s in git('diff','--name-only','main',source,'--','Source').splitlines()}))
evidence=sorted(f for f in out.iterdir() if f.is_file() and f.name!='EVIDENCE-SHA256.json')
write('EVIDENCE-SHA256.json',[dict(file=f.name,bytes=f.stat().st_size,sha256=sha(f)) for f in evidence])
print(json.dumps(dict(sourceSHA=source,automation=len(completed),runtimeAssertions=assertions['passed'],packageFiles=len(files),out=str(out))))
