"""R1a repro/method analysis. Never certifies U04.03 or reclassifies old runs."""
import bisect, hashlib, json, math
from pathlib import Path
from AnalyzeR1 import cadence, percentile, interpolate, vector

VERSION='r1a-repro-entry-1'
def load(path):return [json.loads(s) for s in Path(path).read_text(encoding='utf-8-sig').splitlines()]
def check_raw(raw):
    assert raw[0]['kind']=='begin' and raw[-1]['kind']=='end','incomplete buffer'
    assert not any(r['kind']=='reset' for r in raw),'reset in window'
    rows=[r for r in raw if r['kind']=='frame']
    assert rows and all(r['worldType']==1 and r['netMode']==0 for r in rows),'not Solo Game world'
    return rows
def idle(raw,fps):
    rows=check_raw(raw);start=rows[0]['worldTime']+1.5;end=start+15
    left=interpolate(rows,start);right=interpolate(rows,end)
    selected=[r for r in rows if left['left']['frame']<=r['frame']<=right['right']['frame']]
    primary=cadence(selected,fps)
    assert all(r['combat']['action']==0 and not r['hits'] for r in selected),'not idle'
    costs=[r['collectorExitWall']-r['sampleEntryWall'] for r in selected]
    assert all(x>=0 for x in costs),'negative collector cost'
    compare={}
    for name in ('worldBeginWall','frameBeginWall','collectorExitWall','wall'):
        other=[dict(r,sampleEntryWall=r[name]) for r in selected]
        compare[name]=cadence(other,fps)
    return dict(status='PASS' if primary.get('pass_') else 'INVALID',acceptance=False,purpose='METHOD_ONLY',
        analyzer=VERSION,primary=primary,comparisonOnly=compare,startBoundary=left,endBoundary=right,
        worldDuration=15,wallDuration=right['wall']-left['wall'],
        collectorCostSeconds=dict(p50=percentile(costs,.5),p95=percentile(costs,.95),p99=percentile(costs,.99),max=max(costs)),
        overhead='JSON objects/arrays/strings, diagnostic getters, history iteration and buffer growth per frame; inherited 5Hz U01 metrics logs; native buffer serialization/file flush only after end. Exit stamp follows Event insertion; stamp/return cost excluded.')

def repro(raw,case,fps):
    rows=check_raw(raw);reasons=[]
    edges=[r for r in raw if r['kind']=='PhysicalEdge' and not r.get('console') and r['key'] in ('W','LeftShift')]
    sequence=[(r['key'],r['down']) for r in edges]
    expected={'w-shift':[('W',True),('LeftShift',True)],'shift-w':[('LeftShift',True),('W',True)],
              'w-up-shift':[('W',True),('W',False),('LeftShift',True)],'previous':[('W',True),('LeftShift',True)]}[case]
    if sequence[:len(expected)]!=expected:reasons.append('edge sequence precondition')
    prefix=edges[:len(expected)]
    if len(prefix)<len(expected):reasons.append('missing physical edge')
    same=bool(prefix) and len({r['frame'] for r in prefix})==1
    if case!='previous' and not same:reasons.append('same-frame precondition')
    intents=[r for r in raw if r['kind']=='IntentDirection' and r['commandType']==1]
    prior=[]
    if prefix:
        w=next((r for r in prefix if r['key']=='W' and r['down']),None)
        shift=next((r for r in prefix if r['key']=='LeftShift'),None)
        if w and shift:
            prior=[r for r in rows if w['frame']<=r['frame']<shift['frame'] and any(k['bindingAction']==0 and k['observedPhysical'] for k in r['input']['keys'])]
    if case=='previous' and not prior:reasons.append('previous-frame observation precondition')
    primary=cadence(rows,fps)
    # Structural validity only; cadence is retained separately for these repros.
    structural=[r for r in primary['reasons'] if r not in {'mean FPS outside 5%','fewer than 95% intervals within 10%','frame exceeds two periods'}]
    reasons+=structural
    result=dict(status='INVALID' if reasons else 'FAIL',purpose='REPRO_ONLY',acceptance=False,case=case,
                preconditionReasons=reasons,edges=edges,sameFrame=same,previousHeldFrames=prior,primary=primary,analyzer=VERSION)
    if len(intents)!=1:
        result['gameplayReasons']=['not exactly one dodge sent'];return result
    intent=intents[0];cmd=intent['command'];receive=next((r for r in raw if r['kind']=='Received' and r['command']==cmd),None)
    admit=next((r for r in raw if r['kind']=='AuthorityAdmission' and r['command']==cmd),None)
    end=next((r for r in raw if r['kind']=='dodgeCommit' and r['trajectoryEnd']),None)
    result.update(intent=intent,received=receive,admission=admit,trajectoryEnd=end)
    if admit:
        speed=math.hypot(*vector(admit['velocityBeforeBatch'])[:2]);result['admissionSpeedCmS']=speed
        if case!='previous' and speed>.01:reasons.append('stationary prebatch admission precondition')
    if reasons:result['status']='INVALID'
    wanted=[1,0] if case in ('w-shift','previous') else [0,0];heading=[1,0,0] if wanted[0] else [-1,0,0]
    wrong=[]
    if [intent['sentX'],intent['sentY']]!=wanted:wrong.append('wrong sent snapshot')
    if not receive or [receive['intentX'],receive['intentY']]!=wanted:wrong.append('transport changed snapshot/missing receipt')
    if not admit or vector(admit['modelDirection'])!=heading:wrong.append('authority model direction/missing admission')
    if not end:wrong.append('missing trajectory-end commit')
    result['gameplayReasons']=wrong
    if not reasons:result['status']='FAIL' if wrong else 'PASS'
    return result

def write_result(path,result):
    result['analyzerSHA256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    Path(path).write_text(json.dumps(result,indent=2),encoding='utf-8')
