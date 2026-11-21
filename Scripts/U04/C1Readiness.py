"""Readiness-only state machine; all OS/input/log/time operations injected.

No imports of F60Input, no profiling commands, no gameplay fixture preparation.
After a fault, emission remains permanently latched off. Cleanup sends no input.
"""
import json
import math
import os
import re

class ProbeError(RuntimeError):
    pass

class Journal:
    def __init__(self,path,clock):
        self.file=open(path,'x',encoding='utf-8',newline='\n');self.clock=clock;self.seq=0
        self.context=dict(targetHWND=None,expectedPID=None,actualPID=None,expectedCreationUTC=None,
                          expectedCreationTicks=None,actualCreationTicks=None,isWindow=None,
                          foregroundHWND=None,foregroundPID=None,clientRect=None,clientOriginScreen=None,
                          errors=['target_not_selected'],snapshotMonotonic=None)
    def append(self,event,**data):
        self.seq+=1;row=dict(self.context);row.update(data);row.update(seq=self.seq,monotonic=self.clock(),event=event)
        self.file.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');self.file.flush();os.fsync(self.file.fileno())
        return row
    def close(self):self.file.close()

class FileLog:
    def __init__(self,path):self.path=path
    def size(self):return os.path.getsize(self.path) if os.path.exists(self.path) else 0
    def read(self,offset):
        if not os.path.exists(self.path):return b''
        with open(self.path,'rb') as f:f.seek(offset);return f.read()

def vector(value):
    if isinstance(value,str):
        parts=re.fullmatch(r'X=([-+\d.eE]+) Y=([-+\d.eE]+) Z=([-+\d.eE]+)',value)
        if not parts:raise ProbeError('bad_capsule_vector')
        result=[float(x) for x in parts.groups()]
    else:result=list(value)
    if len(result)!=3 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in result):raise ProbeError('bad_vector')
    return result

class Session:
    def __init__(self,record,backend,log,journal):
        self.record=record;self.b=backend;self.log=log;self.j=journal;self.hwnd=None
        self.failed=False;self.held=set();self.last_input=None;self.native_session=None
        self.pending_metrics=False;self.focus_attempted=False;self.resume_attempted=False
        self.click_anchor=None
        self.j.context.update(expectedPID=record['pid'],expectedCreationUTC=record['creationUTC'],expectedCreationTicks=record['creationTicks'])
        self.j.append('session_created',record=record)

    def observe(self,operation):
        try:s=self.b.inspect(self.hwnd)
        except Exception as e:s=dict(errors=['inspect:'+repr(e)])
        # All journal rows carry the same shape, even when information is unavailable.
        data=dict(targetHWND=self.hwnd,expectedPID=self.record['pid'],actualPID=None,
                  expectedCreationUTC=self.record['creationUTC'],expectedCreationTicks=self.record['creationTicks'],
                  actualCreationTicks=None,isWindow=None,foregroundHWND=None,foregroundPID=None,
                  clientRect=None,clientOriginScreen=None,errors=[])
        data.update(s)
        self.j.context=data|dict(snapshotMonotonic=self.b.now())
        self.j.append(operation,**data,held=sorted(self.held),lastInput=self.last_input,latched=self.failed)
        return data

    def fail(self,reason,snapshot=None):
        self.failed=True
        self.j.append('guard_failed',reason=reason,snapshot=snapshot,held=sorted(self.held),lastInput=self.last_input)
        raise ProbeError(reason)

    def guard(self,operation,foreground=True):
        if self.failed:raise ProbeError('emission_latched_off')
        s=self.observe(operation)
        if s['isWindow'] is False:self.fail('hwnd_invalid',s)
        if s['actualPID'] is not None and s['actualPID']!=self.record['pid']:self.fail('hwnd_pid_mismatch',s)
        if s['actualCreationTicks'] is not None and s['actualCreationTicks']!=self.record['creationTicks']:self.fail('process_creation_mismatch',s)
        if s['errors'] or any(s[k] is None for k in ('isWindow','actualPID','actualCreationTicks','clientRect','clientOriginScreen','foregroundHWND','foregroundPID')):
            self.fail('window_information_error',s)
        if foreground and s['foregroundHWND']!=self.hwnd:self.fail('foreground_hwnd_mismatch',s)
        if foreground and s['foregroundPID']!=self.record['pid']:self.fail('foreground_pid_mismatch',s)
        if s['clientRect']!=[0,0,1280,720]:self.fail('client_rect_changed',s)
        return s

    def select(self,timeout=30):
        deadline=self.b.now()+timeout
        while self.b.now()<deadline:
            windows=self.b.windows(self.record['pid']);self.j.append('window_candidates',windows=windows)
            if len(windows)>1:self.fail('ambiguous_target_hwnd')
            if len(windows)==1:
                self.hwnd=windows[0];self.guard('hwnd_selected',foreground=False);return
            self.b.sleep(.05)
        self.fail('target_hwnd_timeout')

    def focus_once(self):
        if self.focus_attempted:self.fail('focus_retry_forbidden')
        self.focus_attempted=True
        self.guard('before_restore',foreground=False);self.b.restore(self.hwnd)
        self.guard('after_restore',foreground=False)
        self.guard('before_initial_focus',foreground=False);self.b.focus(self.hwnd)
        self.guard('after_initial_focus');self.wait(.25)

    def wait(self,seconds):
        deadline=self.b.now()+seconds
        while self.b.now()<deadline:
            self.guard('before_wait');self.b.sleep(min(.02,deadline-self.b.now()));self.guard('after_wait')

    def emit(self,key,down):
        # This check is adjacent to every individual SendInput, including key-up.
        state=self.guard('before_input:'+key+(' down' if down else ' up'))
        if key=='LMB':
            anchor=self.click_anchor
            if not anchor or any(state[k]!=anchor[k] for k in ('clientRect','clientOriginScreen')):self.fail('click_geometry_changed')
            cursor=self.b.cursor_position();self.j.append('click_actual_cursor',point=cursor)
            if cursor!=anchor['point']:self.fail('click_cursor_changed')
            hit=self.b.window_at(anchor['point'])
            self.j.append('click_edge_hit_test',hit=hit,point=anchor['point'])
            if hit['rootHWND']!=self.hwnd or hit['pid']!=self.record['pid']:self.fail('click_edge_point_changed')
            self.guard('after_click_edge_hit_test')
        planned=dict(key=key,down=down)
        self.j.append('input_planned',**planned)
        # Conservatively retain a pending down if the OS call fails or reports short send.
        if down:self.held.add(key)
        try:sent=self.b.send(key,down)
        except Exception as e:self.fail('input_send_error:'+repr(e))
        if sent!=1:self.fail('input_short_send')
        if not down:self.held.discard(key)
        self.last_input=planned|dict(monotonic=self.b.now())
        self.j.append('input_sent',**self.last_input,held=sorted(self.held))
        self.guard('after_input:'+key)

    def tap(self,key,duration=.035):
        self.emit(key,True);self.wait(duration);self.emit(key,False)

    def console_metrics(self):
        self.tap('Console');self.wait(.2)
        for ch in 'u01metrics':self.tap('CHAR:'+ch,.012)
        self.tap('Enter');self.wait(.25)

    def click_resume(self,x,y):
        if self.resume_attempted:self.fail('resume_retry_forbidden')
        self.resume_attempted=True
        s=self.guard('before_coordinate_conversion');left,top,right,bottom=s['clientRect']
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (x,y)) or not(left<=x<right and top<=y<bottom):self.fail('resume_outside_client',s)
        if not(left<=round(x)<right and top<=round(y)<bottom):self.fail('resume_rounded_outside_client',s)
        point=self.b.client_to_screen(self.hwnd,round(x),round(y))
        after=self.guard('after_coordinate_conversion')
        if any(after[k]!=s[k] for k in ('clientRect','clientOriginScreen')) or point!=[s['clientOriginScreen'][0]+round(x),s['clientOriginScreen'][1]+round(y)]:self.fail('coordinate_geometry_changed')
        self.click_anchor=dict(clientRect=s['clientRect'],clientOriginScreen=s['clientOriginScreen'],point=point)
        self.guard('before_point_hit_test');hit=self.b.window_at(point)
        self.j.append('point_hit_test',client=[x,y],screen=point,hit=hit)
        if hit['rootHWND']!=self.hwnd or hit['pid']!=self.record['pid']:self.fail('resume_point_other_window')
        self.guard('before_cursor_move');self.b.move_cursor(point);self.guard('after_cursor_move')
        self.wait(.08)
        # Recheck the window at the actual point after waiting, before any button edge.
        self.guard('before_click');hit=self.b.window_at(point)
        if hit['rootHWND']!=self.hwnd or hit['pid']!=self.record['pid']:self.fail('resume_point_changed')
        self.emit('LMB',True);self.wait(.08);self.emit('LMB',False);self.guard('after_click')

    def toggle_ime(self):
        self.guard('before_ime');self.emit('Ctrl',True);self.emit('Shift',True)
        self.wait(.06);self.emit('Shift',False);self.emit('Ctrl',False);self.wait(.15);self.guard('after_ime')

    def validate_metrics(self,m):
        expected={'pid':self.record['pid'],'worldType':1,'netMode':0,'sourceSHA':self.record['sourceSHA'],'locallyControlled':True,'localPlayers':1}
        for key,value in expected.items():
            if m.get(key)!=value:self.fail('metrics_identity:'+key)
        if not m.get('pawn') or not m.get('controller') or m.get('owner')!=m['controller']:self.fail('metrics_pawn_ownership')
        if not str(m.get('map','')).endswith('/L_CharacterCombatLab') or not m.get('world') or not m.get('worldContext'):self.fail('metrics_world')
        if not re.fullmatch('[0-9A-Fa-f]{32}',m.get('runID','')):self.fail('metrics_session_missing')
        identity={k:m[k] for k in ('runID','world','worldContext','pawn','controller')}
        if self.native_session is None:self.native_session=identity;self.j.append('native_session_bound',identity=identity)
        elif identity!=self.native_session:self.fail('metrics_session_changed')
        if not isinstance(m.get('worldSeconds'),(int,float)) or not math.isfinite(m['worldSeconds']):self.fail('metrics_world_time')
        vector(m.get('capsuleCenterWorldCm'))

    def fresh_metrics(self,timeout=5):
        if self.pending_metrics:self.fail('metrics_request_overlap')
        self.pending_metrics=True
        try:
            offset=self.log.size();self.j.append('metrics_request',offset=offset)
            # Ignore any line that was already partly written at the request boundary.
            boundary=(offset==0 or self.log.read(offset-1)[:1]==b'\n')
            self.console_metrics();deadline=self.b.now()+timeout
            while self.b.now()<deadline:
                self.guard('metrics_poll')
                if self.log.size()<offset:self.fail('log_truncated')
                data=self.log.read(offset);start=0
                if not boundary:
                    pos=data.find(b'\n')
                    if pos<0:self.wait(.02);continue
                    start=pos+1
                for line in data[start:].splitlines(keepends=True):
                    line_start=offset+start;start+=len(line)
                    if not line.endswith(b'\n'):break
                    if b'Metrics ' not in line:continue
                    try:m=json.loads(line.split(b'Metrics ',1)[1].decode('utf-8-sig'))
                    except (ValueError,UnicodeError):self.fail('metrics_malformed_complete_line')
                    self.validate_metrics(m)
                    sample=dict(requestOffset=offset,lineOffset=line_start,endOffset=offset+start,metrics=m)
                    self.j.append('metrics_received',sample=sample);return sample
                self.wait(.02)
            self.fail('metrics_timeout')
        finally:self.pending_metrics=False

    def pulse_w(self):
        before=self.fresh_metrics();m=before['metrics']
        if m.get('controlState')!=0 or not m.get('windowActive') or not m.get('gateW') or m.get('motorLocked'):self.fail('before_w_not_playing')
        if math.hypot(*vector(m['velocityCmPerSec'])[:2])>1:self.fail('pawn_not_stationary_before_w')
        offset=self.log.size();down=self.b.now();self.j.append('w_log_boundary',offset=offset)
        self.emit('W',True);self.wait(.35);self.emit('W',False);up=self.b.now();self.wait(.35)
        after=self.fresh_metrics();n=after['metrics']
        edges=self.log.read(offset);edges=edges[:edges.rfind(b'\n')+1]
        press=re.findall(rb'PhysicalPress key=(\S+) state=(\d+) accepted=(\d+)',edges)
        w=[p for p in press if p[0]==b'W'];none=[p for p in press if p[0]==b'None']
        observation=dict(before=before,after=after,inputOffset=offset,physicalLogEnd=self.log.size(),down=down,up=up,presses=[list(x.decode() for x in p) for p in press])
        self.j.append('w_observation',observation=observation)
        if not w and none:return 'IME_REQUIRED',observation
        if len(w)!=1 or w[0][1:]!=(b'0',b'1') or b'PhysicalRelease/Rearm key=W' not in edges:self.fail('current_w_edges_missing_or_rejected')
        if n.get('controlState')!=0 or not n.get('windowActive'):self.fail('after_w_not_playing')
        if n['worldSeconds']<=m['worldSeconds']:self.fail('pawn_world_time_not_advancing')
        a,b=vector(m['capsuleCenterWorldCm']),vector(n['capsuleCenterWorldCm']);delta=[y-x for x,y in zip(a,b)]
        yaw=re.search(r'(?:^| )Y=([-+\d.eE]+)',m.get('aimYawPitchDegrees',''))
        if not yaw:self.fail('missing_control_yaw')
        angle=math.radians(float(yaw[1]));forward=delta[0]*math.cos(angle)+delta[1]*math.sin(angle)
        lateral=abs(-delta[0]*math.sin(angle)+delta[1]*math.cos(angle));horizontal=math.hypot(*delta[:2])
        maximum=m.get('maxSpeedCmPerSec',0)*(n['worldSeconds']-m['worldSeconds']+1)
        if horizontal<1 or forward<1 or lateral>max(5,forward*.25) or horizontal>maximum:self.fail('pawn_horizontal_motion_not_matching_w')
        observation['motion']=dict(delta=delta,forwardCm=forward,lateralCm=lateral,horizontalCm=horizontal)
        return 'PASS',observation

    def setup(self):
        self.select();self.focus_once();sample=self.fresh_metrics();m=sample['metrics']
        if m['controlState'] in (1,2):
            resume=m.get('menuButtons',{}).get('Resume')
            if not m.get('menuVisible') or not resume or resume.get('enabled') is not True:self.fail('resume_widget_missing_or_disabled')
            self.click_resume(resume['x'],resume['y']);self.wait(.25);sample=self.fresh_metrics();m=sample['metrics']
        if m['controlState']!=0 or not m.get('windowActive'):self.fail('resume_did_not_enter_playing')
        status,evidence=self.pulse_w()
        if status=='IME_REQUIRED':
            self.toggle_ime();status,evidence=self.pulse_w()
            if status!='PASS':self.fail('ime_single_attempt_failed')
        if self.held:self.fail('held_edges_at_success')
        self.j.append('readiness_pass',evidence=evidence);return evidence

def run_probe(record,backend,log,journal,cleanup=True):
    """Both paths end here: identified process stop only, never keyboard cleanup."""
    session=None;result=dict(status='INVALID')
    def note(event,**data):
        try:journal.append(event,**data)
        except Exception as e:result.update(status='INVALID',journalError=repr(e))
    try:
        session=Session(record,backend,log,journal)
        result.update(evidence=session.setup(),status='PASS')
    except Exception as e:
        if session:session.failed=True
        held=sorted(session.held) if session else []
        note('probe_invalid',error=repr(e),held=held,lastInput=session.last_input if session else None)
        result.update(status='INVALID',error=repr(e),held=held)
    finally:
        # No finish(), release(), quit console, IME restore or focus reacquisition.
        if cleanup:
            try:
                note('before_owned_stop',held=sorted(session.held) if session else [],latched=session.failed if session else True)
                stop=backend.stop_owned(record,timeout=30)
                result.update(processExited=True,exitEvidence=stop);note('owned_process_exited',evidence=stop)
            except Exception as e:
                result.update(status='INVALID',processExited=False,cleanupError=repr(e));note('owned_stop_failed',error=repr(e))
    return result
