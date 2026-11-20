"""Fresh before/after hash inventory; no engine, input, cleanup or private content publication."""
import argparse,csv,json,subprocess
from pathlib import Path
from R1bContract import sha,read,write

def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--verify',type=Path);a=p.parse_args()
    assert not a.out.exists();workspace=a.workspace.resolve()
    if a.verify:
        old=read(a.verify);checks=[dict(path=r['path'],expected=r['sha256'],actual=sha(r['path'])) for r in old['files']]
        status=subprocess.check_output(['git','-C',str(workspace),'status','--porcelain'],text=True).splitlines()
        result=dict(completed=all(r['expected']==r['actual'] for r in checks) and status==old['originalStatus'],checks=checks,originalStatus=status)
        write(a.out,result);assert result['completed'];print('PASS',len(checks),'protected hashes and private status');return
    paths=set()
    def add(path):
        path=Path(path)
        if path.is_file():paths.add(path.resolve())
    def tracked(root):
        for name in subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode('utf-8').split('\0'):
            if name:add(root/name)
    tracked(workspace)
    for folder in ['Docs/Maintenance','Scripts/Maintenance']:
        for f in (workspace/folder).rglob('*'):add(f)
    for stage in ['A','B','B-Diagnostic','B-R1a','B-R1b']:
        clone=workspace/'Artifacts/U04'/stage/'Source'
        tracked(clone)
    identities=['A/Runs/Build-Final-20261117-1148','B/Runs/Build-R3-20261118','B-Diagnostic/Runs/Build-R3-20261118','B-R1a/Runs/Build-R5-20261119']
    for rel in identities:
        identity=workspace/'Artifacts/U04'/rel/'BUILD-IDENTITY.json';index=read(identity);add(identity)
        for r in index['package']:
            f=Path(index['build'])/'Archive/Windows'/r['path'];assert sha(f)==r['sha256'],f;add(f)
        for f,k in [(Path(index['clone'])/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll','moduleSHA256'),(Path(index['engineExecutable']),'engineSHA256')]:assert sha(f)==index[k];add(f)
    for stage in ['D','D-R1']:
        index=workspace/f'Evidence/{stage}/PACKAGE.csv';m=read(workspace/f'Evidence/{stage}/MANIFEST.json');add(index)
        for r in csv.DictReader(index.open(encoding='utf-8-sig',newline='')):
            f=workspace/m['packageRelativePath']/r['path'];assert sha(f)==r['sha256'];add(f)
    for f in (workspace/'Artifacts/U04/B-R1b/Runs').rglob('*'):add(f)
    result=dict(completed=True,originalHead=subprocess.check_output(['git','-C',str(workspace),'rev-parse','HEAD'],text=True).strip(),originalStatus=subprocess.check_output(['git','-C',str(workspace),'status','--porcelain'],text=True).splitlines(),files=[dict(path=str(f),sha256=sha(f)) for f in sorted(paths)])
    write(a.out,result);print('SNAPSHOT',len(paths),'protected files; historical package/module/engine identities verified')

if __name__=='__main__':main()
