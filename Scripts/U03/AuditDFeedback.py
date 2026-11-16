"""Check recorded client feedback identities/freshness and parry loopback; no packet injection claim."""
import argparse,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
records=json.loads((a.session/'all-processes.json').read_text(encoding='utf-8-sig'));rows=[]
pattern=re.compile(r'U03D_FEEDBACK serial=(\d+) kind=(\d+) subject=(\w+) life=(\d+) action=(\d+) encounter=(\w+) revision=(\d+) at=([\d.]+) now=([\d.]+) audio=(\d+)')
for process in records:
 matches=pattern.findall(Path(process['log']).read_text(encoding='utf-8-sig'));seen=set();audible=0
 if process['role']=='Server':assert not matches,'Dedicated server created HUD feedback'
 for serial,kind,subject,life,action,encounter,revision,at,now,audio in matches:
  key=(serial,subject,life,action,encounter,revision);assert key not in seen,('Repeated feedback',process['pid'],key);seen.add(key)
  if audio=='1':assert -1.e-6<=float(now)-float(at)<=.150001;audible+=1
 rows.append(dict(role=process['role'],pid=process['pid'],events=len(matches),audible=audible,duplicateIdentities=0))
combat=Path('Artifacts/U03/D/Runs/FinalCombat-20261115-221500');audio=json.loads((combat/'audio.json').read_text(encoding='utf-8'))
def groups(hz):
 times=[x['time'] for x in audio['peaks'] if abs(x['frequency']-hz)<20];return [t for i,t in enumerate(times) if i==0 or t-times[i-1]>.08]
first,second=groups(660),groups(990);assert len(first)==1 and len(second)==1 and first[0]<second[0],(first,second)
reg=json.loads(Path('Artifacts/U03/D/Runs/FinalRegression-20261116-120100/audio.json').read_text(encoding='utf-8'))
bands={str(h):sum(abs(x['frequency']-h)<25 for x in reg['peaks']) for h in [110,160,220,330,440,660,880,990,1320]};assert all(bands.values()),bands
result=dict(completed=True,processes=rows,parry660Groups=first,parry990Groups=second,regressionFrequencyBands=bands,scope='Recorded identity/audio dedup; initial history/life/late snapshots additionally covered by Native D tests; arbitrary network packet injection not claimed')
(a.out/'feedback-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(dict(completed=True,processes=len(rows),parryGroups=[len(first),len(second)])))
