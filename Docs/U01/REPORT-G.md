# U01-G — Integration verification (in progress)

Source: 5f8a6eabe103a8b31a894c82f32cffb0325474a9, cloned from accepted main into Artifacts/U01/G/Source. Branch: u01/g-integration. G is not accepted or merged.

F closure: accepted 2bd9b56; acceptance records committed/pushed at 5f8a6ea and fast-forwarded into main. Dedicated Editor server scope only; clients 60 FPS/server 30 FPS remains the network review profile.

## Completed evidence

- Fresh Editor/Game full build: PASS, Build-20261105-152800-078-73c759e0.
- Cold MCP TestRunner Automation: 23/23 Success, MCPTests-20261105-153131. U00 Foundation 4, B 2, C 5, D 6, E 4, F 2.
- Windows package: PASS, Package-20261105-153201-862-38caf5d5/Archive/Windows.
- Three-map packaged smoke: 3/3 PASS, SmokeB-20261105-153552.
- Real-input packaged rebind, locks, persistence and lifecycle recordings collected under Artifacts/U01/G/Play; detailed assertion review pending. Lifecycle first preflight failed because Boot has no U01 pawn observer; retained, corrected tool and recorded LifecycleRetry.

## Open checks

First long-play run stopped safely on unexpected foreground change after 534.429 seconds; completed=false. This does not satisfy the ten-minute gate. Evidence is preserved in Play/LongPlay/input.json and long-play-driver.log. A full uninterrupted retry is required.

Packaged 1920x1080, internal 100%, unchanged renderer/scalability 30/60/120 cap trials are running separately. No achieved FPS claim is made before analysis. Save-failure/corruption fixtures, new-source dedicated-network regression, evidence sealing and final review launcher remain pending.

Engine UE5.8.4 CL58902052; MSVC14.51.36260 (toolset14.51.36231), SDK10.0.26100.0. Known compiler preference/deprecation warnings remain in full logs. Original Editor PID2068 remains open; window restoration is required after measurements.

Motor, animation carry and product quality are unchanged. Anime art and combat remain DEFERRED. G status: IN_PROGRESS; no merge or U02 authorized.

## Completed long-session and FPS follow-up

The retry completed 600.233498 seconds (PID6424), with 263 actual input events, 3001 owned Game-world samples, ten focus-return events, and exactly one mapping context throughout. Samples include Playing/Menu/AwaitingResume; 40 samples record inactive game window. See Evidence/G/LONG-PLAY-SUMMARY.json and LONG-PLAY-INPUT.json. The interrupted 534-second attempt remains separate and is not counted as a completed session.

Packaged 1920x1080 fullscreen, internal100%, unchanged project renderer/scalability; 60 seconds per cap, all collected samples focused:

| Runtime cap | Actual average FPS | Frame median / p95 / p99 / max (ms) | Samples |
|---|---:|---|---:|
|30|29.9996|33.3334 / 33.3335 / 33.3381 / 33.4993|1800|
|60|59.9952|16.6667 / 16.6668 / 16.6740 / 19.1400|3600|
|120|89.5167|11.2177 / 12.6885 / 13.3929 / 17.6069|5371|

No >100ms frames in these three measured windows. Runtime cvars confirmed caps30/60/120 and r.ScreenPercentage100. Cap120 does not establish 120FPS: testing at sustained120FPS remains NOT VERIFIED. These are map/path-specific measurements with diagnostics, not a general product performance guarantee. FPS uses measured frame delta, not the requested cap; frame time includes limiting and is not GPU time.

All runtime evidence uses source5f8a6eabe103a8b31a894c82f32cffb0325474a9 and one unchanged package. Evidence/G/PACKAGE.csv indexes every package file with SHA256; MANIFEST.json records the executable and package-index hashes. No rebuild/test/smoke rerun was performed.

Editor observation update: original-project Editor now PID8676, created17:20:42 local; earlier PID2068 is no longer present. The agent did not close/restart the original Editor and leaves current PID8676 open. Do not claim a continuous PID lifetime or restore stale HWND records onto the new process.

## Additional packaged and network regression evidence

- Dedicated Editor server PID8880 + clients10540/10164: completed120seconds real input with split focus. Runtime caps30/60/60 confirmed; server localPlayers0, each client1; two pawns observed; sprint/airborne observed at all three processes; observed speed never exceeded700cm/s beyond floating-point noise. NETWORK-REGRESSION.json and Network-Phase videos retained. This session does not repeat every F reconnect/security case; accepted F history and the unchanged-source Automation remain their evidence.
- Save-failure fixture, retry and corrupt-file load: captured in this same package. Native metrics show save failure stays dirty, successful retry becomes clean, and corrupt-load feedback stays present without dirtying settings. Corrupt slot hash remained unchanged through load/Resume/Quit. Ten actual-input captures completed; CAPTURE-CHECKS.json records duration/Hz/PID, videos retained. Completion/identity checks do not alone assert every timed gameplay expectation.
- Motor package measurements (per-frame collector, interpolated10second stable windows): walk49.9948–50.0003m; sprint69.9944–69.9977m; apex121.748–121.935cm. All within C tolerances. MOTOR-FPS.json records each cap; cap120 is measured at actual89.52FPS.

## Review handoff and remaining work

Play-G.cmd verifies all package file hashes against Evidence/G/PACKAGE.csv, then launches Boot with separate ReviewUser settings. G-MANUAL-CHECKLIST.md is the single consolidated user checklist. No user PASS is assumed. Native source/assets/package are unchanged, so previous full build,23 Automation tests and three smoke maps were not rerun.

G remains IN_PROGRESS: detailed timed assertion review of all input captures and full matrix reconciliation still need completion before READY_FOR_REVIEW. FPS120 remains NOT VERIFIED as an achieved operating point. No acceptance, merge or U02 is performed. The new original-project Editor PID8676 remains open; isolated server/clients were stopped after their measurements.
