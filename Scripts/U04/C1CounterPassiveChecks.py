import argparse
import csv
import json
from pathlib import Path

from C1Counter import CounterSession
from C1CounterChecks import CounterBackend
from C1Offline import FakeLog, record
from C1Readiness import Journal, ProbeError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    out = parser.parse_args().out
    out.mkdir(parents=True)
    cases = {
        'stable': 'PASS', 'partial': 'PASS', 'stale_metrics': 'metrics_timeout',
        'lost_focus': 'foreground_hwnd_mismatch', 'relocked': 'metrics_timeout',
        'w_rejected': 'current_w_edges_missing_or_rejected', 'ime_current_none': 'PASS',
        'no_motion': 'pawn_horizontal_motion_not_matching_w',
    }
    rows = []
    for name, expected in cases.items():
        log = FakeLog()
        backend = CounterBackend(log)
        backend.mode = name
        original = backend.metrics
        def metrics():
            sample = original()
            if name == 'relocked' and backend.metrics_count > 2:
                sample.update(motorLocked=True, motorLockMask=1)
            return sample
        backend.metrics = metrics
        if name in ('partial', 'stale_metrics'):
            log.add('Metrics ' + json.dumps(metrics()) + ('\n' if name == 'stale_metrics' else ''))
        if name == 'partial':
            backend.next_metrics = backend.t + .4
            backend.sleep_fault = lambda b: log.add('\n') if not log.data.endswith(b'\n') else None
        if name == 'lost_focus':
            backend.sleep_fault = lambda b: setattr(b, 'fg', 202) if b.t > 10.3 else None
        journal = Journal(out / (name + '.jsonl'), backend.now)
        session = CounterSession(record(), backend, log, journal, workload={}, output=out)
        try:
            session.setup()
            actual = 'PASS'
        except ProbeError as error:
            actual = str(error)
        finally:
            journal.close()
        if name == 'relocked':
            assert 'motorLockMask' in (out / (name + '.jsonl')).read_text(encoding='utf-8')
        keys = [event['key'] for event in backend.sent]
        assert all(key in ('W', 'Ctrl', 'Shift') for key in keys), keys
        if name in ('stale_metrics', 'lost_focus', 'relocked'):
            assert not keys
        rows.append(dict(case=name, expected=expected, actual=actual, inputCount=len(keys),
                         passed=actual.startswith(expected)))
    with (out / 'cases.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(rows)
    return int(not all(row['passed'] for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())
