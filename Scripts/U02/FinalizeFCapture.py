"""Complete CFR tail hold to the recorded wall-time endpoint; retain original, never accelerate."""
import argparse,json,math,shutil,cv2
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--video',default='Network-F.mp4');a=p.parse_args();m=json.loads((a.capture/'input.json').read_text());v=a.capture/a.video;cap=cv2.VideoCapture(str(v));fps=cap.get(cv2.CAP_PROP_FPS);n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));assert fps==30;missing=math.ceil(m['captureSeconds']*fps)-n;assert 0<=missing<=30
if missing:
 raw=a.capture/(v.stem+'-Unpadded.mp4');assert not raw.exists();shutil.copyfile(v,raw);tmp=a.capture/(v.stem+'-Padded.mp4');writer=cv2.VideoWriter(str(tmp),cv2.VideoWriter_fourcc(*'mp4v'),fps,(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))));assert writer.isOpened();last=None
 for _ in range(n):
  ok,last=cap.read();assert ok;writer.write(last)
 for _ in range(missing):writer.write(last)
 writer.release();cap.release();tmp.replace(v);m.update(videoUnpaddedSeconds=n/fps,videoTailHeldFrames=missing,videoSeconds=(n+missing)/fps,videoTailPolicy='Last observed frame held for final bookkeeping gap to wall-time endpoint; no acceleration/interpolation; unpadded original retained');(a.capture/'input.json').write_text(json.dumps(m,indent=2))
else:cap.release()
print('CFR30 end matched to wall clock, held tail frames',missing)
