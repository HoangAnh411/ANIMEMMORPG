"""Recompute fixed R1a inventory from local raw or published gzip-equivalent raw.

Example: python Scripts/U04/RecomputeR1a.py --published Docs/U04/R1a/Evidence/Review-20261119 --out <new-directory>
Repro gameplay verdict and whole-trace cadence verdict are deliberately separate.
This program cannot emit an acceptance verdict for B/R1b.
"""
import argparse,csv,gzip,hashlib,json,math
from pathlib import Path
from AnalyzeR1a import load,repro,idle,vector

def main():
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--runs',type=Path);g.add_argument('--published',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    base=a.runs or a.published/'Runs';a.out.mkdir(parents=True,exist_ok=False)
    def content(rel):
        f=base/rel
        return f.read_bytes() if f.exists() else gzip.decompress(f.with_name(f.name+'.gz').read_bytes())
    def obj(rel):return json.loads(content(rel).decode('utf-8-sig'))
    def raw(rel):return [json.loads(l) for l in content(rel).decode('utf-8-sig').splitlines()]
    def stored_core(fresh,stored):
        for key,value in fresh.items():assert stored[key]==value,('stored/recomputed mismatch',key)
    def write(name,value):
        (a.out/name).write_text(json.dumps(value,indent=2),encoding='utf-8')
    def table(name,rows):
        with (a.out/name).open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    build=obj('Build-R5-20261119/BUILD-IDENTITY.json');repros=[];controls=[];repro_csv=[];idle_csv=[];warnings=[]
    for fps in (30,60,120):
        session=f'Repro-fps{fps}-20261119';record=obj(session+'/process.json');ledger=obj(session+'/R1a-numeric/LEDGER.json')
        assert record['sourceSHA']==build['sourceSHA'] and record['binarySHA256'].lower()==build['gameSHA256'].lower() and record['targetFPS']==fps
        if not ledger['completed']:warnings.append(dict(session=session,captureError=ledger['error'],resolution='closed original idle-1 raw analyzed without recapture; only unstarted controls2/3 resumed',originalLedgerUnchanged=True))
        for case in ('w-shift','shift-w','w-up-shift','previous'):
            items=[t for t in ledger['trials'] if t.get('case')==case];assert len(items)<=4
            filenames=list((base/session/'Raw').glob(f'fps{fps}-{case}-*.jsonl*'))
            assert len(filenames)==len(items),'unlisted/missing attempt'
            assert sum(t['status']=='PASS' for t in items)==2 and not any(t['status']=='FAIL' for t in items)
            for item in items:
                trial=item['trial'];rel=session+'/Raw/'+trial+'.jsonl';rows=raw(rel);result=repro(rows,case,fps)
                assert hashlib.sha256(content(rel)).hexdigest()==item['rawSHA256']
                stored_core(result,obj(session+'/R1a-numeric/'+trial+'/ASSERTIONS.json'))
                assert all(r['source']==build['sourceSHA'] and r['pid']==record['pid'] for r in rows if r['kind']=='frame')
                result.update(trial=trial,raw=rel,rawSHA256=hashlib.sha256(content(rel)).hexdigest(),process=record)
                repros.append(result);end=result['trajectoryEnd'];origin=vector(end['combat']['dodgeOrigin']);dx=end['position'][0]-origin[0];dy=end['position'][1]-origin[1]
                received_origin=vector(result['received']['receivedPosition']);receipt_dx=end['position'][0]-received_origin[0];receipt_dy=end['position'][1]-received_origin[1]
                w=next(k for k in result['intent']['keys'] if k['bindingAction']==0)
                repro_csv.append(dict(trial=trial,targetFPS=fps,reproGameplayStatus=result['status'],acceptance=False,
                    wholeTraceCadenceStatus='PASS' if result['primary'].get('pass_') else 'INVALID',
                    sameFrame=result['sameFrame'],previousHeldFrames=len(result['previousHeldFrames']),admissionSpeedCmS=result['admissionSpeedCmS'],
                    observedW=w['observedPhysical'],engineHeldW=w['engineHeld'],gateAllowsW=w['gateAllows'],
                    sentX=result['intent']['sentX'],sentY=result['intent']['sentY'],receivedX=result['received']['intentX'],receivedY=result['received']['intentY'],
                    modelDirection=result['admission']['modelDirection'],modelOriginDxCm=dx,modelOriginDyCm=dy,modelOriginDistanceCm=math.hypot(dx,dy),
                    receiptDxCm=receipt_dx,receiptDyCm=receipt_dy,receiptDistanceCm=math.hypot(receipt_dx,receipt_dy),
                    trajectorySeconds=end['combat']['dodgeMotionEnd']-end['combat']['dodgeStart'],releaseGateSeconds=end['combat']['dodgeLockEnd']-end['combat']['dodgeStart'],
                    wholeTraceFPS=result['primary'].get('fps'),wholeTraceInBand=result['primary'].get('within10Percent'),wholeTraceMax=result['primary'].get('max'),
                    nativeSource=build['sourceSHA'],pid=record['pid'],rawSHA256=result['rawSHA256']))
        for index in range(1,4):
            trial=f'fps{fps}-idle-{index}';rel=session+'/Raw/'+trial+'.jsonl';result=idle(raw(rel),fps)
            folder='R1a-numeric-resume-idle2' if fps==120 and index>=2 else 'R1a-numeric'
            name='POSTFLUSH-RECOVERY.json' if fps==120 and index==1 else 'ASSERTIONS.json'
            stored_core(result,obj(session+'/'+folder+'/'+trial+'/'+name))
            result.update(trial=trial,raw=rel,rawSHA256=hashlib.sha256(content(rel)).hexdigest(),process=record)
            controls.append(result);c=result['primary'];cost=result['collectorCostSeconds']
            idle_csv.append(dict(trial=trial,targetFPS=fps,purpose='METHOD_ONLY',acceptance=False,status=result['status'],primaryClock='sampleEntryWall',
                worldStart=result['startBoundary']['time'],worldEnd=result['endBoundary']['time'],worldSeconds=15,wallSeconds=result['wallDuration'],
                firstFrame=result['startBoundary']['left']['frame'],lastFrame=result['endBoundary']['right']['frame'],intervals=c['intervals'],fps=c['fps'],inBand=c['within10Percent'],
                p50=c['p50'],p95=c['p95'],p99=c['p99'],maximum=c['max'],collectorP50=cost['p50'],collectorP95=cost['p95'],collectorP99=cost['p99'],collectorMax=cost['max'],
                nativeSource=build['sourceSHA'],pid=record['pid'],rawSHA256=result['rawSHA256']))
    assert len(repros)==24 and all(r['status']=='PASS' for r in repros)
    assert len(controls)==9 and all(r['status']=='PASS' for r in controls)
    summary=dict(status='R1A_REVIEW_PENDING',BStatus='INCOMPLETE',acceptance=False,R1bStarted=False,build=build,
        reproGameplayPassed=24,reproCadencePassed=sum(r['primary'].get('pass_',False) for r in repros),reproCadenceInvalid=sum(not r['primary'].get('pass_',False) for r in repros),
        idleMethodPassed=9,clock='sampleEntryWall',warnings=warnings,
        scope='Repros certify edge/snapshot behavior only. Whole-trace cadence failures remain visible; none of these runs certify the acceptance matrix. Idle controls certify collector method only.',
        analyzerSHA256=hashlib.sha256(Path(__file__).with_name('AnalyzeR1a.py').read_bytes()).hexdigest(),
        cadenceAnalyzerSHA256=hashlib.sha256(Path(__file__).with_name('AnalyzeR1.py').read_bytes()).hexdigest(),
        recomputeSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    write('SUMMARY.json',summary);write('REPRO-RESULTS.json',repros);write('IDLE-RESULTS.json',controls)
    table('REPRO-RESULTS.csv',repro_csv);table('IDLE-RESULTS.csv',idle_csv)
    print('PASS recomputed24 repro gameplay +9 idle method windows; repro whole-trace cadence',summary['reproCadencePassed'],'PASS /',summary['reproCadenceInvalid'],'INVALID; B INCOMPLETE')

if __name__=='__main__':main()
