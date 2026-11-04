"""Extract D evidence from fresh logs and a completed, PID-guarded package capture."""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--root',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
sha='715238443e33e1a2760ea3d89f4d1698f092e511'
tests=a.root/'MCPTests-20261104-144814'
lines=(tests/'Editor.log').read_text(encoding='utf-8-sig').splitlines()
success=[line for line in lines if 'Test Completed. Result={Success}' in line]
assert len(success)==14 and any('14 tests performed' in line for line in lines)
assert not any('Test Completed. Result={Fail}' in line for line in lines)
measurements=[line for line in lines if 'U01D_MEASURE ' in line]
assert len(measurements)==5 and all('sourceSHA='+sha in line for line in measurements)
capture=a.root/'PlayCaptureFinal'
meta=json.loads((capture/'Run1/process.json').read_text())
assert meta['completed'] and meta['pid']==22692
def utc(text):return datetime.fromisoformat(text.replace('Z','+00:00'))
start=utc(meta['utc'])
end=start+timedelta(seconds=meta['wallSeconds']+1)
samples=[]
for line in (capture/'Game.log').read_text(encoding='utf-8-sig').splitlines():
    if 'Metrics {' not in line:continue
    sample=json.loads(line.split('Metrics ',1)[1])
    if start<=utc(sample['utc'])<=end:samples.append(sample)
assert samples
for s in samples:
    assert s['pid']==meta['pid'] and s['sourceSHA']==sha
    assert s['worldType']==1 and s['netMode']==0 and s['locallyControlled']
    assert s['owner']==s['controller'] and '/Animation/ABP_U01.' in s['animClass']
    assert s['rootMotionMode']==1
phases=sorted({s['animationPoseIndex'] for s in samples})
assert phases==[0,1,2,3,4],phases
def event(action,key):
    return next(e for e in meta['events'] if e['action']==action and e.get('key')==key)
def speeds(t0,t1):
    return [s['animationGroundSpeedCmPerSec'] for s in samples if t0<utc(s['utc'])<t1]
walk=speeds(utc(event('down','W')['utc'])+timedelta(seconds=.8),utc(event('down','Ctrl')['utc'])-timedelta(seconds=.1))
sprint=speeds(utc(event('down','Ctrl')['utc'])+timedelta(seconds=.8),utc(event('up','Ctrl')['utc'])-timedelta(seconds=.1))
assert walk and sprint and all(abs(v-500)<1 for v in walk) and all(abs(v-700)<1 for v in sprint)
ledge=[s for s in samples if utc(s['utc'])>start+timedelta(seconds=19)]
assert any(s['animationPoseIndex']==3 and s['animationVerticalSpeedCmPerSec']<0 for s in ledge)
assert any(s['animationPoseIndex']==4 for s in ledge)
assert not any(s['animationPoseIndex']==2 for s in ledge)
summary={'sourceSHA':sha,'testProcess':json.loads((tests/'process.json').read_text(encoding='utf-8-sig')),
         'tests':success,'physicsMeasurements':measurements,'capture':meta,
         'captureSummary':{'samples':len(samples),'poseIndicesSeen':phases,'stableWalkCmPerSec':[min(walk),max(walk)],
                           'stableSprintCmPerSec':[min(sprint),max(sprint)],'ledgeFallWithoutJumpThenLand':True,
                           'visualFootSliding':'PENDING reviewer assessment of video; bone cycles/calibration do not prove visual quality',
                           'renderFPS':'NOT MEASURED; 10 Hz video capture is not game FPS'},
         'packageSamples':samples}
a.out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary['captureSummary'],ensure_ascii=False))
