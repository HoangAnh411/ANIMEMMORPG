"""CC-A offline replays. All process/clock/window/input/export producers are fake.

Synthetic native-shaped data is explicitly not evidence that native counters work.
"""
import argparse
from contextlib import nullcontext
import copy
import csv
import io
from contextlib import redirect_stderr
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from unittest.mock import patch
import C1CounterRun as entry
from C1CounterValidate import reconcile, validate, COUNTERS
from C1Offline import FakeBackend, FakeLog, record
from C1Run import NATIVE, PROFILE, sha


def fixture(n=1,h=1,placement='in',start=100.,world=30.,record_value=None):
    r=record_value or record(); w=dict(subjects=n,boxes=h,placement=placement); inside=placement=='in'
    m=dict(world='World_01',worldSeconds=world-.5,pawn='Pawn_01',controller='PC_01',combat=dict(pawnId='Attacker',life=2,action=0,damageResults=17,geometryQueries=29))
    after=copy.deepcopy(m);after['worldSeconds']=world+6;after['combat']['action']=1
    a=dict(kind='ActionStarted',event='ActionStarted',pid=r['pid'],world=m['world'],runId=r['runId'],sourceSHA=NATIVE,
           worldType=1,netMode=0,pawn='Pawn_01',owner='PC_01',localRole=3,pawnId='Attacker',life=2,action=1,actionId='Attacker:2:1',lifeId='Attacker:2',
           definition=0,definitionVersion=1,raw=60,wall=start+.3,start=world+.3,gameplaySeconds=world+.3,
           observedSeconds=world+.3,activeStart=world+.46,activeEnd=world+.68,end=world+1.08)
    targets=[dict(subject=f'Target{i}',life=1,lifeGeneration=1,stableHurtboxIds=[1] if h==1 else [1,2,3],
                  hp=999940 if inside else 1000000,maxHP=1000000,shield=0,dead=False,deathCount=0) for i in range(n)]
    hits=[dict(source='Attacker',sourceLife=2,action=1,target=t['subject'],targetLife=1,hurtboxId=1,
               at=world+.5,damage=60,beforeHP=1000000,afterHP=999940,crit=False,death=False,absorbed=0) for t in targets] if inside else []
    after['combat'].update(damageResults=17+len(hits),geometryQueries=29+(4*n*h if inside else 0))
    s=dict(pid=r['pid'],world=m['world'],subjects=n,hurtboxesPerSubject=h,inside=inside,requestedSeconds=5,startWall=start,endWall=start+5,
           fixedTimeStep=False,fixedFrameRate=False,smoothing=False,dilation=1,width=1280,height=720,
           cvars={p.rsplit(' ',1)[0]:float(p.rsplit(' ',1)[1]) for p in PROFILE.split(',')},
           registrationBegin=dict(registeredSubjects=n+1,registeredHurtboxes=n*h+2),registrationEnd=dict(registeredSubjects=n+1,registeredHurtboxes=n*h+2),
           actionEvents=[a],damageEvents=hits,targets=targets,collectIntervals=4,hurtboxVisits=4*(n*h+2),geometryTests=4*n*h,
           queriesPostContactDelta=4*n*h if inside else 0,candidates=4*n*h if inside else 0,confirmedHits=n if inside else 0,
           duplicateSuppression=3*n*h if inside else 0,occlusionCalls=10*n*h+7,actions=1)
    rows=[]
    for i in range(1,301):
        row=dict(wall=start+i/60,world=world+i/60,dt=1/60,frame=i,focus=1)
        for k,v in COUNTERS.items():row[k]=s[v] if i>=45 else 0
        rows.append(row)
    return s,w,r,m,after,rows


class CounterBackend(FakeBackend):
    def __init__(self,log,mode='normal'):
        super().__init__(log,mode='playing');self.case=mode;self.owned=False;self.launches=0;self.commands=[]
        self.begin=None;self.exported=False;self.raw=None;self.rc=None;self.dpi={'offline':True}
        self.gameplay_count=0
    def inventory(self):return [dict(ProcessId=9999,ExecutablePath='D:/Fake/UnrealEditor.exe',creationTicks=99)]
    def launch(self,args,cwd):
        self.launches+=1;self.owned=True
        self.raw=Path(next(a.split('=',1)[1] for a in args if a.startswith('-U04C1Output=')))
    def capture_owned(self):
        r=record();return {k:r[k] for k in ('pid','creationUTC','creationTicks')}
    def verify_owned(self,r):
        self.rc=r
        info={k:r[k] for k in ('pid','creationTicks','executable')}
        return dict(info,argv=r['arguments'],originalHandle=info,queryHandle=info)
    def has_owned(self):return self.owned
    def close_owned(self):self.owned=False
    def stop_launched(self,timeout):
        self.stopped+=1
        proof=dict(identityVerifiedAtStop=self.case!='stop_oserror',handleSource='original_Popen',wait='signaled',
                   **{k:self.rc[k] for k in ('pid','creationTicks','executable')})
        if self.case=='stop_oserror':proof['identityCaptureError']='offline stop-only OSError'
        return proof
    def metrics(self):
        m=super().metrics();m['gateAttack']=True
        n=self.w['subjects'] if hasattr(self,'w') else 1;h=self.w['boxes'] if hasattr(self,'w') else 1
        inside=hasattr(self,'w') and self.w['placement']=='in' and self.exported
        prepared=hasattr(self,'w')
        life=1 if not prepared or self.case=='life_unchanged' else 3 if self.case=='life_double' else 2
        pawn_id='OtherAttacker' if prepared and self.case=='pawn_changed_at_prepare' else 'Attacker'
        action=1 if self.exported or not prepared or self.case=='action_not_reset' else 0
        m['combat']=dict(pawnId=pawn_id,life=life,action=action,phase=4 if action or self.case=='phase_not_idle' else 0,damageResults=17+(n if inside else 0),geometryQueries=29+(4*n*h if inside else 0))
        return m
    def send(self,key,down):
        if key=='Enter' and not down and self.cmd.startswith('u04c1 '):
            text=self.cmd;self.cmd='';self.commands.append(dict(text=text,time=self.t));self.sent.append(dict(key=key,down=down,time=self.t))
            if text.startswith('u04c1 prepare '):
                _,_,n,h,p=text.split();self.w=dict(subjects=int(n),boxes=int(h),placement=p)
                if self.case=='old_output':(self.raw/'summary.json').write_text('{}')
            elif text=='u04c1 begin 5':self.begin=self.t
            else:raise AssertionError('unexpected command')
            return 1
        if key=='LMB' and self.begin is not None:
            self.sent.append(dict(key=key,down=down,time=self.t));self.gameplay_count+=1
            if down:
                self.action_time=self.t
                self.log.add('LogU01Control: PhysicalPress key=LeftMouseButton state=0 accepted=1 reason=Ready\n')
            else:self.log.add('LogU01Control: PhysicalRelease/Rearm key=LeftMouseButton\n')
            return 1
        sent=super().send(key,down)
        if self.case=='focus_during_prepare' and self.cmd.startswith('u04c1 pre'):self.fg=202
        return sent
    def sleep(self,seconds):
        super().sleep(seconds)
        if self.case=='focus_between_lmb' and self.gameplay_count==1 and self.t>=self.action_time+.01:self.fg=202
        if self.begin is not None and self.t>=self.begin+5 and not self.exported and self.case!='missing_summary':
            self.exported=True
            s,w,r,m,a,rows=fixture(self.w['subjects'],self.w['boxes'],self.w['placement'],start=self.begin,world=self.begin,record_value=self.rc)
            s['world']=m['world']=a['world']=self.metrics()['world']
            e=s['actionEvents'][0];e['world']=s['world']
            d=self.action_time-self.begin
            e.update(wall=self.action_time,start=self.action_time,gameplaySeconds=self.action_time,observedSeconds=self.action_time,activeStart=self.action_time+.16,activeEnd=self.action_time+.38,end=self.action_time+.78)
            for hit in s['damageEvents']:hit['at']=self.action_time+.2
            if self.case=='old_capture_life':e.update(life=1,actionId='Attacker:1:1',lifeId='Attacker:1')
            if self.case=='wrong_damage':
                s['damageEvents'][0].update(damage=50,afterHP=999950);s['targets'][0]['hp']=999950
            (self.raw/'summary.json').write_text(json.dumps(s),encoding='utf-8')
            with (self.raw/'frames.csv').open('w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);out=p.parse_args().out
    out.mkdir(parents=True,exist_ok=False);results=[]
    def save(name,expected,actual,details):
        results.append(dict(case=name,expected=expected,actual=actual,passed=expected==actual,details=details))
    def data_case(name,expected,mutate=lambda x:None,n=1,h=1,placement='in'):
        args=list(fixture(n,h,placement));mutate(args);v=reconcile(*args)
        dest=out/name;dest.mkdir()
        (dest/'input.json').write_text(json.dumps(args,indent=2),encoding='utf-8')
        (dest/'validation.json').write_text(json.dumps(v,indent=2),encoding='utf-8')
        save(name,expected,v['status'],v)
    for n in (1,10,40):
        for h in (1,3):
            for placement in ('in','out'):data_case(f'synthetic_{n}_{h}_{placement}','PASS',n=n,h=h,placement=placement)
    data_case('damage_HP_self_consistent','FAIL',lambda x:(x[0]['damageEvents'][0].update(damage=50,afterHP=999950),x[0]['targets'][0].update(hp=999950)))
    data_case('wrong_action','FAIL',lambda x:x[0]['damageEvents'][0].update(action=99))
    data_case('wrong_source_life','FAIL',lambda x:x[0]['damageEvents'][0].update(sourceLife=1))
    data_case('wrong_target_life','FAIL',lambda x:x[0]['damageEvents'][0].update(targetLife=2))
    data_case('wrong_hurtbox','FAIL',lambda x:x[0]['damageEvents'][0].update(hurtboxId=99))
    data_case('H3_multiplied_damage','FAIL',lambda x:(x[0]['damageEvents'].extend(copy.deepcopy(x[0]['damageEvents'])*2),x[0]['targets'][0].update(hp=999820)),h=3)
    data_case('out_still_hit','FAIL',lambda x:x[0]['damageEvents'].append(fixture()[0]['damageEvents'][0]),placement='out')
    data_case('frames_empty','INVALID',lambda x:x[5].clear())
    data_case('frame_gap','INVALID',lambda x:x[5][1].update(frame=99))
    data_case('frame_focus','INVALID',lambda x:x[5][1].update(focus=0))
    data_case('old_pre_window_frame','INVALID',lambda x:x[5][0].update(wall=99))
    data_case('action_outside_window','INVALID',lambda x:x[0]['actionEvents'][0].update(wall=99))
    data_case('old_gameplay_action','INVALID',lambda x:x[0]['actionEvents'][0].update(start=1,gameplaySeconds=1))
    data_case('other_PID','INVALID',lambda x:x[0].update(pid=999))
    data_case('other_world','INVALID',lambda x:x[0].update(world='OtherWorld'))
    data_case('wrong_runID','INVALID',lambda x:x[0]['actionEvents'][0].update(runId='old_run'))
    data_case('missing_action_life','INVALID',lambda x:x[0]['actionEvents'][0].pop('life'))
    data_case('profile_smoothing','INVALID',lambda x:x[0].update(smoothing=True))
    data_case('wrong_registration','FAIL',lambda x:x[0]['registrationEnd'].update(registeredHurtboxes=99))
    data_case('wrong_visits','FAIL',lambda x:x[0].update(hurtboxVisits=99))
    data_case('wrong_post_contact_query','FAIL',lambda x:x[0].update(queriesPostContactDelta=1))
    data_case('old_cumulative_data_excluded','PASS')
    data_case('old_cumulative_data_included','FAIL',lambda x:x[0].update(queriesPostContactDelta=x[0]['queriesPostContactDelta']+29))
    # Nonzero outside occlusion is intentional; no H-1 suppression expectation.
    data_case('out_HUD_occlusion_allowed','PASS',placement='out')
    data_case('suppression_not_H_minus_1','PASS',lambda x:(x[0].update(duplicateSuppression=100),[row.update(suppressed=100) for row in x[5][44:]]),h=3)
    valid_cli=['--build','D:/Offline/Build-03','--id','Fresh-01','--subjects','1','--boxes','1','--placement','in']
    for name,extra in [('trace_on',['--trace','on']),('trace_off_flag',['--trace','off']),('second_action',['--actions','2']),('unsafe_id',['--id','../old']),('bad_N',['--subjects','2']),('bad_H',['--boxes','2']),('bad_placement',['--placement','near'])]:
        try:
            with redirect_stderr(io.StringIO()):entry.parse_args(valid_cli+extra)
            actual='ACCEPTED'
        except SystemExit:actual='REJECTED'
        save('parser_'+name,'REJECTED',actual,dict(realLaunches=0))
    prepare_cases=dict(life_unchanged='prepare_life_increment',life_double='prepare_life_increment',
                       pawn_changed_at_prepare='prepare_identity:pawnId',action_not_reset='prepare_action_reset',
                       phase_not_idle='prepare_phase_idle')
    for case in (*prepare_cases,'old_capture_life','normal','wrong_damage','focus_between_lmb','focus_during_prepare','missing_summary','old_output','stop_oserror','reused_id','stale_metrics'):
        dest=out/('entry_'+case);dest.mkdir()
        with nullcontext(str((dest/'Workspace').resolve())) as temporary:
            root=Path(temporary)/'C1/Source';root.mkdir(parents=True)
            build=root.parent/'Runs/Build-03';exe=build/'Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
            exe.parent.mkdir(parents=True);exe.write_bytes(b'OFFLINE DATA - NOT EXECUTABLE')
            (build/'BUILD-IDENTITY.json').write_text(json.dumps(dict(sourceSHA=NATIVE,clone=str(root),gameSHA256=sha(exe))))
            log=FakeLog();b=CounterBackend(log,case)
            if case=='stale_metrics':b.mode='stale_metrics'
            run=root.parent/'Runs'/case
            if case=='reused_id':run.mkdir();(run/'sentinel.txt').write_text('KEEP')
            # FileLog is supplied by the accepted lifecycle; substitute in-memory
            # producer, synchronizing its bytes before each validator invocation.
            import C1Counter
            actual_probe=entry.run_counter_probe
            def probe(rec,backend,_log,journal,cleanup):
                original= C1Counter.write
                def sync_write(path,value):
                    Path(rec['log']).write_bytes(log.data);original(path,value)
                with patch.object(C1Counter,'write',sync_write):return actual_probe(rec,backend,log,journal,cleanup=cleanup)
            module=types.SimpleNamespace(Backend=lambda:b)
            caught=None
            with patch.object(entry,'ROOT',root),patch.object(entry,'GAME_SHA',sha(exe)),patch.object(entry,'run_counter_probe',probe),patch.dict(sys.modules,{'C1Win32':module}),patch('subprocess.check_output',return_value=b''),patch('subprocess.Popen',side_effect=AssertionError('REAL LAUNCH FORBIDDEN')) as popen:
                try:code=entry.main(['--build',str(build),'--id',case,'--subjects','1','--boxes','1','--placement','in'])
                except RuntimeError as e:caught=str(e);code=1
                assert popen.call_count==0
            expected='PASS' if case=='normal' else 'FAIL' if case=='wrong_damage' else 'INVALID'
            result=json.loads((run/'result.json').read_text()) if (run/'result.json').exists() else dict(status='INVALID')
            final=json.loads((run/'final.json').read_text()) if (run/'final.json').exists() else result
            rows=[json.loads(line) for line in (run/'journal.jsonl').read_text().splitlines()] if (run/'journal.jsonl').exists() else []
            bad=next((r for r in rows if r['event']=='guard_failed'),None)
            input_after=[r for r in rows if bad and r['seq']>bad['seq'] and r['event']=='input_sent']
            assert not input_after
            if case=='focus_between_lmb':assert result['held']==['LMB'] and b.gameplay_count==1
            if case=='stop_oserror':assert result['processExited'] is True and result['exitEvidence']['identityVerifiedAtStop'] is False
            if case in prepare_cases:
                assert bad['reason']==prepare_cases[case] and b.begin is None and b.gameplay_count==0
            if case=='old_capture_life':
                assert 'attacker_life' in result['invalid'] and b.gameplay_count==2
            assert final['status']==result['status'] and code==(0 if expected=='PASS' else 1)
            assert b.launches==(0 if case=='reused_id' else 1)
            if run.exists():(run/'Game.log').write_bytes(log.data)
            post_stop=validate(run,True)
            assert post_stop['status']==expected, post_stop
            for f in run.rglob('*'):
                if f.is_file():
                    target=dest/f.relative_to(run);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(f.read_bytes())
            detail=dict(cli=code,launches=b.launches,stopCalls=b.stopped,result=result,final=final,commands=b.commands,
                        gameplayEdges=b.gameplay_count,beginCount=int(b.begin is not None),fakeInputs=b.sent,inputAfterGuardFailure=len(input_after),exception=caught,postStopValidation=post_stop,realLaunches=0,realInputs=0)
            (dest/'replay.json').write_text(json.dumps(detail,indent=2),encoding='utf-8')
            save('entry_'+case,expected,result['status'],detail)
    with (out/'expected-actual.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['case','expected','actual','passed']);writer.writeheader();writer.writerows({k:r[k] for k in writer.fieldnames} for r in results)
    (out/'results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    failed=[r['case'] for r in results if not r['passed']]
    print(json.dumps(dict(cases=len(results),passed=len(results)-len(failed),failed=failed,realLaunches=0,realInputs=0)))
    return bool(failed)


if __name__=='__main__':raise SystemExit(main())
