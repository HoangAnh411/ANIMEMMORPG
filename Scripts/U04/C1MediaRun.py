"""Build-03 illustration capture, separate from measurement sessions."""
from datetime import datetime, timezone
from pathlib import Path
import re

from PIL import ImageGrab
from C1Counter import prepare_transition
from C1CounterRun import GAME_SHA
from C1ForegroundBatch import git, identities, inventory, snap
from C1MediaVerify import verify_receipt
from C1ProfileRun import ProfileSession
from C1Run import ROOT, NATIVE, arguments, read, write, sha, run_owned_launch
from C1Win32 import Backend


def capture(record, backend, log, journal, cleanup=False):
    out = Path(record['log']).parent
    raw = out/'Raw'
    session = ProfileSession(record, backend, log, journal, workload=record['workload'], output=raw)
    session.setup()
    before = session.playing()
    session.command(session.prepare_command())
    session.wait(2)
    prepared = session.playing()
    transition = prepare_transition(before, prepared)
    state = session.guard('media_before_grab')
    rect = state['clientRect']
    x, y = backend.client_to_screen(session.hwnd, rect[0], rect[1])
    image = ImageGrab.grab(bbox=(x, y, x+rect[2]-rect[0], y+rect[3]-rect[1]), all_screens=True)
    session.guard('media_after_grab')
    stamp = datetime.now(timezone.utc).isoformat()
    image_path = out/'fixture.png'
    image.save(image_path)
    journal.append('media_grab', capturedUTC=stamp, box=[x,y,rect[2],rect[3]], imageSHA256=sha(image_path))
    session.command('u04c1 begin 5')
    session.wait(5.5)
    summary = raw/'summary.json'
    deadline = backend.now()+5
    while not summary.exists() and backend.now()<deadline:
        session.wait(.05)
    session.playing()
    target, = read(summary)['targets']
    process = out/'process.json'
    receipt = out/'media-receipt.json'
    write(receipt, dict(runId=record['runId'], pid=record['pid'], creationTicks=record['creationTicks'],
                        buildSHA256=GAME_SHA, map=record['arguments'][1].split('?')[0], capturedUTC=stamp,
                        imageSHA256=sha(image_path), summarySHA256=sha(summary), processSHA256=sha(process),
                        **{key:target[key] for key in ('subject','life','stableHurtboxIds')}))
    validated = verify_receipt(receipt,image_path,summary,process)
    if len(target['stableHurtboxIds']) != record['workload']['boxes']:
        raise ValueError('media_wrong_hurtbox_count')
    return dict(status='PASS', decode=validated, transition=transition)


def worker(run_id):
    match = re.fullmatch(r'C1-Media-[0-9]+-H([13])', run_id)
    if not match:
        raise ValueError('invalid media run ID')
    runs = ROOT.parent/'Runs'
    out = runs/run_id
    build = runs/'Build-03'
    receipt = read(build/'BUILD-IDENTITY.json')
    exe = build/'Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
    if (receipt['sourceSHA'] != NATIVE or Path(receipt['clone']).resolve() != ROOT
            or receipt['gameSHA256'] != GAME_SHA or sha(exe) != GAME_SHA
            or git('diff',NATIVE,'--','Source','Content','Config','Plugins','AnimeMMORPG.uproject')):
        raise ValueError('media_build_identity')
    before, games = inventory()
    if games:
        raise ValueError('package_active')
    protected = snap()
    out.mkdir()
    (out/'Raw').mkdir()
    (out/'User').mkdir()
    workload = dict(subjects=1, boxes=int(match[1]), placement='in')
    argv = arguments(exe,out,run_id)
    write(out/'command.json',dict(arguments=argv, workload=workload, purpose='fixture illustration'))
    record = dict(runId=run_id, sourceSHA=NATIVE, executable=str(exe), binarySHA256=GAME_SHA,
                  userDir=str(out/'User'), log=str(out/'Game.log'), targetReady=True, workload=workload)
    result = run_owned_launch(Backend(),argv,exe.parent,out,record,probe=capture)
    after,games = inventory()
    result['preservation'] = dict(workspace=protected==snap(), editors=identities(before)<=identities(after), noPackage=not games)
    if not all(result['preservation'].values()):
        result['status']='INVALID'
    write(out/'final.json',result)
    return int(result['status']!='PASS')
