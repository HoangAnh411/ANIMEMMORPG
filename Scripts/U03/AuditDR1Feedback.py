"""Independent checks of recorded R1 presentation decisions and real network logs."""
import argparse,json,re,wave
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--visibility',type=Path,required=True);p.add_argument('--session',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
m=read(a.visibility/'visibility.json');assert m['completed'] and len(m['checks'])==20 and all(r['result']=='PASS' for r in m['checks'])
checks=[]
def check(name,ok):checks.append(dict(name=name,result='PASS' if ok else 'FAIL'));assert ok,name
for role in ['ClientA','ClientB']:
 stages={s['name']:s for s in m['stages'] if 'metrics' in s}
 hidden=stages[role+'-hidden-event']['metrics'];subject=hidden['encounter']['monsterCombat']['pawnId']
 h=next(e for e in hidden['presentation']['events'] if e['subject']==subject and e['kind']==0);serial=h['serial']
 check(role+' hidden contact is neither visible nor audible',not h['visible'] and not h['audio'])
 reveal=stages[role+'-reveal-remainder']['metrics'];v=next(e for e in reveal['presentation']['events'] if e['serial']==serial)
 check(role+' same identity and timestamp gets only remaining visual time',v['at']==h['at'] and v['visible'] and 0<v['remaining']<h['remaining'] and not v['new'] and not v['audio'])
 for suffix in ['expired','expired-hidden','expired-reveal']:
  s=stages[role+'-'+suffix]['metrics'];check(role+' '+suffix+' same revision has no old feedback',s['encounter']['revision']==hidden['encounter']['revision'] and not any(e['serial']==serial for e in s['presentation']['events']))
 partial=stages[role+'-partial-depth']['metrics'];r=next(r for r in partial['presentation']['actors'] if r['subject']==partial['encounter']['monsterCombat']['pawnId'])
 check(role+' anchor is visible while world geometry is partly occluded',r['visible'] and r['subjectClear'] and r['worldDepthSegments']==15 and r['clearSegmentMidpoints']>0 and r['blockedSegmentMidpoints']>0 and partial['presentation']['canvasTelegraphSegments']==0)
 check(role+' old serial stays absent across Retry',partial['encounter']['revision']>hidden['encounter']['revision'] and not any(e['serial']==serial for e in partial['presentation']['events']))
pat=re.compile(r'U03D_FEEDBACK serial=(\d+) kind=(\d+) subject=(\w+) life=(\d+) action=(\d+) encounter=(\w+) revision=(\d+) at=([\d.]+) now=([\d.]+) audio=(\d+)')
records=read(a.session/('all-processes.json' if (a.session/'all-processes.json').exists() else 'processes.json'));rows=[]
for process in records:
 seen=set();audible=0
 with Path(process['log']).open(encoding='utf-8-sig') as f:
  for line in f:
   match=pat.search(line)
   if not match:continue
   serial,kind,subject,life,action,encounter,revision,at,now,sound=match.groups();identity=(serial,subject,life,action,encounter,revision)
   assert identity not in seen,(process['pid'],identity);seen.add(identity)
   if sound=='1':assert -1.e-6<=float(now)-float(at)<=.150001;audible+=1
 if process['role']=='Server':check('Dedicated server emits no HUD/audio feedback',not seen)
 rows.append(dict(role=process['role'],pid=process['pid'],events=len(seen),audible=audible,duplicateIdentities=0))
with wave.open(str(a.visibility/'Output-Loopback.wav')) as w:x=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2).mean(axis=1)/32768;rate=w.getframerate()
bands={str(hz):[] for hz in [330,440]}
for i in range(0,len(x)-4096,512):
 spectrum=np.abs(np.fft.rfft(x[i:i+4096]*np.hanning(4096)));k=int(np.argmax(spectrum));hz=k*rate/4096
 for h in bands:
  if abs(hz-int(h))<20 and spectrum[k]>1:bands[h].append(i/rate)
check('Real output loopback contains new visible hit/Interrupt signals',all(bands.values()))
result=dict(completed=True,checks=checks,processes=rows,loopbackFrequencyWindows=bands,loopbackWarnings=m['warnings'],limits=['Loopback discontinuity warnings retained; no sample-exact audio timing claim','Midpoint visibility samples are diagnostics, not proof of pixel clipping; normal world depth proxy and actual GPU captures supply that evidence','No arbitrary packet injection claim; duplicate/late/life behavior also covered by native tests'])
(a.out/'feedback-r1-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('PASS',len(checks),'R1 checks;',len(rows),'network processes')
