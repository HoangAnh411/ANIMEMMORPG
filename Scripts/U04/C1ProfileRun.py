"""Build-03 method workload, separate from the one-action counter entry."""
import argparse
import re
import subprocess
from pathlib import Path

from C1Counter import CounterSession, prepare_transition
from C1CounterRun import GAME_SHA
from C1Run import ROOT, NATIVE, arguments, read, write, sha, run_owned_launch

WORKLOAD = dict(subjects=10, boxes=3, placement='in')
TRACE = {
    'off': [],
    'timing': ['-trace=cpu,gpu,frame,bookmark,counters,region', '-statnamedevents'],
    'memory': ['-trace=memory,bookmark'],
}
QPC_BIAS = 16777216.0
COMBO = tuple(3*i+t for i in range(20) for t in (0, .32, .77))


class ProfileSession(CounterSession):
    def focus_once(self):
        if not self.record.get('targetReady'):
            return super().focus_once()
        if self.focus_attempted:
            self.fail('focus_retry_forbidden')
        self.focus_attempted=True
        from C1ForegroundCoordinator import process_identity, ready_target
        state=self.guard('target_ready_identity',foreground=False)
        target=process_identity(self.record['pid'])
        if any(target[k]!=self.record[k] for k in ('pid','creationTicks','executable')):
            self.fail('target_ready_pin_mismatch',state)
        self.j.append('target_ready_sent',runId=self.record['runId'],target=target,hwnd=self.hwnd)
        try:
            reply=ready_target(self.record['runId'],target,self.hwnd)
        except RuntimeError as error:
            self.fail(str(error))
        self.j.append('target_ready_reply',reply=reply,workerFocusCalls=0)
        deadline=self.b.now()+5
        while True:
            state=self.guard('initial_foreground_sample',foreground=False)
            if (state['foregroundHWND'],state['foregroundPID'])==(self.hwnd,self.record['pid']):
                break
            if self.b.now()>=deadline:
                self.fail('initial_foreground_timeout',state)
            self.b.sleep(.05)
        self.j.append('initial_foreground_acquired')
        self.guard('initial_foreground_stabilizing')
        self.wait(.25)
        self.j.append('initial_foreground_stable')

    def console(self, text):
        if text not in (self.prepare_command(), 'u04c1 begin 60', 'trace.stop'):
            self.fail('profile_console_command')
        self.j.append('profile_command_start', command=text)
        self.tap('Console')
        self.wait(.2)
        for char in text:
            self.tap('CHAR:' + char, .012)
        self.emit('Enter', True)
        stamp = self.b.now()
        self.wait(.035)
        self.emit('Enter', False)
        self.j.append('profile_command_sent', command=text, down=stamp)
        return stamp

    def until(self, deadline):
        while self.b.now() < deadline:
            self.guard('profile_wait')
            self.b.sleep(max(0, min(.01, deadline-self.b.now())))
        self.guard('profile_deadline')

    def prepare_command(self):
        w = self.workload
        return f"u04c1 prepare {w['subjects']} {w['boxes']} {w['placement']}"

    def capture(self):
        self.setup()
        before = self.playing()
        if any(self.output.iterdir()):
            self.fail('profile_stale_output')
        self.console(self.prepare_command())
        prepared = self.playing()
        transition = prepare_transition(before, prepared)
        warmup = self.b.now()
        self.until(warmup + 30)
        if any(self.output.iterdir()):
            self.fail('profile_stale_output')
        begin = self.console('u04c1 begin 60')
        # Allow the native console command to dispatch before the first action.
        anchor = begin + .25
        plan = []
        for index, t in enumerate(COMBO):
            deadline = anchor + t
            self.until(deadline)
            if self.b.now() > deadline + .08:
                self.fail('profile_input_late:' + str(index))
            self.gameplay_edges = 0
            self.gameplay_edge(True)
            down = self.last_input['monotonic']
            self.until(down + .035)
            self.gameplay_edge(False)
            plan.append(dict(deadline=deadline, down=down, up=self.last_input['monotonic']))
        self.until(begin + 60)
        run = self.output.parent
        deadline = self.b.now() + 10
        while self.b.now() < deadline:
            self.guard('profile_export_wait')
            try:
                summary = read(self.output/'summary.json')
                if (self.output/'frames.csv').read_bytes().endswith(b'\n'):
                    break
            except (OSError, ValueError):
                pass
            self.wait(.05)
        else:
            self.fail('profile_native_export_timeout')
        after = self.playing()
        receipt = dict(before=before, prepared=prepared, after=after, transition=transition,
                       warmupStart=warmup, begin=begin, anchor=anchor, edges=plan,
                       files={name:sha(self.output/name) for name in ('summary.json','frames.csv')})
        write(run/'capture.json', receipt)
        if self.record['mode'] != 'off':
            self.console('trace.stop')
            self.wait(1)
        from C1ProfileValidate import validate
        return validate(run, require_stop=False)


def probe(record, backend, log, journal, cleanup=False):
    session = ProfileSession(record, backend, log, journal, workload=record.get('workload', WORKLOAD), output=record['raw'])
    return session.capture()


def invalid_preflight(reason):
    import json
    print(json.dumps(dict(status='INVALID', error=reason)))
    return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--mode', required=True, choices=TRACE)
    parser.add_argument('--baseline',action='store_true')
    parser.add_argument('--continuation',action='store_true')
    a = parser.parse_args(argv)
    if a.continuation and not a.baseline:
        parser.error('continuation requires baseline')
    workload=WORKLOAD
    if a.baseline:
        from C1Baseline import authorized_matrix
        logical='Timing-r2-1x3-out' if a.continuation and a.id=='Timing-r2-1x3-out-R1' else a.id
        matches=[r for r in authorized_matrix() if r['id']==logical and r['kind']==a.mode]
        if len(matches)!=1:parser.error('baseline ID or kind not in frozen matrix')
        workload={k:matches[0][k] for k in WORKLOAD}
    if not a.baseline and not re.fullmatch(r'C1-Method-[A-Za-z0-9_-]+', a.id):
        parser.error('invalid method run ID')
    build = ROOT.parent/'Runs/Build-03'
    out = build.parent/a.id
    if out.exists():
        return invalid_preflight('profile_stale_output')
    exe = build/'Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
    pdb = exe.with_suffix('.pdb')
    index = read(build/'BUILD-IDENTITY.json')
    if index['sourceSHA'] != NATIVE or Path(index['clone']).resolve() != ROOT or sha(exe) != GAME_SHA or index['gameSHA256'] != GAME_SHA:
        raise RuntimeError('build identity')
    if subprocess.check_output(['git','diff',NATIVE,'--','Source','Content','Config','Plugins','AnimeMMORPG.uproject']):
        raise RuntimeError('native inputs changed')
    from C1Win32 import Backend
    backend = Backend()
    before = backend.inventory()
    if any(Path(row['ExecutablePath']).name.lower()=='animemmorpg.exe' for row in before):
        raise RuntimeError('package already present')
    try:
        out.mkdir()
    except FileExistsError:
        return invalid_preflight('profile_stale_output')
    for name in ('User','Raw'):
        (out/name).mkdir()
    args = arguments(exe,out,a.id) + TRACE[a.mode]
    if TRACE[a.mode]:
        args.append(f'-tracefile={out/"capture.utrace"}')
    else:
        args.append('-notrace')
    record = dict(role='U04C1Method', executable=str(exe), binarySHA256=GAME_SHA,
                  sourceSHA=NATIVE, runId=a.id, userDir=str(out/'User'), log=str(out/'Game.log'),
                  raw=str(out/'Raw'), mode=a.mode, workload=workload, targetReady=a.continuation)
    write(out/'command.json', dict(arguments=args, mode=a.mode, workload=workload,
                                   pdb=str(pdb), pdbSHA256=sha(pdb),
                                   tooling=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()))
    write(out/'protected-before.json', before)
    result = run_owned_launch(backend,args,exe.parent,out,record,probe=probe)
    after = backend.inventory()
    write(out/'protected-after.json',after)
    if not all(row in after for row in before):
        result.update(status='INVALID',protectedIdentityChanged=True)
    write(out/'final.json',result)
    return int(result['status']!='PASS')


if __name__ == '__main__':
    raise SystemExit(main())
