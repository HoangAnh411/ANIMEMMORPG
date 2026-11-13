"""Independent comparisons of already recorded three-process defense samples."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args();data=json.loads((a.run/'network.json').read_text(encoding='utf-8'));assert data['completed'];checks=[]
for stage in data['stages']:
 if 'samples' not in stage:continue
 ps=stage['samples'];states=stage['states'];keys=['immuneEnd','slow','parryStart','parryEnd','guardYaw']
 passed=all(all(v[k]==ps[0][k] for k in keys) for v in ps) and all(v['results']==states[0]['results'] for v in states)
 checks.append({'check':stage['stage']+' immunity/slow/parry deadlines and complete confirmed-result identities agree','result':'PASS' if passed else 'FAIL'})
result={'completed':bool(checks) and all(x['result']=='PASS' for x in checks),'checks':checks,'method':'Compare immutable samples captured from server and both clients after each physical defense stage; not new live input or a simultaneous-hit claim'}
(a.run/'network-extra.json').write_text(json.dumps(result,indent=2),encoding='utf-8');assert result['completed'];print('PASS',len(checks),'additional comparisons')
