"""Live adapter. Imported by the reviewed launcher only; offline tests never instantiate it."""
import ctypes as c
from ctypes import wintypes as w
from datetime import datetime, timedelta, timezone
import hashlib
import json
import subprocess
import time
from C1Identity import verify_identity, creation_ticks, path_key, render_command

def utc_from_ticks(ticks):
    seconds,fraction=divmod(ticks,10_000_000)
    dt=datetime(1601,1,1,tzinfo=timezone.utc)+timedelta(seconds=seconds)
    return dt.strftime('%Y-%m-%dT%H:%M:%S')+f'.{fraction:07d}Z'

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(8388608),b''):h.update(block)
    return h.hexdigest()

class Backend:
    def __init__(self,input_enabled=True):
        self.k=c.WinDLL('kernel32',use_last_error=True)
        k=self.k
        k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
        k.CloseHandle.argtypes=[w.HANDLE]
        k.GetProcessId.argtypes=[w.HANDLE];k.GetProcessId.restype=w.DWORD
        k.GetProcessTimes.argtypes=[w.HANDLE]+[c.POINTER(w.FILETIME)]*4
        k.TerminateProcess.argtypes=[w.HANDLE,w.UINT];k.WaitForSingleObject.argtypes=[w.HANDLE,w.DWORD]
        k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)]
        k.GetExitCodeProcess.argtypes=[w.HANDLE,c.POINTER(w.DWORD)]
        self.process=None;self.owned_handle=None;self.owned_pid=None
        self.handle_closed=False
        self.pinned_ticks=None;self.expected_executable=None;self.stop_evidence=None
        if not input_enabled:return  # Identity-only Windows checks never load user32.
        self.u=c.WinDLL('user32',use_last_error=True);u=self.u
        u.IsWindow.argtypes=[w.HWND];u.IsWindowVisible.argtypes=[w.HWND]
        u.GetForegroundWindow.restype=w.HWND
        u.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)];u.GetWindowThreadProcessId.restype=w.DWORD
        u.GetClientRect.argtypes=[w.HWND,c.POINTER(w.RECT)];u.ClientToScreen.argtypes=[w.HWND,c.POINTER(w.POINT)]
        u.GetAncestor.argtypes=[w.HWND,w.UINT];u.GetAncestor.restype=w.HWND
        u.WindowFromPoint.argtypes=[w.POINT];u.WindowFromPoint.restype=w.HWND
        u.ShowWindow.argtypes=[w.HWND,c.c_int];u.SetForegroundWindow.argtypes=[w.HWND]
        u.SetCursorPos.argtypes=[c.c_int,c.c_int]
        u.GetCursorPos.argtypes=[c.POINTER(w.POINT)]
        u.SetThreadDpiAwarenessContext.argtypes=[w.HANDLE];u.SetThreadDpiAwarenessContext.restype=w.HANDLE
        # Same physical-pixel coordinate system for client conversion and WindowFromPoint.
        c.set_last_error(0);ok=u.SetThreadDpiAwarenessContext(c.c_void_p(-4))
        self.dpi=dict(requested='PER_MONITOR_AWARE_V2',scope='probe_thread',set=bool(ok),error=0 if ok else c.get_last_error())
        if not ok:raise RuntimeError('cannot_establish_probe_dpi_context:'+str(self.dpi))
        class Mouse(c.Structure):_fields_=[('dx',w.LONG),('dy',w.LONG),('data',w.DWORD),('flags',w.DWORD),('time',w.DWORD),('extra',c.c_size_t)]
        class Key(c.Structure):_fields_=[('vk',w.WORD),('scan',w.WORD),('flags',w.DWORD),('time',w.DWORD),('extra',c.c_size_t)]
        class Payload(c.Union):_fields_=[('mouse',Mouse),('key',Key)]
        class Input(c.Structure):_fields_=[('type',w.DWORD),('payload',Payload)]
        self.Mouse,self.Key,self.Payload,self.Input=Mouse,Key,Payload,Input
        u.SendInput.argtypes=[w.UINT,c.POINTER(Input),c.c_int];u.SendInput.restype=w.UINT
        self.callback=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
        u.EnumWindows.argtypes=[self.callback,w.LPARAM]

    def now(self):return time.perf_counter()
    def sleep(self,seconds):time.sleep(max(0,seconds))
    def pid(self,hwnd):
        pid=w.DWORD()
        if not hwnd or not self.u.GetWindowThreadProcessId(hwnd,c.byref(pid)):raise c.WinError(c.get_last_error())
        return pid.value
    def ticks(self,handle):
        values=[w.FILETIME() for _ in range(4)]
        if not self.k.GetProcessTimes(handle,*[c.byref(x) for x in values]):raise c.WinError(c.get_last_error())
        return (values[0].dwHighDateTime<<32)|values[0].dwLowDateTime
    def process_ticks(self,pid):
        handle=self.k.OpenProcess(0x1000,False,pid)
        if not handle:raise c.WinError(c.get_last_error())
        try:return self.ticks(handle)
        finally:self.k.CloseHandle(handle)
    def windows(self,pid):
        found=[]
        @self.callback
        def visit(hwnd,_):
            if self.u.IsWindowVisible(hwnd):
                owner=w.DWORD();self.u.GetWindowThreadProcessId(hwnd,c.byref(owner));rect=w.RECT()
                if owner.value==pid and self.u.GetClientRect(hwnd,c.byref(rect)) and rect.right-rect.left==1280 and rect.bottom-rect.top==720:found.append(hwnd)
            return True
        if not self.u.EnumWindows(visit,0):raise c.WinError(c.get_last_error())
        return found
    def inspect(self,hwnd):
        s=dict(isWindow=bool(hwnd and self.u.IsWindow(hwnd)),errors=[])
        def get(name,fn):
            try:s[name]=fn()
            except Exception as e:s['errors'].append(name+':'+repr(e))
        fg=self.u.GetForegroundWindow();s['foregroundHWND']=fg or 0
        get('foregroundPID',lambda:self.pid(fg) if fg else 0)
        if s['isWindow']:
            get('actualPID',lambda:self.pid(hwnd))
            if s.get('actualPID'):get('actualCreationTicks',lambda:self.process_ticks(s['actualPID']))
            def rect():
                r=w.RECT()
                if not self.u.GetClientRect(hwnd,c.byref(r)):raise c.WinError(c.get_last_error())
                return [r.left,r.top,r.right,r.bottom]
            get('clientRect',rect);get('clientOriginScreen',lambda:self.client_to_screen(hwnd,0,0))
        return s
    def restore(self,hwnd):self.u.ShowWindow(hwnd,9)
    def focus(self,hwnd):return bool(self.u.SetForegroundWindow(hwnd))
    def client_to_screen(self,hwnd,x,y):
        p=w.POINT(x,y)
        if not self.u.ClientToScreen(hwnd,c.byref(p)):raise c.WinError(c.get_last_error())
        return [p.x,p.y]
    def window_at(self,point):
        hwnd=self.u.WindowFromPoint(w.POINT(*point));root=self.u.GetAncestor(hwnd,2) if hwnd else None
        return dict(hwnd=hwnd,rootHWND=root,pid=self.pid(root) if root else 0)
    def move_cursor(self,point):
        if not self.u.SetCursorPos(*point):raise c.WinError(c.get_last_error())
    def cursor_position(self):
        point=w.POINT()
        if not self.u.GetCursorPos(c.byref(point)):raise c.WinError(c.get_last_error())
        return [point.x,point.y]
    def send(self,key,down):
        if key=='LMB':event=self.Input(type=0,payload=self.Payload(mouse=self.Mouse(flags=2 if down else 4)))
        else:
            codes={'W':0x57,'Console':0xc0,'Enter':0x0d,'Ctrl':0xa2,'Shift':0xa0}
            if key.startswith('CHAR:'):
                code=self.u.VkKeyScanW(ord(key[5:]))
                if code<0 or code>>8:raise RuntimeError('console_char_requires_modifier')
            else:code=codes[key]
            event=self.Input(type=1,payload=self.Payload(key=self.Key(vk=code,flags=0 if down else 2)))
        return int(self.u.SendInput(1,c.byref(event),c.sizeof(event)))

    def read_process(self,pid):
        script=f"Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}' | Select-Object @{{n='pid';e={{$_.ProcessId}}}},@{{n='executable';e={{$_.ExecutablePath}}}},@{{n='commandLine';e={{$_.CommandLine}}}},@{{n='creationUTC';e={{$_.CreationDate.ToUniversalTime().ToString('o')}}}} | ConvertTo-Json"
        raw=subprocess.check_output(['powershell','-NoProfile','-Command',script],text=True,creationflags=subprocess.CREATE_NO_WINDOW)
        return json.loads(raw) if raw.strip() else None
    def inventory(self):
        script="Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(UnrealEditor|AnimeMMORPG)\\.exe$'} | Select-Object ProcessId,ExecutablePath,CommandLine,@{n='creationUTC';e={$_.CreationDate.ToUniversalTime().ToString('o')}} | ConvertTo-Json"
        raw=subprocess.check_output(['powershell','-NoProfile','-Command',script],text=True,creationflags=subprocess.CREATE_NO_WINDOW)
        value=json.loads(raw) if raw.strip() else []
        return value if isinstance(value,list) else [value]
    def has_owned(self):
        # If an exception lands immediately after Popen returned, recover only
        # its existing HANDLE object. Never discover a replacement process by PID.
        if self.owned_handle is None and self.process is not None and not self.handle_closed:
            self.owned_handle=w.HANDLE(int(self.process._handle));self.owned_pid=self.process.pid
        return self.owned_handle is not None

    def handle_identity(self,handle):
        pid=int(self.k.GetProcessId(handle))
        if not pid:raise c.WinError(c.get_last_error())
        ticks=self.ticks(handle);size=w.DWORD(32768);name=c.create_unicode_buffer(size.value)
        if not self.k.QueryFullProcessImageNameW(handle,0,name,c.byref(size)):raise c.WinError(c.get_last_error())
        return dict(pid=pid,creationTicks=ticks,creationUTC=utc_from_ticks(ticks),executable=name.value)

    def require_alive(self,handle):
        code=w.DWORD()
        if not self.k.GetExitCodeProcess(handle,c.byref(code)):raise c.WinError(c.get_last_error())
        if code.value!=259:raise RuntimeError('owned_process_not_alive')

    def launch(self,arguments,cwd):
        if self.process is not None:raise RuntimeError('backend_launch_is_single_use')
        self.expected_executable=arguments[0]
        self.process=subprocess.Popen(render_command(arguments),cwd=cwd,creationflags=subprocess.CREATE_NO_WINDOW)
        # Retain this exact Popen HANDLE until all verification and exit evidence
        # is complete. No metadata reads or file writes before ownership is stored.
        self.owned_handle=w.HANDLE(int(self.process._handle));self.owned_pid=self.process.pid
        return self.owned_pid

    def capture_owned(self):
        if not self.has_owned():raise RuntimeError('original_handle_missing')
        info=self.handle_identity(self.owned_handle)
        if info['pid']!=self.owned_pid:raise RuntimeError('original_handle_pid_mismatch')
        if path_key(info['executable'])!=path_key(self.expected_executable):raise RuntimeError('original_handle_executable_mismatch')
        if self.pinned_ticks is not None and info['creationTicks']!=self.pinned_ticks:raise RuntimeError('original_handle_creation_changed')
        self.pinned_ticks=info['creationTicks']
        return info

    def assert_record_handle(self,record,info):
        if info['pid']!=record['pid']:raise RuntimeError('process_pid_mismatch')
        if info['creationTicks']!=record['creationTicks']:raise RuntimeError('process_creation_mismatch')
        if path_key(info['executable'])!=path_key(record['executable']):raise RuntimeError('executable_mismatch')

    def verify_owned(self,record):
        original=self.capture_owned();self.assert_record_handle(record,original)
        self.require_alive(self.owned_handle)
        # This second HANDLE is query-only, never a termination target.
        query=self.k.OpenProcess(0x1000,False,record['pid'])
        if not query:raise c.WinError(c.get_last_error())
        try:
            current=self.handle_identity(query);self.assert_record_handle(record,current)
            self.require_alive(query)
            cim=self.read_process(record['pid'])
            if not cim or cim['pid']!=record['pid']:raise RuntimeError('cim_process_missing_or_pid_changed')
            live=dict(cim,creationTicks=current['creationTicks'],executable=current['executable'],cimCreationUTC=cim.get('creationUTC'))
            identity=verify_identity(record,live)
            self.assert_record_handle(record,self.handle_identity(query));self.require_alive(query)
            self.assert_record_handle(record,self.capture_owned());self.require_alive(self.owned_handle)
        finally:self.k.CloseHandle(query)
        shell=c.WinDLL('shell32',use_last_error=True)
        shell.CommandLineToArgvW.argtypes=[w.LPCWSTR,c.POINTER(c.c_int)]
        shell.CommandLineToArgvW.restype=c.POINTER(w.LPWSTR)
        count=c.c_int();argv=shell.CommandLineToArgvW(live['commandLine'],c.byref(count))
        if not argv:raise c.WinError(c.get_last_error())
        self.k.LocalFree.argtypes=[w.HLOCAL];self.k.LocalFree.restype=w.HLOCAL
        try:
            if [argv[i] for i in range(count.value)]!=identity['argv']:raise RuntimeError('native_argv_parser_disagreement')
        finally:self.k.LocalFree(c.cast(argv,w.HLOCAL))
        if sha(record['executable'])!=record['binarySHA256']:raise RuntimeError('game_hash_changed')
        identity.update(originalHandle=original,queryHandle=current,
                        originalHandleValue=int(self.owned_handle.value),queryHandleValue=int(query))
        try:identity['cimDeltaTicks']=record['creationTicks']-creation_ticks(cim.get('creationUTC'))
        except Exception:identity['cimDeltaTicks']=None
        return identity

    def stop_owned(self,record,timeout):
        # Strict checks on the retained HANDLE; CIM cannot veto owned-child cleanup.
        info=self.capture_owned()
        if info['creationTicks']!=record['creationTicks']:raise RuntimeError('stop_creation_changed')
        if path_key(info['executable'])!=path_key(record['executable']):raise RuntimeError('stop_executable_changed')
        if info['pid']!=record['pid']:raise RuntimeError('stop_pid_changed')
        return self.stop_launched(timeout)

    def stop_launched(self,timeout=30):
        if not self.has_owned():raise RuntimeError('original_handle_missing')
        if self.stop_evidence is not None:return dict(self.stop_evidence)
        # Also handles initialization failure before a record or journal exists.
        # Provenance is Popen's original HANDLE, never a replacement found by PID.
        try:info=self.capture_owned()
        except OSError as e:
            # Identity remains INVALID. An OS metadata-read failure must not leak
            # a child we just created: this is still Popen's retained HANDLE,
            # not an object obtained from a PID lookup. Do not catch mismatches.
            original=int(self.process._handle)
            value=self.owned_handle.value if hasattr(self.owned_handle,'value') else self.owned_handle
            if original!=value or self.process.pid!=self.owned_pid or self.handle_closed:
                raise RuntimeError('original_handle_provenance_changed') from e
            info=dict(pid=self.owned_pid,creationTicks=self.pinned_ticks,
                      executable=self.expected_executable,identityCaptureError=repr(e),
                      identityVerifiedAtStop=False)
        code=w.DWORD()
        if not self.k.GetExitCodeProcess(self.owned_handle,c.byref(code)):raise c.WinError(c.get_last_error())
        terminated=code.value==259
        if terminated and not self.k.TerminateProcess(self.owned_handle,0):raise c.WinError(c.get_last_error())
        if self.k.WaitForSingleObject(self.owned_handle,int(timeout*1000))!=0:raise RuntimeError('owned_exit_timeout')
        if not self.k.GetExitCodeProcess(self.owned_handle,c.byref(code)):raise c.WinError(c.get_last_error())
        self.stop_evidence=dict(info,exitCode=code.value,wait='signaled',terminated=terminated,handleSource='original_Popen')
        return dict(self.stop_evidence)

    def close_owned(self):
        if self.owned_handle is not None:
            # Popen owns CloseHandle; close its wrapper exactly once, after exit evidence.
            if self.stop_evidence is not None:self.process.returncode=self.stop_evidence['exitCode']
            self.process._handle.Close();self.owned_handle=None;self.handle_closed=True
