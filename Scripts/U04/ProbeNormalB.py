"""Verify the ordinary package session does not activate the B fixture."""
import argparse,json,subprocess,time,re
from pathlib import Path
from RegressionClientB import RegressionClientB
p=argparse.ArgumentParser();p.add_argument('--record',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();assert not a.out.exists()
r=json.loads(a.record.read_text(encoding='utf-8-sig'));c=RegressionClientB(r);result={'completed':False,'process':r}
try:
    cmd=subprocess.check_output(['powershell','-NoProfile','-Command',f'(Get-CimInstance Win32_Process -Filter "ProcessId={c.pid}").CommandLine'],text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    assert '-u04bfpsfixture' not in cmd.lower();result['actualCommandLine']=cmd
    c.focus();before=c.metrics();c.console('U04B prepare');time.sleep(.3);c.console('U04B begin forbidden');time.sleep(.2);c.console('U04B end');after=c.metrics()
    result.update(before=before,after=after)
    assert before['combat']['fixtureCritRoll']==after['combat']['fixtureCritRoll']==-1
    location=[float(x) for x in re.findall(r'[XYZ]=([-0-9.]+)',after['capsuleCenterWorldCm'])]
    assert abs(location[1]-20000)>1000 and before['pawn']==after['pawn']
    assert not list(a.record.parent.rglob('forbidden.jsonl'))
    result.update(completed=True,checks=4,scope='ordinary normal-encounter package; no B command-line flag, crit override, B teleport or B capture')
finally:
    c.finish();a.out.write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS normal launcher fixture-off',a.out)
