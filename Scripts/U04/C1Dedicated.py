"""Build-03 dedicated session with one retained handle and log per role."""
import argparse
import json
from pathlib import Path
import re
import socket
import subprocess
import time

from C1ForegroundBatch import git, identities, inventory, snap
from C1Identity import path_key
from C1Run import ROOT, NATIVE, read, sha, write
from C1Win32 import Backend

MAP = '/Game/AnimeMMORPG/Maps/L_NetworkLab'
ROLES = ('Server', 'ClientA', 'ClientB')


def pins():
    receipt = ROOT.parent/'Runs/Build-03/BUILD-IDENTITY.json'
    build = read(receipt)
    if Path(build['clone']).resolve() != ROOT or build['sourceSHA'] != NATIVE:
        raise ValueError('wrong_clone_or_native')
    if git('diff', NATIVE, '--', 'Source', 'Content', 'Config', 'Plugins', 'AnimeMMORPG.uproject'):
        raise ValueError('native_inputs_differ')
    exe = Path(build['engineExecutable']).resolve(strict=True)
    module = (ROOT/'Binaries/Win64/UnrealEditor-AnimeMMORPG.dll').resolve(strict=True)
    for path, key in [(exe, 'engineSHA256'), (module, 'moduleSHA256')]:
        if sha(path) != build[key]:
            raise ValueError(key + '_mismatch')
    for item in build['receipts']:
        if sha(Path(item['path'])) != item['sha256']:
            raise ValueError('build_receipt_mismatch')
    return exe, module, build


def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind(('0.0.0.0', port))


def plan(run, role, port, exe, module, build):
    folder = run/role
    user, log = folder/'User', folder/'Game.log'
    project = ROOT/'AnimeMMORPG.uproject'
    server = role == 'Server'
    mode = [MAP, '-server', f'-port={port}', '-NullRHI', '-nosound'] if server else [
        f'127.0.0.1:{port}', '-game', '-windowed', '-ResX=900', '-ResY=540',
        '-WinX=' + ('0' if role == 'ClientA' else '940'), '-WinY=100']
    cvars = 't.MaxFPS 30,t.IdleWhenNotForeground 0' if server else (
        't.MaxFPS 60,t.IdleWhenNotForeground 0,r.ScreenPercentage 50,'
        'r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,'
        'r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2')
    argv = [str(exe), str(project), *mode, '-DisablePython', '-NoLiveCoding', '-nop4', '-nosplash',
            '-U04R1InputTrace', '-U01FProbe', '-U01Trace', '-U02FProbe', '-U02Trace',
            f'-U01SourceSHA={NATIVE}', f'-U02SourceSHA={NATIVE}', f'-U02RunId={run.name}',
            f'-UserDir={user}', f'-abslog={log}', f'-ExecCmds={cvars}',
            '-ini:EditorSettings:[/Script/UnrealEd.EditorPerformanceSettings]:bThrottleCPUWhenNotForeground=False']
    return dict(role=role, port=port, runId=run.name, sourceSHA=NATIVE, executable=str(exe),
                module=str(module), moduleSHA256=build['moduleSHA256'], binarySHA256=build['engineSHA256'],
                project=str(project), userDir=str(user), log=str(log), arguments=argv)


def loaded_module(record):
    pid = int(record['pid'])
    paths = subprocess.check_output([
        'powershell.exe', '-NoProfile', '-Command',
        f"(Get-Process -Id {pid} -ErrorAction Stop).Modules | Where-Object ModuleName -eq 'UnrealEditor-AnimeMMORPG.dll' | ForEach-Object FileName"
    ], text=True).splitlines()
    if len(paths) != 1 or path_key(paths[0]) != path_key(record['module']) or sha(Path(paths[0])) != record['moduleSHA256']:
        raise ValueError('loaded_module_mismatch')
    return paths[0]


def fresh_state(record, offset):
    with Path(record['log']).open('rb') as stream:
        stream.seek(0, 2)
        if stream.tell() < offset:
            raise ValueError('log_truncated')
        stream.seek(offset)
        raw = stream.read()
    offset_now = offset
    match = None
    for line in raw.splitlines(keepends=True):
        if not line.endswith(b'\n'):
            break
        start = offset_now
        offset_now += len(line)
        if b'U02F_STATE {' not in line:
            continue
        row = json.loads(line.split(b'U02F_STATE ', 1)[1])
        verify_state(record, row)
        match = dict(offset=start, endOffset=offset_now, state=row)
    return match, offset_now


def verify_state(record, row):
    server = record['role'] == 'Server'
    for key, value in [('pid', record['pid']), ('run', record['runId']), ('sourceSHA', NATIVE),
                       ('worldType', 1), ('netMode', 1 if server else 3), ('localPlayers', 0 if server else 1)]:
        if row.get(key) != value:
            raise ValueError('state_mismatch:' + key)
    if row.get('world') != MAP + '.L_NetworkLab':
        raise ValueError('state_mismatch:world')


def wait_ready(record, backend, timeout=180):
    offset = 0
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        backend.require_alive(backend.owned_handle)
        if Path(record['log']).exists():
            sample, offset = fresh_state(record, offset)
            if sample and (record['role'] == 'Server' or any(
                    p['local'] and p['role'] == 2 and p['owner'] != 'None' for p in sample['state']['pawns'])):
                identity = backend.verify_owned(record)
                module = loaded_module(record)
                backend.assert_record_handle(record, backend.capture_owned())
                return dict(sample=sample, identity=identity, loadedModule=module)
        time.sleep(.25)
    raise TimeoutError('ready_timeout:' + record['role'])


def start_roles(run, port, roles):
    exe, module, build = pins()
    check_port(port)
    protected = snap()
    before, games = inventory()
    if games:
        raise ValueError('package_active')
    run.mkdir()
    owned = []
    verdict = dict(status='INCOMPLETE', readiness={}, stops={}, tooling=git('rev-parse', 'HEAD'))
    try:
        for role in roles:
            record = plan(run, role, port, exe, module, build)
            Path(record['userDir']).mkdir(parents=True)
            backend = Backend(input_enabled=False)
            owned.append((role, backend, record))
            write(run/role/'command.json', record)
            backend.launch(record['arguments'], ROOT)
            record.update(backend.capture_owned())
            write(run/role/'process.json', record)
            verdict['readiness'][role] = wait_ready(record, backend)
            write(run/role/'readiness.json', verdict['readiness'][role])
    except Exception as exc:
        verdict.update(status='INVALID', error=f'{type(exc).__name__}: {exc}')
    finally:
        for role, backend, record in reversed(owned):
            if backend.has_owned():
                try:
                    if 'creationTicks' in record:
                        backend.assert_record_handle(record, backend.capture_owned())
                    verdict['stops'][role] = backend.stop_launched()
                except Exception as exc:
                    verdict['stops'][role] = dict(error=str(exc), processExited=False)
                finally:
                    backend.close_owned()
        after, games = inventory()
        verdict['preservation'] = dict(workspace=protected==snap(), editors=identities(before)<=identities(after),
                                       noPackage=not games)
        if not all(verdict['preservation'].values()) or any(
                stop.get('wait') != 'signaled' or stop.get('identityVerifiedAtStop') is not True
                for stop in verdict['stops'].values()):
            verdict['status'] = 'INVALID'
        write(run/'final.json', verdict)
    return verdict


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--server-only', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'C1-Dedicated-[a-zA-Z0-9-]+', args.id) or not 1024 <= args.port <= 65535:
        parser.error('invalid run ID or port')
    result = start_roles(ROOT.parent/'Runs'/args.id, args.port, ROLES[:1] if args.server_only else ROLES)
    raise SystemExit(1 if result['status'] == 'INVALID' else 0)
