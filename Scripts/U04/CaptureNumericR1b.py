"""Frozen R1b numeric runner. No video modules, conversion, encoder or writer.
Only photo() before begin/after closed end may call a media API.
"""
import argparse,json,time,traceback
from pathlib import Path
from R1bContract import CASES,frozen,read,write,sha
from R1bSession import Session,clock
from AnalyzeR1 import analyze

def main():
    p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);a=p.parse_args()
    record=read(a.record);m=frozen(record['batchManifest']);assert record['purpose']=='NUMERIC'
    session=a.record.parent;out=session/'Numeric';out.mkdir(exist_ok=False)
    ledger_path=Path(m['isolationRoot'])/'Runs/BATCH-LEDGER.json'
    ledger=read(ledger_path) if ledger_path.exists() else dict(batchId=m['batchId'],manifestSHA256=sha(record['batchManifest']),processes=[],trials=[],setupErrors=[],stoppedCases={},completedCaps=[],halted=False,R1bStarted=True)
    assert not ledger['halted'] and record['targetFPS']==m['fpsOrder'][len(ledger['completedCaps'])]
    ledger['processes'].append(record);s=None;active=None;focus_recoveries=0
    def save():write(ledger_path,ledger)
    save()
    try:
        s=Session(record);s.readiness()
        for case in CASES:
            if case in ledger['stoppedCases']:continue
            need,limit=m['cases'][case]['required'],m['cases'][case]['limit'];passed=0
            for attempt in range(1,limit+1):
                trial=f"c1-r1b-fps{record['targetFPS']}-{case}-{attempt}";folder=out/trial;folder.mkdir();s.events=[]
                # Setup errors stop the batch; they never cause unbounded retries.
                setup=s.setup(case);write(folder/'SETUP.json',setup);s.photo(folder/'Before.png')
                active=dict(trial=trial,case=case,fps=record['targetFPS'],attempt=attempt,status='WINDOW_START_RESERVED',counted=True,beginInvocation=clock())
                ledger['trials'].append(active);save() # no ledger/file writes inside window
                focus_loss=None
                try:
                    s.begin(trial);s.wait(.4);s.action(case);raw_path,raw=s.end(trial)
                except RuntimeError as error:
                    if 'focus/PID changed' not in str(error) or focus_recoveries>=1:raise
                    focus_loss=dict(error=repr(error),at=clock());focus_recoveries+=1
                    # Current attempt is already invalid. Reacquire only the
                    # identity-guarded owned HWND once, release and flush; NO reset.
                    s.client.focus();s.client.release();raw_path,raw=s.end(trial)
                s.photo(folder/'After.png');write(folder/'INPUT.json',dict(trial=trial,events=s.events,focusLoss=focus_loss))
                frozen(record['batchManifest'])
                result=analyze(raw_path,record['targetFPS'],case)
                frames=[r for r in raw if r['kind']=='frame']
                assert frames and all(r['pid']==record['pid'] and r['source']==record['sourceSHA'] for r in frames),'process/source integrity error'
                analyzer_status=result['status'];effective=analyzer_status
                if focus_loss and analyzer_status!='FAIL':effective='INVALID'
                result.update(trial=trial,process=record,analyzerStatus=analyzer_status,status=effective,harnessFocusLoss=focus_loss,acceptance=True)
                write(folder/'ASSERTIONS.json',result)
                active.update(status=effective,analyzerStatus=analyzer_status,raw=str(raw_path),rawSHA256=sha(raw_path),assertions=str(folder/'ASSERTIONS.json'),assertionsSHA256=sha(folder/'ASSERTIONS.json'),ended=clock())
                save();active=None
                print(trial,effective,'gameplay',result.get('gameplay',{}).get('pass_'),'fps',result.get('cadence',{}).get('fps'),'band',result.get('cadence',{}).get('within10Percent'),flush=True)
                if effective=='FAIL':
                    ledger['stoppedCases'][case]=dict(trial=trial,reason='GAMEPLAY_FAIL',fps=record['targetFPS']);save()
                    print('GAMEPLAY_GATE_STOP',case,trial,flush=True);break
                if effective=='PASS':passed+=1
                if passed==need:break
                if focus_loss and s.client.metrics()['controlState']!=0:
                    b=s.client.metrics()['menuButtons']['Resume'];s.client.click(round(b['x']),round(b['y']));s.wait(.5)
        ledger['completedCaps'].append(record['targetFPS']);save()
    except Exception as error:
        ledger.update(halted=True,haltReason=repr(error),traceback=traceback.format_exc(),haltAt=clock())
        if active:
            active.update(status='INVALID',reason='aborted/crash/tool error; reserved window counts toward limit',error=repr(error))
            if s:
                write(out/active['trial']/'ABORTED-INPUT.json',dict(events=s.events,error=repr(error)))
        else:ledger['setupErrors'].append(dict(fps=record['targetFPS'],error=repr(error),at=clock(),countedAsTrial=False))
        # Preserve and stop. No edits, replacement process/batch, or hidden retry.
        if s and s.active:
            try:s.client.guard();s.command('U04B end')
            except Exception as flush:ledger['flushError']=repr(flush)
        save();raise
    finally:
        if s:s.client.finish()
        save()

if __name__=='__main__':main()
