import json,datetime,re
from pathlib import Path
p=Path('Artifacts/U02/C/Play-61be83b');m=json.loads((p/'Capture/input.json').read_text());t=datetime.datetime.fromisoformat(m['utc'])
raw=(p/'Game.log').read_bytes();samples=[json.loads(l.split('Metrics ',1)[1]) for l in raw[:raw.rfind(b'\n')+1].decode('utf-8-sig').splitlines() if 'Metrics {' in l]
samples=[v for v in samples if 0<(datetime.datetime.fromisoformat(v['utc'].replace('Z','+00:00'))-t).total_seconds()<m['captureSeconds']]
result=json.loads((p/'Capture/ASSERTIONS.json').read_text());checks=[]
def check(name,v):checks.append(dict(check=name,result='PASS' if v else 'FAIL'))
check('Actual C graph loaded',all('/ABP_U02.' in s['animClass'] for s in samples))
for seq in range(1,8):
 a=[s for s in samples if s['combat']['action']==seq and s.get('attackPresented')]
 check('Action '+str(seq)+' presents montage',len(a)>3)
 check('Action '+str(seq)+' returns from montage',any(s['combat']['action']==seq and s['combat']['phase']==4 and not s.get('attackPresented') for s in samples))
 if a:
  points=[list(map(float,re.findall(r'=([-\d.]+)',s['rightHandComponentCm']))) for s in a]
  check('Action '+str(seq)+' actual right hand moves',max(v[2] for v in points)-min(v[2] for v in points)>10)
check('Render root motion ignore',all(s['rootMotionMode']==1 for s in samples))
assert all(c['result']=='PASS' for c in checks),checks
result['checks']+=checks;result['passed']+=len(checks);(p/'Capture/ASSERTIONS.json').write_text(json.dumps(result,indent=2));print('Presentation checks',len(checks),'total',result['passed'])
