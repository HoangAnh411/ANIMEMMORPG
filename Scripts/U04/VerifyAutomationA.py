"""Compare exact expected, discovered and freshly executed test names."""
import argparse,json,re,collections
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args()
def read(n):return json.loads((a.run/n).read_text(encoding='utf-8-sig'))
def unwrap(v):
 if isinstance(v,str):
  try:return unwrap(json.loads(v))
  except (ValueError,TypeError):return v
 if isinstance(v,list):return [unwrap(x) for x in v]
 if isinstance(v,dict):return {k:unwrap(x) for k,x in v.items()}
 return v
def find(v,key):
 if isinstance(v,dict):
  if key in v:yield v[key]
  for x in v.values():yield from find(x,key)
 elif isinstance(v,list):
  for x in v:yield from find(x,key)
expected=read('expected-tests.json');groups=list(find(unwrap(read('discovered-tests.json')),'tests'));assert len(groups)==1,groups
discovered=groups[0];assert all(isinstance(x,str) for x in discovered),discovered[:2]
text=(a.run/'Editor.log').read_text(encoding='utf-8-sig')
matches=re.findall(r'Test Completed\. Result=\{([^}]+)\} Name=\{[^}]+\} Path=\{(AnimeMMORPG\.[^}]+)\}',text)
executed=[n for result,n in matches];counts=collections.Counter(executed)
out=dict(completed=False,expected=expected,discovered=discovered,results=[dict(name=n,result=result) for result,n in matches],missingDiscovery=sorted(set(expected)-set(discovered)),extraDiscovery=sorted(set(discovered)-set(expected)),missingExecution=sorted(set(expected)-set(executed)),extraExecution=sorted(set(executed)-set(expected)),duplicates=[n for n,v in counts.items() if v!=1],format='Raw Editor log and MCP JSON; actual controller schema exposes no XML export')
out['completed']=bool(expected) and set(expected)==set(discovered)==set(executed) and len(matches)==len(expected) and all(r=='Success' for r,n in matches) and 'Automation Test Queue Empty' in text
f=a.run/'NAME-RESULTS.json';assert not f.exists();f.write_text(json.dumps(out,indent=2),encoding='utf-8');assert out['completed'],str(f)
print('PASS exact expected/discovered/executed names:',len(expected))
