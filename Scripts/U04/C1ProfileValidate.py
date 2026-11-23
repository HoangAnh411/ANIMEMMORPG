"""Read-only gameplay, input, and lifetime validation for C1 method runs."""
import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path

from C1Counter import prepare_transition
from C1Identity import path_key
from C1ProfileRun import COMBO, QPC_BIAS, WORKLOAD
from C1Run import PROFILE, read, sha


def require(condition, message):
    if not condition:
        raise ValueError(message)


def window(run, summary, capture, process, rows):
    start, end = summary['startWall'], summary['endWall']
    require(summary['pid']==process['pid'] and summary['world']==capture['prepared']['metrics']['world'], 'summary process/world mismatch')
    require((summary['subjects'],summary['hurtboxesPerSubject'],summary['inside'])==(10,3,True), 'workload mismatch')
    require(summary['requestedSeconds']==60 and 60 <= end-start <= 61, 'native window duration')
    require((summary['width'],summary['height'],summary['dilation'],summary['smoothing'],summary['fixedTimeStep'],summary['fixedFrameRate'])==(1280,720,1,False,False,False), 'time/render profile')
    require(summary['cvars']==dict((k,float(v)) for k,v in (part.split() for part in PROFILE.split(','))), 'profile cvars')
    require(rows and all(int(r['focus'])==1 and start<=float(r['wall'])<=end and float(r['dt'])>0 for r in rows), 'frame window or focus')
    require(all(int(b['frame'])==int(a['frame'])+1 and float(b['wall'])>float(a['wall']) for a,b in zip(rows,rows[1:])), 'frame discontinuity')
    require(float(rows[0]['wall'])-start < 1 and end-float(rows[-1]['wall']) < 1, 'frame boundaries')
    require(capture['begin']-capture['warmupStart']>=30 and abs(start-(capture['begin']+QPC_BIAS))<.25, 'warmup or native clock alignment')
    require(len(capture['edges'])==60, 'missing scheduled edges')
    for offset, edge in zip(COMBO,capture['edges']):
        require(abs(capture['anchor']+offset-edge['deadline'])<1e-6 and 0<=edge['down']-edge['deadline']<=.12 and .035-1e-7<=edge['up']-edge['down']<=.12, 'edge schedule')
        require(start<=edge['down']+QPC_BIAS<edge['up']+QPC_BIAS<=end, 'edge outside native window')
    return start,end


def gameplay(summary,capture,process,start,end):
    errors = []
    def check(ok, reason):
        if not ok and reason not in errors:
            errors.append(reason)
    prepared=capture['prepared']['metrics']
    life=prepared['combat']['life']
    pawn=prepared['combat']['pawnId']
    check(capture['after']['metrics']['combat']['life']==life, 'after life')
    events=[a for a in summary['actionEvents'] if a['kind']=='ActionStarted']
    check([a['raw'] for a in events]==[60,70,90]*20 and summary['actions']==60,'action count or sequence')
    targets={t['subject']:t for t in summary['targets']}
    check(len(targets)==len(summary['targets'])==10,'target cardinality')
    for t in targets.values():
        check(sorted(t['stableHurtboxIds'])==[1,2,3] and t['hp']==995600 and not t['dead'] and t['shield']==0,'target topology or HP')
    identities={}
    for index,(a,edge) in enumerate(zip(events,capture['edges'])):
        require(start<=a['wall']<=end and 0<=a['wall']-(edge['down']+QPC_BIAS)<=.40, 'action outside window or input attribution')
        check(a['action']==index+1 and a['pawnId']==pawn and a['life']==life and a['pawn']==prepared['pawn'] and a['owner']==prepared['controller'] and a['pid']==process['pid'] and a['world']==summary['world'] and a['runId']==process['runId'] and a['sourceSHA']==process['sourceSHA'],'action identity')
        identities[(a['pawnId'],a['life'],a['action'])]=a['raw']
    seen=Counter()
    hp=dict.fromkeys(targets,1000000)
    for d in summary['damageEvents']:
        action=(d['source'],d['sourceLife'],d['action'])
        target=d['target']
        if action not in identities or target not in targets:
            check(False,'damage identity');continue
        t=targets[target]
        seen[action,target]+=1
        check(d['targetLife']==t['life']==t['lifeGeneration'] and d['hurtboxId'] in t['stableHurtboxIds'],'target life or hurtbox')
        damage=identities[action]
        check(d['damage']==damage and d['beforeHP']==hp[target] and d['afterHP']==hp[target]-damage and not d['crit'] and not d['death'] and d['absorbed']==0,'damage or HP transition')
        hp[target]-=damage
    check(len(identities)==60 and len(seen)==600 and all(v==1 for v in seen.values()) and summary['confirmedHits']==len(summary['damageEvents'])==600 and all(hp[k]==t['hp'] for k,t in targets.items()),'damage coverage')
    check(summary['registrationBegin']==summary['registrationEnd']==dict(registeredSubjects=11,registeredHurtboxes=32),'registration')
    return errors


def validate_stop(run, p, journal, status):
    stopped=read(run/'result.json');final=read(run/'final.json')
    proof=final['exitEvidence']
    require(final['status']==stopped['status']==status and stopped['exitEvidence']==proof and final['processExited'] is True and stopped['processExited'] is True,'stop verdict')
    require(proof['identityVerifiedAtStop'] is True and proof['wait']=='signaled' and proof['handleSource']=='original_Popen','stop markers')
    require(type(proof['pid']) is int and type(proof['creationTicks']) is int and proof['pid']==p['pid'] and proof['creationTicks']==p['creationTicks'] and path_key(proof['executable'])==path_key(p['executable']),'stop process identity')
    require([j.get('evidence') for j in journal if j['event']=='original_handle_process_exited']==[proof],'stop journal')


def validate(run, require_stop=True):
    try:
        run=Path(run).resolve()
        c=read(run/'capture.json'); s=read(run/'Raw/summary.json'); p=read(run/'process.json')
        require(c['transition']==prepare_transition(c['before'],c['prepared']), 'prepare transition')
        log=Path(p['log']).read_bytes()
        for key in ('before','prepared','after'):
            sample=c[key]
            require(sample['requestOffset']<=sample['lineOffset']<sample['endOffset']<=len(log),'metrics offsets')
            line=log[sample['lineOffset']:sample['endOffset']]
            require(line.endswith(b'\n') and json.loads(line.split(b'Metrics ',1)[1])==sample['metrics'],'metrics bytes')
            require(all(sample['metrics'][k]==c['prepared']['metrics'][k] for k in ('pid','world','runID','worldContext','pawn','controller')),'metrics identity')
        require(set(c['files'])=={'summary.json','frames.csv'} and all(sha(run/'Raw'/f)==h for f,h in c['files'].items()),'raw hashes')
        journal=[json.loads(line) for line in (run/'journal.jsonl').read_text(encoding='utf8').splitlines()]
        actual=[e for e in journal if e['event']=='input_sent' and e.get('purpose')=='counter-action']
        require(len(actual)==120,'missing guarded edges')
        for edge, down, up in zip(c['edges'],actual[::2],actual[1::2]):
            require(down['key']==up['key']=='LMB' and down['down'] is True and up['down'] is False and 0<=down['monotonic']-edge['down']<=.01 and 0<=up['monotonic']-edge['up']<=.01,'edge journal mismatch')
        with (run/'Raw/frames.csv').open(newline='',encoding='utf-8-sig') as stream:
            rows=list(csv.DictReader(stream))
        start,end=window(run,s,c,p,rows)
        errors=gameplay(s,c,p,start,end)
        counters=dict(visits='hurtboxVisits',geometry='geometryTests',occlusion='occlusionCalls',candidates='candidates',confirmed='confirmedHits',suppressed='duplicateSuppression',intervals='collectIntervals',actions='actions')
        errors.extend('frame counter '+field for key,field in counters.items() if int(rows[-1][key])!=s[field])
        status='FAIL' if errors else 'PASS'
        if require_stop:
            validate_stop(run, p, journal, status)
        times=sorted(float(row['dt'])*1000 for row in rows)
        return dict(status=status, failures=errors, startWall=start,endWall=end,actions=s['actions'],hits=s['confirmedHits'],
                    frames=len(rows),fps=len(rows)/(end-start),
                    frameMs=dict(mean=math.fsum(times)/len(times), **{key:times[math.ceil(len(times)*q)-1] for key,q in [('p50',.5),('p95',.95),('p99',.99),('max',1)]}))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, IndexError) as error:
        return dict(status='INVALID',error=str(error))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    args=parser.parse_args()
    result=validate(args.run)
    print(json.dumps(result,indent=2))
    raise SystemExit(int(result['status']!='PASS'))
