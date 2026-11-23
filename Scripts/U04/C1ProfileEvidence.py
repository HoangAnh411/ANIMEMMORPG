"""Check real Insights exports; a successful CLI exit alone is insufficient."""
import csv
import gzip
import re
from pathlib import Path

from C1Run import read

COUNTERS = dict(HurtboxVisits='hurtboxVisits', GeometryTests='geometryTests',
                OcclusionCalls='occlusionCalls', Candidates='candidates',
                ConfirmedHits='confirmedHits', DuplicateSuppression='duplicateSuppression', Actions='actions')
SCOPES = ('WorldUpdate', 'CollectCandidates', 'Geometry', 'Occlusion',
          'ResolveDedup', 'ApplyDamage', 'DedupFilter')


def open_csv(path):
    """Read an exported CSV or its lossless gzip archive without materializing it."""
    if path.is_file():
        return path.open(encoding='utf-8-sig', newline='')
    return gzip.open(path.with_suffix(path.suffix + '.gz'), 'rt', encoding='utf-8-sig', newline='')


def table(path):
    with open_csv(path) as stream:
        data = list(csv.DictReader(stream))
    if not data:
        raise ValueError('empty export: ' + path.name)
    return data


def inspect(run, out, mode):
    log = (out/'Insights.log').read_text(encoding='utf-8-sig', errors='replace')
    summary = read(run/'Raw/summary.json')
    duration = summary['endWall'] - summary['startWall']
    if mode == 'timing':
        regions = set(re.findall(r"for region 'U04C1_WINDOW' \[([0-9.]+) \.\. ([0-9.]+)\]", log))
        if len(regions) != 1 or not re.search(r'Detected 1 regions?', log):
            raise ValueError('missing unique U04C1_WINDOW')
        start, end = map(float, next(iter(regions)))
        if abs(end-start-duration) > .02:
            raise ValueError('trace region and native window disagree')
        gpu = table(out/'gpu-U04C1_WINDOW.csv')
        frames = table(out/'frames-U04C1_WINDOW.csv')
        cpu = table(out/'events.csv')
        def positive(rows):
            return [r for r in rows if min(float(r['EndTime']),end) > max(float(r['StartTime']),start)]
        gpu, frames, cpu = map(positive, (gpu, frames, cpu))
        if not gpu or not frames or not cpu or not any(r['ThreadName'].startswith('GPU') for r in gpu):
            raise ValueError('missing positive duration frame/CPU/GPU events')
        counters = {}
        zeros = []
        with open_csv(run/'Raw/frames.csv') as stream:
            native_frames=list(csv.DictReader(stream))
        native_columns=dict(hurtboxVisits='visits',geometryTests='geometry',occlusionCalls='occlusion',
                            candidates='candidates',confirmedHits='confirmed',duplicateSuppression='suppressed',actions='actions')
        for name, key in COUNTERS.items():
            path=out/f'counter-{name}.csv'
            with open_csv(path) as stream:
                reader=csv.DictReader(stream)
                if reader.fieldnames!=['Time','Value']:
                    raise ValueError('counter schema: '+name)
                values=[(float(r['Time']),int(r['Value'])) for r in reader]
            if not values and summary[key]==0 and native_frames and all(int(r[native_columns[key]])==0 for r in native_frames):
                # Checked native counters emit only on change. Preserve explicit
                # zero proof from every sampled native frame and the final summary.
                zeros.append(key)
            elif not values or values[-1][1]!=summary[key] or any(not start<=t<=end for t,_ in values):
                raise ValueError('counter samples or final value: '+name)
            counters[key]=len(values)
        stats=table(out/'statistics.csv')
        scopes={r['Name']:r for r in stats if r['Name'].startswith('U04C1_')}
        required=SCOPES[:-1] if summary['inside'] else ('WorldUpdate','CollectCandidates','Geometry')
        if not all('U04C1_'+name in scopes for name in required):
            raise ValueError('missing CPU statistics')
        cpu_cost={}
        frame_count=sum(r['ThreadName']=='Game Frames' for r in frames)
        if not frame_count:
            raise ValueError('no Game Frames track')
        for name,row in scopes.items():
            inclusive,exclusive=float(row['Incl']),float(row['Excl'])
            cpu_cost[name]=dict(count=int(row['Count']), inclusiveSeconds=inclusive,
                                exclusiveSeconds=exclusive, inclusivePerFrame=inclusive/frame_count,
                                exclusivePerFrame=exclusive/frame_count,
                                inclusivePerAction=inclusive/60, exclusivePerAction=exclusive/60)
        for name in SCOPES:
            if not summary['inside']:
                cpu_cost.setdefault('U04C1_'+name, dict(count=0,inclusiveSeconds=0,exclusiveSeconds=0,
                    inclusivePerFrame=0,exclusivePerFrame=0,inclusivePerAction=0,exclusivePerAction=0))
        gpu_pass={}
        for row in gpu:
            key=row['ThreadName']+'/'+row['TimerName']
            gpu_pass[key]=gpu_pass.get(key,0)+min(float(row['EndTime']),end)-max(float(row['StartTime']),start)
        return dict(region=[start,end],gpuEvents=len(gpu),frameEvents=len(frames),counterSamples=counters,
                    cpu=cpu_cost,cpuFrameDenominator=frame_count,gpuSecondsByTrackAndPass=gpu_pass,
                    boundaryPolicy='GPU durations clipped to region; CPU aggregation from Insights',
                    **({'zeroCountersWithoutTraceChanges':zeros} if zeros else {}))
    # Engine query rules use inclusive boundaries. Retain every lifetime row.
    if 'U04C1_START' not in log or 'U04C1_END' not in log:
        raise ValueError('missing memory bookmarks')
    result={}
    compact=any((out/name).is_file() for name in ('stack-sample.csv','stack-sample.csv.gz'))
    if compact:
        sample=[row for row in table(out/'stack-sample.csv') if re.search(r'::[A-Za-z_]|![A-Za-z_]',row['AllocCallstack'])]
        if not sample:
            raise ValueError('no resolved allocation stack in bounded sample')
        result['stackSample']=dict(resolvedRows=len(sample),example=sample[0])
    for name in ('allocations','frees','outstanding-start','outstanding-end'):
        count=size=resolved=resolved_bytes=0
        with open_csv(out/(name+'.csv')) as stream:
            reader = csv.reader(stream)
            header = next(reader, [])
            stack_column = (('FreeFunction' if name == 'frees' else 'AllocFunction') if compact
                            else ('FreeCallstack' if name == 'frees' else 'AllocCallstack'))
            size_index = header.index('Size')
            stack_index = header.index(stack_column)
            symbol = re.compile(r'::[A-Za-z_]|![A-Za-z_]').search
            for row in reader:
                n = int(row[size_index])
                count += 1
                size += n
                if symbol(row[stack_index]):
                    resolved += 1
                    resolved_bytes += n
        if not count:
            raise ValueError('empty memory export '+name)
        if name in ('allocations','frees') and not resolved:
            raise ValueError('no resolved callstack '+name)
        result[name]=dict(count=count,bytes=size,resolved=resolved,resolvedBytes=resolved_bytes)
    result['outstandingDelta']={k:result['outstanding-end'][k]-result['outstanding-start'][k] for k in ('count','bytes')}
    result['allocationRate']={k:dict(perSecond=result['allocations'][k]/duration,
                                     perAction=result['allocations'][k]/60) for k in ('count','bytes')}
    return result
