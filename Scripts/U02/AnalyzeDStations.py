import argparse,json,re
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);a=p.parse_args()
m=json.loads((a.capture/'input.json').read_text());assert m['completed'],'Incomplete capture retained; no runtime PASS';start=datetime.fromisoformat(m['utc']);record=m['process'];raw=Path(record['log']).read_bytes();lines=raw[:raw.rfind(b'\n')+1].decode('utf-8-sig',errors='replace').splitlines()
checks=list(m['checks']);samples=[];hits=[];queries=[]
def relative(v):return (datetime.fromisoformat(v['utc'].replace('Z','+00:00'))-start).total_seconds()
for line in lines:
 if 'Metrics {' in line:
  v=json.loads(line.split('Metrics ',1)[1]);t=relative(v)
  if 0<=t<=m['captureSeconds']:samples.append(v)
 stamp=re.search(r'^\[(\d{4}\.\d\d\.\d\d-\d\d\.\d\d\.\d\d:\d{3})\]',line)
 if not stamp:continue
 utc=datetime.strptime(stamp[1],'%Y.%m.%d-%H.%M.%S:%f').replace(tzinfo=timezone.utc);t=(utc-start).total_seconds()
 if not 0<=t<=m['captureSeconds']:continue
 if 'U02D_QUERY' in line:queries.append(line)
 if 'U02D_CONFIRMED' in line:
  x=re.search(r'time=([^ ]+) source=([0-9A-F]+):(\d+) action=(\d+) target=([0-9A-F]+):(\d+) hurtbox=(\d+)',line);assert x,line
  hits.append(dict(timestamp=float(x[1]),source=x[2],life=int(x[3]),action=int(x[4]),target=x[5],targetLife=int(x[6]),hurtbox=int(x[7]),line=line))
def check(name,v):checks.append(dict(check=name,result='PASS' if v else 'FAIL'))
check('Completed guarded input / IME restored',m['completed'] and m['externalInputMethodRestored'])
check('Owned actual Game standalone with exact source/binary identity',bool(samples) and all(v['sourceSHA']==record['sourceSHA'] and v['pid']==record['pid'] and v['worldType']==1 and v['netMode']==0 and v['owner']==v['controller'] and v['localPlayers']==1 for v in samples))
check('Five server geometry results',len(hits)==5)
ids=[(h['source'],h['life'],h['action'],h['target'],h['targetLife']) for h in hits];check('No repeated hit per action/target life across hurtboxes or frames',len(ids)==len(set(ids)))
for name,stage in m['stages'].items():
 b=stage['after']['combat'];group=[h for h in hits if h['life']==b['life'] and h['action']==b['action']]
 check(name+' actual confirmed log matches diagnostic count',len(group)==stage['expected'])
 check(name+' timestamps strictly within active window',all(b['activeStart']<=h['timestamp']<b['activeEnd'] for h in group))
 if name=='PartialWallHead':check('Partial obstruction resolves the visible head hurtbox',len(group)==1 and group[0]['hurtbox']==2)
check('Actual query trace records blocked and visible hurtboxes',any('visible=0' in q for q in queries) and any('visible=1' in q for q in queries))
check('No unsupported obstruction shapes in reviewed maps',all(v['combat']['geometryUnsupportedShapes']==0 for v in samples))
check('No damage implementation claimed',all('damage=NOT_IMPLEMENTED' in h['line'] for h in hits))
check('Root motion stays ignored',all(v['rootMotionMode']==1 for v in samples))
result=dict(sourceSHA=record['sourceSHA'],automation=False,method='postprocessed real Windows input and native server geometry traces',samples=len(samples),confirmed=len(hits),queries=len(queries),passed=sum(c['result']=='PASS' for c in checks),failed=sum(c['result']=='FAIL' for c in checks),checks=checks,hits=hits)
(a.capture/'ASSERTIONS.json').write_text(json.dumps(result,indent=2));(a.capture/'QUERY-TRACE.log').write_text('\n'.join(queries+[h['line'] for h in hits]))
print(json.dumps(dict(passed=result['passed'],failed=result['failed'],confirmed=len(hits),samples=len(samples))));assert result['failed']==0
