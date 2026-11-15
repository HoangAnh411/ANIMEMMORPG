"""Independent comparisons of saved real process samples. Never replays gameplay."""
import argparse,json,math
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();m=json.loads((a.run/'network.json').read_text(encoding='utf-8'));assert m['completed']
checks=[]
def check(name,ok):checks.append(dict(check=name,result='PASS' if ok else 'FAIL'));assert ok,name
def pair(row,identity):
 e=next(v for v in row['encounters'] if v['id']==identity);actors={v['id']:v for v in row['pawns']}
 return e,[actors[e['player']],actors[e['monster']]]
for stage in m['stages']:
 if 'states' not in stage:continue
 rows=stage['states'];check(stage['stage']+' samples are from three distinct processes',len(rows)==3 and len({r['pid'] for r in rows})==3)
 check(stage['stage']+' review caps and source agree',len({r['sourceSHA'] for r in rows})==1 and all(r['t.MaxFPS']==(30 if r['netMode']==1 else 60) for r in rows))
 pairs=[pair(r,stage['identity']) for r in rows]
 if stage['stage'].endswith('E results'):
  events=stage['events'];check(stage['stage']+' complete damage/defense/Interrupt records agree',events[0]==events[1]==events[2] and events[0]['raw']==80 and events[0]['definition']==4 and events[0]['interrupted'] and events[0]['encounter']==stage['identity'])
  continue
 keys=['life','action','definition','definitionVersion','raw','start','qReady','eReady','dodge','dodgeCharges','hardCC','interruptSequence']
 summaries=[dict(encounter={k:e[k] for k in ['id','revision','result','ai','player','monster']},actors=[{k:v[k] for k in keys}|{'hp':v['vital']['hp'],'vitalLife':v['vital']['lifeGeneration']} for v in actors]) for e,actors in pairs]
 check(stage['stage']+' independent HP/action/AI/result/revision comparison',summaries[0]==summaries[1]==summaries[2])
 if stage['stage'].endswith('E Interrupt'):
  for _,actors in pairs:
   v=actors[0];expected=min(100,75+10*max(0,v['serverSnapshotSeconds']-v['start']-1))
   check(stage['stage']+' resources evaluated at its own authority timestamp',abs(v['energy']-expected)<1.e-6 and v['eReady']==v['start']+6)
before=next(s for s in m['stages'] if s['stage']=='Terminal1');after=next(s for s in m['stages'] if s['stage']=='RetryA')
for x,y in zip(before['states'],after['states']):
 e,actors=pair(x,before['identity']);f,new=pair(y,before['identity'])
 check('RetryA leaves B identity/life/HP/result/revision stable',all(e[k]==f[k] for k in ['id','revision','result']) and all(u['life']==v['life'] and u['action']==v['action'] and u['vital']['hp']==v['vital']['hp'] for u,v in zip(actors,new)))
old=next(s['metrics'] for s in m['stages'] if s['stage']=='BeforeDisconnect');new=next(s['metrics'] for s in m['stages'] if s['stage']=='AfterReconnect')
check('Reconnect is a new encounter/pawn rather than restored combat',old['encounter']['id']!=new['encounter']['id'] and old['combat']['pawnId']!=new['combat']['pawnId'] and old['combat']['eReady']>0 and new['combat']['eReady']==0 and new['combat']['energy']==100 and new['combat']['life']==1)
check('Saved protocol probes include actual server rejections',all(v.get('serverMarker','').endswith('accepted=0') for v in m['events'] if 'probe' in v) and len([v for v in m['events'] if 'probe' in v])>=5)
result=dict(completed=True,sourceSHA=m['processes'][0]['sourceSHA'],method='Saved samples from actual server and both clients; no gameplay replay; input remains sequential',checks=checks)
(a.run/'network-independent.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('PASS',len(checks),'independent network comparisons')
