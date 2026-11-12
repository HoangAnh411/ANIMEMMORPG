"""Verify the actual fresh reconnect process; never count a trigger as a pass."""
import argparse,json
from pathlib import Path
from B1NetworkClient import B1NetworkClient
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--network',type=Path,required=True);a=p.parse_args()
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));r=next(x for x in records if x['role']=='ClientA');c=B1NetworkClient(r);v=c.metrics();old=json.loads((a.network/'network.json').read_text());ids=[p['id'] for p in old['stages'][0]['states'][0]['pawns']]
checks=[{'check':'Fresh authority identity and HP1000','result':'PASS' if v['combat']['pawnId'] not in ids and v['combat']['vital']['hp']==1000 else 'FAIL'},{'check':'Two charges, no old dodge/action/pending replay','result':'PASS' if v['combat']['dodge']==0 and v['combat']['dodgeCharges']==2 and v['combat']['action']==0 and v['combat']['pendingCommand']==0 else 'FAIL'}]
result={'completed':all(x['result']=='PASS' for x in checks),'checks':checks,'process':r,'metrics':v,'method':'Live PID/exe/module/source/project/world/owner guards and native runtime metrics'}
(a.session/'reconnect-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');assert result['completed'];print('Reconnect2/2 PASS')
