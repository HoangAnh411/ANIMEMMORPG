"""U04-B v1: fail-closed analysis of unfiltered rendered game-thread samples.

Percentiles use linear interpolation at rank (n-1)*p (numpy default convention).
Boundary interpolation uses alpha=(boundary-left.worldTime)/(right.worldTime-left.worldTime).
All quantities are centimeters and seconds. No instantaneous-FPS averaging.
"""
import argparse, bisect, hashlib, json, math
from pathlib import Path

VERSION = 'u04b-1'
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
    dt=[b['wall']-a['wall'] for a,b in zip(rows,rows[1:])]
    if any(x<=0 or not math.isfinite(x) for x in dt):
        return {'pass':False,'reasons':['duplicate/nonmonotonic/nonfinite wall timestamp']}
    if any(b['frame']!=a['frame']+1 for a,b in zip(rows,rows[1:])):reasons.append('missing/duplicate frame')
    if any(b['worldTime']<=a['worldTime'] for a,b in zip(rows,rows[1:])):reasons.append('nonmonotonic world time')
    for k in ('pid','world','pawn','reset','source'):
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
                max=max(dt),histogram=histogram,measurement='rendered game-thread frame wall intervals; not scanout')

def interpolate(rows, at):
    times=[r['worldTime'] for r in rows];i=bisect.bisect_right(times,at)-1
    if i<0 or i+1>=len(rows):raise ValueError('boundary not bracketed')
    a,b=rows[i:i+2];alpha=(at-a['worldTime'])/(b['worldTime']-a['worldTime'])
    return dict(time=at,alpha=alpha,left=a,right=b,
                position=[x+(y-x)*alpha for x,y in zip(a['position'],b['position'])],
                wall=a['wall']+(b['wall']-a['wall'])*alpha)

def distance(a,b):return math.hypot(b[0]-a[0],b[1]-a[1])

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
    if any(r['kind']=='reset' for r in raw):result['reason']='reset during capture';return result
    if case in ('walk','sprint'):
        try:g=movement(rows,case=='sprint')
        except (ValueError,KeyError,ZeroDivisionError) as e:result['reason']=str(e);return result
        selected=[r for r in rows if g['firstFrame']<=r['frame']<=g['lastFrame']]
        result['gameplay']=g;result['cadence']=cadence(selected,target)
        result['status']='FAIL' if not g['pass_'] else ('PASS' if result['cadence'].get('pass_') else 'INVALID')
    else:result['reason']='case analyzer not implemented; never accepted'
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('--fps',type=int,choices=[30,60,120],required=True);p.add_argument('--case',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise SystemExit('immutable output exists')
    a.out.write_text(json.dumps(analyze(a.raw,a.fps,a.case),indent=2),encoding='utf-8')
