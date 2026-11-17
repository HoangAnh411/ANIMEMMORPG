# U04-A — READY_FOR_REVIEW

Independent reviewer acceptance is pending. U04-A has not been merged; U04-B/C/D have not started.

U03 dossier was accepted at b2199687 and closed at **25a048d9a6744a991040dbaa7698f10bcda448f6**, pushed to the dossier branch and fast-forwarded/pushed to main with remote SHA verified. U04 branch `u04/a-windows-regression` starts from that exact main. Historical U03 identities remain: binary/source0b25523, technical acceptancea7737f9, technical closure89358c5, user playtest3439fed. Documentation commits are never assigned to those binaries.

## Source and binary identity

Final built source: **b35ef63c7e9ffdfbb4088544350317a8f958723c** in `Artifacts/U04/A/Source`. All later commits change harness/docs only; committed Source/Content/Config/Plugins/.uproject match the built source exactly. No untracked source inputs; tracked clone tree is clean. Generated Build/Binaries/Intermediate/Saved outputs are retained. Main baseline, built source and harness commits are separate identities in [results](A-RESULTS.json) and per-step/per-capture command records.

Only native changes are opt-in **read-only diagnostics** in U01NetworkProbe.cpp and U01Menu.cpp: per-frame/cvar sampling without enabling probe fixtures, and actual settings-widget geometry. Flag `-U04AReadOnlyFrames`; no gameplay API, timing, combat law, settings schema, reflection/header or art change. Clone Live Coding log records exactly `LogLiveCoding: Display: Live coding succeeded` at2026-11-17 04:47:56.258UTC. That process was closed; acceptance uses full UBT Editor/Game builds and cold `-NoLiveCoding` processes, never the patch.

Generate, Development Editor, Development Game and Windows package all exit0, respectively04:48:14–04:48:21,04:48:21–04:48:57,04:48:58–04:49:41,04:49:41–04:50:29UTC. Three cooked maps: L_Boot, L_CharacterCombatLab, L_NetworkLab. UE **5.8.4/CL58902052**; actual selected **MSVC14.51.36260**, Windows SDK**10.0.26100.0**. Build command/result/log/receipts and complete package index are in `Build-Final-20261117-1148`. Built Game executable equals packaged Game hash. Editor module, engine Editor/commandlet executable and every package file are hashed. Process checks add executable, creation time, command scope and actually loaded clone DLL; SHA command-line metadata alone is never proof.

## New execution results

Automation: **140/140 Success**, exact expected=discovered=executed names, no missing/extra/duplicate names, queue empty. Final selected run `Automation-LoadedModule-20261117-1213` also records the actual loaded clone DLL. Initial new Automation run is supplemental, not inherited U03 data. Actual controller schema has no XML-export method: raw Editor log, MCP schemas/discovery and NAME-RESULTS.json provide every test name/result. NullRHI smoke **3/3**, load/headless only.

Every selected capture has real process/world/net-mode/controller/owned local pawn, advancing time and physical Windows input readiness. Frame files additionally prove advancing frame counters and actual cvars; no Editor-world actor is substituted for gameplay. Dedicated server has0 local players, each client1; native module paths come from live processes. Final network readiness also records four advancing tick samples per process.

| New gameplay/capture gate | Result | Fixed run ID |
|---|---|---|
| Solo combat | 24 PASS | `Solo-Combat-Capture-20261117-1156` |
| Defense/Feint/CC/focus | 15 PASS | `Solo-Defense-Capture-20261117-1157` |
| Movement/camera/gravity/focus | 26 PASS | `Solo-Movement-Capture-20261117-1205` |
| Dodge/startup cancel/charges | 38 PASS | `Solo-Dodge-Capture-20261117-1205` |
| Target/occlusion | 15 PASS | `Solo-target-Capture-20261117-1207` |
| Encounter route/return | 11 PASS | `Solo-route-Capture-20261117-1207` |
| Settings Save/Quit | 5 PASS | `Solo-Settings-Save-Capture-20261117-1212` |
| Settings cold reopen/Quit | 2 PASS | `Solo-Settings-Reopen-Capture-20261117-1212` |
| Dedicated Editor + two clients/reconnect | 26 PASS | `Network-Capture-20261117-1230` |
| Two-client visibility/audio | 20 PASS | `Visibility-Capture-20261117-1232` |

Network additionally passes **41 independent comparisons** of saved server/two-client samples, including actions, HP/resources, ownership, Retry isolation and reconnect. Both clients perform real actions; physical input is scheduled sequentially while all processes/worlds run, not two simultaneous human keyboards. Reconnect sees retained old replicated results yet emits no old-encounter feedback/audio. Save/Quit/reopen uses the same isolated preference directory, verifies exact saved bindings/sensitivity/shoulder, fresh combat state and clean product `LogExit: Exiting` on both quits.

Launch guards:5 final refusals (wrong source/module/package, occupied UDP port, existing session); live wrong-source Stop preservation and synchronous live settings-scope conflict refusal also pass. Stop only handles recorded matching identities and restores original placement. Reconnect follows real product Quit and waits native OS exit without stopping an old/reused PID.

No U04-D soak10min/10Retry/5map-cycle claim. Copied lifecycle harness is not presented as an executed soak. No historical U03 gate is counted as a U04 result.

## Conditions, limitations and failed attempts

Host: i7-11800H8C/16T, approximately32GiB RAM, RTX3050Ti Laptop4GiB, driver621.24, Windows11Pro10.0.26300. Initial free space165895614464 bytes; measured existing clone6.65GB/package1.09GB/evidence362MB justified25GiB reserve. Start/final snapshots preserve disk, competing-process working sets/CPU counters and hardware records. No cleanup or engine download.

Review profiles preserved: Solo1280×720/internal50%; network900×540/internal50%, requested client60/server30, idle0, Lumen atlas2048, RT pool minimum128MiB, streaming pool256MiB, Lumen indirect/reflections0, virtual shadows0, shadow quality2. Actual cvars are validated in FRAME-SUMMARY.json. Full capture-window measurements, including setup/menu/reconnect transitions: Solo combat59.99FPS/P95 17.15ms; network server29.86/P95 40.10ms, original ClientA59.88/P95 20.76ms, ClientB59.83/P95 20.27ms, reconnected A56.16/P95 20.55ms. These are measured wall-frame intervals, not caps. **No U04-B, stable60FPS or1080p product acceptance.** Smoothing/network rules and input processing were not changed.

**Packaged Server NOT PASSED.** Existing project targets are Game/Editor only. Installed engine advertises no Win64 Server configuration or UnrealServer receipt. ServerSurvey records exact target source/installed configuration. Before U05, separately review a supported source-engine Server environment and target proposal; no Server target was added and no engine downloaded.

Compiler is newer than preferred14.50.35717; engine deprecation/toolset/asset and audio warnings remain in raw logs. Audio loopback warnings are retained alongside the WAV/native feedback decisions; combat parry660/990Hz ordering was observed. Blockout art only; no prediction, adverse network or product visual acceptance.

All failed/invalid/intermediate execution attempts remain in [run catalog](A-RESULTS.json) and manifest, with original logs/media. They are **not PASS**. Harness corrections include safe IME probing, fresh-life/Resume preconditions while gameplay continues in menus, correct mouse input, grounded-only attack and no-impulse Launch fixture preconditions, physical camera aim into an obstruction, open-space rebind movement, singleton/not-yet-loaded DLL enumeration, and native process exit for reconnect. Negative conflict probes that lost their live owner are invalid; a later synchronous probe with three live owners passed. No gameplay fix was applied after diagnosing these preconditions; no blocking gameplay defect was identified in completed gates.

## Preservation and handoff

Final integrity rehashes the entire final package/module/engine, verifies unchanged committed native inputs, every initial private-file hash, and original Editor executable/creation time/placement. Only original Editor PID6676 remains, matched to the original creation identity and project window; PID alone is not used as proof. It was never saved, closed or restarted. All48 U03 accepted package files still match D-R1 index; U03 launchers/evidence remain unchanged. Original .uproject/config/Maintenance remain uncommitted and untouched.

Contracts: [A-CONTRACTS](A-CONTRACTS.md); matrix: [A-TEST-MATRIX](A-TEST-MATRIX.md); names: [A-EXPECTED-TESTS](A-EXPECTED-TESTS.json); assertion inventory: [A-ASSERTIONS](A-ASSERTIONS.json). Raw evidence: `Artifacts/U04/A/Runs`; raw final package: `Build-Final-20261117-1148/Archive/Windows`. Published evidence/manifest: `Docs/U04/Evidence/A/Review-20261117-1244/MANIFEST.json`, with raw/published SHA256 associations and retained invalid runs. Use `python Scripts/U04/VerifyEvidenceA.py <manifest>` (or `--published-only` on another checkout). Package bytes remain in isolated Artifacts; full file hash index is published.

Branch is to be committed/pushed and remote SHA verified for handoff; exact final commit/remote attestation is provided separately to avoid a self-referential manifest hash. Stop at **READY_FOR_REVIEW**. Independent reviewer decides ACCEPTED/NOT ACCEPTED; no U04 merge or U04-B implementation is authorized here.

Publication note: the first seal attempt used an unresolved relative output path and stopped before producing a manifest. Its partial `Review-20261117-1242` directory and `Publication-Invalid-1242` raw diagnostic are retained. The valid immutable seal is `Review-20261117-1244`; its file index includes that publication failure. This did not invalidate native/gameplay gates.

Legacy D/U03PackageD identifiers in copied harness files are role/provenance labels. U04 identity is established by the isolated A paths, b35ef63 source/build/module/package hashes, fresh process creation identity and new run IDs.
