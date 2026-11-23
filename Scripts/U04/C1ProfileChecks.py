"""Offline method gate checks with synthetic data, no game process."""
import copy
import json
import sys
import io
from contextlib import redirect_stdout
from unittest.mock import patch
import C1ProfileRun as entry
from C1ProfileValidate import validate_stop
from pathlib import Path

from C1ProfileRun import COMBO,QPC_BIAS
from C1ProfileValidate import gameplay,window,validate
from C1ProfileEvidence import inspect,table
from C1Run import PROFILE


def main(out, startup):
    out.mkdir()
    rows=[]
    def check(name, test):
        assert test, name
        rows.append(dict(case=name,status='PASS'))
    start=QPC_BIAS+100
    end=start+60.01
    process=dict(pid=9,runId='fixture',sourceSHA='native')
    metrics=dict(world='world',pawn='pawn',controller='PC',combat=dict(life=2,pawnId='p'))
    capture=dict(prepared=dict(metrics=metrics),after=dict(metrics=metrics),begin=100,anchor=100.25,warmupStart=69)
    capture['edges']=[dict(deadline=100.25+t,down=100.25+t+.001,up=100.25+t+.036) for t in COMBO]
    summary=dict(pid=9,world='world',subjects=10,hurtboxesPerSubject=3,inside=True,
                 startWall=start,endWall=end,requestedSeconds=60,width=1280,height=720,
                 dilation=1,smoothing=False,fixedTimeStep=False,fixedFrameRate=False,
                 cvars=dict((k,float(v)) for k,v in (x.split() for x in PROFILE.split(','))),
                 actions=60,confirmedHits=600,registrationBegin=dict(registeredSubjects=11,registeredHurtboxes=32),
                 actionEvents=[],damageEvents=[])
    summary['registrationEnd']=summary['registrationBegin']
    summary['targets']=[dict(subject=str(i),stableHurtboxIds=[1,2,3],hp=995600,dead=False,shield=0,life=4,lifeGeneration=4) for i in range(10)]
    hp=1000000
    for i,(raw,edge) in enumerate(zip([60,70,90]*20,capture['edges']),1):
        summary['actionEvents'].append(dict(kind='ActionStarted',action=i,raw=raw,wall=edge['down']+QPC_BIAS+.01,
                                            pawnId='p',life=2,pawn='pawn',owner='PC',pid=9,world='world',runId='fixture',sourceSHA='native'))
        summary['damageEvents'] += [dict(source='p',sourceLife=2,action=i,target=str(t),targetLife=4,hurtboxId=1,
                                         damage=raw,beforeHP=hp,afterHP=hp-raw,crit=False,death=False,absorbed=0) for t in range(10)]
        hp-=raw
    frames=[dict(frame=i,wall=start+i/60,dt=1/60,focus=1) for i in range(3601)]
    check('20 combos',window(out,summary,capture,process,frames)==(start,end) and not gameplay(summary,capture,process,start,end))
    target=copy.deepcopy(summary);target['damageEvents'][0]['targetLife']=9
    check('wrong target life','target life or hurtbox' in gameplay(target,capture,process,start,end))
    missing=copy.deepcopy(summary);missing['actionEvents'].pop()
    check('missing action','action count or sequence' in gameplay(missing,capture,process,start,end))
    def rejects(fn, reason):
        try:
            fn()
        except (ValueError,OSError) as error:
            return reason in str(error)
        return False
    outside=copy.deepcopy(summary);outside['actionEvents'][0]['wall']=end+1
    check('outside action',rejects(lambda:gameplay(outside,capture,process,start,end),'outside window'))
    edge=copy.deepcopy(capture);edge['edges'][0].update(down=99,up=99.035)
    check('outside edge',rejects(lambda:window(out,summary,edge,process,frames),'edge schedule'))
    (out/'Raw').mkdir();(out/'Raw/summary.json').write_text(json.dumps(summary))
    check('startup trace',rejects(lambda:inspect(out,startup,'timing'),'unique U04C1_WINDOW'))
    (out/'empty.csv').write_text('ThreadName,StartTime,EndTime\n')
    check('empty GPU export',rejects(lambda:table(out/'empty.csv'),'empty export'))
    check('missing capture',validate(out)['status']=='INVALID')
    fixture=out/'ExportFixture';fixture.mkdir()
    log=fixture/'Insights.log'
    log.write_text("Detected 1 regions\nfor region 'U04C1_WINDOW' [1.0 .. 61.01]\n")
    for name,thread in [('gpu-U04C1_WINDOW','GPU0'),('frames-U04C1_WINDOW','Game Frames'),('events','GameThread')]:
        (fixture/(name+'.csv')).write_text(f'ThreadName,TimerName,StartTime,EndTime\n{thread},Frame,2,3\n')
    check('missing counter samples',rejects(lambda:inspect(out,fixture,'timing'),'counter-HurtboxVisits.csv'))
    log.write_text('U04C1_START U04C1_END')
    (fixture/'allocations.csv').write_text('Size,AllocCallstack\n64,0x00012345\n')
    check('address-only stack',rejects(lambda:inspect(out,fixture,'memory'),'no resolved callstack'))
    fake_root=out/'Source';fake_root.mkdir()
    stale=out/'Runs/C1-Method-Stale';stale.mkdir(parents=True)
    sentinel=stale/'capture.json';sentinel.write_text('original')
    capture_stdout=io.StringIO()
    with patch.object(entry,'ROOT',fake_root), patch('subprocess.Popen',side_effect=AssertionError('launch forbidden')) as popen, redirect_stdout(capture_stdout):
        code=entry.main(['--id',stale.name,'--mode','timing'])
    actual=json.loads(capture_stdout.getvalue())
    check('stale run before launch',code==1 and actual==dict(status='INVALID',error='profile_stale_output') and popen.call_count==0 and sentinel.read_text()=='original')
    rows[-1].update(expected='INVALID:profile_stale_output',actual=actual,launches=0)

    proof=dict(pid=9,creationTicks=134000000000000001,executable='D:/Game/AnimeMMORPG.exe',
               identityVerifiedAtStop=True,wait='signaled',handleSource='original_Popen')
    good=dict(status='PASS',processExited=True,exitEvidence=proof)
    journal=[dict(event='original_handle_process_exited',evidence=proof)]
    for filename in ('result.json','final.json'):
        (out/filename).write_text(json.dumps(good))
    validate_stop(out,proof,journal,'PASS')
    bad=copy.deepcopy(good);bad['exitEvidence']['creationTicks']+=1
    for filename in ('result.json','final.json'):
        (out/filename).write_text(json.dumps(bad))
    # Reopen through the same stop gate used by the profiling validator.
    try:
        validate_stop(out,proof,journal,'PASS')
    except ValueError as error:
        actual=dict(status='INVALID',error=str(error))
    else:
        actual=dict(status='PASS')
    check('reopened wrong stop proof',actual==dict(status='INVALID',error='stop process identity'))
    rows[-1].update(expected='INVALID:stop process identity',actual=actual)
    (out/'cases.json').write_text(json.dumps(rows,indent=2))
    print(f'{len(rows)} method checks passed')


if __name__=='__main__':
    main(Path(sys.argv[1]),Path(sys.argv[2]))
