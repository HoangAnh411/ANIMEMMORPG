"""Compare saved samples from the three actual processes, without replaying gameplay."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args()
m=json.loads((a.run/'network.json').read_text(encoding='utf-8'));assert m['completed']
checks=[]
def check(name,ok):
 checks.append({'check':name,'result':'PASS' if ok else 'FAIL'});assert ok,name
for stage in m['stages']:
 name=stage['stage']
 if name.endswith('Feint') or (name.startswith('Client') and name.endswith('E')):
  ps=stage['samples'];q=name.endswith('Feint');cost=20 if q else 25;cooldown=4 if q else 6
  keys=['pawnId','life','action','definition','definitionVersion','raw','start','qReady','eReady']
  check(name+' definition/deadlines and timestamp-qualified energy',len(ps)==3 and all(all(x[k]==ps[0][k] for k in keys) and abs(x['energy']-min(100,100-cost+10*max(0,x['serverSnapshotSeconds']-x['start']-1)))<1e-6 and x['qReady' if q else 'eReady']==x['start']+cooldown for x in ps))
 if name.startswith('InterruptedResults') or name.startswith('EDefenseResults'):
  states=stage['states'];assert len(states)==3
  # Client0 is ClientA, Client1 is ClientB; each records its local owner in the source log.
  ix=int(name[len('InterruptedResults')] if name.startswith('InterruptedResults') else name[len('EDefenseResults')])
  owner=next(x for x in states[ix+1]['pawns'] if x['local'])
  events=[next(r for r in reversed(s['results']) if r['target']==owner['id'] and r['targetLife']==owner['life'] and r['definition']==4) for s in states]
  check(name+' actual damage/defense/Interrupt histories',events[0]==events[1]==events[2] and events[0]['raw']==80 and events[0]['definitionVersion']==1 and events[0]['interrupted']==name.startswith('InterruptedResults'))
result={'completed':True,'sourceSHA':m['processes'][0]['sourceSHA'],'method':'Independent comparisons of saved actual server/client samples; energy evaluated at each authority snapshot time, not mismatched wall-clock checkpoints','checks':checks}
(a.run/'network-independent.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS',len(checks),'independent three-process sample comparisons')
