"""Offline failure-path checks for the CC-B coordinator (no subprocess or GUI)."""
import argparse
import io
import json
import queue
import sys
from pathlib import Path
from unittest.mock import patch
import C1ForegroundCoordinator as coordinator


def check(name, folder):
    pipes = []
    spawned = []
    class Pipe(io.StringIO):
        def close(self):
            pass

    class Process:
        pid = 123
        _handle = 456

        def __init__(self, args, **kwargs):
            spawned.append(args)
            self.stdin = Pipe()
            self.stdout = io.StringIO("READY\n")
            pipes.append(self.stdin)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def wait(self):
            return int(name == "child_missing_foreground")

    class Kernel:
        def __init__(self, **kwargs):
            pass

        def handle_identity(self, handle):
            return dict(pid=124 if name == "wrong_identity" else 123, executable=sys.executable)

    user = coordinator.USER
    class Grant:
        def AllowSetForegroundWindow(self, pid):
            assert pid == 123
            self.called = True
            return name != "grant_denied"
    grant = Grant()
    def foreground():
        lost = (name == "foreground_changed" and getattr(grant, "called", False)) or (
            name == "second_child_return_failed" and len(pipes) == 2 and pipes[-1].getvalue())
        return (1, 999 if lost else coordinator.os.getpid())

    expected = dict(wrong_identity="worker_identity_mismatch", grant_denied="grant_failed_or_foreground_changed",
                    foreground_changed="grant_failed_or_foreground_changed", child_missing_foreground="child_foreground_failed",
                    second_child_return_failed="coordinator_did_not_regain_foreground")[name]
    with patch.object(coordinator, "Backend", Kernel), patch.object(coordinator, "USER", grant),          patch.object(coordinator, "foreground", foreground), patch.object(coordinator.subprocess, "Popen", Process),          patch.object(coordinator, "CONTROL", folder / name):
        try:
            coordinator.coordinate(queue.Queue())
        except RuntimeError as error:
            actual = str(error)
        else:
            raise AssertionError("missing failure")
    assert expected == actual and all(args[-1] == "demo" for args in spawned)
    if name in ("wrong_identity", "grant_denied", "foreground_changed"):
        assert all(not pipe.getvalue() for pipe in pipes)
    return dict(case=name, expected=expected, actual=actual, packageLaunches=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    folder = parser.parse_args().out
    folder.mkdir(exist_ok=False)
    results = [check(n, folder) for n in ("wrong_identity", "grant_denied", "foreground_changed",
               "child_missing_foreground", "second_child_return_failed")]
    (folder/"results.json").write_text(json.dumps(results,indent=2))
    print(f"{len(results)} checks passed")
