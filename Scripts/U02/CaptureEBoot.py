"""Real Boot / Quit proof, with map transition explicitly leaving owned-pawn metrics behind."""
import argparse,json,time,cv2,numpy as np,ctypes as ct
from pathlib import Path
from datetime import datetime,timezone
from PIL import ImageGrab
from EClient import EClient,u
p=argparse.ArgumentParser();p.add_argument('--record',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--quit-menu',action='store_true');a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
r=json.loads(a.record.read_text(encoding='utf-8-sig'));c=EClient(r);writer=None
kernel=ct.WinDLL('kernel32',use_last_error=True);kernel.OpenProcess.argtypes=[ct.c_ulong,ct.c_int,ct.c_ulong];kernel.OpenProcess.restype=ct.c_void_p
kernel.WaitForSingleObject.argtypes=[ct.c_void_p,ct.c_ulong];kernel.GetExitCodeProcess.argtypes=[ct.c_void_p,ct.POINTER(ct.c_ulong)];kernel.CloseHandle.argtypes=[ct.c_void_p]
process_handle=kernel.OpenProcess(0x101000,False,r['pid']);assert process_handle
m=dict(process=r,completed=False,events=[],frames=[])
try:
 c.prepare();m['ownedInitialMetrics']=c.metrics();bounds=c.bounds();l,t,rr,b=bounds;cv2.setNumThreads(1);writer=cv2.VideoWriter(str(a.out/'Boot-Quit.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),30,(rr-l,b-t));assert writer.isOpened()
 start=time.perf_counter();m['utc']=datetime.now(timezone.utc).isoformat();encoded=0;previous=None
 def grab():
  global encoded,previous
  c.guard();assert c.bounds()==bounds
  frame=cv2.cvtColor(np.array(ImageGrab.grab(bbox=bounds,all_screens=True)),cv2.COLOR_RGB2BGR);now=time.perf_counter()-start
  while encoded/30<now:writer.write(previous if previous is not None else frame);encoded+=1
  previous=frame;m['frames'].append(now)
 def wait(seconds):
  end=time.perf_counter()+seconds
  while time.perf_counter()<end:grab()
 wait(.5);c.press('Escape',True);time.sleep(.06);c.press('Escape',False);wait(.5)
 if a.quit_menu:
  ImageGrab.grab(bbox=bounds,all_screens=True).save(a.out/'QuitMenu.png');grab();c.finish();c.click(640,559)
 else:
  offset=Path(r['log']).stat().st_size;c.click(640,519);wait(3)
  log=Path(r['log']).read_bytes()[offset:].decode('utf-8-sig',errors='replace');assert 'LoadMap' in log and '/Game/AnimeMMORPG/Maps/L_Boot' in log,'Actual Back to Boot button did not load Boot'
  m['bootMapVerified']=True;ImageGrab.grab(bbox=bounds,all_screens=True).save(a.out/'Boot.png');grab();wait(1);c.finish();c.console('Quit')
 m['quitRequested']=True;m['captureSeconds']=m['frames'][-1];m['videoSeconds']=encoded/30
 writer.release();writer=None
 # Once Quit is requested, do not inject input or acquire another window's pixels.
 for _ in range(240):
  if not u.IsWindow(c.hwnd):break
  time.sleep(.25)
 assert not u.IsWindow(c.hwnd),'Quit did not destroy owned window'
 m['windowClosed']=True
 for _ in range(480):
  if kernel.WaitForSingleObject(process_handle,250)==0:break
 assert kernel.WaitForSingleObject(process_handle,0)==0,'Quit did not exit owned process; do not count window closure as PASS'
 exit_code=ct.c_ulong();assert kernel.GetExitCodeProcess(process_handle,ct.byref(exit_code));m['exitCode']=exit_code.value;assert exit_code.value==0
 m['completed']=True;m['externalInputMethodRestored']=not c.ime
except Exception as e:m['error']=str(e);raise
finally:
 if writer:writer.release()
 kernel.CloseHandle(process_handle);c.finish();(a.out/'input.json').write_text(json.dumps(m,indent=2))
print(json.dumps(dict(completed=m['completed'],boot=m.get('bootMapVerified'),quitWindowClosed=m['windowClosed'])))
