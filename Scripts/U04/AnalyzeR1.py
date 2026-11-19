"""U04-R1 candidate: PRIMARY=sampleEntryWall, no clock substitution. Fail-closed analysis of unfiltered rendered game-thread samples.

Percentiles use linear interpolation at rank (n-1)*p (numpy default convention).
Boundary interpolation uses alpha=(boundary-left.worldTime)/(right.worldTime-left.worldTime).
All quantities are centimeters and seconds. No instantaneous-FPS averaging.
"""
import argparse, bisect, hashlib, json, math, re
from pathlib import Path

VERSION = 'u04r1-entry-4'
PROFILE = {'t.IdleWhenNotForeground': 0, 'r.VSync': 0, 'r.ScreenPercentage': 50,
           'r.LumenScene.SurfaceCache.AtlasSize': 2048, 'r.RenderTargetPoolMin': 128,
           'r.Streaming.PoolSize': 256, 'r.Lumen.DiffuseIndirect.Allow': 0,
           'r.Lumen.Reflections.Allow': 0, 'r.Shadow.Virtual.Enable': 0, 'r.ShadowQuality': 2}

def percentile(values, p):
    a=sorted(values); x=(len(a)-1)*p; i=math.floor(x)
    return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(x-i)

def cadence(rows, target):
    reasons=[]
    if len(rows)<2:return {'pass':False,'reasons':['insufficient samples']}
    if any('sampleEntryWall' not in r for r in rows):return {'pass_':False,'reasons':['primary sampleEntryWall missing']}
    dt=[b['sampleEntryWall']-a['sampleEntryWall'] for a,b in zip(rows,rows[1:])]
    if any(x<=0 or not math.isfinite(x) for x in dt):
        return {'pass':False,'reasons':['duplicate/nonmonotonic/nonfinite wall timestamp']}
    if any(b['frame']!=a['frame']+1 for a,b in zip(rows,rows[1:])):reasons.append('missing/duplicate frame')
    if any(b['worldTime']<=a['worldTime'] for a,b in zip(rows,rows[1:])):reasons.append('nonmonotonic world time')
    for k in ('pid','world','pawn','reset','source'):
        if any(k not in r or r[k] is None for r in rows):reasons.append(k+' missing')
        if len({json.dumps(r.get(k),sort_keys=True) for r in rows})!=1:reasons.append(k+' changed')
    if not all(r.get('focus') for r in rows):reasons.append('focus lost')
    for r in rows:
        if r.get('fixed') or r.get('useFixedFrameRate') or r.get('dilation')!=1:reasons.append('fixed frame/time dilation');break
        if (r.get('width'),r.get('height'))!=(1280,720):reasons.append('viewport mismatch');break
        if r.get('cvars')!={**PROFILE,'t.MaxFPS':target}:reasons.append('cvar mismatch/change');break
    for k in ('smoothing','fixedDelta','fixedFrameRate'):
        if len({r.get(k) for r in rows})!=1:reasons.append(k+' changed')
    fps=len(dt)/sum(dt);period=1/target;within=sum(abs(x-period)<=period*.1 for x in dt)/len(dt)
    if abs(fps-target)>target*.05:reasons.append('mean FPS outside 5%')
    if within<.95:reasons.append('fewer than 95% intervals within 10%')
    if max(dt)>2*period:reasons.append('frame exceeds two periods')
    edges=[0,.5,.9,1.1,1.5,2,float('inf')]
    histogram=[{'loPeriods':edges[i],'hiPeriods':edges[i+1] if math.isfinite(edges[i+1]) else None,
                'count':sum(edges[i]<=x/period<edges[i+1] for x in dt)} for i in range(len(edges)-1)]
    return dict(pass_=not reasons, reasons=reasons, intervals=len(dt),wallSeconds=sum(dt),fps=fps,
                within10Percent=within,p50=percentile(dt,.5),p95=percentile(dt,.95),p99=percentile(dt,.99),
                max=max(dt),histogram=histogram,measurement='rendered package game-thread post-actor collector ENTRY; not present/scanout',primaryClock='sampleEntryWall')

def interpolate(rows, at):
    times=[r['worldTime'] for r in rows];i=bisect.bisect_right(times,at)-1
    if i<0 or i+1>=len(rows):raise ValueError('boundary not bracketed')
    a,b=rows[i:i+2];alpha=(at-a['worldTime'])/(b['worldTime']-a['worldTime'])
    return dict(time=at,alpha=alpha,left=a,right=b,
                position=[x+(y-x)*alpha for x,y in zip(a['position'],b['position'])],
                wall=a['sampleEntryWall']+(b['sampleEntryWall']-a['sampleEntryWall'])*alpha)

def distance(a,b):return math.hypot(b[0]-a[0],b[1]-a[1])

def vector(text):return [float(v) for v in re.findall(r'[XYZ]=([-+0-9.eE]+)',text)]

def dodge_chain(raw,rows,direction):
    """Single-Dodge trial correlation. Missing/ambiguous evidence is INVALID.

    Receipt.command is the received command. Receipt.commandId is a stale
    published snapshot and MUST NOT be used as the receipt's command identity.
    Intent/edge pawn paths are bridged to GUID/life by native frame samples.
    """
    def need(condition,reason):
        if not condition:raise ValueError(reason)
    def one(items,reason):
        need(len(items)==1,reason);return items[0]
    def vec(text,reason):
        need(isinstance(text,str),reason)
        number=r'([-+0-9.eE]+)'
        match=re.fullmatch(r'\s*X='+number+r'\s+Y='+number+r'\s+Z='+number+r'\s*',text)
        need(match is not None,reason)
        v=[float(x) for x in match.groups()];need(all(math.isfinite(x) for x in v),reason);return v
    def identity(j):
        pawn,life=j['pawnId'],j['life']
        need(bool(pawn) and isinstance(life,(int,float)) and math.isfinite(life) and life>0 and int(life)==life,'invalid pawn/life correlation')
        need(j['lifeId']==f'{pawn}:{int(life)}','inconsistent lifeId correlation')
        return pawn,life
    def valid_frames(samples):
        need(len(samples)>=2,'insufficient native observation samples')
        quality=cadence(samples,samples[0]['cvars']['t.MaxFPS'])
        timing_only={'mean FPS outside 5%','fewer than 95% intervals within 10%','frame exceeds two periods'}
        structural=[r for r in quality['reasons'] if r not in timing_only]
        need(not structural,'invalid observation data: '+', '.join(structural))
    def serial_prefix(last):
        prefix=raw[:next(i for i,r in enumerate(raw) if r is last)+1]
        serials=[r['diagnosticSerial'] for r in prefix]
        need(all(b==a+1 for a,b in zip(serials,serials[1:])),'missing/duplicate/reordered diagnostic serial before evidence boundary')
    need(raw and raw[0]['kind']=='begin' and raw[-1]['kind']=='end','capture not closed')
    need(sum(r['kind']=='begin' for r in raw)==1 and sum(r['kind']=='end' for r in raw)==1,'ambiguous capture envelope')
    intent=one([r for r in raw if r['kind']=='IntentDirection' and r.get('commandType')==1],'not exactly one Dodge intent')
    need(intent['controlState']==0 and intent['windowActive'] and not intent['motorLocked'],'Dodge intent not in eligible playing state')
    receipt=one([r for r in raw if r['kind']=='Received' and r.get('commandType')==1],'not exactly one authority dodge receipt')
    command=intent['command'];need(command==receipt['command'],'intent/receipt command correlation')
    need(isinstance(command,(int,float)) and math.isfinite(command) and command>0 and int(command)==command,'invalid Dodge command')
    # Trajectory.commandId is the last processed command snapshot. It is a
    # usable cross-check only under this explicitly enforced single-command trial.
    need(all(r['command']==command for r in raw if r['kind']=='Received'),'additional command in single-Dodge trial')
    admission=one([r for r in raw if r['kind']=='AuthorityAdmission' and r.get('command')==command],'missing/ambiguous command-correlated authority admission')
    ident=identity(receipt);need(identity(admission)==ident,'receipt/admission pawn/life correlation')
    need(int(admission['commandId'])==command,'admission commandId correlation')
    mapped=[r for r in rows if r.get('pawnPath')==intent['pawn']]
    need(bool(mapped),'intent pawn path has no native GUID/life bridge')
    need(all(r['pawn']==ident[0] and identity(r['combat'])==ident and r['controller']==intent['controller'] for r in mapped),'intent/frame pawn/life/controller correlation')
    need(len(mapped)==len(rows),'pawn path changed/missing in trial')
    velocity=vec(admission['velocityBeforeBatch'],'invalid authority admission velocityBeforeBatch')
    need(math.hypot(*velocity[:2])<=.01,'not stationary at authority admission (velocityBeforeBatch)')
    # EventSerial establishes controller dispatch order, not OS key state or frame equality.
    serial_prefix(admission)
    at=admission['at'];receive_at=receipt['receive']
    need(all(isinstance(t,(int,float)) and math.isfinite(t) for t in (at,receive_at)) and at>=receive_at,'invalid receipt/admission time')
    admission_rows=[r for r in rows if r['worldTime']<=at]
    valid_frames(admission_rows)
    need(admission_rows[0]['worldTime']<=receive_at<=admission_rows[-1]['worldTime'],'receipt lacks native observation coverage')
    keys={int(k['bindingAction']):k for k in intent['keys']}
    need(all(i in keys for i in (0,1,2,3,10)),'missing binding snapshot')
    aliases={'LeftShift':('LeftShift','RightShift'),'RightShift':('LeftShift','RightShift'),
             'LeftControl':('LeftControl','RightControl'),'RightControl':('LeftControl','RightControl')}
    def physical(binding):return aliases.get(binding,(binding,))
    edges=[r for r in raw if r['kind']=='PhysicalEdge' and r['diagnosticSerial']<intent['diagnosticSerial']]
    need(bool(edges),'missing pre-intent physical edges')
    edge=edges[-1];dodge_key=keys[10]['binding']
    need(edge['key'] in physical(dodge_key) and edge['down'] and edge['newEdge'],'missing new Dodge press before intent')
    need(edge['pawn']==intent['pawn'] and edge['controller']==intent['controller'],'Dodge edge pawn/controller correlation')
    need(edge['frame']==intent['frame'],'Dodge snapshot not at dispatch frame')
    need(edge['key']==dodge_key,'physical modifier alias gate not individually observable')
    def eligible(e,action):
        snapshot=one([k for k in e['keys'] if k['bindingAction']==action],'missing edge binding/gate snapshot')
        need(snapshot['binding']==keys[action]['binding'],'binding changed before Dodge')
        return (e['controlState']==0 and e['windowActive'] and not e['motorLocked'] and not e.get('console',False)
                and snapshot['gateAllows'] and snapshot['observedPhysical'])
    need(eligible(edge,10) and keys[10]['gateAllows'] and keys[10]['observedPhysical'],'Dodge press quarantined/not eligible')
    held={};direction_edges=[]
    for e in edges[:-1]:
        if e['key'] not in {p for i in range(4) for p in physical(keys[i]['binding'])}:continue
        need(e['pawn']==intent['pawn'] and e['controller']==intent['controller'],'direction edge pawn/controller correlation')
        if not e['down']:held.pop(e['key'],None);continue
        if not e['newEdge']:continue
        actions=[i for i in range(4) if e['key'] in physical(keys[i]['binding'])]
        need(all(e['key']==keys[i]['binding'] for i in actions),'direction alias gate not individually observable')
        held[e['key']]=e
        direction_edges.append(e)
    active=[]
    for i in range(4):
        k=keys[i];pressed=bool(k['observedPhysical'] and k['gateAllows'])
        proof=held.get(k['binding'])
        if pressed:need(proof is not None and eligible(proof,i),'held direction lacks eligible pre-Dodge press')
        active.append(pressed and proof is not None)
    snapshot=[int(active[0])-int(active[1]),int(active[3])-int(active[2])]
    expected={'forward':[1,0],'back':[-1,0],'left':[0,-1],'right':[0,1]}[direction]
    need(snapshot==expected,'requested direction not validly held before Dodge edge')
    need(intent['diagnosticSerial']<receipt['diagnosticSerial']<admission['diagnosticSerial'],'intent/receipt/admission order correlation')
    # Establish semantic failures at admission BEFORE asking whether any motor
    # trajectory exists. Rejection is direct evidence, not missing telemetry.
    failures=[]
    sent=[intent['sentX'],intent['sentY']];received=[receipt['intentX'],receipt['intentY']]
    need(all(isinstance(x,(int,float)) and math.isfinite(x) for x in sent+received),'invalid direction snapshot data')
    if sent!=snapshot:failures.append('valid edges produced wrong sent snapshot')
    if received!=sent:failures.append('receipt changed sent direction snapshot')
    yaw=receipt['intentYaw'];need(isinstance(yaw,(int,float)) and math.isfinite(yaw),'invalid intent yaw')
    need(intent['yaw']==yaw,'intent/receipt yaw correlation')
    a=math.radians(yaw);x,y=snapshot;world=[x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),0]
    result=admission['admissionResult']
    need(isinstance(result,(int,float)) and not isinstance(result,bool) and math.isfinite(result) and int(result)==result and 0<=result<=9,'unknown/malformed authority admission result')
    result=int(result)
    if result!=0:failures.append(f'valid Dodge not accepted by authority (admissionResult={result})')
    else:
        model=vec(admission['modelDirection'],'missing admission model direction')
        if any(abs(x-y)>.0001 for x,y in zip(model,world)):failures.append('valid snapshot produced wrong authority model direction')
    base=dict(command=command,pawnId=ident[0],life=ident[1],singleCommandTrial=True,
              intent=intent,receipt=receipt,admission=admission,snapshot=snapshot,expectedWorldDirection=world,
              admissionVelocity=velocity,directionEdges=direction_edges,dodgeEdge=edge,reasons=failures)
    if failures:
        return dict(base,outcome='ADMISSION_FAILURE',failureEstablishedAt='authority admission',
                    end=None,trajectorySequence=None,firstFrame=admission_rows[0]['frame'],lastFrame=admission_rows[-1]['frame'],
                    observationScope='validated evidence through admission; cadence diagnostic only, never acceptance')
    ends=[r for r in raw if r['kind']=='dodgeCommit' and r['trajectoryEnd']]
    need(len(ends)<=1,'ambiguous trajectory-end commit')
    if not ends:
        # Missing terminal data is not automatically gameplay failure. Require
        # a closed, loss-free native stream through the contractual release
        # deadline PLUS the next sampled frame (observation allowance).
        deadline=at+.35
        index=bisect.bisect_left([r['worldTime'] for r in rows],deadline)
        need(index+1<len(rows),'capture too short to observe accepted Dodge completion')
        confirmation=rows[index+1];covered=rows[:index+2]
        valid_frames(covered);serial_prefix(confirmation)
        end_time=raw[-1].get('worldTime',raw[-1].get('observedWorld'))
        need(isinstance(end_time,(int,float)) and math.isfinite(end_time) and end_time>=confirmation['worldTime'],'capture end precedes completion observation')
        state=confirmation['combat']
        need(identity(state)==ident and int(state['commandId'])==command,'completion observation identity/command correlation')
        need(isinstance(state['locked'],bool),'completion lock state missing/malformed')
        sequence=state['dodge'];need(sequence in (receipt['dodge'],receipt['dodge']+1),'ambiguous completion trajectory sequence')
        if sequence==receipt['dodge']:
            failures.append('accepted Dodge produced no observed trajectory in complete capture')
        else:
            need(state['dodgeStart']==admission['modelDodgeStart']==at,'completion observation start correlation')
            if state['locked']:failures.append('accepted Dodge still locked beyond release deadline and observation frame')
        # Unlocked state without terminal commit could be a missing diagnostic
        # event. Do not infer the endpoint/duration from a late frame sample.
        need(bool(failures),'terminal commit missing but frame state does not prove gameplay noncompletion')
        return dict(base,outcome='INCOMPLETE_ACTION',failureEstablishedAt='completion observation',
                    end=None,trajectorySequence=sequence,completionDeadline=deadline,confirmationFrame=confirmation,
                    firstFrame=covered[0]['frame'],lastFrame=covered[-1]['frame'],
                    observationScope='closed loss-free capture through release deadline and next native sample')
    end=ends[0];c=end['combat']
    need(len(end['position'])==3 and all(isinstance(x,(int,float)) and math.isfinite(x) for x in end['position']),'invalid trajectory-end position')
    need(identity(c)==ident,'trajectory pawn/life correlation')
    need(all(end[k]==rows[0][k] for k in ('pid','source','world')),'trajectory process/source/world correlation')
    need(int(c['commandId'])==command,'trajectory command correlation')
    need(c['dodge']==receipt['dodge']+1,'trajectory sequence correlation')
    need(c['dodgeStart']==admission['modelDodgeStart']==admission['at'],'admission/trajectory start correlation')
    need(end['at']==c['dodgeMotionEnd'],'trajectory-end deadline correlation')
    need(admission['diagnosticSerial']<end['diagnosticSerial'],'admission/trajectory event order')
    for commit in [r for r in raw if r['kind']=='dodgeCommit']:
        state=commit['combat']
        need(identity(state)==ident and int(state['commandId'])==command and state['dodge']==c['dodge'] and state['dodgeStart']==c['dodgeStart'],'trajectory commit identity changed')
    return dict(base,outcome='TERMINAL_TRAJECTORY',trajectorySequence=c['dodge'],
                receivedOrigin=vec(receipt['receivedPosition'],'invalid authority receipt position'),
                trajectoryHeading=vec(c['dodgeDirection'],'invalid trajectory direction'),
                end=end)

def dodge(raw,rows,direction):
    chain=dodge_chain(raw,rows,direction)
    if chain['end'] is None:
        return dict(pass_=False,reasons=chain['reasons'],correlation=chain,
                    failureEstablishedAt=chain['failureEstablishedAt'],firstFrame=chain['firstFrame'],lastFrame=chain['lastFrame'],
                    observationScope=chain['observationScope'])
    end=chain['end'];receipt=chain['receipt'];c=end['combat'];start=c['dodgeStart'];stop=c['dodgeMotionEnd'];origin=chain['receivedOrigin']
    heading=chain['trajectoryHeading'];expected=chain['expectedWorldDirection']
    actual=distance(origin,end['position']);reasons=list(chain['reasons'])
    if abs(actual-300)>5:reasons.append('dodge distance')
    if abs(stop-start-.25)>1e-6:reasons.append('trajectory duration')
    if abs(c['dodgeLockEnd']-start-.35)>1e-6:reasons.append('release gate deadline')
    if len(heading)!=3 or any(abs(x-y)>.0001 for x,y in zip(heading,expected)):reasons.append('wrong locked direction')
    observed=[r for r in rows if start<=r['worldTime']<=c['dodgeLockEnd']]
    if not observed:raise ValueError('no dodge observation samples')
    if any(r['combat']['dodgeDirection']!=c['dodgeDirection'] for r in observed):reasons.append('direction changed')
    if any(r['mode']!=1 for r in observed):reasons.append('left ground before release')
    if any(r['kind']=='ActionStarted' and r['gameplaySeconds']<c['dodgeLockEnd'] and r['gameplaySeconds']>=start for r in raw):reasons.append('attack before release')
    a=interpolate(rows,receipt['receive']);b=interpolate(rows,c['dodgeLockEnd'])
    return dict(pass_=not reasons,reasons=reasons,distanceCm=actual,errorCm=actual-300,
                authorityReceive=receipt['receive'],authorityStart=start,authorityMotionEnd=stop,authorityLockEnd=c['dodgeLockEnd'],
                modelOrigin=vector(c['dodgeOrigin']),originRule='authority receipt position, never model velocity/configuration',
                correlation=chain,origin=origin,endCommit=end,firstFrame=a['left']['frame'],lastFrame=b['right']['frame'])

def combo(raw,rows):
    actions=[r for r in raw if r['kind']=='ActionStarted']
    receives=[r for r in raw if r['kind']=='Received' and r['commandType']==6]
    admissions=[r for r in raw if r['kind'] in ('Admitted','Rejected')]
    if len(receives)!=3:raise ValueError('not exactly three authority input receipts')
    if not actions:
        first_admission=[r for r in admissions if re.search(r'command='+str(int(receives[0]['command']))+r'\b',r['detail'])]
        start=first_admission[0]['gameplaySeconds'] if first_admission else receives[0]['receive']
        for i,receive in enumerate(receives[1:]):
            deadline=start+(.4 if i==0 else .85)
            if not deadline-.15<receive['receive']<deadline:raise ValueError('authority input outside buffer')
        return dict(pass_=False,reasons=['valid received combo inputs produced no action'],actions=[],hits=[],
                    firstFrame=rows[0]['frame'],lastFrame=rows[-1]['frame'])
    first=actions[0];last=actions[-1];s=first['start'];e=last['end'];reasons=[]
    # A received edge outside the preceding action buffer cannot certify continuous combo gameplay.
    for i,receive in enumerate(receives[1:]):
        deadline=s+(.4 if i==0 else .85)
        matches=[r for r in admissions if re.search(r'command='+str(int(receive['command']))+r'\b',r['detail'])]
        if not deadline-.15<receive['receive']<deadline:raise ValueError('authority input outside buffer')
        if len(matches)!=1:
            reasons.append('valid received input missing authority admission');continue
        at=matches[0]['gameplaySeconds']
        if not deadline-.15<at<deadline:reasons.append('valid received input processed outside buffer')
        if matches[0]['kind']=='Rejected':reasons.append('valid buffered input rejected')
    if len(actions)!=3 or [r['definition'] for r in actions]!=[0,1,2]:reasons.append('not exactly combo123 actions')
    if len({r['actionId'] for r in actions})!=3:reasons.append('duplicate action')
    if any(r['lifeId']!=first['lifeId'] for r in actions):reasons.append('source life changed')
    if abs(e-s-1.45)>1e-6:reasons.append('authoritative timeline differs from1.45s')
    if any(abs(a['end']-b['start'])>1e-6 for a,b in zip(actions,actions[1:])):reasons.append('noncontinuous actions')
    completed=[r for r in raw if r['kind']=='ActionCompleted']
    if len(completed)!=3 or any(not r['natural'] for r in completed):reasons.append('missing/unnatural authority completion')
    if completed and abs(completed[-1]['at']-s-1.45)>1e-6:reasons.append('actual completion timeline')
    expected_end=s+1.45
    before=[r for r in rows if r['worldTime']<s];after=[r for r in rows if r['worldTime']>=expected_end]
    if not before or not after:raise ValueError('combo bounds not observed')
    b=before[-1];a=after[0]
    if a['combat']['locked']:reasons.append('action still locked at observed end')
    hits=[h for h in a['hits'] if s<=h['time']<=expected_end]
    reasons+=hit_checks(hits,b['pawn'],first['life'],b['target'],b['targetLife'],[x['action'] for x in actions],b['targetVital']['hp'],a['targetVital']['hp'])
    if any(r['combat']['fixtureCritRoll']!=.5 for r in rows if s<=r['worldTime']<=e):reasons.append('crit-off fixture changed')
    return dict(pass_=not reasons,reasons=reasons,actions=actions,hits=hits,authorityDuration=e-s,
                hpBefore=b['targetVital']['hp'],hpAfter=a['targetVital']['hp'],
                observationLag=a['worldTime']-e,firstFrame=b['frame'],lastFrame=a['frame'])

def movement(rows, sprint=False):
    speed=700 if sprint else 500;stable=None;start=None
    for r in rows:
        valid=(r['mode']==1 and abs(math.hypot(*r['velocity'][:2])-speed)<=.01)
        if not valid:stable=None
        elif stable is None:stable=r['worldTime']
        elif r['worldTime']-stable>=.5:start=r['worldTime'];break
    if start is None:raise ValueError('no continuously stable speed for 0.5 world seconds')
    first=interpolate(rows,start);last=interpolate(rows,start+10)
    inside=[r for r in rows if start<r['worldTime']<start+10]
    pts=[first['position']]+[r['position'] for r in inside]+[last['position']]
    forward=last['position'][0]-first['position'][0];lateral=max(abs(p[1]-pts[0][1]) for p in pts)
    return dict(pass_=abs(forward-speed*10)<=50,forwardCm=forward,errorCm=forward-speed*10,
                pathCm=sum(distance(a,b) for a,b in zip(pts,pts[1:])),lateralCm=lateral,
                worldDuration=10,wallDuration=last['wall']-first['wall'],start=first,end=last,
                firstFrame=first['left']['frame'],lastFrame=last['right']['frame'])

def hit_checks(hits, source, life, target, target_life, actions, hp_before, hp_after):
    reasons=[];ids=[(h['source'],h['sourceLife'],h['action'],h['target'],h['targetLife']) for h in hits]
    if len(hits)!=3 or len(set(ids))!=3:reasons.append('duplicate/missing/extra hit')
    if any(h['source']!=source or h['sourceLife']!=life or h['target']!=target or h['targetLife']!=target_life for h in hits):reasons.append('wrong source/target life')
    if [h['action'] for h in hits]!=actions:reasons.append('wrong action')
    if any(h['crit'] or h['absorbed'] or h['defense'] for h in hits):reasons.append('crit/shield/defense active')
    if [h['damage'] for h in hits]!=[60,70,90]:reasons.append('wrong per-hit damage')
    if hp_before-hp_after!=220 or sum(h['damage'] for h in hits)!=220:reasons.append('HP delta mismatch')
    hp=hp_before
    for h in hits:
        if h['hpBefore']!=hp or h['hpAfter']!=hp-h['damage']:reasons.append('unexplained HP change')
        hp=h['hpAfter']
    if hp!=hp_after:reasons.append('unexplained final HP')
    return reasons

def analyze(path,target,case):
    raw=[json.loads(x) for x in path.read_text(encoding='utf-8-sig').splitlines()]
    rows=[r for r in raw if r['kind']=='frame'];result={'version':VERSION,'rawSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'case':case,'target':target,'status':'INVALID'}
    if not raw or raw[0]['kind']!='begin' or raw[-1]['kind']!='end':result['reason']='capture not closed';return result
    if any(r['kind'].lower()=='reset' for r in raw):result['reason']='reset during capture';return result
    if case in ('walk','sprint','combo','forward','back','left','right'):
        try:
            if case in ('walk','sprint'):g=movement(rows,case=='sprint')
            elif case=='combo':g=combo(raw,rows)
            else:g=dodge(raw,rows,case)
        except (ValueError,KeyError,TypeError,OverflowError,ZeroDivisionError) as e:result['reason']=str(e);return result
        selected=[r for r in rows if g['firstFrame']<=r['frame']<=g['lastFrame']]
        result['gameplay']=g;result['cadence']=cadence(selected,target)
        cadence_only={'mean FPS outside 5%','fewer than 95% intervals within 10%','frame exceeds two periods'}
        structural=[reason for reason in result['cadence']['reasons'] if reason not in cadence_only]
        result['status']='INVALID' if structural else ('FAIL' if not g['pass_'] else ('PASS' if result['cadence'].get('pass_') else 'INVALID'))
    else:result['reason']='case analyzer not implemented; never accepted'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('--fps',type=int,choices=[30,60,120],required=True);p.add_argument('--case',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise SystemExit('immutable output exists')
    a.out.write_text(json.dumps(analyze(a.raw,a.fps,a.case),indent=2),encoding='utf-8')
