# U04-B-R1a contract

Base diagnostic 88f07b01e045a36b9922d3f3988c5d483aa11cbd. Separate clone Artifacts/U04/B-R1a/Source, runs under its sibling Runs. Original Editor and all U03/A/B/diagnostic evidence remain protected.

Scope: Dodge observed-edge direction snapshot only; read-only timing/network diagnostics; method verification and regressions. R1b is NOT AUTHORIZED in this phase. Old FAIL/INVALID labels remain immutable. No renderer/runtime timing/motor/admission changes.

Primary clock is sampleEntryWall, captured once at post-actor collector entry. Event stamps wall only. worldBeginWall, frameBeginWall and collectorExitWall are comparison clocks, never alternate gates. Cadence is rendered-package game-thread cadence, not GPU present/scanout. Mean FPS within 5%, at least 95% intervals within 10% period, maximum interval two periods. Keep all frames bracketing window boundaries. Percentile rank=(n-1)*p, linear interpolation. FPS=count(intervals)/sum(interval seconds).

Numerical windows: no screenshot/ImageGrab/color conversion/encoder/writer. Focus guard every 50ms, native focus sampled every frame. Pictures outside window only. Buffer flush after window. Native JSON allocations, buffer growth, per-frame diagnostic work and inherited 5Hz metrics logging remain overhead; entry-to-exit reports collection cost, not zero overhead. Video is a separate illustrative run.

Repro inventory, in order 30,60,120: two qualified runs each ordered W-down/Shift-down, Shift-down/W-down, W-down/W-up/Shift-down, prior-frame-held-W/Shift-down; maximum four attempts per case. Same-frame condition and direction are proven from raw physical edge trace, not SendInput return alone. W-first rest case requires authority prebatch horizontal speed <=0.01cm/s. Any unmet precondition INVALID, valid precondition wrong behavior FAIL and stops gate. Keep all attempts. These are repros, never acceptance trials.

Method controls: three idle 15-world-second windows per FPS without video, plus one separate illustrative video. Full cold-clone Automation (140 baseline + new tests), three-map smoke, combat/dodge/focus/settings regression and dedicated Editor/server30 + two rendered clients60. Build Editor/Game/package from committed native source UE5.8.4 CL58902052, record actual UBT compiler/SDK.

Handoff status concerns R1a only. Reviewer must accept source and method before assigning R1b. No all-B READY_FOR_REVIEW, ACCEPTED, merge, C or D.

Idle window selection, implemented before capture: first native frame worldTime +1.5 through +16.5 seconds, with both bracketing frames retained. Python schedules approximately18 seconds of acquisition; it never defines measured duration. Repro gameplay verdict tests edge/snapshot behavior; whole-buffer cadence is reported independently, including console preparation/termination frames. A repro gameplay PASS is never a cadence/acceptance PASS.

The120 idle-1 postprocessing read raced the native writer. Its complete original buffer is retained and analyzed using the same declared boundaries; the aborted ledger is immutable. Resume is restricted to never-started idle2/3 after verifying completed repro inventory and existing earlier buffers. File-close waiting occurs after end, outside measurement. No replacement capture is permitted.

Final method candidate u04r1-entry-2 also measures Dodge displacement from authority Received.receivedPosition and brackets cadence from receipt through release gate. Synthetic tests cover differing model/receipt origins and missing receipt. This correction does not change cadence formulas or R1a repro/idle results and is not applied to old B evidence. No R1b gameplay batch has run.
