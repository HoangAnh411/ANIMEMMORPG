"""One-action counter diagnostic state machine. No OS operations at import."""
import json
from pathlib import Path
from C1Readiness import Session
from C1Run import sha, write


def prepare_transition(before, prepared):
    """Check the two fresh metrics samples around the single prepare."""
    a, b = before['metrics'], prepared['metrics']
    for key in ('pid', 'runID', 'world', 'worldContext', 'controller', 'pawn'):
        if not a[key] or a[key] != b[key]:
            raise ValueError('prepare_identity:' + key)
    x, y = a['combat'], b['combat']
    if not x['pawnId'] or x['pawnId'] != y['pawnId']:
        raise ValueError('prepare_identity:pawnId')
    if type(x['life']) is not int or type(y['life']) is not int or y['life'] != x['life'] + 1:
        raise ValueError('prepare_life_increment')
    if type(y['action']) is not int or y['action'] != 0:
        raise ValueError('prepare_action_reset')
    if type(y['phase']) is not int or y['phase'] != 0:
        raise ValueError('prepare_phase_idle')
    return dict(beforeLife=x['life'], preparedLife=y['life'],
                beforeOffset=before['lineOffset'], preparedOffset=prepared['lineOffset'])


class CounterSession(Session):
    def __init__(self, *args, workload, output):
        super().__init__(*args)
        self.workload = workload
        self.output = Path(output)
        self.gameplay_edges = 0

    def command(self, text):
        w = self.workload
        allowed = [f"u04c1 prepare {w['subjects']} {w['boxes']} {w['placement']}", 'u04c1 begin 5']
        if text not in allowed:
            self.fail('counter_command_forbidden')
        self.j.append('counter_command_start', command=text)
        self.tap('Console'); self.wait(.2)
        for ch in text:
            self.tap('CHAR:' + ch, .012)
        self.tap('Enter'); self.wait(.25)
        self.j.append('counter_command_sent', command=text)

    def click_resume(self, x, y):
        self.j.append('resume_click_start', purpose='Resume')
        super().click_resume(x, y)
        self.j.append('resume_click_end', purpose='Resume')

    def gameplay_edge(self, down):
        # Separate from Session.emit('LMB'), whose geometry checks are Resume-only.
        # No cursor move, focus retry or release is permitted on this route.
        if self.gameplay_edges != (0 if down else 1):
            self.fail('counter_lmb_order_or_repeat')
        self.guard('before_gameplay_lmb')
        self.j.append('input_planned', key='LMB', down=down, purpose='counter-action')
        if down:
            self.held.add('LMB')
        try:
            sent = self.b.send('LMB', down)
        except Exception as e:
            self.fail('input_send_error:' + repr(e))
        if sent != 1:
            self.fail('input_short_send')
        if not down:
            self.held.discard('LMB')
        self.gameplay_edges += 1
        self.last_input = dict(key='LMB', down=down, monotonic=self.b.now(), purpose='counter-action')
        self.j.append('input_sent', **self.last_input, held=sorted(self.held))
        self.guard('after_gameplay_lmb')

    def playing(self):
        sample = self.fresh_metrics()
        m = sample['metrics']
        if m['controlState'] != 0 or m['windowActive'] is not True or m.get('motorLocked') or m.get('gateAttack') is not True:
            self.fail('counter_not_playing')
        if not m.get('combat', {}).get('pawnId'):
            self.fail('counter_combat_identity_missing')
        return sample

    def capture(self):
        readiness = self.setup()
        before = self.playing()
        if any(self.output.iterdir()):
            self.fail('counter_output_not_empty_before_prepare')
        w = self.workload
        self.command(f"u04c1 prepare {w['subjects']} {w['boxes']} {w['placement']}")
        self.wait(2)
        prepared = self.playing()
        try:
            transition = prepare_transition(before, prepared)
        except (ValueError, KeyError, TypeError) as error:
            self.fail(str(error))
        self.j.append('counter_prepare_transition', **transition)
        if any(self.output.iterdir()):
            self.fail('counter_output_before_begin')
        self.j.append('counter_empty_output_before_begin')
        self.command('u04c1 begin 5')
        self.guard('counter_before_action')
        input_offset = self.log.size()
        self.j.append('counter_action_log_boundary', offset=input_offset)
        self.gameplay_edge(True); self.wait(.035); self.gameplay_edge(False)
        # No console/input while the native five-second capture is active.
        self.wait(5)
        deadline = self.b.now() + 5
        while True:
            self.guard('counter_export_poll')
            files = [self.output / name for name in ('summary.json', 'frames.csv')]
            try:
                json.loads(files[0].read_text(encoding='utf-8-sig'))
                complete = files[1].read_bytes().endswith(b'\n')
            except (OSError, ValueError):
                complete = False
            if complete:
                break
            if self.b.now() >= deadline:
                self.fail('counter_summary_or_frames_timeout')
            self.wait(.05)
        after = self.playing()
        receipt = dict(readiness=readiness, before=before, prepared=prepared, after=after, prepareTransition=transition,
                       files={p.name: sha(p) for p in files}, process=self.record,
                       workload=w, outputWasEmpty=True, inputOffset=input_offset, inputEndOffset=self.log.size())
        self.j.append('counter_capture_complete', receipt=receipt)
        return receipt


def run_counter_probe(record, backend, log, journal, cleanup=False):
    if cleanup:
        raise RuntimeError('outer_original_handle_lifecycle_required')
    s = CounterSession(record, backend, log, journal, workload=record['workload'], output=record['raw'])
    try:
        receipt = s.capture()
        write(Path(record['raw']).parent / 'capture.json', receipt)
        from C1Validate import validate
        result = validate(Path(record['raw']).parent, single=True, require_stop=False)
        journal.append('counter_validation', validation=result)
        return result
    except Exception as e:
        s.failed = True
        journal.append('counter_invalid', error=repr(e), held=sorted(s.held), lastInput=s.last_input)
        return dict(status='INVALID', error=repr(e), held=sorted(s.held), lastInput=s.last_input)
