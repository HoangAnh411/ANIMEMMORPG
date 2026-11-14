# U03-C2 verification matrix

Written before runtime. All rows start **NOT RUN**. Counts are determined by executed tests, never fixed in advance. Assertions do not replace physical input, replication, video or user feel review. Each final run must name producing source commit and binary/package hashes. Preserve invalid/failed/superseded runs and explain reruns.

|Contract|Required layer and cases|Evidence/status|
|---|---|---|
|Prerequisite cleanup|Protected source/config/evidence hashes; retained B2/C1 solo/network launchers actually ready after cleanup; original Editor placement restored|Cleanup audit and C2 preflight; record exact sessions separately|
|AI boundaries|Model + Game world, before/exact/after200/1000/1500/50cm; target death, wall LOS at feet+90; Idle/Chase/Action/Return/Defeated|NOT RUN|
|Return|Game-world navigation around wall; loss in startup/active/recovery; no rechase; no teleport/timeout heal; reset exactly once at50cm; new life/rebase, no pending hit|NOT RUN|
|Monster combat|Definition600HP/100raw/.60/.75/1.50; real Monster admission/barrier/geometry; startup tracking then yaw lock; horizontal stop/gravity; miss at valid admission; block/parry|NOT RUN|
|Interrupt|Before/exact/after active-start and recovery; E unblocked/parried/blocked/shield/lethal; Q no Interrupt; no stun/penalty/Feint/dodge/guard|NOT RUN|
|Causality|Long/short update and reversed collection; hit strictly before cutoff retained, cutoff/after discarded; simultaneous lethal inherited resolver ordering; no epsilon extension|NOT RUN|
|Trajectory regression|Fresh full wall/StepUp/two-pawn retained trajectory tests from U00–C1|NOT RUN|
|Encounter isolation|Game world + dedicated two clients: stationA player/monster only; stationB unaffected by damage/RetryA; unauthorized cross-pair collection/resolution rejected|NOT RUN|
|Retry transaction|Won/Lost valid; Running/spam/duplicate/stale revision/sequence/ID/unowned reject; all component state reset; old callbacks/actions/events cannot mutate new lives|NOT RUN|
|Disconnect/reconnect|Live two-client session: ownership ends and old events invalidated; new encounter/pawn/identity, no old combat restored; stale probes|NOT RUN|
|Tab selection|Pure ranking + LocalPlayer viewport/world:2000/3000cm boundaries, center/3D/ID ties, wall LOS, offscreen, occlusion1s and visibility timer reset, death/life/revision clear|NOT RUN|
|Tab input/presentation|Physical Target toggle/hold/rebind; no RPC or camera/facing mutation; marker/HP hides immediately offscreen/occluded; labelled multi-target fixture separate from gameplay|NOT RUN|
|Physical play/video|Win and lose; Retry; Tab; dodge/parry/Q/E/Interrupt; menu/focus/Resume; held input across Retry; click Retry never attacks; animation phases/warning geometry|NOT RUN|
|Replication|Dedicated Editor+two clients compare HP/action/AI/result/revision at authority snapshot time; clients60/server30, smoothing unchanged. Sequential input explicitly labelled sequential|NOT RUN|
|Build/automation gate|Committed single clone Generate/Editor/Game; MCP TestRunner then actual logs; all U00–C1 plus C2, report every result/errors|NOT RUN|
|Package/smoke|Windows package from verified source/binary; Boot/CharacterCombatLab/NetworkLab three-map smoke|NOT RUN|
|Launcher guards|Source/module/package hashes; wrong hash refusal; readiness then minimize and placement restore; scoped stop|NOT RUN|
|Feel|User evaluation of telegraph readability/chase/return/Retry; B2/C1 playtest status unchanged|PENDING USER REVIEW|

Implementation order: AI/combat focused runs → encounter/Retry focused runs → Tab/UI focused runs → stable full gates. Fixes rerun affected gates; documentation-only changes do not rerun builds/tests. Record implementation/build/verification/fix time separately in REPORT-C2.
