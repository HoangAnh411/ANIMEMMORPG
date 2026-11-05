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
from F60Input import Client, u, k, mouse

class BClient(Client):
    def __init__(self, record):
        self.record=record; self.pid=record['pid']; self.log=Path(record['log']); self.ime=False; self.held=set(); self.mouse_held=False
        exe=Path(record['executable']).resolve()
        assert record['role']=='U02PackageB' and exe.is_relative_to(ROOT/'Artifacts/U02/B') and exe.name=='AnimeMMORPG.exe'
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
        lines=self.log.read_text(encoding='utf-8-sig',errors='replace').splitlines()
        values=[json.loads(l.split('Metrics ',1)[1]) for l in lines if 'Metrics {' in l]
        if not values:raise RuntimeError('No owned runtime metrics yet')
        v=values[-1]
        assert v['pid']==self.pid and v['sourceSHA']==self.record['sourceSHA'] and v['worldType']==1 and v['netMode']==0
        assert v['locallyControlled'] and v['owner']==v['controller'] and v['localPlayers']==1 and 'combat' in v
        assert v['map'].endswith('/L_CharacterCombatLab')
        return v
    def attack(self, down):
        self.guard();mouse(2 if down else 4);self.mouse_held=down
    def release(self):
        super().release()
        if self.mouse_held:mouse(4);self.mouse_held=False
    def prepare(self):
        self.focus()
        if self.metrics()['controlState']==0:
            self.press('Escape',True);time.sleep(.06);self.press('Escape',False);time.sleep(.3)
        observed=self.probe_w()
        if observed!='W':self.toggle_ime();self.ime=True;observed=self.probe_w()
        assert observed=='W'
        self.click(640,205)
        for _ in range(30):
            time.sleep(.1)
            if self.metrics()['controlState']==0:return
        raise RuntimeError('Actual Resume button did not enter Playing')

def main():
    p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--inspect',action='store_true');args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    record=json.loads(args.record.read_text(encoding='utf-8-sig'))
    client=BClient(record);client.focus()
    if args.inspect:
        ImageGrab.grab(bbox=client.bounds(),all_screens=True).save(args.out/'inspect.png');return
    # A known, owned focus target avoids exposing or typing into another application.
    u.CreateWindowExW.restype=w.HWND
    u.CreateWindowExW.argtypes=[w.DWORD,w.LPCWSTR,w.LPCWSTR,w.DWORD,c.c_int,c.c_int,c.c_int,c.c_int,w.HWND,w.HMENU,w.HINSTANCE,c.c_void_p]
    helper=u.CreateWindowExW(0,'STATIC','U02-B focus fixture',0x00CF0000,20,60,400,180,None,None,None,None)
    assert helper
    writer=None;meta=dict(process=record,method='Windows SendInput + real native game metrics + bounded screen video',events=[],completed=False)
    try:
        client.prepare();time.sleep(.3)
        initial=client.metrics();meta['baselineAccepted']=initial['combat']['accepted'];assert initial['combat']['accepted']==0
        left,top,right,bottom=client.bounds();bounds=(left,top,right,bottom)
        cv2.setNumThreads(1)
        writer=cv2.VideoWriter(str(args.out/'Input-B.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(right-left,bottom-top));assert writer.isOpened()
        def down(name):return lambda:client.press(name,True)
        def up(name):return lambda:client.press(name,False)
        def click():client.attack(True);time.sleep(.04);client.attack(False)
        def resume():client.click(640,205)
        def away():
            client.guard();u.ShowWindow(helper,5);u.SetForegroundWindow(helper)
            assert u.GetForegroundWindow()==helper
        def back():
            client.focus();u.ShowWindow(helper,0)
            assert client.metrics()['controlState']==2,'Focus alone resumed controls'
        actions=[
            (1.,'W down',down('W')),(1.05,'Ctrl down',down('Ctrl')),
            (1.7,'LMB hold',lambda:client.attack(True)),(1.75,'startup aim',lambda:mouse(1,35,0)),
            (1.78,'jump while busy',down('Space')),(1.86,'jump release',up('Space')),
            (1.96,'active camera turn',lambda:mouse(1,110,0)),(2.8,'LMB release',lambda:client.attack(False)),
            (3.,'attack edge',click),(3.15,'busy attack edge',click),
            (3.7,'W up',up('W')),(3.72,'Ctrl up',up('Ctrl')),
            (4.2,'attack hold across menu',lambda:client.attack(True)),(4.27,'menu in action',down('Escape')),(4.32,'Escape release',up('Escape')),
            (5.,'LMB release in menu',lambda:client.attack(False)),(5.2,'Resume click',resume),(6.1,'fresh attack after Resume',click),
            (6.8,'W before focus',down('W')),(7.,'attack before focus',click),(7.08,'focus away during action',away),
            (8.,'focus return AwaitingResume',back),(8.3,'Resume while W held',resume),
            (9.,'W release gate',up('W')),(9.1,'fresh W',down('W')),(9.7,'W up',up('W')),
            (10.2,'Interacting on',down('G')),(10.25,'G up',up('G')),(10.4,'attack rejected Interacting',click),
            (10.7,'Interacting off',down('G')),(10.75,'G up',up('G')),(10.9,'attack after Interacting',click),
            (11.5,'jump',down('Space')),(11.56,'jump release',up('Space')),(11.65,'attack rejected airborne',click),
            (11.8,'menu while airborne',down('Escape')),(11.85,'Escape release',up('Escape')),(12.3,'Resume click airborne menu',resume),
            (13.,'final attack',click)]
        frames=[];meta['utc']=datetime.now(timezone.utc).isoformat();start=time.perf_counter();i=0;next_frame=start
        while time.perf_counter()-start<14.5:
            elapsed=time.perf_counter()-start
            while i<len(actions) and elapsed>=actions[i][0]:
                scheduled,label,operation=actions[i];operation();meta['events'].append(dict(label=label,scheduled=scheduled,actual=time.perf_counter()-start));i+=1
            foreground=u.GetForegroundWindow()
            if foreground!=helper:client.guard()
            else:assert 7.0<elapsed<8.1,'Unexpected focus fixture activation'
            assert client.bounds()==bounds,'Capture target moved/resized'
            frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=bounds,all_screens=True)),cv2.COLOR_RGB2BGR)
            writer.write(frame);frames.append(time.perf_counter()-start)
            next_frame+=1/30
            if next_frame>time.perf_counter():time.sleep(next_frame-time.perf_counter())
        meta['completed']=i==len(actions);meta['frames']=frames;meta['captureSeconds']=time.perf_counter()-start
        meta['finalMetrics']=client.metrics()
        ImageGrab.grab(bbox=bounds,all_screens=True).save(args.out/'Final.png')
    finally:
        if writer:writer.release()
        client.finish();u.DestroyWindow(helper)
        meta['externalInputMethodRestored']=not client.ime
        (args.out/'input.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    assert meta['completed'] and meta['externalInputMethodRestored']
    print('Completed guarded input/capture; gameplay assertions still require postprocessing')

if __name__=='__main__':main()
