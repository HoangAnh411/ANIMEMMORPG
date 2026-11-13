"""Record only the default output loopback around an actual physical parry; never a microphone."""
import argparse,json,time,threading,wave,re
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import soundcard as sc
from PIL import ImageGrab
from B2Client import B2Client
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
c=B2Client(json.loads(a.record.read_text(encoding='utf-8-sig')));result={'completed':False,'process':c.record};audio=[];rate=48000
speaker=sc.default_speaker();loop=sc.get_microphone(speaker.name,include_loopback=True);assert loop.isloopback
def until(f,timeout=4):
 end=time.perf_counter()+timeout
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Parry audio input timed out')
  time.sleep(.008)
def capture():
 with loop.recorder(samplerate=rate,channels=2) as r:audio.append(r.record(numframes=rate*3))
try:
 c.focus();observed=c.probe_w()
 if observed!='W':c.toggle_ime();c.ime=True;assert c.probe_w()=='W'
 if c.metrics()['controlState']!=0:c.click(640,305);time.sleep(.3)
 c.console('U03B2Fixture off');c.console('U01FixtureReset Runway');c.console('U03B2Fixture block')
 s=float(re.findall(r'U03B2_FIXTURE label=block start=([0-9.]+)',c.log.read_text(encoding='utf-8-sig'))[-1]);worker=threading.Thread(target=capture);worker.start()
 line=[l for l in c.log.read_text(encoding='utf-8-sig').splitlines() if 'U03B2_FIXTURE label=block start=' in l][-1];wall=datetime.strptime(re.search(r'\[([0-9.:-]+)\]',line).group(1),'%Y.%m.%d-%H.%M.%S:%f').replace(tzinfo=timezone.utc).timestamp();until(lambda:time.time()>=wall+1.10);c.press('RMB',True);until(lambda:c.metrics()['combat']['defenseResult']==2);ImageGrab.grab(bbox=c.bounds(),all_screens=True).save(a.out/'ParryRing.png');worker.join();c.press('RMB',False);c.console('U03B2Fixture off')
 samples=audio[0];pcm=(np.clip(samples,-1,1)*32767).astype('<i2')
 with wave.open(str(a.out/'Parry-Output-Loopback.wav'),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(rate);w.writeframes(pcm.tobytes())
 mono=samples.mean(axis=1);peaks=[]
 for start in range(0,len(mono)-4096,512):
  spectrum=np.abs(np.fft.rfft(mono[start:start+4096]*np.hanning(4096)));freq=np.fft.rfftfreq(4096,1/rate);ix=np.argmax(spectrum)
  if spectrum[ix]>1:peaks.append({'time':start/rate,'frequency':float(freq[ix]),'magnitude':float(spectrum[ix])})
 first=[v for v in peaks if abs(v['frequency']-660)<20];second=[v for v in peaks if abs(v['frequency']-990)<20]
 result.update(loopback=loop.name,isLoopback=True,rate=rate,checks=[{'check':'First660Hz note present','passed':bool(first)},{'check':'Second990Hz note follows first','passed':bool(first and second and first[0]['time']<second[0]['time'])}],peaks=peaks)
 result['completed']=all(x['passed'] for x in result['checks']);assert result['completed'],'Actual loopback did not contain the ordered two-note cue'
finally:
 if c.ime and c.metrics()['controlState']==0:c.press('Escape',True);time.sleep(.035);c.press('Escape',False);time.sleep(.2)
 c.finish();(a.out/'audio.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'completed':result['completed']}))
