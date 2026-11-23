import sys,json,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,'Scripts/U04')
from C1Win32 import Backend
from C1Run import sha
from C1Identity import path_key
p=Path('../CC-B-Batch-Control')
runs=Path('../Runs')
root=Path.cwd().parents[3]
old=json.loads(Path('../CC-B-01-Control/before.json').read_text())
def git(*a):return subprocess.check_output(['git',*a]).decode().strip()
def save(path,v):
 with path.open('x') as f:json.dump(v,f,indent=2)
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def snap():
 files=set(old['hashes'])
 for name in ('CC-B-01-1x1-in','CC-B-01-1x1-in-R1','CC-B-Batch-01-1x1-in'):
  files.update(str(f.resolve()) for f in (runs/name).rglob('*') if f.is_file())
 return dict(head=git('-C',str(root),'rev-parse','HEAD'),status=git('-C',str(root),'status','--porcelain'),hashes={f:sha(f) for f in sorted(files)})
def inventory():
 b=Backend(input_enabled=False); editors=[]; games=[]
 for row in b.inventory():
  pid=row['ProcessId'];h=b.k.OpenProcess(0x1000,False,pid)
  if not h:raise RuntimeError(f'OpenProcess PID {pid}')
  try:i=b.handle_identity(h)
  finally:b.k.CloseHandle(h)
  if Path(i['executable']).name.lower()=='animemmorpg.exe':games.append(i)
  else:
   project=str(root/'AnimeMMORPG.uproject')
   i['project']=project if project.lower() in (row.get('CommandLine') or '').lower() else 'unknown'
   editors.append(i)
 return editors,games
def identities(items):return {(i['pid'],i['creationTicks'],path_key(i['executable'])) for i in items}
def invoke(folder,label,args):
 save(folder/(label+'-argv.json'),args)
 with (folder/(label+'.stdout')).open('xb') as o,(folder/(label+'.stderr')).open('xb') as e:code=subprocess.call(args,stdout=o,stderr=e)
 save(folder/(label+'-exit.json'),code);return code
def main():
 commit=sys.argv[1]
 exe=runs/'Build-03/Archive/Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe'
 digest=sha(exe)
 if git('rev-parse','HEAD')!=commit or git('status','--porcelain') or git('diff','13b4f34','--','Source','Content','Config','Plugins','AnimeMMORPG.uproject') or digest!='282fcefc5156be5f5aa81caf2bc3a764949f2eaf76de081f9c62aa0e2e54e5a5':
  raise RuntimeError('build/tooling preflight mismatch')
 cells=[(n,h,place) for n in (1,10,40) for h in (1,3) for place in ('in','out')]
 ids=[f'CC-B-FG-{i:02d}-{n}x{h}-{place}' for i,(n,h,place) in enumerate(cells,1)]
 ledger=[dict(id=id,subjects=n,boxes=h,placement=placement,status='NOT_RUN') for id,(n,h,placement) in zip(ids,cells)]
 existing=[id for id in ids if (runs/id).exists()]
 if existing:raise RuntimeError(f'run IDs already exist: {existing}')
 before=snap(); save(p/'workspace-before.json',before)
 initial,games=inventory()
 save(p/'preflight.json',dict(commit=commit,gameSHA256=digest,editors=initial,games=games))
 try:
  for row in ledger:
   id=row['id'];run=runs/id; c=p/id;c.mkdir()
   editors,games=inventory()
   save(c/'inventory-before.json',dict(editors=editors,games=games))
   if games or run.exists() or not identities(initial)<=identities(editors):raise RuntimeError('per-cell process or run ID preflight failed')
   row.update(replaces='CC-B-Batch-01-1x1-in' if row is ledger[0] else None,status='INVALID',raw=str(run.resolve()))
   code=invoke(c,'launcher',['python','-B','Scripts/U04/C1CounterRun.py','--build',r'..\Runs\Build-03','--id',id,'--subjects',str(row['subjects']),'--boxes',str(row['boxes']),'--placement',row['placement']])
   row['launcherExit']=code
   if all((run/f).exists() for f in ('capture.json','result.json','final.json')):
    row['validatorExit']=invoke(c,'validator',['python','-B','Scripts/U04/C1Validate.py',str(run),'--single-action'])
    row['validation']=read(run/'validation.json')
   final=read(run/'final.json') if (run/'final.json').exists() else {}
   row['final']=final
   after,games=inventory(); preserved=identities(editors)<=identities(after) and snap()==before
   save(c/'preservation.json',dict(preserved=preserved,editors=after,games=games))
   row['preserved']=preserved
   if preserved and not games:
    checked=row.get('validation',{}).get('status')
    if checked=='FAIL' and final.get('status')=='FAIL':row['status']='FAIL'
    if code==0 and row.get('validatorExit')==0 and checked=='PASS' and final.get('status')=='PASS':
     cap=read(run/'capture.json');summary=read(run/'Raw/summary.json'); process=read(run/'process.json')
     j=[json.loads(l) for l in (run/'journal.jsonl').read_text(encoding='utf-8').splitlines()]
     edges=[e for e in j if e['event']=='input_sent' and e.get('purpose')=='counter-action']
     action=[a for a in summary['actionEvents'] if a['kind']=='ActionStarted'][0]
     prepared=cap['prepared']['metrics']['combat']; aftercombat=cap['after']['metrics']['combat']
     row.update(status='PASS',process={k:process[k] for k in ('pid','creationTicks','executable')},prepare=cap['prepareTransition'],
                preparedCombat={k:prepared[k] for k in ('pawnId','life','action','phase')},edges=[e['seq'] for e in edges],action=action,
                damage=summary['damageEvents'],targets=summary['targets'],registration=[summary['registrationBegin'],summary['registrationEnd']],
                metricsDelta={k:aftercombat[k]-prepared[k] for k in ('geometryQueries','damageResults')})
   save(c/'ledger-entry.json',row)
   print(id,row['status'],final.get('error',''),flush=True)
   if row['status']!='PASS':break
 finally:
  save(p/'ledger.json',ledger)
  save(p/'workspace-after.json',snap())
  pairs=[]
  for n in (1,10,40):
   for place in ('in','out'):
    group=[r for r in ledger if r['subjects']==n and r['placement']==place and r['status']=='PASS']
    if len(group)==2:
     counts=[]
     for row in group:
      from collections import Counter
      counts.append(list(Counter((e['target'],e['targetLife']) for e in row['damage']).values()))
     k=n if place=='in' else 0
     pairs.append(dict(subjects=n,placement=place,runs=[r['id'] for r in group],hitCounts=[len(c) for c in counts],passBoth=all(c==[1]*k for c in counts)))
  save(p/'pairs.json',pairs)
if __name__=='__main__':main()

