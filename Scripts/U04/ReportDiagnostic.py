"""Author a separate diagnostic handoff, without changing B reports or assertions."""
import csv,hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2];isolation=root.parent;runs=isolation/'Runs';docs=root/'Docs/U04/Diagnostics'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[]
for folder in ['Input-30-20261118','Input-30-R2-20261118']:
    inputs.extend(read(runs/folder/'Diagnostic/ANALYSIS.json')['windows'])
timing=read(runs/'Neutral-120-20261118/Diagnostic/ANALYSIS.json')['windows']
assert len(inputs)==12 and len(timing)==9
same=[w for w in inputs if w['result']['sameInputFrame']];prior=[w for w in inputs if w['result']['observedPreviousFrameHeld']]
assert len(same)==8 and len(prior)==4
assert all(w['result']['directionTransportMatches'] for w in inputs)
assert all(not w['result']['engineHeldAtLookup'] and w['result']['sent']==[0,0] and w['result']['stationaryAdmission'] for w in same)
assert all(w['result']['engineHeldAtLookup'] and w['result']['sent']==[1,0] and not w['result']['stationaryAdmission'] for w in prior)
assert all(w['result']['gateAllowsAtLookup'] and w['result']['observedAtLookup'] for w in inputs)
auto=read(runs/'Automation-Final-20261118/NAME-RESULTS.json');assert auto['completed'] and len(auto['results'])==140
old=read(runs/'Final-Integrity-20261118/OLD-PRESERVATION.json');new=read(runs/'Final-Integrity-20261118/DIAGNOSTIC-BINARY.json');editor=read(runs/'Final-Integrity-20261118/EDITOR-FINAL.json')
assert old['completed'] and new['completed'] and editor['completed']
build=read(runs/'Build-R3-20261118/BUILD-IDENTITY.json');source=build['sourceSHA']
result=dict(status='DIAGNOSTIC_ONLY',acceptance=False,baselineB='3f1867ec41768cc836a198c8d865df6de6990c18',
            sourceSHA=source,toolCommit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            gameSHA256=build['gameSHA256'],moduleSHA256=build['moduleSHA256'],inputs=inputs,timing=timing,
            baselineLabelsUnchanged=True,baselineRecomputed=38,baselineSealAssociations=391,oldPreservationChecks=len(old['checks']),
            finalAutomation=140,originalEditorPreserved=True,mechanism='same-frame observed/gated W differs from engine-latched held state; zero sent direction is preserved through authority and takes existing backward fallback',
            limits=['No runtime policy changed. Original B remains INCOMPLETE and its FAIL/INVALID labels are unchanged.',
                    'Previous-frame-held repros have nonzero admission velocity and do not satisfy stationary dodge acceptance.',
                    'Neutral capture controls do not reproduce combo workload and cannot retroactively qualify old combo120 trials.',
                    'No new acceptance batch or threshold/sampling-point change is authorized by this report.'])
out=isolation/'DIAGNOSTIC-GATES.json';assert not out.exists();out.write_text(json.dumps(result,indent=2),encoding='utf-8')
(docs/'INPUT-CAPTURE-RESULTS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
inputrows=[]
for w in inputs:
    r=w['result'];inputrows.append(dict(trial=w['trial'],sameFrame=r['sameInputFrame'],engineHeld=r['engineHeldAtLookup'],observed=r['observedAtLookup'],osHeld=r['osHeldAtLookup'],gateAllows=r['gateAllowsAtLookup'],sentX=r['sent'][0],sentY=r['sent'][1],receivedX=r['receivedDirection'][0],receivedY=r['receivedDirection'][1],modelX=r['modelDirection'][0],admissionCmPerSec=r['admissionSpeed'],previousHeldObserved=r['observedPreviousFrameHeld'],rawSHA256=w['rawSHA256'],raw=w['raw']))
timerows=[]
for w in timing:
    r=w['result'];row=dict(trial=w['trial'],mode=w['mode'],rawSHA256=w['rawSHA256'],raw=w['raw'])
    for point in ['begin','worldBegin','entry','oldWall']:
        for k,v in r[point].items():row[point+'_'+k]=v
    row['collectorP95ms']=r['collectorCostSeconds']['p95']*1000;timerows.append(row)
for name,rows in [('INPUT-REPRO.csv',inputrows),('TIMING-CONTROLS.csv',timerows)]:
    with (docs/name).open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
lines=['# B input/capture diagnostic — no gameplay change','',
       '**DIAGNOSTIC_ONLY. B remains INCOMPLETE, not READY_FOR_REVIEW; no closure or merge.** This follow-up confirms an input-state ordering mechanism and capture/sampling-phase sensitivity. It does not change old B labels, prove a combo defect, or approve a new acceptance batch.','',
       f'Parent B is3f1867ec41768cc836a198c8d865df6de6990c18; main18804bfa32b14471df1ffa4bd7aeaed6cd80074c. Separate branch `u04/b-input-capture-diagnostic`; clone `Artifacts/U04/B-Diagnostic/Source`, runs `Artifacts/U04/B-Diagnostic/Runs`. Built source **{source}**; Game SHA256 `{build["gameSHA256"]}`, Editor module `{build["moduleSHA256"]}`. Full committed Editor/Game/three-map Windows package, UE5.8.4 CL58902052, actual MSVC14.51.36260/SDK10.0.26100.0. Cold processes and actual binary/module/creation identities are retained. No Live Coding acceptance. New plain header APIs were fully rebuilt/reloaded; no new reflected/RPC/property layout.','',
       '## Input trace and observed mechanism','',
       'Source trace: physical Slate preprocessor -> ObservePhysicalKey updates ObservedKeys/release gate -> product direction queries IsInputKeyDown -> PlayerInput::IsPressed reads FKeyState.bDown -> SubmitCombatIntent -> ReceiveIntent -> queued authority SubmitBatch -> AdmitDodge. Engine ProcessNonAxesKeys updates bDown from accumulated key events during ProcessInputStack. Zero local direction takes the existing backward-relative-to-aim fallback. Original B raw lacks exact held-state and sent/received direction, so its two accepted edges alone did not establish direction preparation. [Static audit](Evidence/Review-20261118/Runs/Static-Audit-20261118/AUDIT.json.gz) and frozen raw audit preserve that inference limit.','',
       'Opt-in observer records actual key-edge order/frame, separately engine-held/observed/OS states, release-gate pressed/allowed, exact direction already calculated by product code, received direction, pre-batch admission velocity and model direction. It never changes those values or action flow. Samples/events buffer until explicit end outside the window. All inputs are guarded Windows events.','',
       'Fixed inventory completed:4 legacy consecutive W/Shift,4 single-SendInput-batch W/Shift,4 previous-frame-held repros. In all8 same-input-frame cases, observed W and gate allow are true but engine-held W at lookup is false. Product sends(0,0), authority receives(0,0), admission speed is0, and the unchanged model selects−X. All4 previous-frame cases have raw post-actor W-held evidence before the Shift frame; they send/receive(1,0) and select+X, but admission speed is204.8–273.067 cm/s. No transport-direction mismatch occurs.','',
       '**Conclusion:** these repros establish why consecutive accepted edges do not establish a forward command under the current latched-state lookup. They do not decide whether the product contract should support same-frame physical direction. Preparing W through a previous movement frame resolves direction but fails the stationary admission requirement in these repros. This is a specification/input-semantics decision before any separate gameplay fix. The original fps30-forward-1 FAIL remains unchanged.','',
       '| Repro | Same input frame | Engine W at lookup | Sent / received X | Model X | Admission cm/s | Prior frame W observed |','|---|---|---|---|---:|---:|---|']
for r in inputrows:lines.append(f'|{r["trial"]}|{r["sameFrame"]}|{r["engineHeld"]}|{r["sentX"]} / {r["receivedX"]}|{r["modelX"]:+.0f}|{r["admissionCmPerSec"]:.3f}|{r["previousHeldObserved"]}|')
lines += ['', '## Capture and timestamp controls','',
          'No new combo attacks were run. Existing38 B assertion results recompute unchanged; all7 old combo120 gameplay results remain correct and only3 qualify by the original frame cadence gate. No world-time delta or new clock is substituted into those old verdicts.','',
          'Neutral120 control uses the same rendered lab/pawn/profile and a stationary dummy, no actions/hits, three15-world-second windows per mode in a fixed Latin square. Passive=50ms focus guard/no video; poll=5ms guard/no video; video=5ms guard plus the original ImageGrab/numpy/cvtColor/30FPS VideoWriter pipeline. Mode settling and flush occur outside selected frames; all native frame intervals inside the same declared world bounds are retained. Exact selected wall spans/counts and P50/P95/P99/max are in [CSV](TIMING-CONTROLS.csv) and raw analysis.','',
          'Four real monotonic game-thread points share the same frame counter: Core OnBeginFrame **before** engine rate limiting; UWorld::Tick start **after** rate limiting/before actors; post-actor collector entry; old wall at collector end. Frame alignment, counter continuity, focus, viewport/cvars, dilation1 and disabled fixed-time/frame flags are checked. These are game-thread phase intervals, not GPU/presentation/scanout. No renderer, input, smoothing, timestep or threshold was changed.','',
          '| Window | Core in-band % | World-start % | Collector-entry % | Old wall % | Old-wall FPS | Collector P95 ms |','|---|---:|---:|---:|---:|---:|---:|']
for row in timerows:lines.append(f'|{row["trial"]}|{row["begin_within10Percent"]*100:.2f}|{row["worldBegin_within10Percent"]*100:.2f}|{row["entry_within10Percent"]*100:.2f}|{row["oldWall_within10Percent"]*100:.2f}|{row["oldWall_fps"]:.4f}|{row["collectorP95ms"]:.4f}|')
lines += ['', 'Observed old-wall in-band fraction is99.22–100% without video and88.55–94.33% with video, while all nine world-start series are100%. Core-before-limiter and post-actor phases also show different distributions. This supports capture/phase sensitivity on this neutral workload; it is not evidence that old combo windows would pass without capture or that a particular alternative point should be accepted. New instrumentation adds overhead, the scene is idle, and three repeats per mode are descriptive controls, not a full performance study.','',
          'The old sampler creates a Base wall timestamp but overwrites it in Event after collection. New data records entry/exit separately. Algebra: endInterval = entryInterval + collectorCost[current] − collectorCost[previous]. The residual is retained and synthetic tests verify this identity. That exposes possible observer-point jitter; old raw contains no entry/exit clocks, so no retroactive correction or relabeling is justified.','',
          '## Verification, retained errors and preservation','',
          'Final-source cold MCP Automation140/140 Success, exact expected/discovered/executed names, actual loaded diagnostic DLL verified. Four synthetic diagnostic method groups pass before capture. Frozen B seal391 associations rehashed, all38 old decisions recomputed unchanged, historical/original4392 hashes verified again, and new package/module/engine checks pass. Original Editor PID10880 retains creation2026-11-18T04:17:19.8968150Z and normal rectangles/show state; no save/close/restart. All diagnostic Editor/game processes are closed. All native input/lookup/model/trajectory/damage rules remain unchanged; source diff contains read-only getters/observers and timing hooks only.','',
          'Initial diagnostic compile failed on auto-pointer deduction from TObjectPtr; explicit const APawn pointer fixed the observer before the selected full build. Both builds/logs remain. The first input session recorded two closed windows, then foreground guard aborted during the next setup before action/capture; cause of the transient HWND change is unknown. Its incomplete ledger and error remain. The new process resumed at fixed inventory offset2, retaining all12 recorded repros plus that failed setup, without selecting outcomes. First restore observation after500ms still saw one Editor window minimized; later observation-only verification confirms both initial show/rectangle states. The failed observation remains; helper now permits additional settling checks.','',
          '## Decisions before any new acceptance batch','',
          '1. Owner must define whether neutral same-frame W→Shift should use the physical event stream or a previously latched PlayerInput direction, and define stationary admission explicitly. If a product-input change is desired, review it separately; do not alter dodge motor/trajectory as a workaround.','2. Predeclare the exact game-thread frame phase and review a less intrusive/equivalent video capture method, while keeping the existing5%/95%/10%/two-period criteria, scene/profile and all failures. Do not select the100% phase after seeing this data as an automatic qualification.','3. Only after those method/contract decisions, authorize a fixed new batch if desired. Existing combo120 evidence remains insufficient; no new acceptance batch, U04-C/D, renderer optimization, adverse network, packaged Server, acceptance or merge was performed.','',
          'Published diagnostic manifest: `Docs/U04/Diagnostics/Evidence/Review-20261118/MANIFEST.json`. Original B report/manifest/packages are untouched. The separate branch is committed/pushed with remote attestation outside the immutable seal. Raw data and videos are diagnostic evidence only.']
(docs/'REPORT-INPUT-CAPTURE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
contract=docs/'INPUT-CAPTURE-CONTRACT.md';contract.write_text(contract.read_text(encoding='utf-8').replace('Status: IN_PROGRESS, DIAGNOSTIC_ONLY.','Status: diagnostic execution complete, DIAGNOSTIC_ONLY; B remains INCOMPLETE.'),encoding='utf-8')
print(out)
