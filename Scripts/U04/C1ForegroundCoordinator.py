"""Foreground coordinator for the C1 counter batch. Workers wait for a PID-specific grant."""
import ctypes as ct
from ctypes import wintypes as wt
import json
import os
from pathlib import Path
import queue
import runpy
import subprocess
import sys
import threading
import time
import tkinter as tk

from C1Run import ROOT
from C1Win32 import Backend

HERE = Path(__file__).resolve()
USER = ct.WinDLL("user32", use_last_error=True)
USER.GetForegroundWindow.restype = wt.HWND
USER.AllowSetForegroundWindow.argtypes = [wt.DWORD]
USER.SetForegroundWindow.argtypes = [wt.HWND]
USER.GetWindowThreadProcessId.argtypes = [wt.HWND, ct.POINTER(wt.DWORD)]
CONTROL = ROOT.parent / ("CC-B-Foreground-Control-" + time.strftime("%Y%m%d-%H%M%S"))
OLD = ROOT.parent / "CC-B-Batch-Control"



def foreground():
    hwnd = USER.GetForegroundWindow()
    pid = wt.DWORD()
    if hwnd:
        USER.GetWindowThreadProcessId(hwnd, ct.byref(pid))
    return hwnd, pid.value


def worker(args):
    msg = wt.MSG()
    USER.PeekMessageW(ct.byref(msg), None, 0, 0, 0)
    print('READY', flush=True)
    if sys.stdin.readline().strip() != "GRANTED":
        return 2
    if args == ["demo"]:
        # Separate target process, as with the packaged game.
        with subprocess.Popen([sys.executable, "-B", str(HERE), "target"],
                              stdout=subprocess.PIPE, text=True,
                              creationflags=subprocess.CREATE_NO_WINDOW) as child:
            try:
                hwnd = int(child.stdout.readline())
                accepted = USER.SetForegroundWindow(hwnd)
                time.sleep(.3)
                actual = foreground()
                print(json.dumps(dict(target=hwnd, pid=child.pid, actual=actual, api=accepted)), flush=True)
                return int(actual != (hwnd, child.pid))
            finally:
                if child.poll() is None:
                    child.terminate()
                child.wait(10)
    if args[:1] == ["method"]:
        from C1ProfileRun import main
        return main(args[1:])
    from C1CounterRun import main
    return main(args)


def coordinate(messages):
    CONTROL.mkdir(exist_ok=False)
    def record(event, **fields):
        with (CONTROL / "foreground.jsonl").open("a", encoding="utf8") as f:
            f.write(json.dumps(dict(event=event, time=time.time(), **fields)) + "\n")
            f.flush()
            os.fsync(f.fileno())
    def granted(args, out, err):
        start = time.monotonic()
        while foreground()[1] != os.getpid() and time.monotonic() - start < 5:
            time.sleep(.05)
        if foreground()[1] != os.getpid():
            raise RuntimeError("coordinator_not_foreground_before_worker")
        b = Backend(input_enabled=False)
        with subprocess.Popen([sys.executable, "-B", str(HERE), "worker", *args],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, text=True,
                              creationflags=subprocess.CREATE_NO_WINDOW) as proc:
            try:
                if proc.stdout.readline().strip() != "READY":
                    raise RuntimeError("worker_not_ready")
                identity = b.handle_identity(wt.HANDLE(int(proc._handle)))
                if identity["pid"] != proc.pid or Path(identity["executable"]).resolve() != Path(sys.executable).resolve():
                    raise RuntimeError("worker_identity_mismatch")
                hwnd, pid = foreground()
                if pid != os.getpid():
                    raise RuntimeError("foreground_changed_before_grant")
                ok = bool(USER.AllowSetForegroundWindow(proc.pid))
                error = 0 if ok else ct.get_last_error()
                record("grant", worker=identity, hwnd=hwnd, api=ok, error=error, args=args)
                if not ok or foreground()[1] != os.getpid():
                    raise RuntimeError("grant_failed_or_foreground_changed")
                proc.stdin.write("GRANTED\n")
                proc.stdin.flush()
            finally:
                proc.stdin.close()
            for line in proc.stdout:
                out.write(line)
            return proc.wait()
    for i in (1, 2):
        messages.put(f"Kiểm foreground {i}/2")
        with (CONTROL / f"child-{i}.json").open("x") as out:
            if granted(["demo"], out, None):
                raise RuntimeError("child_foreground_failed")
        deadline = time.monotonic() + 5
        while foreground()[1] != os.getpid() and time.monotonic() < deadline:
            time.sleep(.05)
        record("return_after_child", sample=i, foreground=foreground())
        if foreground()[1] != os.getpid():
            raise RuntimeError("coordinator_did_not_regain_foreground")
    if sys.argv[1:2] == ["method"]:
        from C1ProfileBatch import run_batch
        run_batch(CONTROL, granted, sys.argv[2], messages)
        return
    # Reuse the reviewed per-cell preservation, validator and ledger procedure.
    batch = runpy.run_path(str(HERE.with_name("C1ForegroundBatch.py")))
    g = batch["main"].__globals__
    original_invoke = g["invoke"]
    def invoke(folder, label, args):
        if label != "launcher":
            return original_invoke(folder, label, args)
        messages.put(folder.name)
        g["save"](folder / "launcher-argv.json", args)
        with (folder/"launcher.stdout").open("x") as out, (folder/"launcher.stderr").open("x") as err:
            code = granted(args[3:], out, err)
        g["save"](folder/"launcher-exit.json", code)
        return code
    g.update(invoke=invoke, p=CONTROL)
    batch["main"]()


def gui():
    root = tk.Tk()
    root.title("CC-B · Foreground")
    status = tk.StringVar(value="Sẵn sàng kiểm hai cửa sổ trước khi chạy Build-03")
    tk.Label(root, textvariable=status, padx=24, pady=14).pack()
    messages = queue.Queue()
    errors = []
    def start():
        button.config(state="disabled")
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        def work():
            try:
                coordinate(messages)
            except Exception as error:
                print(repr(error), file=sys.stderr, flush=True)
                errors.append(str(error))
                messages.put(str(error))
            finally:
                messages.put(None)
        threading.Thread(target=work).start()
    button = tk.Button(root, text="Bắt đầu CC-B", command=start)
    button.pack(pady=12)
    def poll():
        while not messages.empty():
            item = messages.get()
            if item is None:
                root.destroy()
                return
            status.set(item)
        root.after(100, poll)
    root.after(100, poll)
    def auto():
        if button["state"] == "disabled":
            return
        if foreground()[1] == os.getpid():
            start()
        elif method:
            root.after(100, auto)
    root.after(600, auto)
    root.mainloop()


if __name__ == "__main__":
    if sys.argv[1:2] == ["worker"]:
        raise SystemExit(worker(sys.argv[2:]))
    if sys.argv[1:2] == ["target"]:
        root = tk.Tk()
        root.title("CC-B · Child check")
        root.update()
        print(int(root.tk.call("wm", "frame", root), 0), flush=True)
        root.after(10000, root.destroy)
        root.mainloop()
    else:
        gui()


