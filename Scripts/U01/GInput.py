"""Guarded input for the packaged G binary; no fallback to an Editor or another PID."""
from pathlib import Path
import ctypes as c,json,subprocess,time
from ctypes import wintypes as w
from F60Input import Client,u,k,key,mouse
from F60Input import VK
VK.update({'Alt':0xa4,'Tab':0x09})

class PackageClient(Client):
 def __init__(self,record):
  self.record=record;self.pid=record['pid'];self.log=Path(record['log']);self.ime=False;self.held=set()
  assert record['role']=='Package' and '/Artifacts/U01/G/' in record['executable'].replace('\\','/') and Path(record['executable']).name=='AnimeMMORPG.exe'
  actual=subprocess.check_output(['powershell','-NoProfile','-Command',f'(Get-CimInstance Win32_Process -Filter "ProcessId={self.pid}").ExecutablePath'],text=True,creationflags=subprocess.CREATE_NO_WINDOW).strip()
  assert Path(actual).resolve()==Path(record['executable']).resolve()
  found=[]
  @c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
  def visit(h,_):
   pid=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(pid));r=w.RECT();u.GetClientRect(h,c.byref(r))
   if pid.value==self.pid and r.right>=640 and r.bottom>=360:found.append(h)
   return True
  for _ in range(240):
   found.clear();u.EnumWindows(visit,0)
   if len(found)==1:break
   time.sleep(.25)
  assert len(found)==1,found;self.hwnd=found[0];b=self.bounds();self.width=b[2]-b[0];self.height=b[3]-b[1]
 def metrics(self):
  with self.log.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-250000));lines=f.read().decode('utf8',errors='replace').splitlines()
  values=[]
  for line in lines:
   if 'Metrics {' in line:
    try:values.append(json.loads(line.split('Metrics ',1)[1]))
    except json.JSONDecodeError:pass
  if not values:raise RuntimeError('No owned packaged Game-world metrics')
  v=values[-1];assert v['pid']==self.pid and v['worldType']==1 and v['netMode']==0 and v['locallyControlled'] and v['localPlayers']==1
  return v
 def focus(self):
  u.ShowWindow(self.hwnd,9);u.SetForegroundWindow(self.hwnd)
  if u.GetForegroundWindow()!=self.hwnd:
   own=k.GetCurrentThreadId();other=u.GetWindowThreadProcessId(u.GetForegroundWindow(),None);target=u.GetWindowThreadProcessId(self.hwnd,None)
   u.AttachThreadInput(own,other,True);attached=target!=other and bool(u.AttachThreadInput(own,target,True))
   try:u.BringWindowToTop(self.hwnd);u.SetActiveWindow(self.hwnd);u.SetForegroundWindow(self.hwnd)
   finally:
    if attached:u.AttachThreadInput(own,target,False)
    u.AttachThreadInput(own,other,False)
  self.guard();time.sleep(.25)
  try:
   if not self.metrics()['windowActive']:self.click(20,20);time.sleep(.3)
  except RuntimeError:pass # Boot has no U01 pawn; it remains UI-only.
 def click_ui(self,x,y):self.click(round(x*self.width/1280),round(y*self.height/720))
 def prepare(self):
  self.focus()
  if not self.metrics()['windowActive']:self.click(20,20);time.sleep(.3)
  if self.metrics()['controlState']==0:self.press('Escape',True);time.sleep(.1);self.press('Escape',False);time.sleep(.3)
  observed=self.probe_w()
  if observed!='W':self.toggle_ime();self.ime=True;observed=self.probe_w()
  assert observed=='W';self.click_ui(640,205 if 'CharacterCombatLab' in self.metrics()['map'] else 322)
  for _ in range(40):
   time.sleep(.1)
   if self.metrics()['controlState']==0:return
  raise RuntimeError('Packaged Resume did not enter Playing')
 def wait_map(self,name,after=None):
  for _ in range(160):
   time.sleep(.1)
   try:v=self.metrics()
   except RuntimeError:continue
   if v['map'].endswith(name) and (after is None or v['utc']>after):return v
  raise RuntimeError('Did not enter owned map '+name)
