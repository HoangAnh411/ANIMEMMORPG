"""Post-stop reporting only; never launches/input/captures or changes frozen tools."""
import argparse,csv,json,math
from pathlib import Path
from R1bContract import frozen,read,write,sha,ROOT,CASES
from AnalyzeR1 import analyze,percentile,vector

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    m=frozen(a.manifest);assert not a.out.exists();a.out.mkdir()
    ledger=read(Path(m['isolationRoot'])/'Runs/BATCH-LEDGER.json');rows=[];costs=[]
    for t in ledger['trials']:
        raw=Path(t['raw']);assert sha(raw)==t['rawSHA256'];saved=read(ROOT/t['assertions'])
        assert sha(ROOT/t['assertions'])==t['assertionsSHA256']
        result=analyze(raw,t['fps'],t['case'])
        assert all(saved.get(k)==v for k,v in result.items() if k!='status'),t['trial']
        assert result['status']==saved['analyzerStatus'],t['trial']
        effective='INVALID' if saved.get('harnessFocusLoss') and result['status']!='FAIL' else result['status']
        assert effective==saved['status']==t['status']
        write(a.out/(t['trial']+'.json'),dict(recomputed=result,effectiveStatus=effective,matchedStored=True))
        g=result.get('gameplay',{});c=result.get('cadence',{});cor=g.get('correlation',{});ad=cor.get('admission',{})
        velocity=vector(ad.get('velocityBeforeBatch',''))
        data=[json.loads(x) for x in raw.read_text(encoding='utf-8-sig').splitlines()];frames=[r for r in data if r['kind']=='frame']
        selected=[r for r in frames if g.get('firstFrame',0)<=r['frame']<=g.get('lastFrame',-1)]
        overhead=[r['collectorExitWall']-r['sampleEntryWall'] for r in selected];costs+=overhead
        rows.append(dict(trial=t['trial'],fps=t['fps'],case=t['case'],attempt=t['attempt'],status=effective,gameplayPass=g.get('pass_'),cadencePass=c.get('pass_',False),meanFPS=c.get('fps'),inBandFraction=c.get('within10Percent'),p50Seconds=c.get('p50'),p95Seconds=c.get('p95'),p99Seconds=c.get('p99'),maxSeconds=c.get('max'),distanceCm=g.get('forwardCm',g.get('distanceCm')),errorCm=g.get('errorCm'),worldSeconds=g.get('worldDuration'),wallSeconds=g.get('wallDuration'),pathCm=g.get('pathCm'),lateralCm=g.get('lateralCm'),authorityDuration=g.get('authorityDuration'),damage=(g.get('hpBefore',0)-g.get('hpAfter',0)) if 'hpBefore' in g else None,admissionHorizontalCmPerSec=math.hypot(*velocity[:2]) if len(velocity)>=2 else None,trajectorySeconds=g.get('authorityMotionEnd',0)-g.get('authorityStart',0) if 'authorityMotionEnd' in g else None,releaseSeconds=g.get('authorityLockEnd',0)-g.get('authorityStart',0) if 'authorityLockEnd' in g else None,collectorP50Seconds=percentile(overhead,.5) if overhead else None,collectorP99Seconds=percentile(overhead,.99) if overhead else None,collectorMaxSeconds=max(overhead) if overhead else None,raw=str(raw),rawSHA256=sha(raw),assertionsSHA256=t['assertionsSHA256']))
    def csvwrite(name,data):
        with (a.out/name).open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    csvwrite('TRIALS.csv',rows)
    matrix=[]
    for fps in m['fpsOrder']:
        for case in CASES:
            ts=[t for t in rows if t['fps']==fps and t['case']==case];passed=sum(t['status']=='PASS' for t in ts);need=m['cases'][case]['required']
            matrix.append(dict(fps=fps,case=case,required=need,limit=m['cases'][case]['limit'],attempts=len(ts),PASS=passed,FAIL=sum(t['status']=='FAIL' for t in ts),INVALID=sum(t['status']=='INVALID' for t in ts),status='PASS' if passed==need else 'INCOMPLETE'))
    csvwrite('MATRIX.csv',matrix)
    result=dict(status='INCOMPLETE',sourceSHA=m['nativeSource'],analyzer=m['analyzerVersion'],analyzerSHA256=m['analyzerSHA256'],recomputedTrials=len(rows),allStoredVerdictsMatched=True,passCount=sum(r['status']=='PASS' for r in rows),requiredPassCount=69,matrix=matrix,halted=ledger['halted'],haltReason=ledger.get('haltReason'),setupErrors=ledger['setupErrors'],illustrations=0,requiredIllustrations=21,collectorCost=dict(samples=len(costs),p50Seconds=percentile(costs,.5),p95Seconds=percentile(costs,.95),p99Seconds=percentile(costs,.99),maxSeconds=max(costs)),readinessInheritedAutomation='144/144 R1a; no rerun',acceptance=False,readyForReviewEntireB=False)
    write(a.out/'GATES.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('matrix','setupErrors')}))

if __name__=='__main__':main()
