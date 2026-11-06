import argparse,json,gzip,hashlib,shutil,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.session=a.session.resolve();root=Path(__file__).resolve().parents[2];out=a.out.resolve();assert out.is_relative_to(root/'Docs/U02/Evidence');out.mkdir(exist_ok=True,parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(out/'.gitattributes').write_text('* -text whitespace=cr-at-eol\n')
for name in ['Action66Open.png','AllBlocked.png','PartialHead.png','Outside.png','SELECTED.log']:
 shutil.copyfile(a.session/'Capture'/name,out/name)
for source in (root/'Artifacts/U02/D/Corner/Independent').iterdir():
 if source.is_file():shutil.copyfile(source,out/source.name)
history=[]
paths=list((root/'Artifacts/U02/D/Corner').glob('*.log'))+[root/'Artifacts/U02/D/Corner/Play/Game.log',root/'Artifacts/U02/D/Corner/Play-Final/Game.log',root/'Artifacts/U02/D/Review-20261106-125757/Game.log']
for source in paths:
 raw=source.read_bytes();s=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig',errors='replace');assert not re.search(r'(?im)\bSecurityToken\s*=\s*[^\s\r\n]+',s)
 target=out/('History-'+source.parent.name+'-'+source.name+'.gz')
 with gzip.open(target,'wb') as f:f.write(raw)
 history.append(dict(file=target.name,rawSHA256=sha(source),original=str(source)))
for source in [root/'Artifacts/U02/D/Corner/Play/INVALID.txt',root/'Artifacts/U02/D/Corner/Play/Capture/input.json',root/'Artifacts/U02/D/Corner/Play-Final/INVALID.txt',root/'Artifacts/U02/D/Corner/Play-Final/Capture/input.json']:
 shutil.copyfile(source,out/('Failed-'+source.parent.parent.name+'-'+source.parent.name+'-'+source.name))
m=json.loads((a.session/'Capture/input.json').read_text());rows=[]
for stage in m['stages']:
 b=stage['after']['combat'];rows.append(dict(case=stage['label'],actionId=b['actionId'],lifeId=b['lifeId'],expectedHits=stage['expectedHits'],actualAction=b['action'],screenshot=stage['label']+'.png',screenshotAcquisitionWindow=[stage['wallSeconds']+.8,stage['screenshotWallSeconds']],screenshotTimestampLimit='upper bound recorded after screenshot and following wait; image/action identity uses visible ID and native trace'))
(out/'CASE-ACTIONS.json').write_text(json.dumps(dict(originalReviewAction=66,originalSource='9CCBE9A14402196C6C5B79AE5C0AB506:2',originalTarget='6FEADC494323CF272968718B5926A5DC:1',notClaimedToIdentifyScreenshotAction=True,reconstructions=rows),indent=2))
(out/'HISTORY-CORNER.json').write_text(json.dumps(history,indent=2))
p=out/'MANIFEST.json';record=json.loads(p.read_text());record.update(revision='corner action66 verification and selected-action diagnostics',oldHandoff='a0c6224',oldVerifiedSource='3a63edd',gameplayCollisionAlgorithmChanged=False,reviewAccepted=False,captureSession=str(a.session.relative_to(root)),nativeDebugChanged=True);p.write_text(json.dumps(record,indent=2))
files=sorted(p for p in out.iterdir() if p.is_file() and p.name!='EVIDENCE-SHA256.json');(out/'EVIDENCE-SHA256.json').write_text(json.dumps([dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in files],indent=2))
