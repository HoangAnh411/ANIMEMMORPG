"""Fixture-off packaged traversal using the reviewed B launcher options."""
import json
import subprocess
from pathlib import Path

from C1ForegroundBatch import git, identities, inventory, snap
from C1ProfileRun import ProfileSession
from C1Run import ROOT, NATIVE, read, run_owned_launch, sha, write
from C1Win32 import Backend


def probe(record, backend, log, journal, cleanup=False):
    session=ProfileSession(record, backend, log, journal, workload={}, output=Path(record['log']).parent)
    evidence=session.setup()
    return dict(status='PASS',playingAndW=evidence,fixture=False)


def worker(run_id):
    if not run_id.startswith('C1-Launcher-') or not run_id.removeprefix('C1-Launcher-').isdigit():
        raise ValueError('invalid launcher run id')
    root=ROOT.parent/'Runs'
    build=root/'Build-03'
    m=read(build/'BUILD-IDENTITY.json')
    exe=build/'Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
    if m['sourceSHA']!=NATIVE or Path(m['clone']).resolve()!=ROOT or sha(exe)!=m['gameSHA256']:
        raise RuntimeError('build identity')
    if git('diff',NATIVE,'--','Source','Content','Config','Plugins','AnimeMMORPG.uproject'):
        raise RuntimeError('native inputs differ')
    before,games=inventory()
    if games:raise RuntimeError('package already active')
    protected=snap()
    out=root/run_id
    out.mkdir()
    (out/'User').mkdir()
    spec=json.loads(subprocess.check_output([
        'powershell.exe','-NoProfile','-File',str(ROOT/'Scripts/U04/ReadSoloLaunchSpec.ps1'),
        '-Package',str(build/'Archive/Windows'),'-Output',str(out),
        '-SourceSHA',NATIVE,'-RunId',run_id,'-FPS','60']))
    if Path(spec['executable']).resolve()!=exe.resolve():
        raise RuntimeError('Solo spec executable mismatch')
    argv=[str(exe),*spec['arguments']]
    if any('fixture' in a.casefold() or 'regression=' in a.casefold() or 'u04c1' in a.casefold() for a in argv):
        raise RuntimeError('fixture argument present')
    record=dict(runId=run_id,sourceSHA=NATIVE,executable=str(exe),binarySHA256=m['gameSHA256'],
                log=str(out/'Game.log'),userDir=str(out/'User'),targetReady=True)
    write(out/'command.json',dict(arguments=argv,entry='StartB.ps1 / SoloLaunchSpec.ps1',spec=spec))
    result=run_owned_launch(Backend(),argv,spec['workingDirectory'],out,record,probe=probe)
    after,games=inventory()
    preserved=dict(workspace=protected==snap(),editors=identities(before)<=identities(after),packageExited=not games)
    write(out/'preservation.json',preserved)
    result['preservation']=preserved
    if not all(preserved.values()):
        result['status']='INVALID'
    write(out/'final.json',result)
    return int(result['status']!='PASS')
