# B input/capture diagnostic — no gameplay change

**DIAGNOSTIC_ONLY. B remains INCOMPLETE, not READY_FOR_REVIEW; no closure or merge.** This follow-up confirms an input-state ordering mechanism and capture/sampling-phase sensitivity. It does not change old B labels, prove a combo defect, or approve a new acceptance batch.

Parent B is3f1867ec41768cc836a198c8d865df6de6990c18; main18804bfa32b14471df1ffa4bd7aeaed6cd80074c. Separate branch `u04/b-input-capture-diagnostic`; clone `Artifacts/U04/B-Diagnostic/Source`, runs `Artifacts/U04/B-Diagnostic/Runs`. Built source **735923c912244dd04fddf1a35d415c96e537410c**; Game SHA256 `4d09c7523b6e9799e7dd3660b9add49ec9086f86ad7518394022f257fb614954`, Editor module `fb64a6db549eb48b533e03865e3e6855fd2c3c3d78e5e90a2309721a8d6d3f23`. Full committed Editor/Game/three-map Windows package, UE5.8.4 CL58902052, actual MSVC14.51.36260/SDK10.0.26100.0. Cold processes and actual binary/module/creation identities are retained. No Live Coding acceptance. New plain header APIs were fully rebuilt/reloaded; no new reflected/RPC/property layout.

## Input trace and observed mechanism

Source trace: physical Slate preprocessor -> ObservePhysicalKey updates ObservedKeys/release gate -> product direction queries IsInputKeyDown -> PlayerInput::IsPressed reads FKeyState.bDown -> SubmitCombatIntent -> ReceiveIntent -> queued authority SubmitBatch -> AdmitDodge. Engine ProcessNonAxesKeys updates bDown from accumulated key events during ProcessInputStack. Zero local direction takes the existing backward-relative-to-aim fallback. Original B raw lacks exact held-state and sent/received direction, so its two accepted edges alone did not establish direction preparation. [Static audit](Evidence/Review-20261118/Runs/Static-Audit-20261118/AUDIT.json.gz) and frozen raw audit preserve that inference limit.

Opt-in observer records actual key-edge order/frame, separately engine-held/observed/OS states, release-gate pressed/allowed, exact direction already calculated by product code, received direction, pre-batch admission velocity and model direction. It never changes those values or action flow. Samples/events buffer until explicit end outside the window. All inputs are guarded Windows events.

Fixed inventory completed:4 legacy consecutive W/Shift,4 single-SendInput-batch W/Shift,4 previous-frame-held repros. In all8 same-input-frame cases, observed W and gate allow are true but engine-held W at lookup is false. Product sends(0,0), authority receives(0,0), admission speed is0, and the unchanged model selects−X. All4 previous-frame cases have raw post-actor W-held evidence before the Shift frame; they send/receive(1,0) and select+X, but admission speed is204.8–273.067 cm/s. No transport-direction mismatch occurs.

**Conclusion:** these repros establish why consecutive accepted edges do not establish a forward command under the current latched-state lookup. They do not decide whether the product contract should support same-frame physical direction. Preparing W through a previous movement frame resolves direction but fails the stationary admission requirement in these repros. This is a specification/input-semantics decision before any separate gameplay fix. The original fps30-forward-1 FAIL remains unchanged.

| Repro | Same input frame | Engine W at lookup | Sent / received X | Model X | Admission cm/s | Prior frame W observed |
|---|---|---|---|---:|---:|---|
|legacy-1|True|False|0 / 0|-1|0.000|False|
|batch-1|True|False|0 / 0|-1|0.000|False|
|previous-1|False|True|1 / 1|+1|273.067|True|
|legacy-2|True|False|0 / 0|-1|0.000|False|
|batch-2|True|False|0 / 0|-1|0.000|False|
|previous-2|False|True|1 / 1|+1|204.800|True|
|legacy-3|True|False|0 / 0|-1|0.000|False|
|batch-3|True|False|0 / 0|-1|0.000|False|
|previous-3|False|True|1 / 1|+1|204.800|True|
|legacy-4|True|False|0 / 0|-1|0.000|False|
|batch-4|True|False|0 / 0|-1|0.000|False|
|previous-4|False|True|1 / 1|+1|204.800|True|

## Capture and timestamp controls

No new combo attacks were run. Existing38 B assertion results recompute unchanged; all7 old combo120 gameplay results remain correct and only3 qualify by the original frame cadence gate. No world-time delta or new clock is substituted into those old verdicts.

Neutral120 control uses the same rendered lab/pawn/profile and a stationary dummy, no actions/hits, three15-world-second windows per mode in a fixed Latin square. Passive=50ms focus guard/no video; poll=5ms guard/no video; video=5ms guard plus the original ImageGrab/numpy/cvtColor/30FPS VideoWriter pipeline. Mode settling and flush occur outside selected frames; all native frame intervals inside the same declared world bounds are retained. Exact selected wall spans/counts and P50/P95/P99/max are in [CSV](TIMING-CONTROLS.csv) and raw analysis.

Four real monotonic game-thread points share the same frame counter: Core OnBeginFrame **before** engine rate limiting; UWorld::Tick start **after** rate limiting/before actors; post-actor collector entry; old wall at collector end. Frame alignment, counter continuity, focus, viewport/cvars, dilation1 and disabled fixed-time/frame flags are checked. These are game-thread phase intervals, not GPU/presentation/scanout. No renderer, input, smoothing, timestep or threshold was changed.

| Window | Core in-band % | World-start % | Collector-entry % | Old wall % | Old-wall FPS | Collector P95 ms |
|---|---:|---:|---:|---:|---:|---:|
|passive-1|99.17|100.00|99.89|100.00|119.9940|0.1627|
|poll-2|99.22|100.00|99.89|99.89|119.9935|0.1641|
|video-3|85.10|100.00|94.39|93.94|119.9899|0.2278|
|video-4|85.71|100.00|94.27|94.33|119.9865|0.2164|
|passive-5|99.17|100.00|99.72|99.83|119.9954|0.1657|
|poll-6|98.83|100.00|99.61|99.56|119.9923|0.1721|
|poll-7|98.50|100.00|99.39|99.50|119.9939|0.1766|
|video-8|81.77|100.00|88.72|88.55|119.9773|0.2824|
|passive-9|98.22|100.00|99.22|99.22|119.9901|0.1821|

Observed old-wall in-band fraction is99.22–100% without video and88.55–94.33% with video, while all nine world-start series are100%. Core-before-limiter and post-actor phases also show different distributions. This supports capture/phase sensitivity on this neutral workload; it is not evidence that old combo windows would pass without capture or that a particular alternative point should be accepted. New instrumentation adds overhead, the scene is idle, and three repeats per mode are descriptive controls, not a full performance study.

The old sampler creates a Base wall timestamp but overwrites it in Event after collection. New data records entry/exit separately. Algebra: endInterval = entryInterval + collectorCost[current] − collectorCost[previous]. The residual is retained and synthetic tests verify this identity. That exposes possible observer-point jitter; old raw contains no entry/exit clocks, so no retroactive correction or relabeling is justified.

## Verification, retained errors and preservation

Final-source cold MCP Automation140/140 Success, exact expected/discovered/executed names, actual loaded diagnostic DLL verified. Four synthetic diagnostic method groups pass before capture. Frozen B seal391 associations rehashed, all38 old decisions recomputed unchanged, historical/original4392 hashes verified again, and new package/module/engine checks pass. Original Editor PID10880 retains creation2026-11-18T04:17:19.8968150Z and normal rectangles/show state; no save/close/restart. All diagnostic Editor/game processes are closed. All native input/lookup/model/trajectory/damage rules remain unchanged; source diff contains read-only getters/observers and timing hooks only.

Initial diagnostic compile failed on auto-pointer deduction from TObjectPtr; explicit const APawn pointer fixed the observer before the selected full build. Both builds/logs remain. The first input session recorded two closed windows, then foreground guard aborted during the next setup before action/capture; cause of the transient HWND change is unknown. Its incomplete ledger and error remain. The new process resumed at fixed inventory offset2, retaining all12 recorded repros plus that failed setup, without selecting outcomes. First restore observation after500ms still saw one Editor window minimized; later observation-only verification confirms both initial show/rectangle states. The failed observation remains; helper now permits additional settling checks.

## Decisions before any new acceptance batch

1. Owner must define whether neutral same-frame W→Shift should use the physical event stream or a previously latched PlayerInput direction, and define stationary admission explicitly. If a product-input change is desired, review it separately; do not alter dodge motor/trajectory as a workaround.
2. Predeclare the exact game-thread frame phase and review a less intrusive/equivalent video capture method, while keeping the existing5%/95%/10%/two-period criteria, scene/profile and all failures. Do not select the100% phase after seeing this data as an automatic qualification.
3. Only after those method/contract decisions, authorize a fixed new batch if desired. Existing combo120 evidence remains insufficient; no new acceptance batch, U04-C/D, renderer optimization, adverse network, packaged Server, acceptance or merge was performed.

Published diagnostic manifest: `Docs/U04/Diagnostics/Evidence/Review-20261118/MANIFEST.json`. Original B report/manifest/packages are untouched. The separate branch is committed/pushed with remote attestation outside the immutable seal. Raw data and videos are diagnostic evidence only.
