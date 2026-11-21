"""Offline replay only: fake Win32, SendInput, process stop, clock and log producer.

Never constructs C1Win32.Backend. Retains expected/actual table, transcript and
durable journals for every replay. Historical command fixtures are read-only.
"""
import argparse
import copy
import csv
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
import types
import sys
import ast
from unittest.mock import patch
from C1Identity import verify_identity, windows_argv, render_command, creation_ticks
from C1Readiness import Journal, Session, ProbeError, run_probe
from C1Run import parse_args, arguments, NATIVE, ROOT

CREATED='2026-11-21T05:45:26.1662990Z'

def record():
    root=Path('D:/Probe With Spaces/Run-01')
    exe=Path('D:/Package With Spaces/AnimeMMORPG.exe')
    args=arguments(exe,root,'Run-01')
    return dict(pid=1234,creationUTC=CREATED,creationTicks=creation_ticks(CREATED),executable=str(exe),binarySHA256='a'*64,sourceSHA=NATIVE,runId='Run-01',userDir=str(root/'User'),log=str(root/'Game.log'),arguments=args)

class FakeLog:
    def __init__(self):self.data=b''
    def size(self):return len(self.data)
    def read(self,offset):return self.data[offset:]
    def add(self,line):self.data+=line.encode('utf-8')

class FakeBackend:
    """No native libraries, subprocesses or real input. All side effects recorded."""
    def __init__(self,log,mode='playing',fault=None):
        self.log=log;self.mode=mode;self.t=10.;self.fg=101;self.fgpid=1234;self.owner=1234
        self.valid=True;self.creation=creation_ticks(CREATED);self.errors=[];self.sent=[]
        self.inspects=0;self.inspect_fault=fault;self.sleep_fault=None;self.after_send=None
        self.focus_calls=0;self.stopped=0;self.verify_calls=0;self.point_calls=0
        self.state=1 if mode.startswith('menu') else 0;self.cmd='';self.metrics_count=0
        self.pulses=0;self.ime=False;self.position=[0.,0.,100.];self.session='a'*32;self.pending=None
        self.rect=[0,0,1280,720];self.origin=[50,60];self.on_convert=None
        self.cursor=[0,0]
        self.log.add('old PhysicalPress key=W state=0 accepted=1 reason=Ready\nold PhysicalRelease/Rearm key=W\n')
    def now(self):return self.t
    def sleep(self,s):
        self.t+=s
        if self.pending and self.mode=='partial_then_complete':self.log.data+=self.pending;self.pending=None
        if self.sleep_fault:self.sleep_fault(self)
    def windows(self,pid):return [101,102] if self.mode=='ambiguous' else [] if self.mode=='no_window' else [101]
    def inspect(self,hwnd):
        self.inspects+=1
        if self.inspect_fault:self.inspect_fault(self)
        return dict(isWindow=self.valid,actualPID=self.owner,actualCreationTicks=self.creation,foregroundHWND=self.fg,foregroundPID=self.fgpid,clientRect=self.rect[:],clientOriginScreen=self.origin[:],errors=self.errors[:])
    def restore(self,hwnd):pass
    def focus(self,hwnd):
        self.focus_calls+=1
        if self.mode=='focus_denied':self.fg=202;self.fgpid=9999
    def client_to_screen(self,hwnd,x,y):
        if self.on_convert:self.on_convert(self)
        return [50+x,60+y]
    def window_at(self,point):
        self.point_calls+=1
        bad=self.mode=='menu_other_point' or self.mode=='menu_point_changed' and self.point_calls>=2
        return dict(hwnd=303,rootHWND=202 if bad else 101,pid=1234)
    def move_cursor(self,point):self.cursor=point[:]
    def cursor_position(self):return self.cursor[:]
    def metrics(self):
        self.metrics_count+=1
        m=dict(pid=1234,sourceSHA=NATIVE,worldType=1,netMode=0,locallyControlled=True,localPlayers=1,runID=self.session,
               world='/Game/AnimeMMORPG/Maps/L_CharacterCombatLab.L_CharacterCombatLab',worldContext='Context_01',map='/Game/AnimeMMORPG/Maps/L_CharacterCombatLab',pawn='Pawn_01',controller='PC_01',owner='PC_01',
               worldSeconds=self.t,controlState=self.state,windowActive=True,gateW=True,motorLocked=False,velocityCmPerSec='X=0.000 Y=0.000 Z=0.000',capsuleCenterWorldCm=self.position[:],aimYawPitchDegrees='P=0.000 Y=0.000 R=0.000',maxSpeedCmPerSec=500,menuVisible=self.state!=0)
        if self.state:m['menuButtons']=dict(Resume=dict(x=640,y=240,enabled=True))
        if self.mode=='menu_missing':m.pop('menuButtons',None)
        if self.mode=='menu_outside':m['menuButtons']['Resume']['x']=1280
        if self.mode=='menu_rounded_outside':m['menuButtons']['Resume']['x']=1279.9
        if self.mode=='menu_disabled':m['menuButtons']['Resume']['enabled']=False
        if self.mode=='wrong_pid':m['pid']=999
        if self.mode=='wrong_world':m['worldType']=3
        if self.mode=='wrong_net':m['netMode']=3
        if self.mode=='wrong_source':m['sourceSHA']='f'*40
        if self.mode=='missing_session':m.pop('runID')
        if self.mode=='wrong_owner':m['owner']='OtherPC'
        if self.mode=='session_changed' and self.metrics_count>1:m['runID']='b'*32
        if self.mode=='pawn_changed' and self.pulses:m['pawn']='Pawn_02'
        if self.mode=='world_time_still':m['worldSeconds']=1.
        if self.mode=='not_active':m['windowActive']=False
        if self.mode=='not_playing':m['controlState']=7
        return m
    def send(self,key,down):
        self.sent.append(dict(key=key,down=down,time=self.t))
        if not down and key.startswith('CHAR:'):self.cmd+=key[5:]
        if key=='Enter' and not down:
            if self.cmd!='u01metrics':raise RuntimeError('unexpected console command:'+self.cmd)
            self.cmd=''
            if self.mode!='stale_metrics':
                line='LogU01Control: Display: Metrics '+json.dumps(self.metrics())+'\n'
                if self.mode=='malformed_metrics':line='LogU01Control: Display: Metrics {broken}\n'
                if self.mode in ('partial_metrics','partial_then_complete'):
                    raw=line.encode();self.log.data+=raw[:len(raw)//2];self.pending=raw[len(raw)//2:]
                else:self.log.add(line)
                if self.mode=='log_truncated':self.log.data=b''
        if key=='LMB' and not down and self.mode!='menu_no_transition':self.state=0
        if key=='Shift' and not down:self.ime=True
        if key=='W' and down:
            self.pulses+=1
            if self.mode not in ('stale_w','old_none'):
                observed='None' if self.mode in ('ime_current_none','ime_fails') and not self.ime or self.mode=='ime_fails' else 'W'
                accepted=0 if self.mode=='w_rejected' else 1
                self.log.add(f'LogU01Control: PhysicalPress key={observed} state=0 accepted={accepted} reason=Ready\n')
        if key=='W' and not down:
            if self.mode not in ('stale_w','old_none'):self.log.add('LogU01Control: PhysicalRelease/Rearm key=W\n')
            if self.mode not in ('no_motion','stale_w','old_none','ime_fails') and not (self.mode=='ime_current_none' and not self.ime):
                delta=[0,0,100] if self.mode=='z_only' else [-100,0,0] if self.mode=='reverse_motion' else [100,100,0] if self.mode=='lateral_motion' else [100,0,0]
                self.position=[a+b for a,b in zip(self.position,delta)]
        if self.after_send:self.after_send(self,key,down)
        return 0 if self.mode=='short_send' else 1
    def verify_owned(self,r):
        self.verify_calls+=1
        if self.mode=='cleanup_identity_changed':raise RuntimeError('process_creation_mismatch')
    def stop_owned(self,r,timeout):
        self.verify_owned(r)
        self.stopped+=1
        if self.mode=='exit_timeout':raise RuntimeError('owned_exit_timeout')
        return dict(pid=r['pid'],creationUTC=r['creationUTC'],exitCode=0,wait='fake-signaled',identityVerifiedAtStop=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False);results=[];suite=unittest.TestSuite()
    def add(name,expected,fn):
        def test(self):
            actual,details=fn()
            results.append(dict(case=name,expected=expected,actual=actual,passed=actual==expected,**details))
            self.assertEqual(actual,expected)
        cls=type('Offline_'+name,(unittest.TestCase,),{'runTest':test})
        suite.addTest(cls())

    def identity_case(mutate=None,old=None):
        r=record()
        if old:
            command=json.loads((ROOT.parent/'Runs'/old/'command.json').read_text())['arguments']
            r['arguments']=command;r['executable']=command[0]
            r['runId']=old;r['userDir']=next(x.split('=',1)[1] for x in command if x.startswith('-UserDir='));r['log']=next(x.split('=',1)[1] for x in command if x.startswith('-abslog='))
        live=dict(pid=r['pid'],creationUTC=CREATED,creationTicks=creation_ticks(CREATED),executable=r['executable'],commandLine=render_command(r['arguments']))
        if mutate:mutate(r,live)
        try:identity=verify_identity(r,live);actual='PASS'
        except Exception as e:actual=str(e)
        return actual,dict(record=r,live=live)
    add('identity_spaces_and_quoted_sha','PASS',lambda:identity_case(lambda r,l:l.update(commandLine=l['commandLine'].replace('-U02SourceSHA='+NATIVE,'-U02SourceSHA="'+NATIVE+'"'))))
    add('identity_unquoted_sha','PASS',identity_case)
    for old in ('Method-Timing-01','Method-Timing-01-Replacement'):
        add('historical_argv_'+old,'PASS',lambda old=old:identity_case(old=old))
    # Use the actual recorded raw quoted command line from recovery, not just regenerated argv.
    def historical_raw():
        actual,details=identity_case(old='Method-Timing-01');r=details['record'];l=details['live']
        raw=json.loads((ROOT.parent/'Runs/Method-Timing-01/recovery-identity.json').read_text())
        l.update(pid=raw['ProcessId'],creationUTC=raw['creationUTC'],executable=raw['ExecutablePath'],commandLine=raw['CommandLine']);r.update(pid=l['pid'],creationUTC=l['creationUTC'],creationTicks=creation_ticks(l['creationUTC']));l['creationTicks']=r['creationTicks']
        try:verify_identity(r,l);actual='PASS'
        except Exception as e:actual=str(e)
        return actual,dict(record=r,live=l)
    add('historical_raw_quoted_command','PASS',historical_raw)
    mutations=[('sha_wrong',lambda s:s.replace(NATIVE,'f'*40),'argument_mismatch:-u02sourcesha'),
               ('sha_prefix',lambda s:s.replace(NATIVE,NATIVE+'00'),'argument_mismatch:-u02sourcesha'),
               ('sha_in_other_argument',lambda s:s.replace('-U02SourceSHA='+NATIVE,'-Note=-U02SourceSHA='+NATIVE),'argument_mismatch:-u02sourcesha'),
               ('wrong_userdir',lambda s:render_command([x+'-extra' if x.casefold().startswith('-userdir=') else x for x in windows_argv(s)]),'argument_mismatch:-userdir'),
               ('wrong_log',lambda s:s.replace('Game.log','Game.log.extra'),'argument_mismatch:-abslog'),
               ('wrong_runid',lambda s:s.replace('-U02RunId=Run-01','-U02RunId=Run-010'),'argument_mismatch:-u02runid'),
               ('duplicate_sha',lambda s:s+' -U02SourceSHA='+NATIVE,'duplicate_argument:-u02sourcesha')]
    def mutate_command(mut,r,live):
        before=live['commandLine'];after=mut(before);assert before!=after,'negative fixture mutation did nothing'
        live['commandLine']=after
    for name,mut,expected in mutations:add('identity_'+name,expected,lambda mut=mut:identity_case(lambda r,l:mutate_command(mut,r,l)))
    add('identity_wrong_exe','executable_mismatch',lambda:identity_case(lambda r,l:l.update(executable='D:/Other/AnimeMMORPG.exe')))
    add('identity_wrong_argv_exe','argv_executable_mismatch',lambda:identity_case(lambda r,l:l.update(commandLine=l['commandLine'].replace(r['executable'],'D:/Other/AnimeMMORPG.exe',1))))
    add('identity_pid_reuse','process_creation_mismatch',lambda:identity_case(lambda r,l:l.update(creationTicks=creation_ticks(CREATED)+10_000_000)))
    add('identity_wrong_pid','process_pid_mismatch',lambda:identity_case(lambda r,l:l.update(pid=1235)))
    def parser_roundtrip():
        cases=[['D:/With Spaces/app.exe','-Path=D:/Path With Spaces/','-Value=a"b'],['D:/app.exe','-Empty=','-Tail=D:\\Tail With Spaces\\']]
        good=all(windows_argv(render_command(case))==case for case in cases)
        return 'PASS' if good else 'FAIL',dict(cases=cases)
    add('argv_roundtrip_quotes_backslashes','PASS',parser_roundtrip)

    def static_route():
        files=['C1Run.py','C1Readiness.py']
        banned={'prepare','begin','finish','release','toggle_ime_restore','wait_until'}
        calls=[]
        for name in files:
            tree=ast.parse((ROOT/'Scripts/U04'/name).read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):calls.append(node.func.attr)
                if isinstance(node,ast.ImportFrom):assert node.module not in ('F60Input','IdentityProcessA')
        assert not banned.intersection(calls),calls
        return 'PASS',dict(files=files,forbiddenCalls=sorted(banned),foundForbiddenCalls=[])
    add('static_readiness_only_route','PASS',static_route)

    def replay(name,mode='playing',fault=None,configure=None):
        path=args.out/(name+'.journal.jsonl');log=FakeLog();b=FakeBackend(log,mode,fault)
        if mode=='old_none':log.add('old PhysicalPress key=None state=0 accepted=1\n')
        if mode=='stale_metrics':log.add('old Metrics '+json.dumps(b.metrics())+'\n')
        if configure:configure(b)
        j=Journal(path,b.now)
        try:result=run_probe(record(),b,log,j)
        finally:j.close()
        rows=[json.loads(l) for l in path.read_text().splitlines()]
        fault_rows=[i for i,x in enumerate(rows) if x['event'] in ('guard_failed','probe_invalid')]
        sent_after=sum(x['event']=='input_sent' for x in rows[min(fault_rows)+1:]) if fault_rows else 0
        assert sent_after==0,'input after failure'
        assert [x['seq'] for x in rows]==list(range(1,len(rows)+1))
        assert all(b['monotonic']>=a['monotonic'] for a,b in zip(rows,rows[1:]))
        fields=['targetHWND','expectedPID','actualPID','expectedCreationUTC','actualCreationTicks','foregroundHWND','foregroundPID','clientRect','clientOriginScreen']
        assert all(all(k in x for k in fields) for x in rows)
        assert b.focus_calls<=1,'focus reacquisition'
        assert b.stopped==(0 if mode=='cleanup_identity_changed' else 1),'unexpected process stop count'
        if mode=='stale_w' or mode=='old_none':assert not b.ime,'IME based on historical evidence'
        actual=result['status']
        if actual=='INVALID':
            err=result.get('error') or result.get('cleanupError','')
            actual='INVALID:'+re.sub(r'^\w+\([\'"]|[\'"]\)$','',err)
        details=dict(result=result,inputCount=len(b.sent),eventsAfterFault=sent_after,focusAttempts=b.focus_calls,stopAttempts=b.stopped,imeToggled=b.ime,journal=path.name)
        return actual,details

    modes=[('playing','PASS'),('menu','PASS'),('partial_then_complete','PASS'),('ime_current_none','PASS'),
           ('focus_denied','INVALID:foreground_hwnd_mismatch'),('ambiguous','INVALID:ambiguous_target_hwnd'),('no_window','INVALID:target_hwnd_timeout'),
           ('menu_missing','INVALID:resume_widget_missing_or_disabled'),('menu_disabled','INVALID:resume_widget_missing_or_disabled'),('menu_outside','INVALID:resume_outside_client'),('menu_rounded_outside','INVALID:resume_rounded_outside_client'),
           ('menu_other_point','INVALID:resume_point_other_window'),('menu_point_changed','INVALID:resume_point_changed'),('menu_no_transition','INVALID:resume_did_not_enter_playing'),
           ('wrong_pid','INVALID:metrics_identity:pid'),('wrong_world','INVALID:metrics_identity:worldType'),('wrong_net','INVALID:metrics_identity:netMode'),('wrong_source','INVALID:metrics_identity:sourceSHA'),
           ('missing_session','INVALID:metrics_session_missing'),('wrong_owner','INVALID:metrics_pawn_ownership'),('session_changed','INVALID:metrics_session_changed'),
           ('pawn_changed','INVALID:metrics_session_changed'),('world_time_still','INVALID:pawn_world_time_not_advancing'),
           ('not_active','INVALID:resume_did_not_enter_playing'),('not_playing','INVALID:resume_did_not_enter_playing'),
           ('stale_metrics','INVALID:metrics_timeout'),('partial_metrics','INVALID:metrics_timeout'),('malformed_metrics','INVALID:metrics_malformed_complete_line'),('log_truncated','INVALID:log_truncated'),
           ('stale_w','INVALID:current_w_edges_missing_or_rejected'),('old_none','INVALID:current_w_edges_missing_or_rejected'),('w_rejected','INVALID:current_w_edges_missing_or_rejected'),
           ('no_motion','INVALID:pawn_horizontal_motion_not_matching_w'),('z_only','INVALID:pawn_horizontal_motion_not_matching_w'),('reverse_motion','INVALID:pawn_horizontal_motion_not_matching_w'),('lateral_motion','INVALID:pawn_horizontal_motion_not_matching_w'),
           ('ime_fails','INVALID:ime_single_attempt_failed'),('short_send','INVALID:input_short_send'),
           ('cleanup_identity_changed','INVALID:process_creation_mismatch'),('exit_timeout','INVALID:owned_exit_timeout')]
    for mode,expected in modes:add('replay_'+mode,expected,lambda mode=mode:replay('replay_'+mode,mode))

    guard_cases=[('hwnd_invalid',lambda b:setattr(b,'valid',False)),('hwnd_pid_mismatch',lambda b:setattr(b,'owner',999)),
                 ('process_creation_mismatch',lambda b:setattr(b,'creation',b.creation+1)),('foreground_hwnd_mismatch',lambda b:setattr(b,'fg',102)),
                 ('foreground_pid_mismatch',lambda b:setattr(b,'fgpid',999)),('window_information_error',lambda b:b.errors.append('GetClientRect failed'))]
    for reason,mutation in guard_cases:
        def configure(b,mutation=mutation):b.after_send=lambda b,key,down:mutation(b)
        add('guard_after_down_'+reason,'INVALID:'+reason,lambda reason=reason,configure=configure:replay('guard_after_down_'+reason,configure=configure))
    # Focus changes after a character down, before its matching up; no further global release.
    def between_console(b):b.after_send=lambda b,key,down:setattr(b,'fg',102) if key=='CHAR:m' and down else None
    add('loss_mid_console_down','INVALID:foreground_hwnd_mismatch',lambda:replay('loss_mid_console_down',configure=between_console))
    def during_click_wait(b):
        b.sleep_fault=lambda b:setattr(b,'fg',102) if b.sent and b.sent[-1]['key']=='LMB' and b.sent[-1]['down'] else None
    add('loss_between_mouse_down_up','INVALID:foreground_hwnd_mismatch',lambda:replay('loss_between_mouse_down_up','menu',configure=during_click_wait))
    def during_w_wait(b):b.sleep_fault=lambda b:setattr(b,'fg',102) if b.sent and b.sent[-1]['key']=='W' and b.sent[-1]['down'] else None
    add('loss_between_w_down_up','INVALID:foreground_hwnd_mismatch',lambda:replay('loss_between_w_down_up',configure=during_w_wait))
    def during_ime(b):b.after_send=lambda b,key,down:setattr(b,'fg',102) if key=='Ctrl' and down else None
    add('loss_during_ime','INVALID:foreground_hwnd_mismatch',lambda:replay('loss_during_ime','ime_current_none',configure=during_ime))
    def convert_failure(b):b.on_convert=lambda b:setattr(b,'origin',[51,60])
    add('client_origin_changed','INVALID:coordinate_geometry_changed',lambda:replay('client_origin_changed','menu',configure=convert_failure))
    def cursor_changed(b):
        b.sleep_fault=lambda b:setattr(b,'cursor',[999,999]) if b.cursor!=[0,0] else None
    add('actual_cursor_moved_before_click','INVALID:click_cursor_changed',lambda:replay('actual_cursor_moved_before_click','menu',configure=cursor_changed))
    def throws(b):
        def inspect_error(_):raise OSError('fake GetWindowThreadProcessId failure')
        b.inspect_fault=inspect_error
    add('win32_information_exception','INVALID:window_information_error',lambda:replay('win32_information_exception',configure=throws))
    add('preexisting_partial_metrics_not_accepted','INVALID:metrics_timeout',lambda:replay('preexisting_partial_metrics_not_accepted',configure=lambda b:b.log.add('LogU01Control: Metrics {"old":')))
    def overlap():
        log=FakeLog();b=FakeBackend(log);j=Journal(args.out/'overlap.journal.jsonl',b.now);s=Session(record(),b,log,j);s.pending_metrics=True
        try:s.fresh_metrics();actual='FAIL'
        except ProbeError as e:actual=str(e)
        finally:j.close()
        return actual,dict(inputCount=len(b.sent))
    add('metrics_one_pending_request','metrics_request_overlap',overlap)

    def full_entry(name,mode='playing',bad_hash=False):
        import C1Run
        with tempfile.TemporaryDirectory() as temp:
            fake_root=Path(temp)/'C1/Source';fake_root.mkdir(parents=True)
            build=fake_root.parent/'Runs/Build-03';build.mkdir(parents=True)
            exe=build/'Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe';exe.parent.mkdir(parents=True);exe.write_bytes(b'NOT AN EXECUTABLE: OFFLINE FIXTURE')
            index=dict(sourceSHA=NATIVE,clone=str(fake_root),gameSHA256='0'*64 if bad_hash else C1Run.sha(exe))
            (build/'BUILD-IDENTITY.json').write_text(json.dumps(index))
            log=FakeLog();backend=FakeBackend(log,mode);backend.dpi=dict(fake=True);backend.launches=0;backend.commands=[]
            protected=[dict(ProcessId=9999,ExecutablePath='D:/Engine/UnrealEditor.exe',CommandLine='original',creationUTC=CREATED)]
            backend.inventory=lambda:copy.deepcopy(protected)
            def fake_launch(arguments,cwd):
                backend.launches+=1;backend.commands=arguments[:];return 1234
            backend.launch=fake_launch
            backend.closed=False
            backend.has_owned=lambda:backend.launches>0 and not backend.closed
            backend.capture_owned=lambda:dict(pid=1234,creationUTC=CREATED,creationTicks=creation_ticks(CREATED),executable=backend.commands[0])
            backend.stop_launched=lambda timeout:backend.stop_owned(backend.capture_owned(),timeout)
            backend.close_owned=lambda:setattr(backend,'closed',True)
            if mode=='entry_focus_loss':backend.after_send=lambda b,key,down:setattr(b,'fg',102)
            module=types.SimpleNamespace(Backend=lambda:backend)
            with patch.object(C1Run,'ROOT',fake_root),patch.object(C1Run,'FileLog',lambda path:log),patch.dict(sys.modules,{'C1Win32':module}),patch('subprocess.check_output',return_value=b''),patch('subprocess.Popen',side_effect=AssertionError('REAL PROCESS LAUNCH FORBIDDEN')) as popen:
                try:
                    code=C1Run.main(['--readiness-only','--build',str(build),'--id',name,'--trace','off'])
                    result=json.loads((fake_root.parent/'Runs'/name/'result.json').read_text());actual=result['status']
                    rows=[json.loads(l) for l in (fake_root.parent/'Runs'/name/'journal.jsonl').read_text().splitlines()]
                    faults=[i for i,x in enumerate(rows) if x['event']=='guard_failed']
                    assert not faults or not any(x['event']=='input_sent' for x in rows[faults[0]+1:])
                    # Preserve full entry/exit transcript files for reviewer replay.
                    evidence=args.out/name;evidence.mkdir()
                    for f in (fake_root.parent/'Runs'/name).glob('*'):
                        if f.is_file():(evidence/f.name).write_bytes(f.read_bytes())
                except RuntimeError as e:actual=str(e);result=None;code=None
                assert popen.call_count==0
            return actual,dict(fakeLaunches=backend.launches,realLaunches=popen.call_count,inputCount=len(backend.sent),result=result,exitCode=code,plannedArguments=backend.commands)
    add('entry_to_exit_success','PASS',lambda:full_entry('entry_to_exit_success'))
    add('entry_to_exit_failure','INVALID',lambda:full_entry('entry_to_exit_failure','entry_focus_loss'))
    add('entry_game_hash_mismatch','Game hash mismatch',lambda:full_entry('entry_game_hash_mismatch',bad_hash=True))

    def stop_handle(mode):
        # Actual adapter stop code with an original fake HANDLE. OpenProcess is
        # forbidden here: cleanup must never find a termination target by PID.
        from C1Win32 import Backend
        r=record();events=[]
        class Kernel:
            def OpenProcess(self,*a):raise AssertionError('stop must not reopen by PID')
            def GetProcessId(self,h):return r['pid']
            def QueryFullProcessImageNameW(self,h,flags,buffer,size):buffer.value='D:/Wrong/app.exe' if mode=='wrong_exe' else r['executable'];return 1
            def TerminateProcess(self,h,code):events.append('terminate');return 1
            def WaitForSingleObject(self,h,ms):events.append(['wait',ms]);return 258 if mode=='timeout' else 0
            def GetExitCodeProcess(self,h,code):code._obj.value=0 if 'terminate' in events else 259;return 1
        b=Backend.__new__(Backend);b.k=Kernel();b.owned_handle=44;b.owned_pid=r['pid'];b.stop_evidence=None
        ticks=creation_ticks(CREATED)+(1 if mode=='reused_pid' else 0)
        b.pinned_ticks=ticks;b.expected_executable='D:/Wrong/app.exe' if mode=='wrong_exe' else r['executable']
        b.ticks=lambda h:ticks
        b.process=types.SimpleNamespace(_handle=types.SimpleNamespace(Close=lambda:events.append('close')))
        try:b.stop_owned(r,30);actual='PASS'
        except Exception as e:actual=str(e)
        finally:b.close_owned()  # Fake fixture only, including failure; no real child exists.
        assert events[-1]=='close'
        assert events.count('terminate')==(0 if mode in ('reused_pid','wrong_exe') else 1)
        return actual,dict(fakeKernelEvents=events,realProcessOperations=0)
    for mode,expected in [('success','PASS'),('reused_pid','stop_creation_changed'),('wrong_exe','stop_executable_changed'),('timeout','owned_exit_timeout')]:
        add('stop_handle_'+mode,expected,lambda mode=mode:stop_handle(mode))

    def journal_failure():
        log=FakeLog();b=FakeBackend(log);real=Journal(args.out/'journal_failure.jsonl',b.now)
        class BrokenJournal:
            def __init__(self):self.context=real.context;self.failed_at=None
            def append(self,event,**data):
                if b.sent:
                    if self.failed_at is None:self.failed_at=len(b.sent)
                    raise OSError('fake journal disk full')
                return real.append(event,**data)
        broken=BrokenJournal()
        try:result=run_probe(record(),b,log,broken)
        finally:real.close()
        assert len(b.sent)==broken.failed_at and b.stopped==1
        return result['status'],dict(inputCount=len(b.sent),inputCountAtJournalFailure=broken.failed_at,stopAttempts=b.stopped,result=result)
    add('journal_failure_stops_input_and_cleans_owned_process','INVALID',journal_failure)

    for purpose in ('method','correctness','overhead','baseline','illustrative'):
        def rejected(purpose=purpose):
            with patch('subprocess.Popen',side_effect=AssertionError('live launch forbidden')) as launch,patch('sys.stderr',new=io.StringIO()):
                try:parse_args(['--readiness-only','--build','D:/NoBuild','--id','Offline','--purpose',purpose,'--trace','off']);actual='FAIL'
                except SystemExit as e:actual='REJECTED' if e.code==2 else 'FAIL'
                assert launch.call_count==0
            return actual,dict(launches=launch.call_count)
        add('entry_blocks_'+purpose,'REJECTED',rejected)

    stream=io.StringIO();outcome=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    transcript=stream.getvalue();(args.out/'transcript.txt').write_text(transcript,encoding='utf-8');print(transcript)
    report=dict(scope='OFFLINE FAKE BACKENDS ONLY; no game/Editor/build/Unreal tests/input/network',testsRun=outcome.testsRun,passed=outcome.wasSuccessful(),cases=results,unittestErrors=len(outcome.errors),unittestFailures=len(outcome.failures))
    (args.out/'results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    with (args.out/'cases.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['case','expected','actual','passed']);writer.writeheader();writer.writerows({k:r[k] for k in writer.fieldnames} for r in results)
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
if __name__=='__main__':main()
