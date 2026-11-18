"""Read-only final verification of B identities and protected original/U03/U04-A artifacts."""
import argparse,csv,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--workspace',required=True,type=Path);p.add_argument('--build',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
assert not a.out.exists();root=a.workspace.resolve();clone=Path(__file__).resolve().parents[2];checks=[]
def sha(f):
    h=hashlib.sha256()
    with f.open('rb') as s:
        for chunk in iter(lambda:s.read(8388608),b''):h.update(chunk)
    return h.hexdigest()
def check(f,expected,group):
    actual=sha(f);checks.append(dict(path=str(f),group=group,expected=expected.lower(),actual=actual,passed=actual==expected.lower()))
def load(f):return json.loads(f.read_text(encoding='utf-8-sig'))
pref=load(root/'Artifacts/U04/B/Runs/Preflight-20261118/PRESERVED-FILES.json')
for r in pref:check(Path(r['path']),r['sha256'],'original preflight files')
for manifest in [root/'Docs/U04/Evidence/A/Review-20261117-1244/MANIFEST.json',root/'Evidence/D/MANIFEST.json',root/'Evidence/D-R1/MANIFEST.json']:
    for r in load(manifest)['files']:
        check(root/r['raw'],r['rawSHA256'],manifest.parent.name+' raw')
        check(root/r['published'],r['publishedSHA256'],manifest.parent.name+' published')
for name in ['D','D-R1']:
    manifest=load(root/f'Evidence/{name}/MANIFEST.json');index=root/f'Evidence/{name}/PACKAGE.csv'
    check(index,manifest['packageIndexSHA256'],name+' package index')
    package=root/manifest['packageRelativePath']
    for r in csv.DictReader(index.open(encoding='utf-8-sig',newline='')):
        check(package/r['path'],r['sha256'],name+' package')
for identity,group in [(root/'Artifacts/U04/A/Runs/Build-Final-20261117-1148/BUILD-IDENTITY.json','A build'),(a.build,'B build')]:
    m=load(identity);package=Path(m['build'])/'Archive/Windows'
    for r in m['package']:check(package/r['path'],r['sha256'],group+' package')
    check(Path(m['clone'])/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll',m['moduleSHA256'],group+' module')
    check(Path(m['engineExecutable']),m['engineSHA256'],group+' engine')
m=load(a.build)
native_diff=subprocess.check_output(['git','-C',str(clone),'diff',m['sourceSHA'],'--','Source','Content','Config','Plugins','AnimeMMORPG.uproject'],text=True)
native_untracked=subprocess.check_output(['git','-C',str(clone),'ls-files','--others','--exclude-standard','--','Source','Content','Config','Plugins','AnimeMMORPG.uproject'],text=True)
baseline=load(root/'Artifacts/U04/B/Runs/Preflight-20261118/PREFLIGHT.json')
head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
status=subprocess.check_output(['git','-C',str(root),'status','--short'],text=True).splitlines()
result=dict(completed=all(r['passed'] for r in checks) and not native_diff and not native_untracked and head==baseline['baseline'] and status==baseline['originalStatus'],
            checks=checks,builtSource=m['sourceSHA'],nativeInputsUnchanged=not native_diff,noUntrackedNativeInputs=not native_untracked,
            originalHead=head,originalStatus=status,originalStatusMatches=status==baseline['originalStatus'])
a.out.write_text(json.dumps(result,indent=2),encoding='utf-8');assert result['completed'],str(a.out)
print('PASS',len(checks),'protected file/artifact hashes and original/native source state')
