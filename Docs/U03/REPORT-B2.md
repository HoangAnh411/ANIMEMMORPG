# U03-B2 — ACCEPTED (technical)

Branch `u03/b2-defense-cc`, based on main `88244cf67ddc679fec2ceaccb0d9f68c40ce653a`. The user confirmed **ACCEPTED về kỹ thuật tại fa5c74cb**, verified native source **515f8190a35afbc8663669419c6ce502967e3df3**, and authorized documentation closure and fast-forward/push of main. **Người dùng chưa chơi thử; presentation vẫn blockout. Chưa chấp nhận cảm giác chơi hoặc hình ảnh sản phẩm.** See [technical acceptance](ACCEPTANCE-B2.md). No C1 is authorized.

## Runtime

Guard/parry/posture, slow/hard CC/continuous-lock budget/immunity and X now share the existing U03 timeline and cooperative world barrier. Guard/X/release use the existing dispatcher, rebind and physical release gate. Guard admission validates the replacement before cancelling normal-attack startup; rejected commands preserve the attack. Guard follows authority aim, walks at200cm/s and disallows sprint/jump.

The existing U02 resolver still owns geometry → life/action/dedup → defense at hit time → damage/crit/shield → death → surviving effects → publish. Block uses factor.30 before the final rounding; parry consumes dedup without a crit roll, damage, posture loss or adverse hit effects. Current model state at the committed hit barrier decides defense; bounded presentation history never rewrites a past hit. A separate parry feedback identity/time preserves the ring/two-note cue when a later simultaneous hit becomes a block.

CC deadlines, budget exhaustion, immunity expiry, slow expiry and eligible posture regeneration split the timeline. Hard CC and death cut the remaining action/dodge trajectory at that event timestamp; B1-R1 retained paths and relative capsule CCD remain the collision/commit path. X clears current hard CC/slow/pending launch/budget, grants1s hard CC immunity and spends its30s cooldown only on success. Saved moves do not own these life-bound authority states.

One runtime module remains; no module/plugin/framework/GAS, prediction, lag compensation or packaged Server was added. Q/E/Feint/Tab/encounter/Retry gameplay and C1/C2 remain outside this delivery.

## New evidence

All builds/tests/packages below use committed source in `Artifacts/U03/B2/Source`; the original open Editor is not evidence of a loaded B2 binary. UE5.8.4 CL58902052, VS14.51.36260 and Windows SDK10.0.26100.0 were recorded by the actual build commands/logs.

| Gate | Run | Result |
|---|---|---|
| Generate/Editor/Game | Build-20261113-121422 | exit0, Result: Succeeded |
| MCP TestRunner + completion logs | MCPTests-20261113-121631 |107 Success,0 Failed, queue107 complete |
| Windows Development package | Package-20261113-121631 |UAT exit0, BUILD SUCCESSFUL |
| Package smoke | Smoke-20261113-1218 |Boot/CharacterCombatLab/NetworkLab3/3 |
| Physical input/video | InputCapture-20261113-1219 |22/22, completed=true |
| Actual output-loopback audio | Audio-20261113-1221 |Python exit0; ordered660Hz then990Hz detected |
| Dedicated Editor + two clients | NetworkCapture-20261113-1225 |21/21 live checks +6/6 independent saved-sample comparisons |
| Two-client dodge regression | DodgeNetworkRegression-20261113-1235 |22/22, completed=true |
| Disconnect/reconnect with old X cooldown | Session-20261113-122206 |2/2 live checks; new identity and fresh state |

107 tests comprise the93 inherited U00–B1-R1 tests rerun against this binary and14 B2 tests. The B2 cases cover half-open parry/cooldown edges, inclusive guard angles/coincident source, independent hit flags, posture break/refill/eligible integration, stronger/equal/shorter CC, continuous lock/free reset/immunity, X/slow/airborne behavior, real world crit/shield/dedup/lethal effects, late guard/release/aim, old guard/life identities, collection reversal and long/short updates. Hard CC is tested at actual mid-wall/StepUp committed poses; slow is tested during the retained dodge without changing its300cm path. Shared U02 damage rounding assertions run again through the same damage implementation.

The22 physical checks use actual Windows mouse/keyboard input with PID/executable/hash/world/ownership/focus guards. Fixtures create labelled enemies only. The recording includes held/released RMB, parry followed by ordinary blocking, break/X, grab/X, startup cancellation/combo reset, natural CC expiry with held movement, guard200/no sprint/jump, real UI Guard→C/X→Z rebind and restoring defaults, plus menu/focus/Resume/release gates. Video is wall-clock30FPS encoding; it is not evidence that gameplay rendered at120FPS.

The audio artifact records the default output loopback, not a microphone. The actual cue contains the two ordered tones. The capture backend emitted `SoundcardRuntimeWarning: data discontinuity in recording`; raw warning logs remain. This is not an audio fidelity acceptance claim.

The network capture sends real defense input sequentially from each client, then compares the same pawn/life/guard sequence, HP/posture, CC/X and parry state across the dedicated server and both clients. Six independent comparisons also check immunity/slow/parry deadlines and the full confirmed-result histories. The22-check dodge regression checks actual W direction, authority swept distance, two peers, sequential resources, negative probes and actual cvars. These separate-client inputs are **not** evidence of two simultaneous hits; the stable simultaneous-hit and two-pawn CCD evidence is the Game-world Automation fixtures.

Before reconnect, the old client actually used X on a labelled grab and retained a nonzero cooldown. A new guarded process then received a new pawn identity, HP1000/posture100, no guard/CC/slow/X cooldown, two dodge charges and no old action/pending replay. The verification ran while the new process was live; process records include both old and reconnect PIDs. Stop verified source/executable/module/userDir/hash ownership and restored the original Editor placement.

## Failed, invalid and superseded runs

All raw runs remain under `Artifacts/U03/B2`; the manifest publishes strict decoded/redacted copies and hashes, including failures.

- Initial builds failed on a shadowed local and missing `FActionId` hash; the next hash fix needed ADL for Unreal's GUID hash. The exact compiler output/file lines remain in each build log.
- The first simultaneous-hit fixture lacked its second valid contact. Both attackers are now spawned/settled before admission, with an admission assertion and independently aimed geometry. The next run passed, including reversed collection and update partitioning.
- The first slow-distance assertion placed an enemy capsule at the end of the dodge path, so normal pawn collision clipped the dodge. Moving that test source sideways keeps the incoming attack contact while removing the physical blocker; the final test passes.
- InputCapture-1155 scheduled a physical edge from a quantized metrics sample and arrived after the hit; it is invalid for parry-success evidence. The harness now schedules from the fixture's logged wall timestamp; gameplay windows are unchanged.
- InputCapture-1159 exposed a real letter-rebind bug: OS reconciliation read only Unreal's virtual-key map and falsely released Guard C. Character-map fallback was added and covered by Automation plus the final physical C/Z tests.
- Solo presentation QA found a duplicate HUD from a locally controlled AI fixture. The initial Session-121003 was explicitly stopped before network assertions and is marked invalid. Filtering HUD to actual local players briefly affected the inherited native aim adapter, caught by `AdmissionCancelAndYaw`; that adapter was restored, with fixture aim set explicitly at attack admission. Final107/107 passes.
- DodgeNetworkRegression-1228 was invalid after deliberately ahead-sequence negative probes; real warm-up edges now catch the controller counter up before a lab reset and fresh measurement. DodgeNetworkRegression-1232 stopped on a UTF-8 tail beginning inside a partial line. The reader now drops only the incomplete first line before strict decoding;1235 passed22/22.
- The first stale-session Stop wrapper had an extra PowerShell JSON array wrapper and failed before any process mutation. Direct assignment/foreach fixed it; the final Stop succeeded and placement was verified.
- Audio-1220 produced a valid completed waveform result, but PowerShell reported its native stderr warnings as a wrapper error. Audio-1221 captures combined output and records Python exit0 separately; warnings were retained.

Earlier successful source0f6169f/1a88773 runs are historical evidence for those binaries. They do not substitute for the final source gates above. B1/B1-R1 reports and evidence are unchanged.

## Play, environment and limits

[Solo launcher](../../Play-U03-B2.cmd), [network launcher](../../Play-U03-B2-Network.cmd), [Stop](../../Stop-U03-B2.cmd), [short checklist](../../Play-U03-B2-CHECKLIST.md). Launchers check source/binary/package association and hashes, retain the existing client60/server30 profile and record original Editor window placement. Both launchers were exercised: source/package/module/engine hashes checked, all original Editor windows verified minimized after clients ready, and placement restoration verified after Stop, including reconnect processes. Stop includes reconnect processes and skips already restored old sessions.

The private `Config/DefaultEngine.ini` is kept byte-for-byte and excluded from staging; its hash is audited without publishing its contents/token. The original Editor PID6760 remains open, without save/restart or Live Coding. Added reflected snapshot/RPC layout and headers require a full build and Editor restart for any future original-Editor synchronization, with unsaved content preserved first. The launchers run the verified clone/package; Play in the original Editor is **not guaranteed to load B2**.

Presentation is a development blockout: guard frame/HUD, labelled enemy capsules/attack boxes, distinct text/block/break signals, parry ring and generated two-note sound. No product guard animation, profession skill art or visual-quality acceptance is claimed. Launch/grab/stun/knockdown/slow are explicitly labelled test effects; launch has no invented impulse. These enemies are resolver fixtures, not monster AI, an encounter or enabled product PvP.

Compiler/toolchain preference warnings, engine deprecations, native fixture mesh/socket warnings, audio-capture warnings and expected unowned-RPC warnings are retained in evidence. Local network verification does not cover adverse networks, latency compensation/U05, packaged Server, U04 benchmarking or product visual feel. Reviewer decides ACCEPTED; the user judges feel/readability. No main merge or C1 is authorized.

## Artifacts and stop point

[Contracts](B2-CONTRACTS.md), [test matrix](B2-TEST-MATRIX.md), [manifest](Evidence/B2/MANIFEST.json), [package hashes](Evidence/B2/PACKAGE.csv), [strict encoding audit](Evidence/B2/ENCODING-VERIFICATION.json), [warnings/failed-run output](Evidence/B2/WARNINGS.json) and [test traces](Evidence/B2/TEST-TRACES.json).

[Final input video](Evidence/B2/Runs/Runs/InputCapture-20261113-1219/Input-B2.mp4), [network defense video](Evidence/B2/Runs/Runs/NetworkCapture-20261113-1225/Network-B2.mp4), [network dodge video](Evidence/B2/Runs/Runs/DodgeNetworkRegression-20261113-1235/Network-B2.mp4), [parry ring](Evidence/B2/Runs/Runs/Audio-20261113-1221/ParryRing.png) and [actual two-note output](Evidence/B2/Runs/Runs/Audio-20261113-1221/Parry-Output-Loopback.wav).

Stop at **READY_FOR_REVIEW U03-B2** after branch push/remote SHA verification. No ACCEPTED marker, main merge, C1/C2 implementation or original-Editor synchronization is performed.

## Technical acceptance and documentation closure

The READY_FOR_REVIEW/no-merge statements above describe the original handoff. The user subsequently accepted B2 **technically at `fa5c74cbd9853faa23a642d8c73c667c7e3682d2`, source `515f8190a35afbc8663669419c6ce502967e3df3`**, and explicitly authorized this documentation closure and fast-forward/push of main. [ACCEPTANCE-B2](ACCEPTANCE-B2.md) records its scope and limits.

**The user has not playtested B2. Presentation remains blockout; user feel/readability and product visuals are not accepted.** The existing automated input/video evidence is not user playtesting. All results above are inherited from the recorded handoff; no builds/tests were rerun for this documentation-only closure. Original evidence/manifests, failed/invalid runs and warnings remain unchanged. No runtime/assets/config/tooling changes or Editor interaction are made. Stop after verifying the branch/main remote SHA; do not begin C1 or close U03 overall.
