"""Synthetic method verification only; never counts as binary gameplay evidence."""
import copy, unittest, tempfile, json
from pathlib import Path
from AnalyzeR1 import PROFILE,cadence,percentile,interpolate,hit_checks,combo,dodge,movement,analyze

def frames(fps=120,n=1201):
    return [dict(wall=i/fps,sampleEntryWall=i/fps,worldTime=i/fps,frame=i,pid=4,world='GameLab',pawn='P',source='sha',reset=0,
                 focus=True,fixed=False,useFixedFrameRate=False,dilation=1,width=1280,height=720,
                 cvars={**PROFILE,'t.MaxFPS':120},smoothing=False,fixedDelta=1/30,fixedFrameRate=30,
                 position=[500*i/fps,0,98]) for i in range(n)]

class Method(unittest.TestCase):
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
        rows=frames(n=160);c=dict(dodgeStart=.5,dodgeMotionEnd=.75,dodgeLockEnd=.85,dodgeOrigin='X=0 Y=0 Z=98',dodgeDirection='X=1 Y=0 Z=0')
        for r in rows:r.update(mode=1,velocity=[0,0,0],combat=c)
        commit=dict(kind='dodgeCommit',trajectoryEnd=True,position=[300,0,98],combat=c)
        receipt=dict(kind='Received',commandType=1,command=4,receive=.48,receivedPosition='X=0 Y=0 Z=98')
        self.assertTrue(dodge([receipt,commit],rows,'forward')['pass_'])
        self.assertEqual(dodge([receipt,commit],rows,'forward')['firstFrame'],57)
        receipt['receivedPosition']='X=12 Y=0 Z=98'
        self.assertFalse(dodge([receipt,commit],rows,'forward')['pass_'])
        receipt['receivedPosition']='X=0 Y=0 Z=98'
        commit['position'][0]=294.9;self.assertFalse(dodge([receipt,commit],rows,'forward')['pass_'])
        with self.assertRaisesRegex(ValueError,'authority dodge receipt'):dodge([commit],rows,'forward')
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
