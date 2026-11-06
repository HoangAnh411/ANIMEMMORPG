import argparse,json,re,hashlib,cv2
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);a=p.parse_args();cap=a.session/'Capture';m=json.loads((cap/'input.json').read_text());assert m['completed'] and m['externalInputMethodRestored']
raw=(a.session/'Game.log').read_bytes();lines=raw[:raw.rfind(b'\n')+1].decode('utf-8-sig',errors='replace').splitlines();selected=[l for l in lines if 'U02D_SELECTED action=' in l];confirmed=[l for l in lines if 'U02D_CONFIRMED ' in l];checks=list(m['checks'])
def check(name,ok):checks.append(dict(check=name,result='PASS' if ok else 'FAIL'))
for stage in m['stages']:
 b=stage['after']['combat'];needle=f":{b['life']}:{b['action']} "
 rows=[l for l in selected if needle in l];hits=[l for l in confirmed if f":{b['life']} action={b['action']} " in l]
 check(stage['label']+' isolated selected action rows exist',bool(rows))
 check(stage['label']+' exact action confirmation count',len(hits)==stage['expectedHits'])
 if stage['label']=='Action66Open':
  check('Reconstruction body and head independently valid',all(any(f'hurtbox={h} ' in l and 'result=VALID' in l for l in rows) for h in (1,2)))
  check('Reconstruction confirms body once',len(hits)==1 and 'hurtbox=1 ' in hits[0])
 if stage['label']=='AllBlocked':check('Both hurtboxes blocked, actual wall marker recorded',all(any(f'hurtbox={h} ' in l and 'result=BLOCKED' in l and 'wall=/Game/' in l for l in rows) for h in (1,2)))
 if stage['label']=='PartialHead':check('Partial body blocked, head valid and confirmed',any('hurtbox=1 ' in l and 'result=BLOCKED' in l for l in rows) and any('hurtbox=2 ' in l and 'result=VALID' in l for l in rows) and len(hits)==1 and 'hurtbox=2 ' in hits[0])
 if stage['label']=='Outside':check('Outside selected action hurtboxes reported',all('result=OUTSIDE' in l for l in rows))
v=cv2.VideoCapture(str(cap/'Corner.mp4'));duration=v.get(cv2.CAP_PROP_FRAME_COUNT)/v.get(cv2.CAP_PROP_FPS);v.release();check('Encoded duration matches wall timestamp',abs(duration-m['captureSeconds'])<1/30+.01)
result=dict(sourceSHA=m['process']['sourceSHA'],passed=sum(x['result']=='PASS' for x in checks),failed=sum(x['result']=='FAIL' for x in checks),checks=checks,scope='real Windows input selected-action diagnostics and native confirmed geometry; no damage or screenshot-action identification',videoSeconds=duration,wallSeconds=m['captureSeconds'],capturedFrames=len(m['frames']))
(cap/'ASSERTIONS.json').write_text(json.dumps(result,indent=2));(cap/'SELECTED.log').write_text('\n'.join(selected+confirmed));print(json.dumps(result,indent=2));assert result['failed']==0
