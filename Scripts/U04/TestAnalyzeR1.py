"""Synthetic method verification only; never counts as binary gameplay evidence."""
import copy, unittest, tempfile, json
from pathlib import Path
from AnalyzeR1 import PROFILE,cadence,percentile,interpolate,hit_checks,combo,dodge,movement,analyze

def frames(fps=120,n=1201):
    return [dict(wall=i/fps,sampleEntryWall=i/fps,worldTime=i/fps,frame=i,pid=4,world='GameLab',pawn='P',source='sha',reset=0,
                 focus=True,fixed=False,useFixedFrameRate=False,dilation=1,width=1280,height=720,
                 cvars={**PROFILE,'t.MaxFPS':120},smoothing=False,fixedDelta=1/30,fixedFrameRate=30,
                 position=[500*i/fps,0,98]) for i in range(n)]

def dodge_fixture():
    c=dict(pawnId='P',life=1,lifeId='P:1',commandId='4',dodge=1,dodgeStart=.5,dodgeMotionEnd=.75,dodgeLockEnd=.85,dodgeOrigin='X=0 Y=0 Z=98',dodgeDirection='X=1 Y=0 Z=0')
    rows=frames(n=160)
    for r in rows:r.update(kind='frame',pawnPath='PawnPath',controller='PC',mode=1,velocity=[0,0,0],combat=copy.deepcopy(c))
    def keys(shift=False):
        return [dict(bindingAction=i,binding=k,observedPhysical=(i==0 or i==10 and shift),gateAllows=True) for i,k in [(0,'W'),(1,'S'),(2,'A'),(3,'D'),(10,'LeftShift')]]
    common=dict(pawn='PawnPath',controller='PC',controlState=0,windowActive=True,motorLocked=False,console=False,frame=57)
    w=dict(common,kind='PhysicalEdge',key='W',down=True,newEdge=True,keys=keys(),worldTime=.48)
    shift=dict(common,kind='PhysicalEdge',key='LeftShift',down=True,newEdge=True,keys=keys(True),worldTime=.480001)
    intent=dict(common,kind='IntentDirection',commandType=1,command=4,sentX=1,sentY=0,yaw=0,keys=keys(True),worldTime=.480002)
    receipt=dict(kind='Received',pawnId='P',life=1,lifeId='P:1',commandId='0',dodge=0,commandType=1,command=4,receive=.48,receivedPosition='X=0 Y=0 Z=98',intentX=1,intentY=0,intentYaw=0,worldTime=.480003)
    admission=dict(kind='AuthorityAdmission',pawnId='P',life=1,lifeId='P:1',commandId='4',command=4,at=.5,modelDodgeStart=.5,admissionResult=0,modelDirection='X=1 Y=0 Z=0',velocityBeforeBatch='X=0 Y=0 Z=0',worldTime=.5)
    commit=dict(kind='dodgeCommit',trajectoryEnd=True,position=[300,0,98],combat=copy.deepcopy(c),at=.75,worldTime=.75,pid=4,source='sha',world='GameLab')
    raw=[dict(kind='begin',worldTime=-1),w,shift,intent,receipt,admission,commit]+rows+[dict(kind='end',worldTime=2)]
    raw.sort(key=lambda r:r['worldTime'])
    for i,r in enumerate(raw):r['diagnosticSerial']=i+1
    return raw,rows

def dodge_verdict(raw):
    with tempfile.TemporaryDirectory(prefix='u04-r1-tool-') as folder:
        p=Path(folder)/'synthetic.jsonl';p.write_text('\n'.join(json.dumps(r) for r in raw),encoding='utf-8')
        return analyze(p,120,'forward')

class Method(unittest.TestCase):
    def test_admission_velocity_is_authoritative(self):
        raw,rows=dodge_fixture();self.assertEqual(dodge_verdict(raw)['status'],'PASS')
        admission=next(r for r in raw if r['kind']=='AuthorityAdmission')
        # Prior native samples remain zero; actual batch velocity invalidates admission.
        admission['velocityBeforeBatch']='X=0.010001 Y=0 Z=0'
        self.assertEqual(dodge_verdict(raw)['status'],'INVALID')
        admission['velocityBeforeBatch']='X=0.006 Y=0.008 Z=12'
        self.assertEqual(dodge_verdict(raw)['status'],'PASS') # horizontal norm=.01
        for value in [None,'X=nan Y=0 Z=0','X=0 Y=0','Z=0 Y=0 X=100']:
            admission['velocityBeforeBatch']=value;self.assertEqual(dodge_verdict(raw)['status'],'INVALID')
        del admission['velocityBeforeBatch'];self.assertEqual(dodge_verdict(raw)['status'],'INVALID')
    def test_dodge_missing_wrong_or_ambiguous_correlation(self):
        for kind in ['IntentDirection','Received','AuthorityAdmission','dodgeCommit']:
            raw,_=dodge_fixture();raw=[r for r in raw if r['kind']!=kind]
            self.assertEqual(dodge_verdict(raw)['status'],'INVALID',kind)
        for kind,key,value in [('Received','command',5),('AuthorityAdmission','command',5),('AuthorityAdmission','life',2),('Received','pawnId','Other'),('IntentDirection','pawn','OtherPath')]:
            raw,_=dodge_fixture();next(r for r in raw if r['kind']==kind)[key]=value
            self.assertEqual(dodge_verdict(raw)['status'],'INVALID',(kind,key))
        for kind in ['IntentDirection','Received','AuthorityAdmission']:
            raw,_=dodge_fixture();del next(r for r in raw if r['kind']==kind)['command']
            self.assertEqual(dodge_verdict(raw)['status'],'INVALID',kind)
        raw,_=dodge_fixture();admission=next(r for r in raw if r['kind']=='AuthorityAdmission');admission.update(life=2,lifeId='P:2')
        self.assertEqual(dodge_verdict(raw)['status'],'INVALID')
        raw,_=dodge_fixture();receipt=next(r for r in raw if r['kind']=='Received');receipt.update(pawnId='Other',lifeId='Other:1')
        self.assertEqual(dodge_verdict(raw)['status'],'INVALID')
        for key,value in [('commandId','5'),('life',2),('dodge',2),('dodgeStart',.51)]:
            raw,_=dodge_fixture();next(r for r in raw if r['kind']=='dodgeCommit')['combat'][key]=value
            self.assertEqual(dodge_verdict(raw)['status'],'INVALID',key)
        raw,_=dodge_fixture();admission=copy.deepcopy(next(r for r in raw if r['kind']=='AuthorityAdmission'));raw.insert(-1,admission)
        self.assertEqual(dodge_verdict(raw)['status'],'INVALID')
    def test_direction_release_quarantine_and_rebind(self):
        raw,_=dodge_fixture();w=next(r for r in raw if r['kind']=='PhysicalEdge' and r['key']=='W')
        up=copy.deepcopy(w);up.update(down=False,worldTime=.4800005)
        raw.append(up);raw.sort(key=lambda r:r['worldTime'])
        for i,r in enumerate(raw):r['diagnosticSerial']=i+1
        # Even a held-state snapshot claiming W cannot replace a missing live edge.
        self.assertEqual(dodge_verdict(raw)['status'],'INVALID')
        raw,_=dodge_fixture();w=next(r for r in raw if r['kind']=='PhysicalEdge' and r['key']=='W');w['keys'][0]['gateAllows']=False
        self.assertEqual(dodge_verdict(raw)['status'],'INVALID')
        raw,_=dodge_fixture();next(r for r in raw if r['kind']=='IntentDirection')['motorLocked']=True
        self.assertEqual(dodge_verdict(raw)['status'],'INVALID')
        raw,_=dodge_fixture()
        for r in raw:
            if r['kind']=='PhysicalEdge' and r['key']=='W':r['key']='H'
            for k in r.get('keys',[]):
                if k['bindingAction']==0:k['binding']='H'
        self.assertEqual(dodge_verdict(raw)['status'],'PASS')
    def test_four_prepared_cardinals(self):
        for action,key,x,y in [(0,'W',1,0),(1,'S',-1,0),(2,'A',0,-1),(3,'D',0,1)]:
            raw,rows=dodge_fixture();heading=f'X={x} Y={y} Z=0'
            for r in raw:
                if r['kind']=='PhysicalEdge' and r['key']=='W':r['key']=key
                for k in r.get('keys',[]):
                    if k['bindingAction'] in range(4):k['observedPhysical']=k['bindingAction']==action
                if r['kind']=='IntentDirection':r.update(sentX=x,sentY=y)
                if r['kind']=='Received':r.update(intentX=x,intentY=y)
                if r['kind']=='AuthorityAdmission':r['modelDirection']=heading
                if 'combat' in r:r['combat']['dodgeDirection']=heading
                if r['kind']=='dodgeCommit':r['position']=[300*x,300*y,98]
            direction={0:'forward',1:'back',2:'left',3:'right'}[action]
            self.assertTrue(dodge(raw,rows,direction)['pass_'],direction)
    def test_direction_after_dodge_is_not_preparation(self):
        raw,_=dodge_fixture();w=next(r for r in raw if r['kind']=='PhysicalEdge' and r['key']=='W')
        w['worldTime']=.481
        for r in raw:
            if r['kind'] in ('IntentDirection','PhysicalEdge') and r is not w:
                next(k for k in r['keys'] if k['bindingAction']==0)['observedPhysical']=False
        raw.sort(key=lambda r:r['worldTime'])
        for i,r in enumerate(raw):r['diagnosticSerial']=i+1
        self.assertEqual(dodge_verdict(raw)['status'],'INVALID')
    def test_valid_edges_wrong_snapshot_transport_or_model_is_fail(self):
        for kind,key,value in [('IntentDirection','sentX',0),('Received','intentX',0),('AuthorityAdmission','modelDirection','X=-1 Y=0 Z=0')]:
            raw,_=dodge_fixture();next(r for r in raw if r['kind']==kind)[key]=value
            self.assertEqual(dodge_verdict(raw)['status'],'FAIL',(kind,key))
        raw,_=dodge_fixture()
        for r in raw:
            if r['kind']=='dodgeCommit':r['combat']['dodgeDirection']='X=-1 Y=0 Z=0'
        self.assertEqual(dodge_verdict(raw)['status'],'FAIL')
    def test_fps_is_count_over_total_not_instantaneous_mean(self):
        a=frames(n=3);a[0]['sampleEntryWall']=0;a[1]['sampleEntryWall']=1/120;a[2]['sampleEntryWall']=3/120
        self.assertAlmostEqual(cadence(a,120)['fps'],80)
    def test_exact_cadence_thresholds(self):
        def with_intervals(intervals):
            a=frames(n=len(intervals)+1);at=0
            for i,r in enumerate(a):
                r['sampleEntryWall']=at
                if i<len(intervals):at+=intervals[i]
            return a
        period=1/120
        self.assertTrue(cadence(with_intervals([period]*95+[period*1.11]*5),120)['pass_'])
        self.assertIn('fewer than 95% intervals within 10%',cadence(with_intervals([period]*94+[period*1.11]*6),120)['reasons'])
        # Put the doubled interval first to avoid accumulated binary rounding at equality.
        self.assertTrue(cadence(with_intervals([period*2]+[period]*99),120)['pass_'])
        self.assertIn('frame exceeds two periods',cadence(with_intervals([period*2+1e-8]+[period]*99),120)['reasons'])
    def test_entry_immutable_and_no_clock_fallback(self):
        a=frames()
        for i,r in enumerate(a):r['wall']+=i*.001
        self.assertAlmostEqual(cadence(a,120)['fps'],120)
        del a[30]['sampleEntryWall']
        self.assertIn('primary sampleEntryWall missing',cadence(a,120)['reasons'])
        source=(Path(__file__).resolve().parents[2]/'Source/AnimeMMORPG/U04/U04BFPSFixture.cpp').read_text(encoding='utf-8')
        self.assertEqual(source.count('SetNumberField(TEXT("sampleEntryWall")'),1)
        self.assertNotIn('sampleEntryWall',source.split('void Event(')[1].split('void BeginWorld(')[0])
    def test_boundary_frame_selection(self):
        a=frames(n=1300);left=interpolate(a,.003);right=interpolate(a,10.003)
        selected=[r for r in a if left['left']['frame']<=r['frame']<=right['right']['frame']]
        self.assertEqual(selected[0]['frame'],0);self.assertEqual(selected[-1]['frame'],1201)
        self.assertEqual(len(selected)-1,1201)

    def test_invalid_focus_keeps_observed_gameplay_failure(self):
        rows=frames(n=1500)
        for r in rows:r.update(kind='frame',mode=1,velocity=[500,0,0],position=[450*r['worldTime'],0,98])
        rows[400]['focus']=False
        with tempfile.TemporaryDirectory(prefix='u04b-method-') as directory:
            p=Path(directory)/'synthetic.jsonl';p.write_text('\n'.join(json.dumps(r) for r in [{'kind':'begin'}]+rows+[{'kind':'end'}]),encoding='utf-8')
            result=analyze(p,120,'walk')
        self.assertEqual(result['status'],'INVALID');self.assertFalse(result['gameplay']['pass_'])
    def test_movement_window(self):
        a=frames(n=1500)
        for r in a:r.update(mode=1,velocity=[500,0,0])
        g=movement(a);self.assertTrue(g['pass_']);self.assertAlmostEqual(g['worldDuration'],10)
    def test_combo_authority_and_buffer(self):
        rows=frames(n=260);starts=[.5,.9,1.35];ends=[.9,1.35,1.95]
        actions=[dict(kind='ActionStarted',start=s,end=e,action=i+1,definition=i,life=1,lifeId='P:1',actionId=f'P:1:{i+1}') for i,(s,e) in enumerate(zip(starts,ends))]
        hits=[dict(source='P',sourceLife=1,action=i+1,target='T',targetLife=2,time=t,damage=d,crit=False,absorbed=0,defense=0,hpBefore=h,hpAfter=h-d) for i,(t,d,h) in enumerate([(.66,60,600),(1.08,70,540),(1.61,90,470)])]
        for r in rows:
            r.update(pawn='P',target='T',targetLife=2,hits=[h for h in hits if h['time']<=r['worldTime']],combat={'fixtureCritRoll':.5,'locked':.5<=r['worldTime']<1.95})
            r['targetVital']={'hp':600-sum(h['damage'] for h in r['hits'])}
        receives=[dict(kind='Received',commandType=6,command=i+1,receive=t) for i,t in enumerate([.5,.82,1.27])]
        admissions=[dict(kind='Admitted',detail=f'command={i+1}',gameplaySeconds=t) for i,t in enumerate([.5,.82,1.27])]
        completed=[dict(kind='ActionCompleted',at=e,natural=True) for e in ends]
        raw=actions+receives+admissions+completed
        self.assertTrue(combo(raw,rows)['pass_'])
        completed[-1]['at']+=.000002;self.assertFalse(combo(raw,rows)['pass_']);completed[-1]['at']-=.000002
        admissions[1]['gameplaySeconds']=.7
        self.assertFalse(combo(raw,rows)['pass_']) # valid receipt, late/early processing is gameplay FAIL
        self.assertFalse(combo(receives+admissions,rows)['pass_']) # valid edges cannot become INVALID merely because no action started
        receives[1]['receive']=.7
        with self.assertRaisesRegex(ValueError,'outside buffer'):combo(raw,rows)
    def test_dodge_commit_position(self):
        raw,rows=dodge_fixture();commit=next(r for r in raw if r['kind']=='dodgeCommit');receipt=next(r for r in raw if r['kind']=='Received')
        self.assertTrue(dodge(raw,rows,'forward')['pass_'])
        self.assertEqual(dodge(raw,rows,'forward')['firstFrame'],57)
        receipt['receivedPosition']='X=12 Y=0 Z=98'
        self.assertFalse(dodge(raw,rows,'forward')['pass_'])
        receipt['receivedPosition']='X=0 Y=0 Z=98'
        commit['position'][0]=294.9;self.assertFalse(dodge(raw,rows,'forward')['pass_'])
    def test_cadence_and_cap(self):
        a=frames();self.assertTrue(cadence(a,120)['pass_']);self.assertAlmostEqual(cadence(a,120)['fps'],120)
        self.assertFalse(cadence(frames(60),120)['pass_'])
    def test_continuity(self):
        a=frames();del a[100];self.assertIn('missing/duplicate frame',cadence(a,120)['reasons'])
        a=frames();a[100]['sampleEntryWall']=a[99]['sampleEntryWall'];self.assertFalse(cadence(a,120).get('pass_',False))
        a=frames();
        for r in a[100:]:r['sampleEntryWall']+=.1
        self.assertIn('frame exceeds two periods',cadence(a,120)['reasons'])
    def test_config_identity(self):
        for k,v in [('source','other'),('reset',1),('focus',False),('dilation',.5),('fixed',True)]:
            a=frames();a[500][k]=v;self.assertFalse(cadence(a,120).get('pass_',False),k)
        a=frames();a[500]['cvars']['r.VSync']=1;self.assertFalse(cadence(a,120)['pass_'])
    def test_percentiles_interpolation(self):
        self.assertEqual(percentile([4,1,3,2],.5),2.5);self.assertAlmostEqual(percentile([1,2,3,4],.95),3.85)
        a=frames(n=1300);x=interpolate(a,.003);y=interpolate(a,10.003)
        self.assertAlmostEqual(y['position'][0]-x['position'][0],5000);self.assertAlmostEqual(y['wall']-x['wall'],10)
    def test_hit_integrity(self):
        hs=[dict(source='P',sourceLife=1,action=i+1,target='T',targetLife=2,damage=d,crit=False,absorbed=0,defense=0,hpBefore=h,hpAfter=h-d) for i,(d,h) in enumerate([(60,600),(70,540),(90,470)])]
        check=lambda h:hit_checks(h,'P',1,'T',2,[1,2,3],600,380)
        self.assertEqual(check(hs),[])
        for k,v in [('action',1),('sourceLife',2),('targetLife',3),('crit',True),('hpBefore',550)]:
            h=copy.deepcopy(hs);h[1][k]=v;self.assertTrue(check(h),k)
        self.assertTrue(check(hs+[hs[0]]))

if __name__=='__main__':unittest.main(verbosity=2)
