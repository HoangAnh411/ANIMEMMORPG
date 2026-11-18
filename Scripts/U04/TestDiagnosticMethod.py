import copy,unittest
from AnalyzeDiagnostic import input_result,stats,timing_result
from AnalyzeB import PROFILE

def keys(held):return {'keys':[dict(binding='W',engineHeld=held,observedPhysical=True,osHeld=True,gateAllows=True)]}
def sample_input(previous=False):
    frames=[dict(kind='frame',frame=i,worldTime=i/30,velocity=[128 if previous else 0,0,0],input=keys(previous)) for i in [8,9,10,11]]
    edges=[dict(kind='PhysicalEdge',key=k,down=d,frame=f,diagnosticSerial=n,wall=100+n/1000) for n,(k,d,f) in enumerate([('W',True,8 if previous else 10),('LeftShift',True,10),('W',False,11),('LeftShift',False,11)])]
    x=1 if previous else 0
    intent=dict(kind='IntentDirection',commandType=1,command=1,frame=10,sentX=x,sentY=0,**keys(previous))
    received=dict(kind='Received',command=1,intentX=x,intentY=0)
    admission=dict(kind='AuthorityAdmission',command=1,velocityBeforeBatch='X=128 Y=0 Z=0' if previous else 'X=0 Y=0 Z=0',modelDirection='X=1 Y=0 Z=0' if previous else 'X=-1 Y=0 Z=0')
    end=dict(kind='dodgeCommit',trajectoryEnd=True,position=[300 if previous else -300,0,98],combat={'dodgeOrigin':'X=0 Y=0 Z=98'})
    return frames+edges+[intent,received,admission,end]

class Method(unittest.TestCase):
    def test_empty_same_frame_is_not_inferred_from_accepted_edges(self):
        r=input_result(sample_input());self.assertTrue(r['sameInputFrame']);self.assertFalse(r['engineHeldAtLookup']);self.assertEqual(r['sent'],[0,0]);self.assertEqual(r['modelDirection'],[-1,0,0]);self.assertFalse(r['acceptance'])
    def test_previous_frame_and_admission_velocity_are_distinct_requirements(self):
        r=input_result(sample_input(True));self.assertTrue(r['observedPreviousFrameHeld']);self.assertEqual(r['sent'],[1,0]);self.assertFalse(r['stationaryAdmission']);self.assertEqual(r['admissionSpeed'],128)
    def test_fps_formula_and_nonmonotonic(self):
        self.assertEqual(stats([0,1/60,2/60])['fps'],60)
        with self.assertRaises(ValueError):stats([0,0,1])
    def test_timestamp_cost_identity(self):
        rows=[]
        for i in range(2161):
            entry=100+i/120;cost=.0002+(i%2)*.001
            rows.append(dict(kind='frame',frame=i,frameBeginCounter=i,worldBeginCounter=i,frameBeginWall=entry-.002,worldBeginWall=entry-.001,sampleEntryWall=entry,wall=entry+cost,worldTime=i/120,focus=True,dilation=1,fixed=False,useFixedFrameRate=False,cvars={**PROFILE,'t.MaxFPS':120},combat={'action':0},hits=[],width=1280,height=720,source='sha',pid=1,world='Lab',pawn='P',reset=0))
        r=timing_result(rows);self.assertLess(r['costDifferenceIdentityMaxResidual'],1e-12);self.assertEqual(r['entry']['within10Percent'],1);self.assertLess(r['oldWall']['within10Percent'],.95);self.assertFalse(r['acceptance'])
        rows[400]['frameBeginCounter']+=1
        with self.assertRaises(AssertionError):timing_result(rows)

if __name__=='__main__':unittest.main(verbosity=2)
