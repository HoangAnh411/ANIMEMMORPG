"""Separate illustrative processes AFTER numeric phase; never acceptance input."""
import argparse,threading,time,traceback
from pathlib import Path
import cv2,numpy as np
from PIL import ImageGrab
from R1bContract import CASES,frozen,read,write
from R1bSession import Session

def main():
    p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);a=p.parse_args();record=read(a.record);m=frozen(record['batchManifest'])
    ledger=read(Path(m['isolationRoot'])/'Runs/BATCH-LEDGER.json')
    assert record['purpose']=='ILLUSTRATIVE' and ledger['completedCaps']==m['fpsOrder'] and not ledger['halted']
    out=a.record.parent/'Illustrative';out.mkdir();s=Session(record);report=dict(completed=False,acceptance=False,trials=[],process=record)
    cv2.setNumThreads(1)
    try:
        s.readiness()
        for case in CASES:
            if case in ledger['stoppedCases']:
                report['trials'].append(dict(case=case,status='SKIPPED_GAMEPLAY_GATE_STOP',acceptance=False));continue
            trial=f"illustrative-fps{record['targetFPS']}-{case}";folder=out/trial;folder.mkdir();s.events=[]
            write(folder/'SETUP.json',s.setup(case));s.photo(folder/'Before.png')
            video=cv2.VideoWriter(str(folder/'ILLUSTRATIVE.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(1280,720));assert video.isOpened()
            stop=threading.Event();errors=[];counter=[0]
            def capture():
                start=time.perf_counter();previous=None
                while not stop.is_set():
                    try:
                        s.client.guard();frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=s.client.bounds(),all_screens=True)),cv2.COLOR_RGB2BGR)
                        cv2.putText(frame,trial+' | ILLUSTRATIVE ONLY | video30FPS',(10,27),cv2.FONT_HERSHEY_SIMPLEX,.48,(0,255,255),1)
                        while counter[0]/30<time.perf_counter()-start:video.write(previous if previous is not None else frame);counter[0]+=1
                        previous=frame
                    except Exception as error:errors.append(repr(error));stop.set()
                    stop.wait(.025)
            s.begin(trial);worker=threading.Thread(target=capture);worker.start()
            try:s.wait(.4);s.action(case)
            finally:stop.set();worker.join();video.release()
            raw_path,raw=s.end(trial);s.photo(folder/'After.png');write(folder/'INPUT.json',dict(events=s.events,mediaErrors=errors,acceptance=False))
            assert not errors,errors
            report['trials'].append(dict(trial=trial,case=case,status='RECORDED_ILLUSTRATION',raw=str(raw_path),videoFrames=counter[0],videoFPS=30,acceptance=False))
            write(out/'LEDGER.json',report);print(trial,'ILLUSTRATIVE_ONLY',flush=True)
        report['completed']=True
    except Exception as error:report.update(error=repr(error),traceback=traceback.format_exc());raise
    finally:
        if s.active:
            try:s.client.guard();s.command('U04B end')
            except Exception as error:report['flushError']=repr(error)
        s.client.finish();write(out/'LEDGER.json',report)

if __name__=='__main__':main()
