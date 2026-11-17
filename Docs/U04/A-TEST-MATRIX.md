# U04-A test matrix

All gates below are NOT RUN until backed by a new run. Exact inherited assertion literals: [A-ASSERTIONS.json](A-ASSERTIONS.json); expected test names: [A-EXPECTED-TESTS.json](A-EXPECTED-TESTS.json). Dynamic network stage comparisons also cover each saved authority/proxy stage, not just literal assertions.

| Gate | Cases and required evidence | Harness |
|---|---|---|
| Build | clean committed source, Generate/Editor/Game/package completion, three maps, receipts/toolchain and full hashes | BuildA |
| Automation | expected=discovered=executed names; each Success, queue empty, fresh process/log | VerifyDTests (U04 copy) |
| Smoke | Boot/CharacterCombatLab/NetworkLab NullRHI load and clean exit | SmokeDPackage |
| Readiness | process/hash/world/netmode/controller/local player/possessed pawn, increasing time and actual pawn input | ReadinessA |
| Movement/camera | walk/sprint/jump/shoulder, wall/slope/ledge, camera obstruction, gravity while combat locked | CaptureDInput route + CaptureDRegression |
| Combat | combo/cost/cooldown/startup replacement, dodge, block/parry/guardbreak/CC/X, Q Feint/E Interrupt, no duplicate hit/timing change | combat + regression + Automation |
| Encounter | Tab never auto-aims, Won/Lost/Retry; life/revision/resources reset; watermark/settings/release gate retained | combat/target + network |
| Presentation | occluded labels/HP/audio, full/partial telegraphs; life/reconnect no stale feedback | CaptureDR1Visibility + CaptureDAudio + network |
| Focus | held input across Escape/AltTab/rebind/Retry; Resume only, release before new command | target/route/regression |
| Settings | sensitivity/shoulder/key/conflict, Save/Quit/reopen, isolated preference root | target + CaptureDLifecycle settings-only/reopen |
| Network | dedicated Editor+two active clients; action/HP/resources authority/proxy agreement, owner encounters, one-sided Retry and reconnect isolation | CaptureDNetwork + VerifyDNetworkSamples |
| Launch/Stop | refuse wrong source/module/package, occupied port/session; scoped stop preserves unrelated processes and restores placement | VerifyLaunchGuardsA + Stop |
| Seal | rehash raw/published evidence; retain failed/invalid runs and warnings; host/private hashes and original Editor preserved | SealA |

Solo complete and network complete are mandatory; both clients perform actions. One reconnect and Save/Quit/reopen are integration checks only; no substitute for U04-D soak10min/10Retry/5map cycles. No packaged Server or performance gate is claimed.
