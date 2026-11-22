"""Dedicated Build-03 counter correctness entry; one process, one action, no trace.

CC-A authorizes fake-backend execution only. Live use needs separate CC-B approval.
"""
import argparse
import re
import subprocess
from pathlib import Path
from C1Run import ROOT, NATIVE, arguments, read, write, sha, run_owned_launch
from C1Counter import run_counter_probe

GAME_SHA = '282fcefc5156be5f5aa81caf2bc3a764949f2eaf76de081f9c62aa0e2e54e5a5'


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, required=True)
    p.add_argument('--id', required=True)
    p.add_argument('--subjects', type=int, choices=[1, 10, 40], required=True)
    p.add_argument('--boxes', type=int, choices=[1, 3], required=True)
    p.add_argument('--placement', choices=['in', 'out'], required=True)
    a = p.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', a.id):
        p.error('unsafe run ID')
    return a


def main(argv=None):
    a = parse_args(argv)
    build = a.build.resolve()
    if build != ROOT.parent / 'Runs/Build-03':
        raise RuntimeError('only Build-03 is allowed')
    out = ROOT.parent / 'Runs' / a.id
    if out.exists():
        raise RuntimeError('run ID already used; no reuse or replacement')
    index = read(build / 'BUILD-IDENTITY.json')
    if index['sourceSHA'] != NATIVE or Path(index['clone']).resolve() != ROOT:
        raise RuntimeError('build source mismatch')
    if subprocess.check_output(['git', '-C', str(ROOT), 'diff', NATIVE, '--', 'Source', 'Content', 'Config', 'Plugins', 'AnimeMMORPG.uproject']):
        raise RuntimeError('native inputs changed')
    exe = build / 'Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
    if index['gameSHA256'] != GAME_SHA or sha(exe) != GAME_SHA:
        raise RuntimeError('Build-03 Game hash mismatch')
    from C1Win32 import Backend
    backend = Backend()
    protected = backend.inventory()
    if any(Path(p['ExecutablePath']).name.lower() == 'animemmorpg.exe' for p in protected):
        raise RuntimeError('package already active')
    out.mkdir(exist_ok=False)
    for name in ('User', 'Raw'):
        (out / name).mkdir()
    workload = dict(subjects=a.subjects, boxes=a.boxes, placement=a.placement)
    args = arguments(exe, out, a.id)
    write(out / 'protected-before.json', protected)
    write(out / 'command.json', dict(arguments=args, purpose='counter-correctness', trace='off', actions=1,
                                    workload=workload, dpi=backend.dpi))
    base = dict(role='U04C1Counter', executable=str(exe), binarySHA256=GAME_SHA, sourceSHA=NATIVE,
                runId=a.id, userDir=str(out / 'User'), log=str(out / 'Game.log'), raw=str(out / 'Raw'), workload=workload)
    result = run_owned_launch(backend, args, exe.parent, out, base, probe=run_counter_probe)
    try:
        after = backend.inventory(); write(out / 'protected-after.json', after)
        if not all(p in after for p in protected):
            result.update(status='INVALID', protectedIdentityChanged=True)
    except Exception as e:
        result.update(status='INVALID', protectedInventoryError=repr(e))
    write(out / 'final.json', result)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
