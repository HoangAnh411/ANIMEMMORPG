"""Reconcile counters with product damage identities and independently exported HP."""
import argparse,csv,json,math
from pathlib import Path
from collections import Counter,defaultdict
from C1Run import read,write

def validate(run,single=False):
    s=read(run/'Raw/summary.json');cmd=read(run/'command.json')['workload'];errors=[]
    def check(ok,text):
        if not ok:errors.append(text)
    n,h=cmd['subjects'],cmd['boxes'];inside=cmd['placement']=='in';count=1 if single else 60
    starts=[e for e in s['actionEvents'] if e['kind']=='ActionStarted']
    check(len(starts)==count,f'ActionStarted count {len(starts)} expected {count}')
    check(s['actions']==len(starts),'action counter vs product event mismatch')
    check(len({e['actionId'] for e in starts})==count,'action identities not unique')
    check([e['raw'] for e in starts]==([60] if single else [60,70,90]*20),'combo definitions/order differ')
    events=s['damageEvents'];expected=n*count if inside else 0
    check(len(events)==expected,f'Product damage events {len(events)} expected {expected}')
    check(s['confirmedHits']==len(events),'confirmed counter vs product damage event mismatch')
    identities=[(e['source'],e['sourceLife'],e['action'],e['target'],e['targetLife']) for e in events]
    check(len(set(identities))==len(identities),'multiple damage events per action/subject/life')
    subjects={t['subject']:t for t in s['targets']};check(len(subjects)==n,'target subject count differs')
    for t in subjects.values():
        check(sorted(t['stableHurtboxIds'])==([1] if h==1 else [1,2,3]),'stable hurtbox IDs differ')
        damage=[e for e in events if e['target']==t['subject']]
        check(len(damage)==(count if inside else 0),'per-subject event count differs')
        hp=1000000
        for e in damage:
            check(e['targetLife']==t['life'],'target life changed')
            check(e['beforeHP']==hp and e['afterHP']==hp-e['damage'],'HP transition differs from damage')
            check(not e['crit'] and not e['death'] and e['absorbed']==0,'unexpected crit/death/shield')
            hp=e['afterHP']
        check(hp==t['hp'] and not t['dead'] and t['deathCount']==0,'final actor HP differs from event reconstruction')
    check(s['registrationBegin']==s['registrationEnd'],'registration changed inside window')
    # Product attacker has its own hurtboxes; their actual count is kept, not assumed away.
    reg=s['registrationBegin'];check(reg['registeredSubjects']==n+1,'registered subjects include unexpected/missing actor')
    check(reg['registeredHurtboxes']>=n*h,'registered hurtbox gauge too small')
    check(s['hurtboxVisits']==s['collectIntervals']*reg['registeredHurtboxes'],'visits != collected intervals * actual registrations')
    check(s['geometryTests']==s['collectIntervals']*n*h,'geometry != collected intervals * eligible target hurtboxes')
    check(s['queriesPostContactDelta']==(s['geometryTests'] if inside else 0),'post-contact Queries differs from known geometry fixture')
    check(s['candidates']>=s['confirmedHits'],'candidate/hit ordering impossible')
    if not inside:check(s['occlusionCalls']==0 and s['candidates']==0,'out-of-range generated visibility/candidate work')
    check(not s['fixedTimeStep'] and not s['fixedFrameRate'] and s['dilation']==1,'time policy differs')
    expected_cv={'t.MaxFPS':60,'t.IdleWhenNotForeground':0,'r.VSync':0,'r.ScreenPercentage':50,'r.LumenScene.SurfaceCache.AtlasSize':2048,'r.RenderTargetPoolMin':128,'r.Streaming.PoolSize':256,'r.Lumen.DiffuseIndirect.Allow':0,'r.Lumen.Reflections.Allow':0,'r.Shadow.Virtual.Enable':0,'r.ShadowQuality':2}
    check(s['cvars']==expected_cv,'render/profile cvars differ')
    check(s['width']==1280 and s['height']==720,'viewport differs')
    rows=list(csv.DictReader((run/'Raw/frames.csv').open()));check(all(int(r['focus']) for r in rows),'focus lost')
    check(all(int(b['frame'])==int(a['frame'])+1 for a,b in zip(rows,rows[1:])),'frame counter gap')
    result=dict(status='PASS' if not errors else 'FAIL',errors=errors,actions=len(starts),productHits=len(events),registered=reg,counters={k:s[k] for k in ['collectIntervals','hurtboxVisits','geometryTests','occlusionCalls','queriesPostContactDelta','candidates','confirmedHits','duplicateSuppression']},candidateConfirmedRatio=s['candidates']/s['confirmedHits'] if s['confirmedHits'] else None,windowSeconds=s['endWall']-s['startWall'])
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--single-action',action='store_true');a=p.parse_args()
    v=validate(a.run,a.single_action);write(a.run/'validation.json',v);print(json.dumps(v,indent=2));raise SystemExit(0 if v['status']=='PASS' else 1)
