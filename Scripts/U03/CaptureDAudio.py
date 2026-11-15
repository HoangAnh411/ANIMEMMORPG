"""Output loopback only, around a guarded physical input/video run. Never opens a microphone."""
import argparse,json,subprocess,threading,time,wave,hashlib,shutil
from pathlib import Path
import numpy as np
import soundcard as sc
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--regression',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
stop=threading.Event();blocks=[];rate=48000;speaker=sc.default_speaker();loop=sc.get_microphone(speaker.name,include_loopback=True);assert loop.isloopback
def capture():
 with loop.recorder(samplerate=rate,channels=2) as r:
  while not stop.is_set():blocks.append(r.record(numframes=4800))
t=threading.Thread(target=capture);t.start();started=time.time();code=-1
try:
 script=Path(__file__).with_name('CaptureDRegression.py' if a.regression else 'CaptureDInput.py')
 args=['python','-X','utf8',str(script),'--record',str(a.record),'--out',str(a.out)]
 if not a.regression:args+=['--mode','combat']
 harness=a.out/'harness';harness.mkdir(exist_ok=True)
 for name in [script.name,'CaptureDAudio.py','DClient.py']:
  shutil.copyfile(Path(__file__).with_name(name),harness/name)
 (a.out/'command.json').write_text(json.dumps(dict(startedUTC=started,arguments=args,scriptSHA256=hashlib.sha256(script.read_bytes()).hexdigest(),process=json.loads(a.record.read_text(encoding='utf-8-sig'))),indent=2),encoding='utf-8')
 code=subprocess.call(args)
finally:
 stop.set();t.join();samples=np.concatenate(blocks) if blocks else np.zeros((0,2));pcm=(np.clip(samples,-1,1)*32767).astype('<i2')
 with wave.open(str(a.out/'Output-Loopback.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(rate);w.writeframes(pcm.tobytes())
 mono=samples.mean(axis=1);peaks=[]
 for i in range(0,len(mono)-4096,512):
  spectrum=np.abs(np.fft.rfft(mono[i:i+4096]*np.hanning(4096)));k=int(np.argmax(spectrum))
  if spectrum[k]>1:peaks.append(dict(time=i/rate,frequency=k*rate/4096,magnitude=float(spectrum[k])))
 first=[v for v in peaks if abs(v['frequency']-660)<20];second=[v for v in peaks if abs(v['frequency']-990)<20]
 result=dict(inputExitCode=code,loopback=loop.name,isLoopback=True,rate=rate,startedUTC=started,seconds=len(samples)/rate,peaks=peaks,parry660=bool(first),parry990After660=bool(first and second and first[0]['time']<second[-1]['time']))
 (a.out/'audio.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
raise SystemExit(code)
