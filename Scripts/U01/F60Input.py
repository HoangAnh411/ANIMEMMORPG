"""Guarded real Windows input for F60 measurements; never targets the original Editor."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import json,subprocess,time

u=c.WinDLL('user32',use_last_error=True);k=c.WinDLL('kernel32',use_last_error=True)
u.GetForegroundWindow.restype=w.HWND
u.GetWindowThreadProcessId.argtypes=[w.HWND,c.POINTER(w.DWORD)]
u.GetClientRect.argtypes=[w.HWND,c.POINTER(w.RECT)];u.ClientToScreen.argtypes=[w.HWND,c.POINTER(w.POINT)]
for name in ('SetForegroundWindow','SetActiveWindow','BringWindowToTop'):getattr(u,name).argtypes=[w.HWND]
u.ShowWindow.argtypes=[w.HWND,c.c_int]
class Mouse(c.Structure):_fields_=[('dx',w.LONG),('dy',w.LONG),('data',w.DWORD),('flags',w.DWORD),('time',w.DWORD),('extra',c.c_size_t)]
class Key(c.Structure):_fields_=[('vk',w.WORD),('scan',w.WORD),('flags',w.DWORD),('time',w.DWORD),('extra',c.c_size_t)]
class Payload(c.Union):_fields_=[('mouse',Mouse),('key',Key)]
class Input(c.Structure):_fields_=[('type',w.DWORD),('payload',Payload)]
u.SendInput.argtypes=[w.UINT,c.POINTER(Input),c.c_int]
VK={'W':0x57,'S':0x53,'Ctrl':0xa2,'Shift':0xa0,'Space':0x20,'V':0x56,'Escape':0x1b,'Enter':0xd,'Console':0xc0}
def emit(event):
 if u.SendInput(1,c.byref(event),c.sizeof(Input))!=1:raise c.WinError(c.get_last_error())
def key(name,down):emit(Input(type=1,payload=Payload(key=Key(vk=VK.get(name,ord(name) if len(name)==1 else 0),flags=0 if down else 2))))
def mouse(flags,dx=0,dy=0):emit(Input(type=0,payload=Payload(mouse=Mouse(flags=flags,dx=dx,dy=dy))))
class Client:
 def __init__(self,record,stage='F'):
  self.record=record;self.pid=record['pid'];self.log=Path(record['log']);self.ime=False;self.held=set()
  assert record['role'] in ('ClientA','ClientB') and '-game' in record['arguments']
  cmd=subprocess.check_output(['powershell','-NoProfile','-Command',f'(Get-CimInstance Win32_Process -Filter "ProcessId={self.pid}").CommandLine'],text=True,creationflags=subprocess.CREATE_NO_WINDOW).replace('\\','/')
  assert record['project'].replace('\\','/').lower() in cmd.lower() and '-game' in cmd and '-server' not in cmd
  assert Path(record['executable']).name=='UnrealEditor.exe' and stage in ('F','G') and ('/Artifacts/U01/'+stage+'/Source/') in record['project'].replace('\\','/')
  found=[]
  @c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
  def visit(h,_):
   pid=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(pid));r=w.RECT();u.GetClientRect(h,c.byref(r))
   if pid.value==self.pid and r.right==900 and r.bottom==540:found.append(h)
   return True
  u.EnumWindows(visit,0);assert len(found)==1,found;self.hwnd=found[0]
 def focus(self):
  u.ShowWindow(self.hwnd,9);u.SetForegroundWindow(self.hwnd)
  if u.GetForegroundWindow()!=self.hwnd:
   own=k.GetCurrentThreadId();other=u.GetWindowThreadProcessId(u.GetForegroundWindow(),None);target=u.GetWindowThreadProcessId(self.hwnd,None)
   u.AttachThreadInput(own,other,True);attached=target!=other and bool(u.AttachThreadInput(own,target,True))
   try:u.BringWindowToTop(self.hwnd);u.SetActiveWindow(self.hwnd);u.SetForegroundWindow(self.hwnd)
   finally:
    if attached:u.AttachThreadInput(own,target,False)
    u.AttachThreadInput(own,other,False)
  self.guard();time.sleep(.2)
  # Win32 foreground alone is not proof that Slate has activated its viewport.
  # A real click in a blank menu corner activates it without selecting Resume.
  if not self.metrics()['windowActive']:self.click(20,20)
  for _ in range(30):
   self.guard()
   if self.metrics()['windowActive']:return
   time.sleep(.1)
  raise RuntimeError('Win32 foreground did not activate the native game viewport')
 def guard(self):
  pid=w.DWORD();u.GetWindowThreadProcessId(self.hwnd,c.byref(pid))
  if pid.value!=self.pid or u.GetForegroundWindow()!=self.hwnd:raise RuntimeError('Input focus/PID changed; abort rather than steal focus')
 def bounds(self):
  r=w.RECT();p=w.POINT();u.GetClientRect(self.hwnd,c.byref(r));u.ClientToScreen(self.hwnd,c.byref(p));return(p.x,p.y,p.x+r.right,p.y+r.bottom)
 def metrics(self):
  with self.log.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-250000));lines=f.read().decode('utf8',errors='replace').splitlines()
  values=[]
  for l in lines:
   if 'Metrics {' in l:
    try:values.append(json.loads(l.split('Metrics ',1)[1]))
    except json.JSONDecodeError:pass
  assert values and values[-1]['pid']==self.pid and values[-1]['worldType']==1 and values[-1]['netMode']==3
  return values[-1]
 def press(self,name,down):
  self.guard();key(name,down)
  if down:self.held.add(name)
  else:self.held.discard(name)
 def click(self,x,y):
  self.guard();left,top,_,_=self.bounds();u.SetCursorPos(left+x,top+y);time.sleep(.08);mouse(2);time.sleep(.08);mouse(4)
 def toggle_ime(self):
  self.guard();key('Ctrl',True);key('Shift',True);time.sleep(.06);key('Shift',False);key('Ctrl',False);time.sleep(.15)
 def probe_w(self):
  size=self.log.stat().st_size;self.press('W',True);time.sleep(.15);self.press('W',False)
  for _ in range(30):
   time.sleep(.1)
   with self.log.open('rb') as f:f.seek(size);s=f.read().decode('utf8',errors='replace')
   if 'PhysicalPress key=W ' in s:return 'W'
   if 'PhysicalPress key=None ' in s:return 'None'
  raise RuntimeError('No native physical-key observation for IME probe')
 def prepare(self):
  self.focus()
  if self.metrics()['controlState']==0:self.press('Escape',True);time.sleep(.1);self.press('Escape',False);time.sleep(.25)
  observed=self.probe_w()
  if observed!='W':self.toggle_ime();self.ime=True;observed=self.probe_w()
  assert observed=='W';self.click(450,241)
  for _ in range(20):
   time.sleep(.1)
   if self.metrics()['controlState']==0:return
  raise RuntimeError('Resume did not enter Playing')
 def console(self,text):
  self.guard();key('Console',True);time.sleep(.06);key('Console',False);time.sleep(.2)
  for ch in text.lower():
   code=u.VkKeyScanW(ord(ch))&255;emit(Input(type=1,payload=Payload(key=Key(vk=code))));time.sleep(.012);emit(Input(type=1,payload=Payload(key=Key(vk=code,flags=2))));time.sleep(.012)
  key('Enter',True);time.sleep(.06);key('Enter',False);time.sleep(.25)
 def release(self):
  for name in list(self.held):key(name,False)
  self.held.clear()
 def finish(self):
  self.release()
  if self.ime and u.GetForegroundWindow()==self.hwnd:self.toggle_ime();self.ime=False
