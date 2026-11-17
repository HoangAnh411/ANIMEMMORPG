"""Fresh gameplay readiness and physical owned-pawn input, before acceptance capture."""
import argparse,json,time,hashlib,subprocess
from pathlib import Path
from DClient import DClient
from DNetworkClient import DNetworkClient
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--network',action='store_true');a=p.parse_args()
out=a.session/'READINESS.json';assert not out.exists()
records=json.loads((a.session/('processes.json' if a.network else 'process.json')).read_text(encoding='utf-8-sig'))
if not a.network:records=[records]
m=dict(completed=False,processes=records,samples=[],inputs=[])
try:
 for r in records:
  if r['role']=='Server':
   rows=[]
   for line in Path(r['log']).read_text(encoding='utf-8-sig').splitlines():
    if 'U02F_STATE {' in line:rows.append(json.loads(line.split('U02F_STATE ',1)[1]))
   selected=rows[-4:];assert len(selected)==4
   assert all(v['pid']==r['pid'] and v['sourceSHA']==r['sourceSHA'] and v['netMode']==1 and v['worldType']==1 and v['localPlayers']==0 and 'L_NetworkLab' in v['world'] for v in selected)
   assert all(y['time']>x['time'] for x,y in zip(selected,selected[1:]));m['samples'].append(dict(role='Server',samples=selected));continue
  c=(DNetworkClient if a.network else DClient)(r)
  samples=[]
  for _ in range(4):samples.append(c.metrics());time.sleep(.35)
  assert all(y['worldSeconds']>x['worldSeconds'] for x,y in zip(samples,samples[1:]))
  assert len({v['pawn'] for v in samples})==1 and all(v['pawn'] and v['controller']==v['owner'] and v['locallyControlled'] and v['localPlayers']==1 for v in samples)
  m['samples'].append(dict(role=r['role'],samples=samples))
  try:
   c.focus()
   observed=c.probe_w()
   if observed!='W':c.toggle_ime();c.ime=True;observed=c.probe_w()
   assert observed=='W', 'Windows input method did not deliver W'
   if c.metrics().get('encounter',{}).get('result',0):
    old=c.metrics()['encounter']['revision'];b=c.metrics()['menuButtons']['Retry encounter'];c.click(round(b['x']),round(b['y']))
    end=time.perf_counter()+6
    while c.metrics()['encounter']['revision']==old:
     assert time.perf_counter()<end;time.sleep(.03)
   if c.metrics()['controlState']!=0:
    b=c.metrics()['menuButtons']['Resume'];c.click(round(b['x']),round(b['y']));time.sleep(.25)
   before=c.metrics();c.press('W',True);time.sleep(.35);after=c.metrics();c.press('W',False)
   m['inputs'].append(dict(role=r['role'],input='physical W down/up',before=before,after=after,result='PASS'))
   assert before['pawn']==after['pawn'] and before['capsuleCenterWorldCm']!=after['capsuleCenterWorldCm']
   c.press('Escape',True);time.sleep(.04);c.press('Escape',False)
  finally:c.finish()
 m['completed']=True
except Exception as e:m['error']=repr(e);raise
finally:out.write_text(json.dumps(m,indent=2),encoding='utf-8')
print('PASS readiness',out)
