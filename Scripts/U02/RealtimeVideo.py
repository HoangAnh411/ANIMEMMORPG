"""Re-export historical frame captures against their recorded wall-time timestamps."""
import argparse,cv2,json,bisect
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--video',type=Path,required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
m=json.loads(a.input.read_text(encoding='utf-8-sig'));times=m['frames'];duration=m['captureSeconds']
c=cv2.VideoCapture(str(a.video));frames=[]
while True:
    ok,f=c.read()
    if not ok:break
    frames.append(f)
c.release();assert len(frames)==len(times) and frames
h,w=frames[0].shape[:2];v=cv2.VideoWriter(str(a.out),cv2.VideoWriter_fourcc(*'mp4v'),30,(w,h));assert v.isOpened()
n=0
while n/30<duration:
    i=max(0,bisect.bisect_right(times,n/30)-1);v.write(frames[i]);n+=1
v.release()
a.out.with_suffix('.json').write_text(json.dumps(dict(inputVideo=str(a.video),inputMetadata=str(a.input),sourceFrames=len(frames),wallSeconds=duration,outputFrames=n,outputFPS=30,outputSeconds=n/30,policy='hold last observed frame until next timestamp; no invented motion'),indent=2))
assert abs(n/30-duration)<1/30
