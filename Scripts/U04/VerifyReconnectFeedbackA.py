"""Check retained replicated history did not become old feedback in a reconnected process."""
import argparse,json,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);a=p.parse_args();m=json.loads((a.capture/'network.json').read_text(encoding='utf-8'));assert m['completed']
old=next(s['metrics'] for s in m['stages'] if s['stage']=='BeforeDisconnect');new=next(s['metrics'] for s in m['stages'] if s['stage']=='AfterReconnect')
r=next(v for v in m['reconnectProcesses'] if v['role']=='ClientA');text=Path(r['log']).read_text(encoding='utf-8-sig');states=[]
for line in text.splitlines():
 if 'U02F_STATE {' in line:states.append(json.loads(line.split('U02F_STATE ',1)[1]))
old_id=old['encounter']['id'];retained=[v for s in states for v in s['results'] if v.get('encounter')==old_id]
feedback=[line for line in text.splitlines() if 'U03D_FEEDBACK ' in line]
stale=[line for line in feedback if 'encounter='+old_id+' ' in line]
assert states and retained, 'Must observe old replicated history, not merely an empty log'
assert not stale, 'Old encounter feedback replayed after reconnect'
out=dict(completed=True,sourceSHA=r['sourceSHA'],oldEncounter=old_id,newEncounter=new['encounter']['id'],retainedOldResults=len({v['serial'] for v in retained}),newProcessPID=r['pid'],oldEncounterFeedback=stale,newProcessFeedback=feedback,method='Fresh reconnect process sees historical replicated results but never requests feedback/audio for the old encounter')
f=a.capture/'reconnect-feedback.json';assert not f.exists();f.write_text(json.dumps(out,indent=2),encoding='utf-8');print('PASS reconnect feedback watermark with retained historical results')
