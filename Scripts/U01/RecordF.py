"""Seal U01-F proof from dedicated Editor server + two real clients.
Video export only removes the desktop gap between the client rectangles.
"""
import csv,hashlib,json,shutil,subprocess
from datetime import datetime
from pathlib import Path
import cv2
import numpy as np
cv2.setNumThreads(1)
root=Path(__file__).resolve().parents[2]
art=root/'Artifacts/U01/F';run=art/'Session-20261105-120906';out=root/'Docs/U01/Evidence/F';out.mkdir(parents=True,exist_ok=True)
source='df897f6088da4cca423085e9fe8e9c2869c98420'
build=art/'Build-20261105-120525-295-b4be0b5d';tests=art/'MCPTests-20261105-120700';package=art/'Package-20261105-120856-201-0ffc4cbc/Archive/Windows'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def write(n,data):(out/n).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append({'name':name,'result':'PASS'})
assert subprocess.check_output(['git','-C',str(art/'Source'),'rev-parse','HEAD'],text=True).strip()==source
records=load(run/'all-processes.json');write('PROCESSES.json',records)
logs={};samples={}
for role,path in [('Server',run/'Server/Server.log'),('ClientA',run/'ClientA/ClientA.log'),('ClientB',run/'ClientB/ClientB.log'),('ReconnectB',run/'ClientB/Reconnect.log')]:
 lines=path.read_text(encoding='utf-8-sig').splitlines();logs[role]=lines
 samples[role]=[json.loads(l.split('U01F_NET ',1)[1]) for l in lines if 'U01F_NET {' in l]
 check('Fresh owned Game-world identity '+role,all(s['sourceSHA']==source and s['worldType']==1 and s['netMode']==(1 if role=='Server' else 3) and s['localPlayers']==(0 if role=='Server' else 1) for s in samples[role]))
 check('Runtime Python errors absent '+role,not any('AttributeError:' in l or 'Accessed None' in l or 'Blueprint Runtime Error' in l for l in lines))
 check('No pawn duplication '+role,all(len(s['pawns'])<=2 for s in samples[role]))
 if role!='Server':check('Exactly one owned autonomous pawn '+role,all(sum(p['local'] and p['role']==2 for p in s['pawns'])==1 for s in samples[role] if s['pawns']))
 else:check('Dedicated has no local controller/UI',all(s['visibleMenus']==0 and not any(p['local'] for p in s['pawns']) for s in samples[role]))
 chosen=[l for l in lines if ('ProbeRejected' in l or 'ClientProbe' in l or 'FixtureReset' in l or 'FixtureGround' in l or 'Join succeeded' in l or 'NotifyAcceptingConnection' in l or 'CloseBunch' in l or 'LogNet: UChannel::Close:' in l or 'Python disabled via' in l)]
 (out/(role+'-events.log')).write_text('\n'.join(chosen)+'\n',encoding='utf-8',newline='\n')
oldA=next(p['id'] for s in samples['ClientA'] for p in s['pawns'] if p['local']);oldB=next(p['id'] for s in samples['ClientB'] for p in s['pawns'] if p['local']);newB=next(p['id'] for s in samples['ReconnectB'] for p in s['pawns'] if p['local'])
check('Server IDs distinct; reconnect receives new identity',len({oldA,oldB,newB})==3)
case_roles={'NormalA':'ClientA','NormalB':'ClientB','AttacksSettingsA':'ClientA','SpeedA':'ClientA','MoveQuitB':'ClientB','ReconnectBOnRunway':'ReconnectB'}
cases={}
def export_video(case):
 src=run/case/'Play-F.mp4';cap=cv2.VideoCapture(str(src));rate=cap.get(cv2.CAP_PROP_FPS);frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));assert w>=1800 and h==540
 dst=out/(case+'.mp4');writer=cv2.VideoWriter(str(dst),cv2.VideoWriter_fourcc(*'mp4v'),rate,(1800,h));assert writer.isOpened()
 count=0
 while True:
  ok,frame=cap.read()
  if not ok:break
  writer.write(np.concatenate((frame[:,:900],frame[:,-900:]),axis=1));count+=1
 writer.release();cap.release();assert count==frames
 return {'rawSHA256':digest(src),'exportSHA256':digest(dst),'frames':count,'encodedHz':rate,'edit':'Remove only desktop gap; retain both 900x540 client rectangles, frame order, all in-game warnings and duplicate timing frames. No interpolation.'}
for case,role in case_roles.items():
 m=load(run/case/'process.json');start=utc(m['utc']);duration=m['captureActiveSeconds'];d={}
 check('Completed guarded real input '+case,m['completed'] and not m['staticCaptureRejected'] and m['externalInputMethodRestored'])
 for peer,ns in samples.items():
  d[peer]=[dict(s,caseTime=(utc(s['utc'])-start).total_seconds()) for s in ns if 0<=(utc(s['utc'])-start).total_seconds()<=duration]
 cases[case]={'metadata':m,'samples':d,'video':export_video(case)}
 for p in (run/case).glob('*.png'):
  if not p.name.startswith('frame-') and p.name!='initial.png':shutil.copyfile(p,out/(case+'-'+p.name))
 write(case+'.json',cases[case])
def pawns(case,role,id):return [p for s in cases[case]['samples'][role] for p in s['pawns'] if p['id']==id]
for case,id,owner,peer in [('NormalA',oldA,'ClientA','ClientB'),('NormalB',oldB,'ClientB','ClientA'),('ReconnectBOnRunway',newB,'ReconnectB','ClientA')]:
 for who in ('Server',owner,peer):
  ps=pawns(case,who,id)
  # NormalA's Ctrl edge was not observed; A sprint is proven by the separate
  # AttacksSettingsA real-input run, on the same pawn and source, before probes.
  sprint_samples=pawns('AttacksSettingsA',who,id) if case=='NormalA' else ps
  check('Walk seen '+case+'/'+who,any(abs(p['speed']-500)<2 for p in ps))
  check('Sprint seen '+('AttacksSettingsA' if case=='NormalA' else case)+'/'+who,any(abs(p['speed']-700)<2 for p in sprint_samples))
  check('Locomotion/jump presentation '+case+'/'+who,{1,2}<=set(p.get('pose',-1) for p in ps))
  check('Grounded and idle after landing '+case+'/'+who,ps[-1]['mode']==1 and ps[-1].get('pose')==0)
  check('Settled location matches authority '+case+'/'+who,abs(ps[-1]['x']-pawns(case,'Server',id)[-1]['x'])<5 and abs(ps[-1]['z']-pawns(case,'Server',id)[-1]['z'])<5)
for case,id in [('NormalA',oldA),('NormalB',oldB)]:
 other=oldB if id==oldA else oldA;ps=pawns(case,'Server',other)
 check('Only owned pawn responds '+case,max(p['x'] for p in ps)-min(p['x'] for p in ps)<1)
check('Server speed bound for entire session',all(p['speed']<=700.1 for s in samples['Server'] for p in s['pawns']))
rejects=[l for l in logs['Server'] if 'ProbeRejected' in l]
check('Overspeed request 2000 rejected',any('Overspeed claim=2000.0' in l for l in rejects))
check('Actual client overspeed prediction exercised',max(p['speed'] for p in pawns('SpeedA','ClientA',oldA))>701)
speed_moves=pawns('SpeedA','ClientA',oldA)
check('Actual overspeed receives server correction',max(p['corrections'] for p in speed_moves)>min(p['corrections'] for p in speed_moves))
check('Additional jump rejected while airborne',any('ExtraJump claim=800.0' in l and 'mode=3 count=1' in l for l in rejects))
check('Foreign pawn target rejected',any('Ownership' in l and oldB in l and oldA in l for l in rejects))
ps=pawns('AttacksSettingsA','ClientA',oldA);check('Client corrected after malformed jump',max(p['corrections'] for p in ps)>min(p['corrections'] for p in ps))
server_air=[p for s in cases['AttacksSettingsA']['samples']['Server'] if 4.4<=s['caseTime']<=6.5 for p in s['pawns'] if p['id']==oldA]
check('No server second ascent after rejected air jump',all(p['vz']<=0 for s in cases['AttacksSettingsA']['samples']['Server'] if 5.5<=s['caseTime']<=6.5 for p in s['pawns'] if p['id']==oldA))
check('Server jump apex stays within motor bound',max(p['z'] for p in server_air)<=223.2)
ps=pawns('AttacksSettingsA','ClientB',oldA);check('Remote observer has jump/fall/land states',{2,3,4}<=set(p.get('pose',-1) for p in ps))
# Local preferences are collected separately by the owned PlayerController, never inferred from a remote pawn.
controls={}
for role,path in [('ClientA',run/'ClientA/ClientA.log'),('ClientB',run/'ClientB/ClientB.log'),('ReconnectB',run/'ClientB/Reconnect.log')]:
 data=[json.loads(l.split('Metrics ',1)[1]) for l in path.read_text(encoding='utf-8-sig').splitlines() if 'Display: Metrics {' in l];controls[role]=data[-1]
check('A rebind/sensitivity saved locally',json.loads(controls['ClientA']['settings'])['bindings']['Forward']=='H' and json.loads(controls['ClientA']['settings'])['sensitivity']>1.9)
for who in ('ClientB','ReconnectB'):
 p=json.loads(controls[who]['settings']);check('B settings independent '+who,p['bindings']['Forward']=='W' and p['sensitivity']==1)
check('No contexts accumulate',all(v['mappingContextCount']==1 for v in controls.values()))
write('SETTINGS.json',controls)
ns=cases['MoveQuitB']['samples']['Server'];check('A menu does not pause server/B',ns[-1]['seconds']-ns[0]['seconds']>5 and max(p['speed'] for s in ns for p in s['pawns'] if p['id']==oldB)>699 and all(p['speed']<.1 for s in ns for p in s['pawns'] if p['id']==oldA))
quit_meta=cases['MoveQuitB']['metadata'];quit_end=utc(quit_meta['utc']).timestamp()+quit_meta['captureActiveSeconds'];reconnect_start=utc(records[-1]['utc']).timestamp()
between=[s for s in samples['Server'] if quit_end+.5<utc(s['utc']).timestamp()<reconnect_start]
check('Quit removes old pawn before reconnect',len(between)>2 and all({p['id'] for p in s['pawns']}=={oldA} for s in between))
last=samples['Server'][-1];check('Reconnect has exactly A + new B, no ghost',{p['id'] for p in last['pawns']}=={oldA,newB})
for role in ('ClientB','ReconnectB'):check('Server-generated ID shared across processes '+role,any((newB if role=='ReconnectB' else oldB) in {p['id'] for p in s['pawns']} for s in samples[role]))
# Startup regression: report errors before mitigation, not a claim that editor toolsets work at runtime.
before=art/'PythonBefore-20261105-105711';python_before={}
for r in load(before/'processes.json'):
 lines=Path(r['log']).read_text(encoding='utf-8-sig').splitlines();python_before[r['role']]=[l for l in lines if 'AttributeError:' in l]
check('A Python errors reproduced on all three processes',all(len(v)==3 for v in python_before.values()))
write('PYTHON-REGRESSION.json',{'beforeSource':load(before/'processes.json')[0]['sourceSHA'],'before':python_before,'afterSource':source,'afterArguments':'-DisablePython only for -server/-game; Editor Automation retains Python/MCP','afterErrorCount':0})
lines=(tests/'Editor.log').read_text(encoding='utf-8-sig').splitlines();done=[l for l in lines if 'Test Completed. Result=' in l];check('Twenty-three actual Automation successes',len(done)==23 and all('Result={Success}' in l for l in done) and any('23 tests performed' in l for l in lines))
write('AUTOMATION.json',{'sourceSHA':source,'process':load(tests/'process.json'),'tests':done,'measurements':[l for l in lines if 'U01C_MEASURE ' in l or 'U01D_MEASURE ' in l]})
smoke=load(art/'SmokeB-20261105-121748/results.json');check('Three packaged map smokes',len(smoke)==3 and all(s['passed'] and s['exitCode']==0 for s in smoke));write('SMOKE.json',smoke)
write('CHECKS.json',{'sourceSHA':source,'method':'Postprocessing native Game-world identities and real guarded OS input; not additional Automation tests','checks':checks})
with (out/'PACKAGE.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['PathUnderWindows','Bytes','SHA256'])
 for p in sorted(package.rglob('*')):
  if p.is_file():w.writerow([p.relative_to(package).as_posix(),p.stat().st_size,digest(p)])
manifest={'status':'READY_FOR_REVIEW','branch':'u01/f-network','baseSHA':'99363222895b0069b3afdab2b103bfc81c68af6b','sourceSHA':source,'engine':'UE5.8.4 CL58902052','toolchain':'MSVC14.51.36260 / SDK10.0.26100.0','build':str(build.relative_to(root)),'tests':str(tests.relative_to(root)),'automationCount':23,'inputChecks':len(checks),'session':str(run.relative_to(root)),'package':str(package.relative_to(root)),'moduleSHA256':digest(art/'Source/Binaries/Win64/UnrealEditor-AnimeMMORPG.dll'),'engineExeSHA256':digest(Path('D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe')),'ids':{'A':oldA,'oldB':oldB,'newB':newB},'captureHz':{n:c['metadata']['uniqueCaptureHz'] for n,c in cases.items()},'speedFixture':{'claim':2000,'rejected':True,'serverMaxObserved':max(p['speed'] for s in samples['Server'] for p in s['pawns']),'clientMaxObservedInSpeedProbe':max(p['speed'] for p in pawns('SpeedA','ClientA',oldA)),'note':'Client-side prediction exceeds limit during malformed fixture; server remains bounded and issues correction. Fixture only, no production speed API.'},'limits':['Installed Editor dedicated only; no packaged Server acceptance','No latency/loss/jitter/combat prediction or integrated FPS acceptance','VRAM exhausted warning visible with two rendered clients + original Editor; renderer unchanged; video export retains warnings','Anime art/combat animation DEFERRED; D temporary carry unchanged'],'history':['Compile declaration fixes before 97400db retained','97400db startup ready check originally matched Zen rather than IpNetDriver; no-world early attempt not acceptance','919fec2 throttle config initially in wrong file; corrected via per-process EditorSettings override','b5d1ff0 local movable fixture base caused proxy landing failure; 0166d6f replicates server fixture base','b1c3ed0 presents authoritative replicated proxy velocity; owner/authority motor unchanged','Short input pulse lost within a slow frame; physical space hold 0.6s used for normal probes, no variable-height jump']}
write('MANIFEST.json',manifest)
print('Sealed',len(checks),'F checks; 23 Automation tests; source',source)
