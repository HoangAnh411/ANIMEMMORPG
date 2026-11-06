"""Extract observed video frames at matching action-relative wall times."""
from pathlib import Path
from datetime import datetime
import argparse,json,cv2
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
items=[];sheet=Image.new('RGB',(2560,720))
for row,session in enumerate([a.before,a.after]):
 m=json.loads((session/'Capture/input.json').read_text());start=datetime.fromisoformat(m['utc']);ev=[]
 for l in (session/'Game.log').read_text(encoding='utf-8-sig',errors='replace').splitlines():
  if 'U02B_EVENT {' in l:
   v=json.loads(l.split('U02B_EVENT ',1)[1])
   if v['event']=='Accepted' and 0<=(datetime.fromisoformat(v['utc'].replace('Z','+00:00'))-start).total_seconds()<=m['captureSeconds']:ev.append(v)
 first=(datetime.fromisoformat(ev[0]['utc'].replace('Z','+00:00'))-start).total_seconds();cap=cv2.VideoCapture(str(session/'Capture/Input-C.mp4'))
 for col,offset in enumerate([0,.08,.17,.25,.39,.5]):
  at=first+offset;cap.set(cv2.CAP_PROP_POS_MSEC,at*1000);ok,f=cap.read();assert ok
  name=('Before' if row==0 else 'After')+'-'+str(offset)+'.png';cv2.imwrite(str(a.out/name),f)
  if col<4:
   im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((640,360));ImageDraw.Draw(im).text((12,12),f'{session.name} action +{offset:.2f}s',fill='yellow');sheet.paste(im,(col*640,row*360))
  items.append(dict(file=name,video=str(session/'Capture/Input-C.mp4'),wallRelativeSeconds=at,actionOffset=offset,sourceSHA=m['process']['sourceSHA']))
 cap.release()
sheet.save(a.out/'Compare.png');(a.out/'FRAMES.json').write_text(json.dumps(items,indent=2))
