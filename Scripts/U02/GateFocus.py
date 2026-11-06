import argparse,json,statistics
from pathlib import Path
from datetime import datetime
p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);a=p.parse_args();b=json.loads((a.before/'FocusBaseline/analysis.json').read_text());f=json.loads((a.after/'FocusAfter/analysis.json').read_text());checks=[]
def ck(n,v):checks.append(dict(check=n,result='PASS' if v else 'FAIL'))
def ep(s):return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
records=json.loads((a.after/'processes.json').read_text(encoding='utf-8-sig'));frames={r['role']:[json.loads(l) for l in Path(next(x.split('=',1)[1].strip(chr(34)) for x in r['arguments'] if x.startswith('-U01FPerfFile='))).read_text().splitlines()] for r in records}
ck('Baseline and final each10 complete transfers',b['completed'] and f['completed'] and len(b['trials'])==len(f['trials'])==10)
summary=[];rolling=[]
for band in ['0:0.5','0.5:2','2:5','5:15']:
 for role in ['ClientA','ClientB','Server']:
  q=dict(band=band,role=role)
  for label,m in [('before',b),('after',f)]:q[label]=dict(worstP95=max(t['bins'][band]['allRoles'][role]['wallMs']['p95'] for t in m['trials']),max=max(t['bins'][band]['allRoles'][role]['wallMs']['max'] for t in m['trials']))
  summary.append(q)
  if band!='0:0.5':ck(role+' no sustained drop '+band,q['after']['worstP95']<(40 if role=='Server' else 25))
for t in f['trials']:
 start=ep(t['focusUTC'])
 ck(str(t['index'])+' native frame files cover full15s',all(ep(frames[r][-1]['utc'])>=start+15 for r in frames))
 for role in ['ClientA','ClientB']:
  v=[ep(q['utc'])-start for q in frames[role] if start-1<=ep(q['utc'])<=start+15];counts=[sum(s<=x<s+1 for x in v) for s in [i*.25 for i in range(57)]];rolling.append(dict(index=t['index'],role=role,minOneSecondFrames=min(counts)));ck(str(t['index'])+' '+role+' every rolling1s >=50 frames',min(counts)>=50)
latencies={}
for name in ['keyToOwnedTransformMs','keyToServerTransformMs','keyToPeerTransformMs']:
 def st(m):
  v=sorted(t[name] for t in m['trials']);return dict(median=statistics.median(v),p95=v[int((len(v)-1)*.95)],max=max(v))
 latencies[name]=dict(before=st(b),after=st(f));ck(name+' p95 not worse than baseline plus one sample quantum',latencies[name]['after']['p95']<=latencies[name]['before']['p95']+1)
window=json.loads((a.after/'FocusAfter/windows.json').read_text());ck('Both original Editor HWNDs actually minimized throughout',len(window)>100 and all(len(w['editors'])==2 and all(e['iconic'] for e in w['editors']) for w in window));inp=json.loads((a.after/'FocusAfter/INPUT-ASSERTIONS.json').read_text());ck('Resume/release/repress71 input checks pass',inp['failed']==0);res=dict(passed=sum(x['result']=='PASS' for x in checks),failed=sum(x['result']=='FAIL' for x in checks),criteria='No multi-second degradation: both clients p95<25ms in .5-2/2-5/5-15 bands and every rolling1s >=50 frames; server p95<40ms; latency p95 no worse beyond1ms UTC quantization. These are diagnostic regression gates, not product performance acceptance.',checks=checks,bins=summary,latencies=latencies,rolling=rolling);(a.after/'FocusAfter/GATE.json').write_text(json.dumps(res,indent=2));print(json.dumps(dict(passed=res['passed'],failed=res['failed'],latencies=latencies)));print('\n'.join(c['check'] for c in checks if c['result']=='FAIL'));assert not res['failed']
