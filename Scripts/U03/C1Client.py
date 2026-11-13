"""Real Windows input/video with U02 PID/executable/hash/world/owner/focus/IME guards."""
import argparse
import ctypes as c
from ctypes import wintypes as w
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import cv2
import numpy as np
from PIL import ImageGrab

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Scripts/U01'))
from F60Input import Client, u, k, mouse, key, VK
from F60Input import Input, Payload, Key, emit
VK.update({'Alt':0xa4,'Tab':0x09})

class C1Client(Client):
    def press(self,name,down):
        if name=='RMB':
            self.guard();mouse(8 if down else 16);self.right_held=down;return
        if name!='Shift':return super().press(name,down)
        self.guard();emit(Input(type=1,payload=Payload(key=Key(vk=0,scan=0x2a,flags=8|(0 if down else 2)))))
        if down:self.held.add(name)
        else:self.held.discard(name)
    def __init__(self, record):
        self.record=record; self.pid=record['pid']; self.log=Path(record['log']); self.ime=False; self.held=set(); self.mouse_held=False
        exe=Path(record['executable']).resolve()
        assert record['role']=='U03PackageC1' and exe.is_relative_to(ROOT/'Artifacts/U03/C1') and exe.name=='AnimeMMORPG.exe'
        actual=subprocess.check_output(['powershell','-NoProfile','-Command',f'(Get-CimInstance Win32_Process -Filter "ProcessId={self.pid}").ExecutablePath'],text=True,creationflags=subprocess.CREATE_NO_WINDOW).strip()
        assert Path(actual).resolve()==exe and hashlib.sha256(exe.read_bytes()).hexdigest().upper()==record['binarySHA256'].upper()
        found=[]
        @c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
        def visit(h,_):
            pid=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(pid));r=w.RECT();u.GetClientRect(h,c.byref(r))
            if pid.value==self.pid and r.right==1280 and r.bottom==720:found.append(h)
            return True
        for _ in range(240):
            found.clear();u.EnumWindows(visit,0)
            if len(found)==1:
                self.hwnd=found[0]
                try:self.metrics();break
                except (AssertionError,RuntimeError,FileNotFoundError):pass
            time.sleep(.25)
        assert len(found)==1
        self.hwnd=found[0]; self.metrics()
    def metrics(self):
        if hasattr(self,'_metrics_time') and time.perf_counter()-self._metrics_time<1./60:return self._metrics_value
        with self.log.open('rb') as stream:
            stream.seek(0,2);end=stream.tell();stream.seek(max(0,end-250000))
            raw=stream.read()
        if end>250000:raw=raw[raw.find(b'\n')+1:]
        # The writer may be appending a JSON sample; consume only completed log lines.
        lines=raw[:raw.rfind(b'\n')+1].decode('utf-8-sig',errors='strict').splitlines()
        values=[json.loads(l.split('Metrics ',1)[1]) for l in lines if 'Metrics {' in l]
        if not values:raise RuntimeError('No owned runtime metrics yet')
        v=values[-1]
        assert v['pid']==self.pid and v['sourceSHA']==self.record['sourceSHA'] and v['worldType']==1 and v['netMode']==0
        assert v['locallyControlled'] and v['owner']==v['controller'] and v['localPlayers']==1 and 'combat' in v
        assert v['map'].endswith('/L_CharacterCombatLab')
        self._metrics_time=time.perf_counter();self._metrics_value=v
        return v
    def attack(self, down):
        self.guard();mouse(2 if down else 4);self.mouse_held=down
    def focus(self):
        # Windows may deny SetForegroundWindow from a new console process even
        # with AttachThreadInput. A physical Alt edge unlocks foreground activation;
        # verify the exact owned HWND before allowing ANY gameplay injection.
        owner=w.DWORD();u.GetWindowThreadProcessId(self.hwnd,c.byref(owner))
        assert owner.value==self.pid
        u.ShowWindow(self.hwnd,9)
        key('Alt',True);key('Alt',False)
        u.SetForegroundWindow(self.hwnd)
        for _ in range(30):
            if u.GetForegroundWindow()==self.hwnd:break
            time.sleep(.02)
        self.guard();time.sleep(.25)
        if not self.metrics()['windowActive']:self.click(20,20)
        for _ in range(30):
            self.guard()
            if self.metrics()['windowActive']:return
            time.sleep(.05)
        raise RuntimeError('Owned HWND foreground but Slate viewport inactive')
    def release(self):
        if getattr(self,'right_held',False):mouse(16);self.right_held=False
        super().release()
        if self.mouse_held:mouse(4);self.mouse_held=False
    def prepare(self):
        self.focus()
        if self.metrics()['controlState']==0:
            self.press('Escape',True);time.sleep(.06);self.press('Escape',False);time.sleep(.3)
        observed=self.probe_w()
        if observed!='W':self.toggle_ime();self.ime=True;observed=self.probe_w()
        assert observed=='W'
        # Default PlayerStart is not the measured runway. Use its real lab reset button.
        self.click(640,358);time.sleep(.4)
        self.click(640,205)
        for _ in range(30):
            time.sleep(.1)
            if self.metrics()['controlState']==0:return
        raise RuntimeError('Actual Resume button did not enter Playing')
