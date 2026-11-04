"""Windows package evidence using real OS input, guarded by exact executable/PID/focus.

Requires the already installed Pillow, numpy and OpenCV; installs nothing.
Actions JSON contains timed down/up (W/A/S/D/Ctrl/Space/V/Escape), click or move.
Use --inspect first to review the actual game window before choosing UI coordinates.
"""
import argparse
import ctypes as c
from ctypes import wintypes as w
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import zlib

import cv2
import numpy as np
from PIL import ImageGrab
cv2.setNumThreads(1) # Avoid oversubscribing the foreground game's CPU workers.

p = argparse.ArgumentParser()
p.add_argument('--pid', type=int, required=True)
p.add_argument('--exe', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--actions', type=Path)
p.add_argument('--duration', type=float, default=22)
p.add_argument('--inspect', action='store_true')
p.add_argument('--hz', type=int, default=60, choices=[30,60])
p.add_argument('--window-dc', action='store_true', help='Use exact client DC instead of bounded screen DC')
p.add_argument('--us-layout', action='store_true', help='Temporarily request US layout only on target game thread; restore afterwards')
p.add_argument('--game-log', type=Path, help='Require runtime movement confirmation for injected W/Ctrl')
p.add_argument('--no-movement-probe', action='store_true', help='E rebind/lock runs validate metrics offline, not hard-coded W/Ctrl probes')
p.add_argument('--virtual-keys', action='store_true', help='Use Win32 virtual-key injection instead of scan-code injection')
p.add_argument('--ime-toggle-ctrl-shift', action='store_true', help='Probe W in locked menu; toggle external input method only if needed, restore if changed')
a = p.parse_args()
if not 0 < a.duration <= 60:
    raise RuntimeError('Evidence run limited to 60 seconds')
user = c.WinDLL('user32', use_last_error=True)
kernel = c.WinDLL('kernel32', use_last_error=True)
kernel.OpenProcess.restype = w.HANDLE
kernel.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
kernel.CloseHandle.argtypes = [w.HANDLE]
handle = kernel.OpenProcess(0x1000, False, a.pid)
if not handle:
    raise c.WinError(c.get_last_error())
buffer, size = c.create_unicode_buffer(32768), w.DWORD(32768)
try:
    if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, c.byref(size)):
        raise c.WinError(c.get_last_error())
finally:
    kernel.CloseHandle(handle)
exe = a.exe.resolve(strict=True)
if Path(buffer.value).resolve() != exe or exe.name != 'AnimeMMORPG.exe':
    raise RuntimeError('Refuse input: PID does not match exact packaged executable')
user.GetForegroundWindow.restype = w.HWND
user.IsWindowVisible.argtypes = [w.HWND]
user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
user.SetForegroundWindow.argtypes = [w.HWND]
user.ShowWindow.argtypes = [w.HWND, c.c_int]
user.GetClientRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
user.ClientToScreen.argtypes = [w.HWND, c.POINTER(w.POINT)]
windows = []
callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
@callback_type
def enum_window(hwnd, _):
    pid = w.DWORD()
    user.GetWindowThreadProcessId(hwnd, c.byref(pid))
    if pid.value == a.pid:
        rect = w.RECT()
        user.GetClientRect(hwnd, c.byref(rect))
        if rect.right >= 640 and rect.bottom >= 360:
            windows.append(hwnd)
    return True
user.EnumWindows(enum_window, 0)
if len(windows) != 1:
    raise RuntimeError(f'Requires one unambiguous game window, found {len(windows)}')
hwnd = windows[0]
user.ShowWindow(hwnd, 9)
user.SetForegroundWindow(hwnd)
if user.GetForegroundWindow() != hwnd:
    # Coordinate with the existing foreground queue once at startup. During the
    # run we never steal focus back: guard() aborts if another window takes it.
    foreground_thread = user.GetWindowThreadProcessId(user.GetForegroundWindow(), None)
    target_thread = user.GetWindowThreadProcessId(hwnd, None)
    current_thread = kernel.GetCurrentThreadId()
    user.AttachThreadInput(current_thread, foreground_thread, True)
    target_attached=target_thread!=foreground_thread and bool(user.AttachThreadInput(current_thread,target_thread,True))
    try:
        user.BringWindowToTop.argtypes=[w.HWND]
        user.SetActiveWindow.argtypes=[w.HWND]
        user.BringWindowToTop(hwnd)
        user.SetActiveWindow(hwnd)
        user.SetForegroundWindow(hwnd)
    finally:
        if target_attached:user.AttachThreadInput(current_thread,target_thread,False)
        user.AttachThreadInput(current_thread, foreground_thread, False)
time.sleep(.8)
def guard():
    pid = w.DWORD()
    user.GetWindowThreadProcessId(hwnd, c.byref(pid))
    if pid.value != a.pid or user.GetForegroundWindow() != hwnd:
        active_pid=w.DWORD();user.GetWindowThreadProcessId(user.GetForegroundWindow(),c.byref(active_pid))
        raise RuntimeError(f'Game lost focus (foreground PID={active_pid.value}, target PID={a.pid}): abort input and release held keys')
def bounds():
    rect, point = w.RECT(), w.POINT()
    user.GetClientRect(hwnd, c.byref(rect))
    user.ClientToScreen(hwnd, c.byref(point))
    return point.x, point.y, point.x + rect.right, point.y + rect.bottom

class Mouse(c.Structure):
    _fields_ = [('dx', w.LONG), ('dy', w.LONG), ('data', w.DWORD), ('flags', w.DWORD), ('time', w.DWORD), ('extra', c.c_size_t)]
class Key(c.Structure):
    _fields_ = [('vk', w.WORD), ('scan', w.WORD), ('flags', w.DWORD), ('time', w.DWORD), ('extra', c.c_size_t)]
class Payload(c.Union):
    _fields_ = [('mouse', Mouse), ('key', Key)]
class Input(c.Structure):
    _fields_ = [('type', w.DWORD), ('payload', Payload)]
user.SendInput.argtypes = [w.UINT, c.POINTER(Input), c.c_int]
keys = {'W': 0x11, 'A': 0x1e, 'S': 0x1f, 'D': 0x20, 'Ctrl': 0x1d, 'Shift':0x2a,'Space': 0x39, 'V': 0x2f, 'Escape': 0x01}
keys.update({'H':0x23,'J':0x24,'L':0x26,'U':0x16,'T':0x14,'Y':0x15,'B':0x30,'N':0x31,'O':0x18,'P':0x19,'G':0x22,'Q':0x10,'F5':0x3f})
virtual_keys={'W':0x57,'A':0x41,'S':0x53,'D':0x44,'Ctrl':0xa2,'Shift':0xa0,'Space':0x20,'V':0x56,'Escape':0x1b}
virtual_keys.update({k:ord(k) for k in ('H','J','L','U','T','Y','B','N','O','P','G','Q')});virtual_keys['F5']=0x74
held = set()
def send_key(key, down):
    if key in ('MiddleMouse','ThumbMouse','ThumbMouse2'):
        extra=0 if key=='MiddleMouse' else 1 if key=='ThumbMouse' else 2
        flags=(0x20 if down else 0x40) if key=='MiddleMouse' else (0x80 if down else 0x100)
        event=Input(type=0,payload=Payload(mouse=Mouse(data=extra,flags=flags)))
        if user.SendInput(1,c.byref(event),c.sizeof(Input))!=1:raise c.WinError(c.get_last_error())
        if down:held.add(key)
        else:held.discard(key)
        return
    event = Input(type=1, payload=Payload(key=Key(vk=virtual_keys[key] if a.virtual_keys else 0,scan=keys[key], flags=(0 if a.virtual_keys else 8) | (0 if down else 2))))
    if user.SendInput(1, c.byref(event), c.sizeof(Input)) != 1:
        raise c.WinError(c.get_last_error())
    if down: held.add(key)
    else: held.discard(key)
def mouse(flags, dx=0, dy=0):
    event = Input(type=0, payload=Payload(mouse=Mouse(dx=dx, dy=dy, flags=flags)))
    if user.SendInput(1, c.byref(event), c.sizeof(Input)) != 1:
        raise c.WinError(c.get_last_error())

a.out.mkdir(parents=True, exist_ok=False)
guard()
ImageGrab.grab(bbox=bounds(), all_screens=True).save(a.out / 'initial.png')
meta = {'pid': a.pid, 'hwnd': hwnd, 'executable': str(exe), 'binarySHA256': hashlib.sha256(exe.read_bytes()).hexdigest(),
        'utc': datetime.now(timezone.utc).isoformat(), 'method': 'Win32 SendInput guarded by foreground package HWND/PID; client-area BitBlt capture, backend recorded in captureDC',
        'opencv': cv2.__version__, 'captureTargetHz': a.hz, 'events': []}
meta['captureDC']='window-client' if a.window_dc else 'screen-client-bounds'
if a.inspect:
    (a.out / 'process.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    raise SystemExit(0)
actions = json.loads(a.actions.read_text(encoding='utf-8-sig'))
if actions != sorted(actions, key=lambda item: item['time']):
    raise RuntimeError('Actions must be time ordered')
left, top, right, bottom = bounds()
video = cv2.VideoWriter(str(a.out / 'Play-E.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), a.hz, (right-left, bottom-top))
if not video.isOpened():
    raise RuntimeError('Video encoder unavailable')
frames, pending, times = 0, list(actions), []
last_frame, duplicated = None, 0
image_hashes=set()
validation_due=[]
user.GetKeyboardLayout.argtypes=[w.DWORD];user.GetKeyboardLayout.restype=w.HANDLE
user.LoadKeyboardLayoutW.argtypes=[w.LPCWSTR,w.UINT];user.LoadKeyboardLayoutW.restype=w.HANDLE
user.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
game_thread=user.GetWindowThreadProcessId(hwnd,None)
old_layout=user.GetKeyboardLayout(game_thread)
meta['keyboardLayoutBefore']=hex(old_layout)
meta['keyInjection']='virtual-key SendInput' if a.virtual_keys else 'scan-code SendInput'
# Read only the verified game client bounds. Window DC is an experimental option:
# flip-model surfaces may be stale. Count distinct images and retain real frame
# timestamps; encoder FPS alone is never evidence of capture or transition quality.
gdi = c.WinDLL('gdi32', use_last_error=True)
user.GetDC.argtypes=[w.HWND]; user.GetDC.restype=w.HDC
user.ReleaseDC.argtypes=[w.HWND,w.HDC]
gdi.CreateCompatibleDC.argtypes=[w.HDC];gdi.CreateCompatibleDC.restype=w.HDC
gdi.SelectObject.argtypes=[w.HDC,w.HANDLE];gdi.SelectObject.restype=w.HANDLE
gdi.DeleteObject.argtypes=[w.HANDLE];gdi.DeleteDC.argtypes=[w.HDC]
gdi.BitBlt.argtypes=[w.HDC,c.c_int,c.c_int,c.c_int,c.c_int,w.HDC,c.c_int,c.c_int,w.DWORD]
class BitmapHeader(c.Structure):
    _fields_=[('size',w.DWORD),('width',w.LONG),('height',w.LONG),('planes',w.WORD),('bits',w.WORD),('compression',w.DWORD),('imageBytes',w.DWORD),('xppm',w.LONG),('yppm',w.LONG),('used',w.DWORD),('important',w.DWORD)]
class BitmapInfo(c.Structure):
    _fields_=[('header',BitmapHeader),('colors',w.DWORD*3)]
gdi.CreateDIBSection.argtypes=[w.HDC,c.POINTER(BitmapInfo),w.UINT,c.POINTER(c.c_void_p),w.HANDLE,w.DWORD]
gdi.CreateDIBSection.restype=w.HANDLE
source_hwnd=hwnd if a.window_dc else None
dc=user.GetDC(source_hwnd); memory_dc=gdi.CreateCompatibleDC(dc)
info=BitmapInfo(header=BitmapHeader(size=c.sizeof(BitmapHeader),width=right-left,height=-(bottom-top),planes=1,bits=32))
pixels=c.c_void_p();bitmap=gdi.CreateDIBSection(dc,c.byref(info),0,c.byref(pixels),None,0)
if not bitmap or not pixels.value:raise RuntimeError('Client DIB capture unavailable')
previous=gdi.SelectObject(memory_dc,bitmap)
pixel_array=np.ctypeslib.as_array((c.c_ubyte*((right-left)*(bottom-top)*4)).from_address(pixels.value)).reshape(bottom-top,right-left,4)
start, next_frame = time.perf_counter(), 0.
ime_toggled=False
def toggle_input_method():
    guard();send_key('Ctrl',True);send_key('Shift',True);time.sleep(.06)
    send_key('Shift',False);send_key('Ctrl',False);time.sleep(.15)
def live_metrics():
    with a.game_log.open('rb') as log:
        log.seek(0,2);log.seek(max(0,log.tell()-48000));tail=log.read().decode('utf-8',errors='replace')
    observed=[]
    for line in tail.splitlines():
        if 'Metrics {' in line:
            try: observed.append(json.loads(line.split('Metrics ',1)[1]))
            except json.JSONDecodeError: pass
    if not observed or observed[-1]['pid']!=a.pid:raise RuntimeError('No unambiguous current game metrics')
    return observed[-1]
def probe_w():
    offset=a.game_log.stat().st_size
    send_key('W',True);time.sleep(.05);send_key('W',False)
    for _ in range(10):
        time.sleep(.05)
        with a.game_log.open('rb') as log:
            log.seek(offset);text=log.read().decode('utf-8',errors='replace')
        if 'PhysicalPress key=W ' in text:return 'W'
        if 'PhysicalPress key=None ' in text:return 'None'
    raise RuntimeError('No game key observation for safe menu W probe')
try:
    if a.us_layout:
        us_layout=user.LoadKeyboardLayoutW('00000409',0x80)
        user.PostMessageW(hwnd,0x50,0,c.c_ssize_t(us_layout).value)
        time.sleep(.25)
        if user.GetKeyboardLayout(game_thread)&0xffff != 0x0409:raise RuntimeError('Target game did not accept US layout request')
    if a.game_log:
        current=live_metrics();meta['preflightControlState']=current['controlState']
        if current['controlState']==0:
            send_key('Escape',True);time.sleep(.03);send_key('Escape',False);time.sleep(.25)
    if a.ime_toggle_ctrl_shift:
        if not a.game_log:raise RuntimeError('Adaptive IME setup requires game log')
        meta['menuWProbeBefore']=probe_w()
        if meta['menuWProbeBefore']!='W':
            toggle_input_method();ime_toggled=True;meta['externalInputMethodToggle']='Ctrl+Shift only after observed W conversion; restored on exit'
            meta['menuWProbeAfter']=probe_w()
            if meta['menuWProbeAfter']!='W':raise RuntimeError('Input method still replaces W; reject setup')
    meta['keyboardLayoutDuring']=hex(user.GetKeyboardLayout(game_thread))
    start=time.perf_counter();meta['utc']=datetime.now(timezone.utc).isoformat()
    while (elapsed := time.perf_counter() - start) < a.duration:
        guard()
        for check in list(validation_due):
            if elapsed >= check['due']:
                latest=live_metrics()
                if latest['pid']!=a.pid or latest['controlState']!=0 or latest['animationGroundSpeedCmPerSec']<=check['minimum']:
                    raise RuntimeError('Injected movement not confirmed by game; reject capture')
                meta.setdefault('inputValidation',[]).append(dict(check,observedUtc=latest['utc'],speed=latest['animationGroundSpeedCmPerSec']))
                validation_due.remove(check)
        while pending and elapsed >= pending[0]['time']:
            event = pending.pop(0)
            if event['action'] in ('down', 'up'):
                send_key(event['key'], event['action'] == 'down')
                if a.game_log and not a.no_movement_probe and event['action']=='down' and event['key'] in ('W','Ctrl'):
                    validation_due.append({'due':elapsed+.4,'key':event['key'],'minimum':3 if event['key']=='W' else 650})
            elif event['action']=='snapshot':
                ImageGrab.grab(bbox=bounds(),all_screens=True).save(a.out/(event['name']+'.png'))
            elif event['action']=='focus-cycle':
                user.ShowWindow(hwnd,6);time.sleep(event.get('seconds',1.0));user.ShowWindow(hwnd,9)
                user.SetForegroundWindow(hwnd);time.sleep(.5);guard()
                meta.setdefault('focusChecks',[]).append(live_metrics() if a.game_log else {'method':'OS minimize/restore'})
            elif event['action']=='drag':
                user.SetCursorPos(left+event['x'],top+event['y']);time.sleep(.08);mouse(2)
                for step in range(1,11):
                    user.SetCursorPos(left+int(event['x']+(event['endX']-event['x'])*step/10),top+event['y']);time.sleep(.04)
                mouse(4)
            elif event['action'] == 'move':
                mouse(1, event['dx'], event['dy'])
            elif event['action'] == 'click':
                x, y = event['x'], event['y']
                if not 0 <= x < right-left or not 0 <= y < bottom-top:
                    raise RuntimeError('Click outside game client')
                user.SetCursorPos(left+x, top+y)
                time.sleep(.06) # Let Slate process pointer motion before hit testing the press.
                mouse(2); time.sleep(.03); mouse(4)
            else:
                raise RuntimeError('Unknown evidence action')
            meta['events'].append(dict(event, actualTime=elapsed, utc=datetime.now(timezone.utc).isoformat()))
        if elapsed >= next_frame:
            while last_frame is not None and frames < int(elapsed*a.hz):
                video.write(last_frame); times.append(None); frames += 1; duplicated += 1
            if bounds() != (left,top,right,bottom):raise RuntimeError('Game client moved/resized during capture')
            if not gdi.BitBlt(memory_dc,0,0,right-left,bottom-top,dc,0 if a.window_dc else left,0 if a.window_dc else top,0x40CC0020):raise RuntimeError('Client-area BitBlt failed')
            last_frame = cv2.cvtColor(pixel_array,cv2.COLOR_BGRA2BGR)
            image_hashes.add(zlib.crc32(last_frame))
            video.write(last_frame)
            if frames % a.hz == 0:cv2.imwrite(str(a.out/f'frame-{frames:04}.png'),last_frame)
            times.append(elapsed); frames += 1; next_frame = frames/a.hz
        time.sleep(.005)
    meta['completed'] = True
finally:
    meta['captureActiveSeconds']=time.perf_counter()-start
    for key in list(held): send_key(key, False)
    if ime_toggled:
        try:
            toggle_input_method();meta['externalInputMethodRestoreChordSent']=True
        except RuntimeError as error:
            meta['externalInputMethodRestoreError']=str(error)
    meta['externalInputMethodRestored']=not ime_toggled or meta.get('externalInputMethodRestoreChordSent',False)
    video.release()
    if a.us_layout:
        user.PostMessageW(hwnd,0x50,0,c.c_ssize_t(old_layout).value);time.sleep(.15)
        meta['keyboardLayoutRestored']=user.GetKeyboardLayout(game_thread)==old_layout
    gdi.SelectObject(memory_dc,previous);gdi.DeleteObject(bitmap);gdi.DeleteDC(memory_dc);user.ReleaseDC(source_hwnd,dc)
    meta['frames'] = frames
    meta['duplicatedFrames'] = duplicated
    meta['frameTimesSeconds'] = times
    meta['wallSeconds'] = time.perf_counter()-start
    unique=[t for t in times if t is not None]
    gaps=np.diff(unique)
    meta['uniqueCaptureHz']=(len(unique)-1)/(unique[-1]-unique[0]) if len(unique)>1 else 0
    meta['distinctImageCount']=len(image_hashes)
    meta['distinctImageHz']=(len(image_hashes)-1)/(unique[-1]-unique[0]) if len(unique)>1 else 0
    meta['staticCaptureRejected']=len(image_hashes)<min(5,len(unique)/2)
    meta['uniqueFrameGapP95Seconds']=float(np.percentile(gaps,95)) if len(gaps) else None
    meta['uniqueFrameGapMaxSeconds']=float(max(gaps)) if len(gaps) else None
    (a.out / 'process.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
print(json.dumps({'frames': frames, 'wallSeconds': meta['wallSeconds'], 'out': str(a.out)}))
if meta.get('externalInputMethodRestoreError'):raise RuntimeError('Input-method restoration not confirmed; inspect capture metadata')
if meta['staticCaptureRejected']:raise RuntimeError('Readback images are static; reject stale-DC video')
