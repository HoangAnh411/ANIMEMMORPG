"""Build-03 illustration capture, separate from measurement sessions."""
import ctypes
import json
from datetime import datetime, timezone
from pathlib import Path
import re

from PIL import ImageGrab
from C1Counter import prepare_transition
from C1CounterRun import GAME_SHA
from C1ForegroundBatch import git, identities, inventory, snap
from C1MediaVerify import verify_receipt
from C1ProfileRun import ProfileSession, QPC_BIAS
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


def capture_combo(record, backend, log, journal, cleanup=False):
    out = Path(record['log']).parent
    raw = out/'Raw'
    session = ProfileSession(record, backend, log, journal, workload=record['workload'], output=raw)
    session.setup()
    before = session.playing()
    session.command(session.prepare_command())
    session.wait(2)
    prepared = session.playing()
    transition = prepare_transition(before, prepared)
    session.command('u04c1 begin 5')
    anchor = backend.now()
    edges = []
    for offset in (0, .32, .77):
        session.until(anchor+offset)
        if backend.now()-anchor-offset > .08:
            session.fail('focused_combo_dispatch_late')
        session.gameplay_edges = 0
        session.gameplay_edge(True)
        edges.append(session.last_input['monotonic'])
        session.wait(.035)
        session.gameplay_edge(False)
    session.until(anchor+5.25)
    summary = read(raw/'summary.json')
    after = session.playing()
    write(out/'combo-receipt.json',dict(before=before,prepared=prepared,after=after,edges=edges,transition=transition,
                                       summarySHA256=sha(raw/'summary.json')))
    from C1FocusedProof import combo_receipt
    return combo_receipt(summary, prepared['metrics'], after['metrics'], edges, QPC_BIAS, record)


def capture_dodge(record, backend, log, journal, cleanup=False):
    from AnalyzeR1 import dodge, distance, vector
    from C1FocusedProof import check_dodge

    class DodgeSession(ProfileSession):
        def b_command(self, command):
            self.tap('Console')
            self.wait(.2)
            for char in command:
                self.tap('CHAR:'+char, .012)
            self.tap('Enter')
            self.wait(.25)
            journal.append('focused_console', command=command)

        def ordered_press(self, case):
            w = backend.Input(type=1,payload=backend.Payload(key=backend.Key(vk=0x57)))
            shift = backend.Input(type=1,payload=backend.Payload(key=backend.Key(scan=0x2a,flags=8)))
            pair = (backend.Input*2)(*((w,shift) if case=='w-shift' else (shift,w)))
            self.guard('dodge_before_batch')
            self.held.update(('W','Shift'))
            sent = backend.u.SendInput(2,pair,ctypes.sizeof(backend.Input))
            journal.append('focused_ordered_press', case=case, sent=sent)
            if sent!=2:
                self.fail('dodge_partial_send')
            self.guard('dodge_after_batch')

    out=Path(record['log']).parent
    raw=out/'Raw'
    session=DodgeSession(record, backend, log, journal, workload={},output=raw)
    session.setup()
    results={}
    for case in ('w-shift','shift-w'):
        session.b_command('u04b prepare')
        session.wait(.8)
        sample=session.playing()
        journal.append('focused_dodge_boundary',case=case,offset=log.size(),sample=sample)
        session.b_command('u04b begin '+case)
        session.ordered_press(case)
        session.wait(.10)
        session.emit('Shift',False)
        session.emit('W',False)
        session.wait(.85)
        session.b_command('u04b end')
        path=raw/(case+'.jsonl')
        rows=[json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines()]
        frames=[row for row in rows if row['kind']=='frame']
        if not frames or any(row['pid']!=record['pid'] or row['source']!=NATIVE or row['worldType']!=1 or row['netMode']!=0 for row in frames):
            raise ValueError('focused_dodge_frame_identity')
        result=check_dodge(rows,case)
        if result['status']=='PASS':
            if case=='w-shift':
                measured=dodge(rows,frames,'forward')
                result['trajectory']=measured
                if not measured['pass_']:
                    result['status']='FAIL'
            else:
                admission, end, receipt=(result[k] for k in ('admission','trajectoryEnd','received'))
                combat=end['combat']
                origin=vector(receipt['receivedPosition'])
                actual=distance(origin,end['position'])
                result['trajectory']=dict(distanceCm=actual, motion=combat['dodgeMotionEnd']-combat['dodgeStart'],
                                          lock=combat['dodgeLockEnd']-combat['dodgeStart'])
                if (int(combat['commandId'])!=receipt['command'] or combat['dodge']!=receipt['dodge']+1
                        or admission['admissionResult']!=0 or combat['dodgeStart']!=admission['at']
                        or abs(actual-300)>5 or abs(result['trajectory']['motion']-.25)>1e-6
                        or abs(result['trajectory']['lock']-.35)>1e-6):
                    result['status']='FAIL'
        results[case]=result
        write(out/(case+'-verdict.json'),result)
        if result['status']!='PASS':
            break
    return dict(status=next(reversed(results.values()))['status'], cases=list(results))


def worker(run_id):
    match = re.fullmatch(r'C1-Media-[0-9]+-H([13])', run_id)
    combo = re.fullmatch(r'C1-FocusedCombo-[0-9]+', run_id)
    dodge_run = re.fullmatch(r'C1-FocusedDodge-[0-9]+', run_id)
    focus_run = re.fullmatch(r"C1-FocusedFocus-[0-9]+",run_id)
    if not any((match,combo,dodge_run,focus_run)):
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
    if focus_run:
        from C1FocusCapture import wait_for_w_up
        wait_for_w_up(lambda down,n: print(f"focus_worker_prelaunch_key down={down} consecutive={n}",flush=True),
                      lambda: True,lambda: None,required=False)
    out.mkdir()
    (out/'Raw').mkdir()
    (out/'User').mkdir()
    workload = dict(subjects=1, boxes=int(match[1]) if match else 1, placement='in')
    argv = arguments(exe,out,run_id)
    if dodge_run:
        argv = [arg for arg in argv if not arg.startswith('-U04C1')]
        argv += ['-U04BFPSFixture','-U04BInputDiagnostic',f'-U04BOutput={out/"Raw"}']
    write(out/'command.json',dict(arguments=argv, workload=workload, purpose='focused combat' if combo else 'fixture illustration'))
    record = dict(runId=run_id, sourceSHA=NATIVE, executable=str(exe), binarySHA256=GAME_SHA,
                  userDir=str(out/'User'), log=str(out/'Game.log'), targetReady=True, workload=workload)
    if focus_run:
        from C1FocusCapture import capture as focus_capture
    result = run_owned_launch(Backend(),argv,exe.parent,out,record,probe=focus_capture if focus_run else capture_dodge if dodge_run else capture_combo if combo else capture)
    after,games = inventory()
    result['preservation'] = dict(workspace=protected==snap(), editors=identities(before)<=identities(after), noPackage=not games)
    if not all(result['preservation'].values()):
        result['status']='INVALID'
    write(out/'final.json',result)
    return int(result['status']!='PASS')
