"""Single immutable C1 run. Windows input only; no resolver/gameplay shortcuts.

Method probes may shorten warmup/window; they are never baseline runs.
"""
import argparse,ctypes as c,json,subprocess,sys,time,hashlib,traceback,os
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Scripts/U01'))
from F60Input import Client,u,w,k,key,mouse,VK
VK.update({"Alt":0xa4})
from IdentityProcessA import verify

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
    p=Path(p);assert not p.exists(),p;p.write_text(json.dumps(v,indent=2),encoding='utf-8')
def ps(script):return subprocess.check_output(['powershell','-NoProfile','-Command',script],text=True,creationflags=subprocess.CREATE_NO_WINDOW)

class InputClient(Client):
    def __init__(self,r):
        self.record=r;self.pid=r['pid'];self.log=Path(r['log']);self.held=set();self.ime=False
        self.identity=verify(r);found=[]
        @c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
        def visit(h,_):
            pid=w.DWORD();u.GetWindowThreadProcessId(h,c.byref(pid));rect=w.RECT();u.GetClientRect(h,c.byref(rect))
            if pid.value==self.pid and rect.right==1280 and rect.bottom==720:found.append(h)
            return True
        for _ in range(240):
            found.clear();u.EnumWindows(visit,0)
            if len(found)==1:break
            time.sleep(.25)
        assert len(found)==1,found;self.hwnd=found[0]
    def focus(self):
        u.ShowWindow(self.hwnd,9);key('Alt',True);key('Alt',False);u.SetForegroundWindow(self.hwnd)
        time.sleep(.5);self.guard()
    def metrics(self):
        self.console('u01metrics');time.sleep(.15)
        values=[json.loads(l.split('Metrics ',1)[1]) for l in self.log.read_text(encoding='utf-8-sig').splitlines() if 'Metrics {' in l]
        assert values and values[-1]['pid']==self.pid;return values[-1]
    def setup(self):
        self.focus();self.click(20,20);m=self.metrics()
        if m['controlState']!=0:
            # Product menu Resume button, fixed viewport; verified by fresh metrics.
            self.click(640,241);time.sleep(.4);m=self.metrics()
        assert m['controlState']==0,m
        self.press('W',True);time.sleep(.1);self.press('W',False)
        text=self.log.read_text(encoding='utf-8-sig')
        if 'PhysicalPress key=None ' in text and 'PhysicalPress key=W ' not in text:
            self.toggle_ime();self.ime=True
            self.press('W',True);time.sleep(.1);self.press('W',False)
        assert 'PhysicalPress key=W ' in self.log.read_text(encoding='utf-8-sig')
        return m

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--id',required=True)
    p.add_argument('--subjects',type=int,choices=[1,10,40],required=True);p.add_argument('--boxes',type=int,choices=[1,3],required=True)
    p.add_argument('--placement',choices=['in','out'],required=True);p.add_argument('--trace',choices=['off','timing','memory'],required=True)
    p.add_argument('--purpose',choices=['method','correctness','overhead','baseline','illustrative'],required=True)
    p.add_argument('--warmup',type=float,default=30);p.add_argument('--duration',type=float,default=60);p.add_argument('--single-action',action='store_true')
    a=p.parse_args();index=read(a.build/'BUILD-IDENTITY.json');assert Path(index['clone']).resolve()==ROOT
    assert not subprocess.check_output(['git','-C',str(ROOT),'diff',index['sourceSHA'],'--','Source','Content','Config','Plugins','AnimeMMORPG.uproject'])
    if a.purpose in ('baseline','overhead'):assert a.warmup==30 and a.duration==60 and not a.single_action
    if a.purpose=='baseline':assert read(ROOT/'Docs/U04/C1/GATES.json')['methodology']=='PASS','Methodology gate is not PASS; matrix must remain stopped'
    out=ROOT.parent/'Runs'/a.id;out.mkdir(parents=True,exist_ok=False);user=out/'User';user.mkdir();raw=out/'Raw';raw.mkdir()
    exe=a.build/'Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe';assert sha(exe)==index['gameSHA256']
    active=ps("Get-CimInstance Win32_Process -Filter \"Name='AnimeMMORPG.exe'\" | Select-Object ProcessId,ExecutablePath | ConvertTo-Json")
    assert not active.strip(),'A package is active; no retry kill/Start'
    log=out/'Game.log';profile='t.MaxFPS 60,t.IdleWhenNotForeground 0,r.VSync 0,r.ScreenPercentage 50,r.LumenScene.SurfaceCache.AtlasSize 2048,r.RenderTargetPoolMin 128,r.Streaming.PoolSize 256,r.Lumen.DiffuseIndirect.Allow 0,r.Lumen.Reflections.Allow 0,r.Shadow.Virtual.Enable 0,r.ShadowQuality 2'
    args=[str(exe),'/Game/AnimeMMORPG/Maps/L_CharacterCombatLab?U03Regression=1','-windowed','-ResX=1280','-ResY=720','-WinX=0','-WinY=30','-nosplash','-NoLiveCoding','-U04C1Profile',f'-U04C1Output={raw}',f'-U02SourceSHA={index["sourceSHA"]}',f'-U02RunId={a.id}',f'-UserDir={user}',f'-abslog={log}',f'-ExecCmds={profile}']
    if a.trace!='off':args += [f'-trace={"cpu,gpu,frame,bookmark,counters" if a.trace=="timing" else "memory,bookmark"}',f'-tracefile={out/"capture.utrace"}','-statnamedevents']
    write(out/'command.json',dict(arguments=args,workload=vars(a)|{'build':str(a.build)},utc=datetime.now(timezone.utc).isoformat()))
    # UE parses its raw Windows command line: quote values after '=' explicitly.
    command=' '.join(('"'+v+'"') if i==0 else (v.split('=',1)[0]+'="'+v.split('=',1)[1]+'"') if '=' in v and ' ' in v else v for i,v in enumerate(args))
    proc=subprocess.Popen(command,cwd=exe.parent,creationflags=subprocess.CREATE_NO_WINDOW)
    r=dict(role='U04C1Package',pid=proc.pid,executable=str(exe),sourceSHA=index['sourceSHA'],binarySHA256=index['gameSHA256'],userDir=str(user),log=str(log),arguments=args)
    client=None
    try:
        identity=verify(r);r['creationUTC']=identity['creationUTC'];write(out/'process.json',r)
        client=InputClient(r);write(out/'readiness.json',client.setup())
        client.console(f'u04c1 prepare {a.subjects} {a.boxes} {a.placement}')
        def wait_until(t):
            while time.perf_counter()<t:
                assert proc.poll() is None,'Owned package exited';client.guard();time.sleep(min(.02,max(0,t-time.perf_counter())))
        warm=time.perf_counter();wait_until(warm+a.warmup);write(out/'warmup.json',dict(start=warm,end=time.perf_counter()))
        events=[];client.console(f'u04c1 begin {a.duration:g}');start=time.perf_counter()
        for combo in range(1 if a.single_action else 20):
            for attack,offset in enumerate([0] if a.single_action else [0,.32,.77]):
                wait_until(start+3*combo+offset);client.guard();before=time.perf_counter();mouse(2);wait_until(before+.035);mouse(4)
                events.append(dict(combo=combo+1,attack=attack+1,down=before,up=time.perf_counter()))
        wait_until(start+a.duration);write(out/'input.json',dict(events=events,start=start,end=time.perf_counter()))
        deadline=time.perf_counter()+30
        while not (raw/'summary.json').exists():
            assert time.perf_counter()<deadline,'Missing closed summary';time.sleep(.1)
        client.console('quit')
        proc.wait(timeout=30)
        write(out/'exit.json',dict(exitCode=proc.returncode,summary=str(raw/'summary.json'),traceBytes=(out/'capture.utrace').stat().st_size if a.trace!='off' else 0))
    except BaseException as e:
        write(out/'INVALID.json',dict(error=str(e),traceback=traceback.format_exc()))
        # One identity-guarded termination, then wait up to30s. No restart/retry.
        if proc.poll() is None:
            verify(r);assert sha(exe)==r['binarySHA256'];proc.terminate();proc.wait(timeout=30)
        raise
    finally:
        if client is not None:client.finish()
if __name__=='__main__':main()
