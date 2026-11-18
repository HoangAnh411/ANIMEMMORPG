"""Output-only repro and timing-point comparisons; never emits acceptance PASS."""
import argparse,hashlib,json,math,re
from pathlib import Path
from AnalyzeB import percentile,PROFILE

def vec(text):return [float(x) for x in re.findall(r'[XYZ]=([-+0-9.eE]+)',text)]
def key(input,binding='W'):return next(k for k in input['keys'] if k['binding']==binding)
def input_result(raw):
    frames=[r for r in raw if r['kind']=='frame'];directions=[r for r in raw if r['kind']=='IntentDirection' and r['commandType']==1]
    if len(directions)!=1:raise ValueError('not exactly one recorded dodge direction')
    intent=directions[0];command=intent['command'];receive=next(r for r in raw if r['kind']=='Received' and r['command']==command)
    admitted=next(r for r in raw if r['kind']=='AuthorityAdmission' and r['command']==command)
    edges=[r for r in raw if r['kind']=='PhysicalEdge' and r['key'] in ('W','LeftShift')]
    downs=[r for r in edges if r['down']];w=next(r for r in downs if r['key']=='W');shift=next(r for r in downs if r['key']=='LeftShift')
    prior=[r for r in frames if r['frame']<intent['frame'] and r['frame']>=w['frame'] and key(r['input'])['engineHeld']]
    end=next(r for r in raw if r['kind']=='dodgeCommit' and r['trajectoryEnd'])
    v=vec(admitted['velocityBeforeBatch']);direction=vec(admitted['modelDirection']);held=key(intent)
    origin=vec(end['combat']['dodgeOrigin']);distance=math.hypot(end['position'][0]-origin[0],end['position'][1]-origin[1])
    return dict(status='DIAGNOSTIC_ONLY',acceptance=False,sameInputFrame=w['frame']==shift['frame'],
                edgeOrder=[dict(key=r['key'],down=r['down'],frame=r['frame'],serial=r['diagnosticSerial'],wall=r['wall']) for r in edges],
                intent=intent,received=receive,admission=admitted,previousHeldFrames=[dict(frame=r['frame'],world=r['worldTime'],velocity=r['velocity'],input=r['input']) for r in prior],
                engineHeldAtLookup=held['engineHeld'],observedAtLookup=held['observedPhysical'],osHeldAtLookup=held['osHeld'],gateAllowsAtLookup=held['gateAllows'],
                sent=[intent['sentX'],intent['sentY']],receivedDirection=[receive['intentX'],receive['intentY']],modelDirection=direction,
                admissionVelocity=v,admissionSpeed=math.hypot(*v[:2]),stationaryAdmission=math.hypot(*v[:2])<=.01,
                directionTransportMatches=[intent['sentX'],intent['sentY']]==[receive['intentX'],receive['intentY']],distanceCm=distance,
                observedPreviousFrameHeld=bool(prior),firstFrame=frames[0]['frame'],lastFrame=frames[-1]['frame'])

def stats(values,fps=120):
    if len(values)<2 or any(not math.isfinite(x) for x in values) or any(b<=a for a,b in zip(values,values[1:])):raise ValueError('nonmonotonic/missing timing data')
    dt=[b-a for a,b in zip(values,values[1:])];period=1/fps
    return dict(intervals=len(dt),fps=len(dt)/sum(dt),within10Percent=sum(abs(d-period)<=period*.1 for d in dt)/len(dt),p50=percentile(dt,.5),p95=percentile(dt,.95),p99=percentile(dt,.99),max=max(dt),overTwoPeriods=sum(d>2*period for d in dt))

def timing_result(raw):
    allframes=[r for r in raw if r['kind']=='frame'];start=allframes[0]['worldTime']+2.5;end=start+15
    rows=[r for r in allframes if start<=r['worldTime']<=end]
    assert rows and all(b['frame']==a['frame']+1 for a,b in zip(rows,rows[1:])), 'missing frames'
    assert all(r['frameBeginCounter']==r['worldBeginCounter']==r['frame'] for r in rows), 'begin/actor frame alignment mismatch'
    assert all((r.get('width'),r.get('height'))==(1280,720) for r in rows), 'viewport changed'
    for name in ['source','pid','world','pawn','reset']:
        assert all(name in r for r in rows) and len({r[name] for r in rows})==1, name+' changed/missing'
    assert all(r['focus'] and r['dilation']==1 and not r['fixed'] and not r['useFixedFrameRate'] and r['cvars']=={**PROFILE,'t.MaxFPS':120} for r in rows), 'focus/profile/time changed'
    assert all(r['combat']['action']==0 and not r['hits'] for r in rows), 'control workload contains actions/hits'
    entry=[r['sampleEntryWall'] for r in rows];wall=[r['wall'] for r in rows];cost=[w-e for w,e in zip(wall,entry)]
    residual=[(wall[i]-wall[i-1])-(entry[i]-entry[i-1])-(cost[i]-cost[i-1]) for i in range(1,len(rows))]
    return dict(status='DIAGNOSTIC_ONLY',acceptance=False,worldStart=start,worldEnd=end,selectedFrames=len(rows),
                begin=stats([r['frameBeginWall'] for r in rows]),worldBegin=stats([r['worldBeginWall'] for r in rows]),entry=stats(entry),oldWall=stats(wall),
                collectorCostSeconds=dict(p50=percentile(cost,.5),p95=percentile(cost,.95),max=max(cost)),
                costDifferenceIdentityMaxResidual=max(abs(r) for r in residual),
                clocks='Core OnBeginFrame before rate limiting; UWorld::Tick start after rate limiting; post-actor collector entry; legacy post-collector wall. All real game-thread events, not scanout.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--mode',choices=['input','timing'],required=True);p.add_argument('--allow-partial',action='store_true');a=p.parse_args()
    ledger=json.loads((a.session/'Diagnostic/LEDGER.json').read_text(encoding='utf-8'));assert ledger['completed'] or a.allow_partial
    out=a.session/'Diagnostic/ANALYSIS.json';assert not out.exists();results=[]
    for item in ledger['windows']:
        path=Path(item['raw']);raw=[json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines()]
        assert raw[0]['kind']=='begin' and raw[-1]['kind']=='end' and not any(r['kind'].lower()=='reset' for r in raw)
        result=(input_result if a.mode=='input' else timing_result)(raw);results.append(dict(**item,rawSHA256=hashlib.sha256(path.read_bytes()).hexdigest(),result=result))
    out.write_text(json.dumps(dict(status='DIAGNOSTIC_ONLY',acceptance=False,mode=a.mode,captureCompleted=ledger['completed'],captureError=ledger.get('error'),analyzerSHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),windows=results),indent=2),encoding='utf-8');print(out)
