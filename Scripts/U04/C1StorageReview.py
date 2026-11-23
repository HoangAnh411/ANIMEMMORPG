"""Verify gzip consumers and calculate the baseline storage gate."""
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from C1ProfileEvidence import inspect, open_csv
from C1ProfileValidate import validate
from C1Run import ROOT, read, write


def main(out):
    parent = ROOT.parent
    control = parent/'CC-B-Foreground-Control-20261123-091739'
    ledger = read(control/'method-ledger.json')
    complete = read(out/'roundtrip-complete.json')
    assert len(ledger)==8 and len(complete['runs'])==5
    overhead = read(control/'overhead.json')
    assert len(overhead)==3
    runs = []
    for row in ledger:
        run = Path(row['raw'])
        assert run.is_absolute() and run.name==row['id'] and validate(run)['status']=='PASS'
        if row['mode']=='off':
            continue
        folder = out/row['id']
        data = read(folder/'storage.json')
        evidence = inspect(run, folder, row['mode'])
        if row['mode']=='memory':
            assert evidence==row['export'], 'gzip memory summary differs from validated pilot'
            for key in ('count','bytes'):
                assert evidence['allocations'][key]-evidence['frees'][key]==evidence['outstandingDelta'][key]
        else:
            assert evidence==row['export'], 'gzip timing summary differs from validated run'
            tracks = {}
            with open_csv(folder/'gpu-U04C1_WINDOW.csv') as stream:
                for item in csv.DictReader(stream):
                    if item['TimerName']=='Frame' and float(item['Duration'])>0:
                        key=item['ThreadName']
                        per_track=tracks.setdefault(key,dict(count=0,totalClippedSeconds=0))
                        start,end=evidence['region']
                        clipped=max(0,min(end,float(item['EndTime']))-max(start,float(item['StartTime'])))
                        if clipped:
                            per_track['count']+=1
                            per_track['totalClippedSeconds']+=clipped
            assert tracks
            evidence['gpuFrameTracks']=tracks
        raw_csv=sum(f['rawBytes'] for f in data['files'])
        gz_csv=sum(f['gzipBytes'] for f in data['files'])
        retained=data['originalRetainedBytes']-raw_csv+gz_csv
        cache=run/'capture.ucache'
        runs.append(dict(id=row['id'],mode=row['mode'],retainedBytes=retained,
                         rawCSVBytes=raw_csv,gzipCSVBytes=gz_csv,traceBytes=data['traceBytes'],
                         nonCSVBytes=data['originalRetainedBytes']-raw_csv,
                         analysisCacheBytes=cache.stat().st_size if cache.exists() else 0,
                         evidence=evidence,files=data['files']))
        print(row['id'],'gzip consumer PASS',flush=True)
    timing=max(r['retainedBytes'] for r in runs if r['mode']=='timing')
    memory=next(r['retainedBytes'] for r in runs if r['mode']=='memory')
    permanent=36*timing+12*memory
    # Permanent includes one cache per run. Reserve another observed cache copy
    # while a single synchronous export and its gzip archive coexist.
    memory_temporary=max(r['rawCSVBytes']+r['analysisCacheBytes'] for r in runs)
    reserve=(permanent+memory_temporary+3)//4
    required=permanent+memory_temporary+reserve
    free=shutil.disk_usage(parent/'Runs').free
    result=dict(status='READY_FOR_BASELINE_REVIEW' if required<=free else 'BLOCKED',
                method='ACCEPTED workload and overhead; P1/P2 PASS',
                timingPerRunBytes=timing,memoryPerRunBytes=memory,
                timingRetainedBytes=36*timing,memoryRetainedBytes=12*memory,permanentBytes=permanent,
                extraTemporaryPeakBytes=memory_temporary,reserveBytes=reserve,
                reserveBasis='ceil(25% of permanent + extra temporary peak)',requiredBytes=required,
                freeBytes=free,shortfallBytes=max(0,required-free),marginBytes=free-required,
                measuredUTC=datetime.now(timezone.utc).isoformat(),
                guard='Before each launch/export require free >= remaining retained + peak staging + reserve. Reserve single export at a time. Pause before the next launch if measured sizes exceed the per-run forecast and recompute with observed maxima.',
                storagePolicy='gzip only receipt CSVs from new exports. Keep native raw, .utrace, log, receipts, cache and other evidence as-is. Count plain CSV and gzip concurrently; stream gzip at postcheck. An external plain-only reader needs staging of up to one uncompressed export.',
                limit='10x3/in only; 40x3 extrapolation; no historic deletion or relocation.',
                evidenceLevels=dict(counterReset='Observed run-relative state and counters across process boundaries; reset mechanism source checked',
                                    reopen='Source only',twoWorldIsolation='Source only',counterAggregate='Count and values cross-checked; no per-event attribution for occlusion/suppression'),
                baseline=dict(timing='0/36',memory='0/12'),runs=runs,overhead=overhead)
    write(out/'review.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('runs','overhead')},indent=2),flush=True)


if __name__=='__main__':
    main(Path(sys.argv[1]).resolve())
