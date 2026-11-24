"""Build-03 focus quarantine regression with a process-owned auxiliary window."""
import ctypes
from ctypes import wintypes
import math
import os
import time
from pathlib import Path

from C1ProfileRun import ProfileSession
from C1Readiness import vector


def w_down():
    read_key = ctypes.WinDLL('user32').GetAsyncKeyState
    read_key.argtypes = [ctypes.c_int]
    read_key.restype = ctypes.c_short
    return bool(read_key(0x57) & 0x8000)


def wait_for_w_up(sample, active, waiting, required):
    consecutive=0
    while consecutive<2:
        if not active():
            consecutive=0
            time.sleep(.1)
            continue
        down=w_down()
        consecutive=0 if down else consecutive+1
        sample(down,consecutive)
        if down:
            waiting()
            if not required:
                raise RuntimeError('WAITING_FOR_KEY_RELEASE')
        if consecutive<2:
            time.sleep(.1)


def capture(record, backend, log, journal, cleanup=False):
    class FocusSession(ProfileSession):
        auxiliary = None
        watch_auxiliary = False

        def guard(self, operation, foreground=True):
            if not self.watch_auxiliary:
                return super().guard(operation, foreground)
            state = super().guard(operation, foreground=False)
            actual = (state['foregroundHWND'],state['foregroundPID'])
            hwnd,pid,ticks = self.auxiliary
            if not backend.u.IsWindow(hwnd) or backend.pid(hwnd)!=pid or backend.process_ticks(pid)!=ticks:
                self.fail('focus_auxiliary_identity',state)
            if actual != (hwnd,pid):
                self.fail('focus_unexpected_window',state)
            return state

    session=FocusSession(record, backend, log, journal, workload={}, output=Path(record["log"]).parent/"Raw")
    wait_for_w_up(lambda down,n: journal.append('focus_pre_setup_key',down=down,consecutive=n),
                  lambda: True, lambda: None, required=False)
    session.setup()
    user=backend.u
    user.GetAsyncKeyState.argtypes=[ctypes.c_int]
    user.GetAsyncKeyState.restype=ctypes.c_short
    user.CreateWindowExW.argtypes=[wintypes.DWORD,wintypes.LPCWSTR,wintypes.LPCWSTR,wintypes.DWORD,
                                   ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,
                                   wintypes.HWND,wintypes.HMENU,wintypes.HINSTANCE,wintypes.LPVOID]
    user.CreateWindowExW.restype=wintypes.HWND
    user.DestroyWindow.argtypes=[wintypes.HWND]
    aux=user.CreateWindowExW(0,'STATIC','C1 focus test owned window',0x00CF0000,50,50,400,160,None,None,None,None)
    if not aux:
        raise ctypes.WinError(ctypes.get_last_error())
    pid=os.getpid()
    session.auxiliary=(aux,pid,backend.process_ticks(pid))
    playing=session.before_w_metrics()
    actor=playing['metrics']['combat']

    def phase(name, sample=None):
        sample = session.fresh_metrics() if sample is None else sample
        m=sample['metrics']
        physical=bool(user.GetAsyncKeyState(0x57)&0x8000)
        journal.append('focus_phase',phase=name,sample=sample,physicalW=physical)
        if (m['combat']['pawnId'],m['combat']['life'])!=(actor['pawnId'],actor['life']):
            session.fail('focus_pawn_life_changed')
        return m,physical

    def motion(a,b):
        return math.dist(vector(a['capsuleCenterWorldCm'])[:2],vector(b['capsuleCenterWorldCm'])[:2])

    try:
        start,physical=phase('initial_playing',playing)
        if physical or start['controlState']!=0 or start['gateW'] is not True:
            session.fail('focus_initial_state')
        offset=log.size()
        session.emit('W',True)
        moving,physical=phase('accepted_hold')
        if (not physical or b'PhysicalPress key=W state=0 accepted=1' not in log.read(offset)
                or motion(start,moving)<1):
            session.fail('focus_initial_movement_missing')
        session.guard('before_deliberate_focus_loss')
        user.ShowWindow(aux,4)  # SW_SHOWNOACTIVATE
        api=backend.focus(aux)
        journal.append('focus_to_auxiliary',api=api,pinned=list(session.auxiliary),offset=log.size())
        session.watch_auxiliary=True
        awaiting,physical=phase('awaiting_resume_inactive')
        for _ in range(6):
            if awaiting['controlState']==2 and not awaiting['windowActive']:
                break
            awaiting,physical=phase('awaiting_resume_poll')
        if awaiting['controlState']!=2 or awaiting['windowActive'] or not physical:
            session.fail('focus_awaiting_resume_missing')
        session.guard('before_return')
        api=backend.focus(session.hwnd)
        session.watch_auxiliary=False
        journal.append('focus_return_to_game',api=api,offset=log.size())
        deadline=backend.now()+2
        while True:
            state=session.guard('focus_return_observation',foreground=False)
            observed=(state['foregroundHWND'],state['foregroundPID'])
            if observed==(session.hwnd,record['pid']):
                break
            if observed not in ((0,0),(None,0),(aux,pid)) or backend.now()>=deadline:
                session.fail('focus_return_not_observed',state)
            backend.sleep(.025)
        session.wait(.25)
        returned,physical=phase('awaiting_resume_active')
        if returned['controlState']!=2 or not returned['windowActive'] or not physical:
            session.fail('focus_return_state')
        resume=returned['menuButtons']['Resume']
        session.resume_attempted=False
        session.click_resume(resume['x'],resume['y'])
        session.wait(.35)
        blocked,physical=phase('playing_hold_blocked')
        session.wait(.35)
        still,still_physical=phase('playing_still_blocked')
        if any(m['controlState']!=0 or m['gateW'] is not False or
               math.hypot(*vector(m['velocityCmPerSec'])[:2])>.5 for m in (blocked,still)):
            session.fail('focus_quarantine_gate_or_speed')
        if not physical or not still_physical or motion(blocked,still)>.5 or still['worldSeconds']<=blocked['worldSeconds']:
            session.fail('focus_quarantine_hold_or_motion')
        offset=log.size()
        session.emit('W',False)
        released,physical=phase('released_rearmed')
        if physical or released['gateW'] is not True or b'PhysicalRelease/Rearm key=W' not in log.read(offset):
            session.fail('focus_rearm_missing')
        status,new=session.pulse_w()
        if status!='PASS':
            session.fail('focus_new_edge_unrecognized')
        _,physical=phase('new_edge_pawn',new['after'])
        session.guard('focus_final_key_up')
        if physical:
            session.fail('focus_final_key_still_down')
        return dict(status='PASS',heldDeltaCm=motion(blocked,still),newEdge=new)
    except Exception:
        state=session.observe('focus_error_key_observation')
        journal.append('focus_error_key',physicalW=w_down(),held=sorted(session.held),
                       lastInput=session.last_input,snapshot=state)
        if 'W' in session.held and not session.failed and (state.get('foregroundHWND'),state.get('foregroundPID'))==(session.hwnd,record['pid']):
            session.watch_auxiliary=False
            session.emit('W',False)
        raise
    finally:
        user.DestroyWindow(aux)
