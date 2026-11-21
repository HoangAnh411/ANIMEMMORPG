"""C1 readiness-only launcher. Package execution requires separate reviewer authorization.

This entry contains no profiling workload path. Offline imports perform no Win32,
process launch, input, Editor, build or network operations.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from C1Readiness import FileLog, Journal, run_probe

ROOT=Path(__file__).resolve().parents[2]
NATIVE='13b4f34f07bd1cb8e7402984d9479fd5eb9fe2e7'
PROFILE='t.MaxFPS 60,t.IdleWhenNotForeground 0,r.VSync 0,r.ScreenPercentage 50,r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8388608),b''):h.update(block)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)

def parse_args(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--readiness-only',action='store_true',required=True)
    p.add_argument('--purpose',choices=['readiness'],default='readiness')
    p.add_argument('--trace',choices=['off'],default='off')
    p.add_argument('--build',type=Path,required=True);p.add_argument('--id',required=True)
    a=p.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}',a.id):p.error('unsafe run ID')
    return a

def arguments(exe,out,run_id):
    return [str(exe),'/Game/AnimeMMORPG/Maps/L_CharacterCombatLab?U03Regression=1',
            '-windowed','-ResX=1280','-ResY=720','-WinX=0','-WinY=30','-nosplash','-NoLiveCoding',
            '-U04C1Profile',f'-U04C1Output={out/"Raw"}',f'-U02SourceSHA={NATIVE}',
            f'-U01SourceSHA={NATIVE}',f'-U02RunId={run_id}',f'-UserDir={out/"User"}',
            f'-abslog={out/"Game.log"}',f'-ExecCmds={PROFILE}','-U01Trace']

def run_owned_launch(backend,args,cwd,out,base,probe=None,writer=None,journal_factory=None):
    """Own the original HANDLE across every post-launch initialization failure."""
    writer=writer or write;journal_factory=journal_factory or Journal
    result=dict(status='INVALID',processExited=False);journal=None;record=None
    def note(event,**data):
        if journal:
            try:journal.append(event,**data);return True
            except Exception as e:result.update(status='INVALID',journalError=repr(e));return False
    try:
        backend.launch(args,cwd)
        pinned=backend.capture_owned()
        record=dict(base,**pinned,arguments=args)
        writer(out/'process.json',record)
        journal=journal_factory(out/'journal.jsonl',backend.now)
        proof=backend.verify_owned(record)
        if not note('launch_identity_verified',identity=proof):raise RuntimeError('identity_journal_write_failed')
        # No nested process stop: this outer lifecycle also covers failure before HWND selection.
        result.update((probe or run_probe)(record,backend,FileLog(record['log']),journal,cleanup=False))
    except BaseException as e:
        result.update(status='INVALID',error=repr(e));note('launch_or_probe_invalid',error=repr(e))
    finally:
        if backend.has_owned():
            try:
                note('before_original_handle_stop')
                stop=backend.stop_launched(timeout=30)
                result.update(processExited=True,exitEvidence=stop)
                note('original_handle_process_exited',evidence=stop)
            except Exception as e:
                result.update(status='INVALID',processExited=False,cleanupError=repr(e))
                note('original_handle_stop_failed',error=repr(e))
            finally:
                if result['processExited']:
                    try:backend.close_owned()
                    except Exception as e:result.update(status='INVALID',handleCloseError=repr(e))
        if journal:
            try:journal.close()
            except Exception as e:result.update(status='INVALID',journalError=repr(e))
        # Best effort only; disk failure must never prevent original-HANDLE cleanup.
        try:writer(out/'result.json',result)
        except Exception as e:result.update(status='INVALID',resultWriteError=repr(e))
    return result

def main(argv=None):
    a=parse_args(argv)
    build=a.build.resolve()
    if build!=ROOT.parent/'Runs/Build-03':raise RuntimeError('Build-03 is the only allowed readiness binary')
    index=read(build/'BUILD-IDENTITY.json')
    if index['sourceSHA']!=NATIVE or Path(index['clone']).resolve()!=ROOT:raise RuntimeError('build source mismatch')
    if subprocess.check_output(['git','-C',str(ROOT),'diff',NATIVE,'--','Source','Content','Config','Plugins','AnimeMMORPG.uproject']):raise RuntimeError('native inputs changed')
    exe=build/'Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
    if sha(exe)!=index['gameSHA256']:raise RuntimeError('Game hash mismatch')
    out=ROOT.parent/'Runs'/a.id;out.mkdir(exist_ok=False)
    for folder in ('User','Raw'):(out/folder).mkdir()
    from C1Win32 import Backend
    backend=Backend();protected=backend.inventory()
    if any(Path(p['ExecutablePath']).name.lower()=='animemmorpg.exe' for p in protected):raise RuntimeError('package already active; no retry/kill/start')
    write(out/'protected-before.json',protected)
    args=arguments(exe,out,a.id);write(out/'command.json',dict(arguments=args,purpose='readiness-only',trace='off',dpi=backend.dpi))
    base=dict(role='U04C1Readiness',executable=str(exe),binarySHA256=index['gameSHA256'],sourceSHA=NATIVE,runId=a.id,userDir=str(out/'User'),log=str(out/'Game.log'))
    result=run_owned_launch(backend,args,exe.parent,out,base)
    try:
        after=backend.inventory();write(out/'protected-after.json',after)
        if not all(p in after for p in protected):result.update(status='INVALID',protectedIdentityChanged=True)
    except Exception as e:result.update(status='INVALID',protectedInventoryError=repr(e))
    # result.json is immutable; final.json also records post-stop protection checks.
    write(out/'final.json',result)
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
