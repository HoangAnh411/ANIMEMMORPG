import json,re,csv,hashlib,subprocess
from pathlib import Path
r=Path.cwd();a=r/'Artifacts/U01/G';o=r/'Docs/U01/Evidence/G';source='5f8a6eabe103a8b31a894c82f32cffb0325474a9';review='9c89d08e5e14590166e7933e405e95887afb1b54'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=load(o/'MANIFEST.json');package=r/manifest['packagePath'];files=list(csv.DictReader((o/'PACKAGE.csv').open(encoding='utf8')))
assert digest(o/'PACKAGE.csv')==manifest['packageIndexSHA256']
for row in files:
 p=package/row['PathUnderWindows'];assert p.stat().st_size==int(row['Bytes']) and digest(p)==row['SHA256'],p
lines=(a/'MCPTests-20261105-153131/Editor.log').read_text(encoding='utf-8-sig',errors='replace').splitlines();tests=[]
for l in lines:
 m=re.search(r'Test Completed\. Result=\{(\w+)\} Name=\{[^}]+\} Path=\{([^}]+)\}',l)
 if m:tests.append({'name':m[2],'result':m[1],'log':l})
assert len(tests)==23 and all(t['result']=='Success' for t in tests) and sum(t['name'].startswith('AnimeMMORPG.U00.') for t in tests)==4
(o/'AUTOMATION-RESULTS.json').write_text(json.dumps({'sourceSHA':source,'method':'Read existing fresh cold-clone MCP TestRunner log; no test rerun at closure','tests':tests},indent=2))
results={}
for label in ('Generate','Editor','Game'):
 v=load(a/'Build-20261105-152800-078-73c759e0'/(label+'.result.json'));assert v['ExitCode']==0;results[label]=v
v=load(a/'Package-20261105-153201-862-38caf5d5/Package.result.json');assert v['ExitCode']==0;results['Package']=v
smoke=load(a/'SmokeB-20261105-153552/results.json');assert len(smoke)==3 and all(x['passed'] and x['exitCode']==0 for x in smoke);(o/'SMOKE.json').write_text(json.dumps(smoke,indent=2));(o/'BUILD-RESULTS.json').write_text(json.dumps(results,indent=2))
assert not subprocess.check_output(['git','diff','--name-only','edf885ac79d900977a43a404019eadce0244ed47',source,'--','Source','Content','Config'],text=True).strip()
assert not subprocess.check_output(['git','diff','--name-only',source,review,'--','Source','Content','Config'],text=True).strip()
checks=load(o/'TIMED-CHECKS.json');assert len(checks)==56 and all(c['result']=='PASS' for c in checks)
closure={'acceptedReviewSHA':review,'binarySourceSHA':source,'packageFilesVerified':len(files),'packageIndexSHA256':manifest['packageIndexSHA256'],'gameExecutableSHA256':manifest['gameExecutableSHA256'],'automation':{'passed':23,'foundation':4,'U01':19},'existingCapturesTimedChecks':56,'smokePassed':3,'sourceContentConfigUnchangedFromAcceptedF':True,'mandatoryTechnicalEvidenceGaps':[],'limits':['Art anime and official weapon carry DEFERRED','Packaged Server NOT ACCEPTED','Sustained120FPS NOT VERIFIED; cap120 actually89.5167FPS at1920x1080/internal100%','Physical input-to-display latency NOT MEASURED; transform timings only','Exact GPU/driver/VRAM mechanism NOT ESTABLISHED; interrupted resource sampler retained','Original Editor newest native-code load NOT VERIFIED; independent disk-binary clone/package used','F reconnect/security/settings evidence retained from accepted F; not all replayed in G network session'],'historyRetained':['534.429second interrupted long session; not ten-minute PASS','Boot-observer preflight failure','IME-contaminated focus attempt','GPU resource sampler file-lock failure','Earlier Live Coding/build/runtime warning history']}
(o/'CLOSURE-AUDIT.json').write_text(json.dumps(closure,indent=2));print('Closure audit PASS:',len(files),'package hashes;23Automation;56timedchecks;3smoke')
