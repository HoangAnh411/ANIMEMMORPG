"""Read the frozen B repro and all seven existing combo120 windows without relabeling."""
import argparse,hashlib,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--baseline',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();assert not a.out.exists()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=a.baseline.resolve();fail=read(base/'Runs/FPS30-R2-20261118/Capture/fps30-forward-1/ASSERTIONS.json');rawfile=base/'Runs/FPS30-R2-20261118/Raw/fps30-forward-1.jsonl'
assert sha(rawfile)==fail['rawSHA256'];raw=[json.loads(x) for x in rawfile.read_text(encoding='utf-8-sig').splitlines()]
events=[r for r in raw if r['kind'] not in ('frame','dodgeCommit')]
physical=[line for line in (base/'Runs/FPS30-R2-20261118/Game.log').read_text(encoding='utf-8-sig').splitlines() if '04.42.13:' in line and ('Display: PhysicalPress key=' in line or 'Display: PhysicalRelease/Rearm key=' in line)]
combo=[]
for i in range(1,8):
    name=f'fps120-combo-{i}';original=read(base/'Runs/FPS120-20261118/Capture'/name/'ASSERTIONS.json');f=base/'Runs/FPS120-20261118/Raw'/(name+'.jsonl');assert sha(f)==original['rawSHA256']
    rows=[json.loads(x) for x in f.read_text(encoding='utf-8-sig').splitlines() if json.loads(x)['kind']=='frame'];g=original['gameplay'];selected=[r for r in rows if g['firstFrame']<=r['frame']<=g['lastFrame']]
    residual=[((b['wall']-a['wall'])-(b['worldTime']-a['worldTime']))*1000 for a,b in zip(selected,selected[1:])]
    combo.append(dict(trial=name,originalStatus=original['status'],gameplay=bool(g['pass_']),oldCadence=original['cadence'],rawSHA256=sha(f),
                      wallMinusWorldIntervalMs=dict(min=min(residual),max=max(residual)),
                      note='World-time deltas are diagnostic comparison only, not replacement rendered-frame evidence; original labels retained.'))
engine=Path('D:/Software/UE_5.8/Engine/Source/Runtime')
files=[engine/'Engine/Private/PlayerController.cpp',engine/'Engine/Private/UserInterface/PlayerInput.cpp',engine/'Engine/Private/UnrealEngine.cpp',engine/'Launch/Private/LaunchEngineLoop.cpp']
out=dict(status='DIAGNOSTIC_ONLY',acceptance=False,baselineB='3f1867ec41768cc836a198c8d865df6de6990c18',failLabelRetained=fail['status'],originalRawSHA256=sha(rawfile),
         physicalLog=physical,rawEvents=events,originalInputEmission=fail['inputEvents'],originalDodge=fail['gameplay'],
         missingOriginalFields=['product engine-held key state at direction lookup','release-gate pressed state at lookup','sent local direction','authority received direction','pre-batch admission velocity'],
         flow=['FU01PhysicalObserver::HandleKeyDownEvent -> ObservePhysicalKey (before UMG/EnhancedInput)',
               'ObservedKeys.Add; ReleaseGate.Down; product direction reads IsInputKeyDown && ReleaseGate.Allows',
               'APlayerController::IsInputKeyDown -> UPlayerInput::IsPressed -> FKeyState.bDown',
               'UPlayerInput::ProcessNonAxesKeys updates bDown from accumulated press/release event counts during ProcessInputStack',
               'SubmitCombatIntent -> ReceiveIntent queued with direction -> ProcessQueuedIntents -> FTimelineModel::SubmitBatch -> AdmitDodge',
               'AdmitDodge normalizes local direction; zero chooses backward relative to aim'],
         originalInferenceLimit='Accepted edges do not identify the actual held-key lookup or sent direction. No retroactive harness/runtime classification.',
         originalSampler='Base creates a wall timestamp, then Event overwrites wall after Sample collection; only the later stamp is retained in old raw data.',
         combo120=combo,engineSource=[dict(path=str(f),sha256=sha(f)) for f in files])
a.out.write_text(json.dumps(out,indent=2),encoding='utf-8');print(a.out)
