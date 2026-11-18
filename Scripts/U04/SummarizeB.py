"""Aggregate all recorded attempts without discarding cadence failures or gameplay failures."""
import argparse,csv,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--runs',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
a.out.mkdir(exist_ok=False,parents=True);rows=[]
for f in sorted(a.runs.glob('FPS*/Capture/*/ASSERTIONS.json')):
    r=json.loads(f.read_text(encoding='utf-8'));g=r.get('gameplay',{});c=r.get('cadence',{})
    rows.append(dict(trial=r['trial'],targetFPS=r['target'],case=r['case'],status=r['status'],
                     measuredFPS=c.get('fps'),within10Percent=c.get('within10Percent'),p50=c.get('p50'),p95=c.get('p95'),p99=c.get('p99'),max=c.get('max'),
                     distanceCm=g.get('forwardCm',g.get('distanceCm')),errorCm=g.get('errorCm'),pathCm=g.get('pathCm'),lateralCm=g.get('lateralCm'),
                     wallDuration=g.get('wallDuration'),worldDuration=g.get('worldDuration'),comboSeconds=g.get('authorityDuration'),
                     damage=g.get('hpBefore',0)-g.get('hpAfter',0) if r['case']=='combo' else None,
                     reasons=json.dumps(dict(invalid=r.get('reason'),cadence=c.get('reasons'),gameplay=g.get('reasons')),sort_keys=True),
                     assertionPath=str(f.resolve()),assertionSHA256=hashlib.sha256(f.read_bytes()).hexdigest(),rawSHA256=r['rawSHA256']))
required={case:(5 if case=='combo' else 3) for case in ['walk','sprint','forward','back','left','right','combo']}
gates=[]
for fps in [30,60,120]:
    for case,need in required.items():
        selected=[r for r in rows if r['targetFPS']==fps and r['case']==case];passed=sum(r['status']=='PASS' for r in selected)
        gates.append(dict(targetFPS=fps,case=case,required=need,passed=passed,attempts=len(selected),status='PASS' if passed>=need else 'MISSING_EVIDENCE'))
result=dict(status='FPS_MATRIX_COMPLETE' if all(g['status']=='PASS' for g in gates) else 'INCOMPLETE',gates=gates,trials=rows,
            note='All attempts retained. FPS matrix completeness alone does not establish READY_FOR_REVIEW; regressions, identities and integrity also required.')
(a.out/'RESULTS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
if rows:
    with (a.out/'TRIALS.csv').open('w',newline='',encoding='utf-8') as out:
        writer=csv.DictWriter(out,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
print(result['status'],len(rows),'attempts')
