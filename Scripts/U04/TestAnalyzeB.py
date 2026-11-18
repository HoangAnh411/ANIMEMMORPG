"""Synthetic method verification only; never counts as binary gameplay evidence."""
import copy, unittest
from AnalyzeB import PROFILE,cadence,percentile,interpolate,hit_checks

def frames(fps=120,n=1201):
    return [dict(wall=i/fps,worldTime=i/fps,frame=i,pid=4,world='GameLab',pawn='P',source='sha',reset=0,
                 focus=True,fixed=False,useFixedFrameRate=False,dilation=1,width=1280,height=720,
                 cvars={**PROFILE,'t.MaxFPS':120},smoothing=False,fixedDelta=1/30,fixedFrameRate=30,
                 position=[500*i/fps,0,98]) for i in range(n)]

class Method(unittest.TestCase):
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
