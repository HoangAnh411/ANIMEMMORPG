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

import cv2
import numpy as np
from PIL import ImageGrab

p = argparse.ArgumentParser()
p.add_argument('--pid', type=int, required=True)
p.add_argument('--exe', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--actions', type=Path)
p.add_argument('--duration', type=float, default=22)
p.add_argument('--inspect', action='store_true')
p.add_argument('--hz', type=int, default=60, choices=[30,60])
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
    current_thread = kernel.GetCurrentThreadId()
    user.AttachThreadInput(current_thread, foreground_thread, True)
    try:
        user.SetForegroundWindow(hwnd)
    finally:
        user.AttachThreadInput(current_thread, foreground_thread, False)
time.sleep(.8)
def guard():
    pid = w.DWORD()
    user.GetWindowThreadProcessId(hwnd, c.byref(pid))
    if pid.value != a.pid or user.GetForegroundWindow() != hwnd:
        raise RuntimeError('Game lost focus: abort input and release held keys')
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
keys = {'W': 0x11, 'A': 0x1e, 'S': 0x1f, 'D': 0x20, 'Ctrl': 0x1d, 'Space': 0x39, 'V': 0x2f, 'Escape': 0x01}
held = set()
def send_key(key, down):
    event = Input(type=1, payload=Payload(key=Key(scan=keys[key], flags=8 | (0 if down else 2))))
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
        'utc': datetime.now(timezone.utc).isoformat(), 'method': 'Win32 SendInput guarded by foreground package HWND/PID; client-area capture',
        'opencv': cv2.__version__, 'captureTargetHz': a.hz, 'events': []}
if a.inspect:
    (a.out / 'process.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    raise SystemExit(0)
actions = json.loads(a.actions.read_text(encoding='utf-8-sig'))
if actions != sorted(actions, key=lambda item: item['time']):
    raise RuntimeError('Actions must be time ordered')
left, top, right, bottom = bounds()
video = cv2.VideoWriter(str(a.out / 'Play-D.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), a.hz, (right-left, bottom-top))
if not video.isOpened():
    raise RuntimeError('Video encoder unavailable')
frames, pending, times = 0, list(actions), []
last_frame, duplicated = None, 0
# Capture the verified client DC directly: desktop PIL capture was too slow to
# assess a 100ms transition. Keep measured unique-frame timestamps, not just FPS metadata.
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
dc=user.GetDC(hwnd); memory_dc=gdi.CreateCompatibleDC(dc)
info=BitmapInfo(header=BitmapHeader(size=c.sizeof(BitmapHeader),width=right-left,height=-(bottom-top),planes=1,bits=32))
pixels=c.c_void_p();bitmap=gdi.CreateDIBSection(dc,c.byref(info),0,c.byref(pixels),None,0)
if not bitmap or not pixels.value:raise RuntimeError('Client DIB capture unavailable')
previous=gdi.SelectObject(memory_dc,bitmap)
pixel_array=np.ctypeslib.as_array((c.c_ubyte*((right-left)*(bottom-top)*4)).from_address(pixels.value)).reshape(bottom-top,right-left,4)
start, next_frame = time.perf_counter(), 0.
try:
    while (elapsed := time.perf_counter() - start) < a.duration:
        guard()
        while pending and elapsed >= pending[0]['time']:
            event = pending.pop(0)
            if event['action'] in ('down', 'up'):
                send_key(event['key'], event['action'] == 'down')
            elif event['action'] == 'move':
                mouse(1, event['dx'], event['dy'])
            elif event['action'] == 'click':
                x, y = event['x'], event['y']
                if not 0 <= x < right-left or not 0 <= y < bottom-top:
                    raise RuntimeError('Click outside game client')
                user.SetCursorPos(left+x, top+y)
                mouse(2); time.sleep(.03); mouse(4)
            else:
                raise RuntimeError('Unknown evidence action')
            meta['events'].append(dict(event, actualTime=elapsed, utc=datetime.now(timezone.utc).isoformat()))
        if elapsed >= next_frame:
            while last_frame is not None and frames < int(elapsed*a.hz):
                video.write(last_frame); times.append(None); frames += 1; duplicated += 1
            if bounds() != (left,top,right,bottom):raise RuntimeError('Game client moved/resized during capture')
            if not gdi.BitBlt(memory_dc,0,0,right-left,bottom-top,dc,0,0,0x40CC0020):raise RuntimeError('Client BitBlt failed')
            last_frame = cv2.cvtColor(pixel_array,cv2.COLOR_BGRA2BGR)
            video.write(last_frame)
            if frames % a.hz == 0:cv2.imwrite(str(a.out/f'frame-{frames:04}.png'),last_frame)
            times.append(elapsed); frames += 1; next_frame = frames/a.hz
        time.sleep(.005)
    meta['completed'] = True
finally:
    for key in list(held): send_key(key, False)
    video.release()
    gdi.SelectObject(memory_dc,previous);gdi.DeleteObject(bitmap);gdi.DeleteDC(memory_dc);user.ReleaseDC(hwnd,dc)
    meta['frames'] = frames
    meta['duplicatedFrames'] = duplicated
    meta['frameTimesSeconds'] = times
    meta['wallSeconds'] = time.perf_counter()-start
    unique=[t for t in times if t is not None]
    gaps=np.diff(unique)
    meta['uniqueCaptureHz']=(len(unique)-1)/(unique[-1]-unique[0]) if len(unique)>1 else 0
    meta['uniqueFrameGapP95Seconds']=float(np.percentile(gaps,95)) if len(gaps) else None
    meta['uniqueFrameGapMaxSeconds']=float(max(gaps)) if len(gaps) else None
    (a.out / 'process.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
print(json.dumps({'frames': frames, 'wallSeconds': meta['wallSeconds'], 'out': str(a.out)}))
