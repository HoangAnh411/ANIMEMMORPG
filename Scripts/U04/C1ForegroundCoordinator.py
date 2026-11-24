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


def process_identity(pid):
    backend = Backend(input_enabled=False)
    handle = backend.k.OpenProcess(0x1000, False, pid)
    if not handle:
        raise ct.WinError(ct.get_last_error())
    try:
        return backend.handle_identity(handle)
    finally:
        backend.k.CloseHandle(handle)


def owner(hwnd):
    pid = wt.DWORD()
    USER.GetWindowThreadProcessId(hwnd, ct.byref(pid))
    return pid.value


def ready_target(run_id, target, hwnd):
    message = dict(runId=run_id, worker=process_identity(os.getpid()), target=target, hwnd=hwnd)
    print("TARGET_READY " + json.dumps(message), flush=True)
    reply = queue.Queue()
    threading.Thread(target=lambda: reply.put(sys.stdin.readline()), daemon=True).start()
    try:
        raw = reply.get(timeout=7)
        result = json.loads(raw)
    except (queue.Empty, ValueError) as error:
        raise RuntimeError("target_ready_no_reply") from error
    if result.get("runId") != run_id or result.get("hwnd") != hwnd or not result.get("ok"):
        raise RuntimeError("target_ready_rejected:" + str(result.get("reason")))
    return result


def transfer_target(message, worker, expected_run, expected_exe, seen, coordinator_pid,
                    identity_reader=process_identity, owner_reader=owner,
                    current_foreground=foreground, focus=None):
    from C1Identity import path_key
    reply = dict(runId=message.get("runId"), hwnd=message.get("hwnd"), ok=False, calls=0)
    target = message.get("target", {})
    hwnd = reply["hwnd"]
    try:
        if seen or reply["runId"] != expected_run or message.get("worker") != worker or identity_reader(worker["pid"]) != worker:
            raise ValueError("duplicate_or_wrong_worker_session")
        if type(hwnd) is not int or owner_reader(hwnd) != target["pid"]:
            raise ValueError("target_hwnd_owner")
        if identity_reader(target["pid"]) != target or path_key(target["executable"]) != path_key(str(expected_exe)):
            raise ValueError("target_process_identity")
        actual = current_foreground()
        reply["before"] = actual
        if actual == (hwnd, target["pid"]):
            reply.update(ok=True, branch="already_foreground")
        elif actual[1] == coordinator_pid:
            focus = focus or USER.SetForegroundWindow
            reply.update(ok=True, branch="coordinator_direct", calls=1,
                         apiResult=bool(focus(hwnd)), callerPID=coordinator_pid)
        else:
            raise ValueError("third_party_foreground")
    except (OSError, KeyError, ValueError, RuntimeError) as error:
        reply["reason"] = str(error)
    return reply


def fixture_precondition(hidden, visible, coordinator):
    if hidden['hwnd'] != visible['hwnd'] or hidden['target'] != visible['target']:
        raise RuntimeError('fixture_hwnd_pin_mismatch')
    if (hidden['visible'] or not visible['visible']
            or tuple(hidden['foreground']) != coordinator
            or tuple(visible['foreground']) != coordinator):
        raise RuntimeError('fixture_precondition_not_met')


def delayed_win32_target():
    """Show a native top-level window without activating it or changing z-order."""
    user = USER
    user.CreateWindowExW.argtypes = [
        wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD,
        ct.c_int, ct.c_int, ct.c_int, ct.c_int,
        wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID,
    ]
    user.CreateWindowExW.restype = wt.HWND
    user.IsWindowVisible.argtypes = [wt.HWND]
    user.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ct.c_int, ct.c_int, ct.c_int, ct.c_int, wt.UINT]
    user.GetMessageW.argtypes = [ct.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT]
    user.TranslateMessage.argtypes = [ct.POINTER(wt.MSG)]
    user.DispatchMessageW.argtypes = [ct.POINTER(wt.MSG)]
    hwnd = user.CreateWindowExW(0, "STATIC", "C1 foreground child", 0x00CF0000,
                               180, 180, 380, 180, None, None, None, None)
    if not hwnd:
        raise ct.WinError(ct.get_last_error())
    target = process_identity(os.getpid())
    def report():
        print(json.dumps(dict(hwnd=hwnd, target=target, visible=bool(user.IsWindowVisible(hwnd)),
                              foreground=foreground(), monotonic=time.monotonic())), flush=True)
    time.sleep(5)
    report()
    flags = 0x0040 | 0x0010 | 0x0004 | 0x0002 | 0x0001
    if not user.SetWindowPos(hwnd, None, 0, 0, 0, 0, flags):
        raise ct.WinError(ct.get_last_error())
    report()
    message = wt.MSG()
    while user.GetMessageW(ct.byref(message), None, 0, 0) > 0:
        user.TranslateMessage(ct.byref(message))
        user.DispatchMessageW(ct.byref(message))


def worker(args):
    msg = wt.MSG()
    USER.PeekMessageW(ct.byref(msg), None, 0, 0, 0)
    print('READY', flush=True)
    if sys.stdin.readline().strip() != "GRANTED":
        return 2
    if args == ["demo-target-ready"]:
        started=time.monotonic()
        coordinator=foreground()
        if coordinator[1]!=os.getppid():
            raise RuntimeError("fixture_precondition_not_met")
        with subprocess.Popen([sys.executable,"-B",str(HERE),"target-delayed"],stdout=subprocess.PIPE,text=True,
                              creationflags=subprocess.CREATE_NO_WINDOW) as child:
            try:
                hidden=json.loads(child.stdout.readline())
                visible=json.loads(child.stdout.readline())
                print(json.dumps(dict(event="fixture_visibility",before=hidden,after=visible,coordinator=coordinator)),flush=True)
                fixture_precondition(hidden,visible,coordinator)
                hwnd=visible['hwnd']
                target=process_identity(child.pid)
                USER.IsWindowVisible.argtypes=[wt.HWND]
                if target!=visible['target'] or owner(hwnd)!=child.pid or not USER.IsWindowVisible(hwnd):
                    raise RuntimeError("fixture_hwnd_pin_mismatch")
                if foreground()!=coordinator:
                    raise RuntimeError("fixture_precondition_not_met")
                result=ready_target("demo-target-ready",target,hwnd)
                deadline=time.monotonic()+5
                while foreground()!=(hwnd,child.pid) and time.monotonic()<deadline:time.sleep(.05)
                stable=time.monotonic()+.25
                while time.monotonic()<stable:
                    if foreground()!=(hwnd,child.pid):
                        print(json.dumps(dict(error="direct_foreground_transfer_denied",handshake=result,after=foreground())),flush=True)
                        return 1
                    time.sleep(.02)
                print(json.dumps(dict(handshake=result,child=child.pid,hwnd=hwnd,stable=True,elapsed=time.monotonic()-started)),flush=True)
                return 0
            finally:
                if child.poll() is None:child.terminate()
                child.wait(10)
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
    if args[:1] == ["acceptance-launch"]:
        from C1AcceptanceLaunch import worker as launch
        return launch(args[args.index("--id")+1])
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
    activation_notice = False
    def wait_for_activation():
        nonlocal activation_notice
        if foreground()[1] != os.getpid():
            record("waiting_for_activation", foreground=foreground())
            if not activation_notice:
                messages.put("Ch?n c?a s? C1 Method Coordinator m?t l?n.")
                activation_notice = True
            while foreground()[1] != os.getpid():
                time.sleep(.1)

    def granted(args, out, err, created=None):
        if sys.argv[1:2] in (["method"], ["baseline"], ["acceptance"]):
            wait_for_activation()
        elif foreground()[1] != os.getpid():
            raise RuntimeError("coordinator_not_foreground_before_worker")
        b = Backend(input_enabled=False)
        if sys.argv[1:2] in (["method"], ["baseline"], ["acceptance"]):
            wait_for_activation()
        with subprocess.Popen([sys.executable, "-B", str(HERE), "worker", *args],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, text=True,
                              creationflags=subprocess.CREATE_NO_WINDOW) as proc:
            if created:
                created(proc.pid)
            handshake = args == ["demo-target-ready"] or "--continuation" in args
            seen = False
            try:
                if proc.stdout.readline().strip() != "READY":
                    raise RuntimeError("worker_not_ready")
                identity = b.handle_identity(wt.HANDLE(int(proc._handle)))
                if identity["pid"] != proc.pid or Path(identity["executable"]).resolve() != Path(sys.executable).resolve():
                    raise RuntimeError("worker_identity_mismatch")
                hwnd, pid = foreground()
                if pid != os.getpid():
                    raise RuntimeError("foreground_changed_before_grant")
                ok = True if handshake else bool(USER.AllowSetForegroundWindow(proc.pid))
                record("worker_ready", worker=identity, hwnd=hwnd, api=ok, args=args, targetReady=handshake)
                if not ok or foreground()[1] != os.getpid():
                    raise RuntimeError("grant_failed_or_foreground_changed")
                proc.stdin.write("GRANTED\n")
                proc.stdin.flush()
                if not handshake:
                    proc.stdin.close()
                for line in proc.stdout:
                    out.write(line)
                    out.flush()
                    if handshake and line.startswith("TARGET_READY "):
                        payload=json.loads(line[len("TARGET_READY "):])
                        demo=args==["demo-target-ready"]
                        run_id="demo-target-ready" if demo else args[args.index("--id")+1]
                        expected=Path(sys.executable) if demo else ROOT.parent/"Runs/Build-03/Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe"
                        record("target_ready", message=payload)
                        if not demo:
                            from C1Run import read
                            pinned=read(ROOT.parent/"Runs"/run_id/"process.json")
                            if pinned["runId"]!=run_id or any(pinned[k]!=payload["target"].get(k) for k in ("pid","creationTicks","executable")):
                                raise RuntimeError("target_ready_package_pin_mismatch")
                        observed=foreground()
                        if demo and observed!=(hwnd,os.getpid()):
                            reply=dict(runId=run_id,hwnd=payload.get('hwnd'),ok=False,calls=0,
                                       reason='fixture_precondition_not_met',before=observed)
                        else:
                            reply=transfer_target(payload,identity,run_id,expected,seen,os.getpid())
                        seen=True
                        record("target_focus_response", **reply)
                        proc.stdin.write(json.dumps(reply)+"\n")
                        proc.stdin.flush()
            finally:
                proc.stdin.close()
            return proc.wait()
    direct = 0
    continuation = (sys.argv[1:2] == ["baseline"] and len(sys.argv)>3) or sys.argv[1:2]==["acceptance"]
    for i in (1, 2):
        messages.put(f"Kiểm foreground {i}/2")
        with (CONTROL / f"child-{i}.json").open("x") as out:
            if granted(["demo-target-ready" if continuation else "demo"], out, None):
                out.flush()
                lines=(CONTROL/f"child-{i}.json").read_text().splitlines()
                if continuation and lines and 'direct_foreground_transfer_denied' in lines[-1]:
                    raise RuntimeError('direct_foreground_transfer_denied')
                raise RuntimeError("child_foreground_failed")
        if continuation:
            evidence=json.loads((CONTROL/f"child-{i}.json").read_text().splitlines()[-1])
            direct+=int(evidence["handshake"]["branch"]=="coordinator_direct" and evidence["stable"])
        deadline = time.monotonic() + 5
        while foreground()[1] != os.getpid() and time.monotonic() < deadline:
            time.sleep(.05)
        record("return_after_child", sample=i, foreground=foreground())
        if sys.argv[1:2] in (["method"], ["baseline"], ["acceptance"]):
            wait_for_activation()
        elif foreground()[1] != os.getpid():
            raise RuntimeError("coordinator_did_not_regain_foreground")
    if sys.argv[1:2] in (["method"], ["baseline"], ["acceptance"]):
        if sys.argv[1:2] == ["acceptance"]:
            if not direct:
                raise RuntimeError("direct_foreground_transfer_unproven")
            run_id=sys.argv[2]
            with (CONTROL/'launcher.stdout').open('x') as out,(CONTROL/'launcher.stderr').open('x') as err:
                code=granted(["acceptance-launch","--id",run_id,"--continuation"],out,err)
            from C1Run import write
            write(CONTROL/'launcher-result.json',dict(runId=run_id,exitCode=code,guiDirect=direct))
            return
        if sys.argv[1:2] == ["baseline"]:
            from C1Baseline import run_batch
            if continuation:
                if not direct:
                    raise RuntimeError("direct_foreground_transfer_unproven")
                from C1Run import write
                write(CONTROL/"target-ready-gui.json",dict(tests=2,direct=direct,commit=sys.argv[2]))
            run_batch(CONTROL, granted, sys.argv[2], messages, sys.argv[3] if continuation else None)
            return
        from C1ProfileBatch import run_batch
        run_batch(CONTROL, granted, sys.argv[2], messages, sys.argv[3:] or None)
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
    method = sys.argv[1:2] in (["method"], ["baseline"], ["acceptance"])
    root.title("C1 Regression Coordinator" if sys.argv[1:2]==["acceptance"] else "C1 Method Coordinator" if method else "CC-B " + chr(183) + " Foreground")
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
    if sys.argv[1:2] == ["target-delayed"]:
        delayed_win32_target()
    elif sys.argv[1:2] == ["target"]:
        root = tk.Tk()
        root.title("CC-B Child check")
        root.update()
        print(int(root.tk.call("wm", "frame", root), 0), flush=True)
        root.after(10000, root.destroy)
        root.mainloop()
    else:
        gui()


