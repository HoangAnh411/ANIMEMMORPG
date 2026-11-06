"""Verify already recorded reconnect against initial and post-fixture life, without replaying input."""
import argparse,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);a=p.parse_args();out=a.session/'Disconnect';m=json.loads((out/'ASSERTIONS.json').read_text());shutil.copyfile(out/'ASSERTIONS.json',out/'FAILED-LIFE-ASSUMPTION.json');assert m['noDamageAfterRemoval'];records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));by={r['role']:r for r in records}
def rows(k):
 raw=Path(by[k]['log']).read_bytes();return [json.loads(l.split('U02F_STATE ',1)[1]) for l in raw[:raw.rfind(b'\n')+1].decode('utf-8-sig',errors='replace').splitlines() if 'U02F_STATE {' in l]
allrows={k:rows(k) for k in by};states={k:v[-1] for k,v in allrows.items()};new=next(p['id'] for p in states['ClientA']['pawns'] if p['local']);assert new!=m['oldPawn'];initial=next(p for row in allrows['Server'] for p in row['pawns'] if p['id']==new);assert initial['life']==1 and initial['action']==0 and initial['accepted']==0
life=next(p['life'] for p in states['Server']['pawns'] if p['id']==new);events=states['Server']['results'][-2:];assert life==2 and all(e['source']==new and e['sourceLife']==life and e['action']==1 for e in events)
assert all(v['results']==states['Server']['results'] and len(v['pawns'])==2 for v in states.values())
def core(v):return sorted((t['id'],t['lifeGeneration'],t['hp'],t['shield'],t['dead']) for t in v['targets'])
assert all(core(v)==core(states['Server']) for v in states.values());m.update(completed=True,newPawn=new,initialReconnectSubject=initial,postFixtureLife=life,reconnectedProcesses=records,reconnectStates=states,freshIdentityAndCommand=True,verification='native raw logs: new subject life1/action0 before setup; lab setup increments tolife2; first real input action1 agrees on all processes');m.pop('error',None);(out/'ASSERTIONS.json').write_text(json.dumps(m,indent=2));print('PASS reconnect initial life1, post-fixture life2/action1, distinct pawn/session identity and three-process HP/results agreement')
