"""Synthetic method verification only; never counts as binary gameplay evidence."""
import copy, unittest
from AnalyzeB import PROFILE,cadence,percentile,interpolate,hit_checks,combo,dodge,movement

def frames(fps=120,n=1201):
    return [dict(wall=i/fps,worldTime=i/fps,frame=i,pid=4,world='GameLab',pawn='P',source='sha',reset=0,
                 focus=True,fixed=False,useFixedFrameRate=False,dilation=1,width=1280,height=720,
                 cvars={**PROFILE,'t.MaxFPS':120},smoothing=False,fixedDelta=1/30,fixedFrameRate=30,
                 position=[500*i/fps,0,98]) for i in range(n)]

class Method(unittest.TestCase):
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
        receives=[dict(kind='Received',commandType=6,command=i+1) for i in range(3)]
        admissions=[dict(kind='Admitted',detail=f'command={i+1}',gameplaySeconds=t) for i,t in enumerate([.5,.82,1.27])]
        completed=[dict(kind='ActionCompleted',at=e,natural=True) for e in ends]
        raw=actions+receives+admissions+completed
        self.assertTrue(combo(raw,rows)['pass_'])
        completed[-1]['at']+=.000002;self.assertFalse(combo(raw,rows)['pass_']);completed[-1]['at']-=.000002
        admissions[1]['gameplaySeconds']=.7
        with self.assertRaisesRegex(ValueError,'outside buffer'):combo(raw,rows)
    def test_dodge_commit_position(self):
        rows=frames(n=160);c=dict(dodgeStart=.5,dodgeMotionEnd=.75,dodgeLockEnd=.85,dodgeOrigin='X=0 Y=0 Z=98',dodgeDirection='X=1 Y=0 Z=0')
        for r in rows:r.update(mode=1,velocity=[0,0,0],combat=c)
        commit=dict(kind='dodgeCommit',trajectoryEnd=True,position=[300,0,98],combat=c)
        self.assertTrue(dodge([commit],rows,'forward')['pass_'])
        commit['position'][0]=294.9;self.assertFalse(dodge([commit],rows,'forward')['pass_'])
    def test_cadence_and_cap(self):
        a=frames();self.assertTrue(cadence(a,120)['pass_']);self.assertAlmostEqual(cadence(a,120)['fps'],120)
        self.assertFalse(cadence(frames(60),120)['pass_'])
    def test_continuity(self):
        a=frames();del a[100];self.assertIn('missing/duplicate frame',cadence(a,120)['reasons'])
        a=frames();a[100]['wall']=a[99]['wall'];self.assertFalse(cadence(a,120).get('pass_',False))
        a=frames();
        for r in a[100:]:r['wall']+=.1
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
