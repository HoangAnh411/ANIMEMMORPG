"""Frozen R1b contract checks, performed outside numeric windows."""
import hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CASES=('walk','sprint','forward','back','left','right','combo')
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8388608),b''):h.update(chunk)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,data):Path(path).write_text(json.dumps(data,indent=2),encoding='utf-8')
def frozen(path):
    m=read(path);assert m['batchId']=='R1b-20261120-C1' and m['status']=='FROZEN'
    assert m['nativeSource']=='8cbcb6a6d6dfc4e29bff8731a6aaab187f887cb4'
    assert m['analyzerVersion']=='u04r1-entry-4'
    assert ROOT==Path(m['clone']).resolve()
    for r in m['frozenFiles']:assert sha(ROOT/r['path'])==r['sha256'],('Frozen tool changed',r['path'])
    assert not subprocess.check_output(['git','-C',str(ROOT),'diff',m['nativeSource'],'--','Source','Content','Config','Plugins','AnimeMMORPG.uproject'])
    assert not subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain','--untracked-files=all','--','Source','Content','Config','Plugins','AnimeMMORPG.uproject'])
    i=m['inheritance'];assert sha(i['manifest'])==i['manifestSHA256'] and sha(i['ledger'])==i['ledgerSHA256'] and sha(i['evidenceManifest'])==i['evidenceManifestSHA256']
    old=read(i['manifest']);ledger=read(i['ledger']);assert ledger['halted'] and ledger['completedCaps']==[30]
    assert len(i['trials'])==23 and ledger['trials']==i['trials']
    assert all(t['status']=='PASS' and t['fps']==30 for t in i['trials'])
    for key in ('nativeSource','analyzerVersion','analyzerSHA256','profile','cases','cadence','windows'):
        assert m[key]==old[key],('Continuation changed accepted policy',key)
    for f in old['frozenFiles']:assert sha(Path(old['clone'])/f['path'])==f['sha256']
    for t in i['trials']:
        assert sha(t['raw'])==t['rawSHA256']
        assert sha(Path(old['clone'])/t['assertions'])==t['assertionsSHA256']
    return m
def reused_package(m):
    index=read(m['buildIdentity']);assert sha(m['buildIdentity'])==m['buildIdentitySHA256']
    assert index['sourceSHA']==m['nativeSource']
    package=Path(m['packageRoot'])
    assert package==(Path(index['build'])/'Archive/Windows').resolve()
    for f in index['package']:assert sha(package/f['path'])==f['sha256'],f['path']
    assert sha(Path(index['clone'])/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll')==index['moduleSHA256']==m['moduleSHA256']
    assert sha(index['engineExecutable'])==index['engineSHA256']==m['engineSHA256']
    assert sha(Path(index['engineExecutable']).with_name('UnrealEditor-Cmd.exe'))==index['engineCommandletSHA256']
    assert index['engineVersion']['PatchVersion']==4 and index['engineVersion']['Changelist']==58902052
    assert sha(package/'AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe')==m['gameSHA256']
    return index

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    assert not a.out.exists();m=frozen(a.manifest);index=reused_package(m)
    write(a.out,dict(completed=True,sourceSHA=m['nativeSource'],toolSHA=m['toolCommit'],batchManifestSHA256=sha(a.manifest),packageFiles=len(index['package']),gameSHA256=m['gameSHA256'],moduleSHA256=m['moduleSHA256'],engineSHA256=m['engineSHA256']))
