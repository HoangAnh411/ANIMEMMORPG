"""Give the old client a real X cooldown before disconnect; no defensive intent fixture."""
import argparse,json,time
from pathlib import Path
from B2NetworkClient import B2NetworkClient
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);a=p.parse_args()
records=json.loads((a.session/'processes.json').read_text(encoding='utf-8-sig'));c=B2NetworkClient(next(r for r in records if r['role']=='ClientA'))
def command(mode):
 (a.session/'command.txt').write_text(str(time.time_ns())+' '+mode,encoding='utf-8');time.sleep(.3)
def until(f):
 end=time.perf_counter()+5
 while not f():
  if time.perf_counter()>end:raise RuntimeError('Reconnect setup timeout')
  time.sleep(.01)
try:
 c.prepare();command('b2-off')
 # Catch up real controller edges after the deliberately ahead-sequence negative probes.
 for _ in range(3):c.press('Shift',True);time.sleep(.035);c.press('Shift',False);time.sleep(.12)
 command('hit');time.sleep(.4);command('b2-grab');until(lambda:c.metrics()['combat']['hardCC']==4)
 c.press('X',True);time.sleep(.035);c.press('X',False);until(lambda:c.metrics()['combat']['xReady']>c.metrics()['combat']['serverSnapshotSeconds']+28);command('b2-off')
 v=c.metrics();assert v['combat']['xReady']>0
 (a.session/'reconnect-before.json').write_text(json.dumps({'process':c.record,'metrics':v,'method':'Physical X on labelled authority grab before disconnect'},indent=2),encoding='utf-8')
finally:
 if c.ime and c.metrics()['controlState']==0:c.press('Escape',True);time.sleep(.035);c.press('Escape',False);time.sleep(.2)
 c.finish()
