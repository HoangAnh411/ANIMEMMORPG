# C1 regression continuation

C1 remains **INCOMPLETE**. Build-03 baseline remains **BASELINE_ACCEPTED**, with 36 timing and 12 memory windows. Existing 144/144 Automation results and all three smoke maps were verified against raw before this continuation.

| Gate | Evidence | State |
|---|---|---|
| Solo rendered fixture-off | Build-03 run C1-Launcher-20261124200800 through the Solo launch spec shared with StartB.ps1. The prior direct package run is preserved separately. The new run has a fresh W press and release, 115.571 cm of forward movement, and original handle stop proof. | PASS |
| Combat, dodge, focus | A focused Build-03 capture is still needed for combo damage, ordered dodge edges, menu/focus and held-key quarantine. | NOT_RUN |
| Dedicated Editor plus two clients | C1-Dedicated-Trio-01 reached dedicated and both client Game worlds. Original INVALID verdict preserved. Recheck links pawn/life and replicated encounter identity to the local and authority owners. Controller object names are process-local. All three owned handles signaled. No controlled action/hit or encounter damage isolation was captured. | CONNECTION_ONLY |
| Fixture media | A read-only image check is available. Separate paired H=1 and H=3 captures and native subject/hurtbox evidence remain pending. | NOT_CAPTURED |

Artifacts are under C1-Acceptance-Regression-Offline-02, with hashes in manifest.json. Raw logs remain local. The dedicated recheck records the original log byte ranges. Earlier raw and the original checkout are preserved.

The Solo entry and harness share SoloLaunchSpec.ps1. The harness owns the launched handle and uses U01Trace for observation. Reproduce the reviewed Solo spec without launch using ReadSoloLaunchSpec.ps1 with the Build-03 Archive/Windows directory, a new output directory, native SHA 13b4f34f07bd1cb8e7402984d9479fd5eb9fe2e7, a new run ID and FPS 60. The runtime entry is `python -B Scripts/U04/C1ForegroundCoordinator.py acceptance C1-Launcher-<new-numeric-id>`. Dedicated startup is `python -B Scripts/U04/C1Dedicated.py --id C1-Dedicated-<new-id> --port <free-udp-port>`. Image validation is `python -B Scripts/U04/C1MediaVerify.py <image> <summary.json> --build Build-03`.

Reopen and simultaneous world isolation are source-only for the C1 measurement fixture. Full callstack coverage is a 50 ms sample. Occlusion and suppression are aggregate counters. Review profile B covers one process, one Game world and one measurement window.

## Focused proof tooling

Solo is ACCEPTED by the reviewer. The local offline dossier at `../C1-Regression-Proof-Offline-03` contains 12 matching expected/actual results and a SHA-256 manifest. Its two images are synthetic verifier inputs.

The dodge helper requires the same native dispatch frame and stationary velocity at authority admission. The dedicated helper requires a new authority action and matching damage receipt, target life and HP across all three roles. The media verifier decodes the image and checks its receipt against the process record, Build-03 and native summary. Run it with `python -B Scripts/U04/C1MediaVerify.py <image> <summary> --process <process.json> --receipt <receipt.json>`.

Combat, controlled focus and dedicated gameplay still need capture integration and runtime evidence. Dedicated encounter isolation requires an active attack by B with a demonstrated damage opportunity and a positive control. The two fixture illustrations still need a real capture producer on Build-03. C1 remains INCOMPLETE.

## Build-03 focused runtime

The run IDs below identify the C1 package evidence. The runtime ledger and manifest are under `../C1-Focused-Runtime-20261124-03`.

- C1-FocusedCombo-2026112403 PASS. Native summary joins actions 1/2/3 to 60/70/90 damage. Authority target HP fell from 1,000,000 to 999,780.
- C1-FocusedDodge-2026112403 PASS for both ordered pairs. Native dispatch frames and command IDs are in the ledger. Forward and fallback backward both traveled 300.000 cm to rounding. Both satisfied stationary admission, 250 ms motion and 350 ms release deadlines.
- C1-Media-2026112403-H1 and H3 PASS. Both 1280 by 720 PNGs decoded and show the same player/dummy framing. The images show placement. The native summaries establish stable hurtbox IDs [1] and [1,2,3] for one subject/life per process.

All four processes have original-handle, signaled exit evidence checked against PID, FILETIME and executable. Their workspace and Editor preservation checks passed. Controlled focus quarantine and dedicated replicated damage/isolation remain open.


## Focus and dedicated gameplay continuation

C1 remains INCOMPLETE. Control-flow checks verified that focus retains W through Resume and that the dedicated entry runs capture_gameplay between verify_owners and owned stop. Runtime artifacts and SHA-256 manifest are in C1-Focus-Dedicated-Review-04.

| Gate | Verdict | Evidence |
|---|---|---|
| Focus quarantine | INVALID | C1-FocusedFocus-2026112404 recorded accepted held W and inactive AwaitingResume. An empty foreground HWND interrupted return before Resume. The recovered handoff tooling preserved that run. Attempts 05 and 06 hit the initial gateW guard before a new W edge. The Windows key-state check observed W still down. Quarantine after Resume and subsequent rearm remain unverified. |
| Dedicated replicated damage | PASS | C1-Dedicated-Gameplay-04. Client A issued E. Authority action 1, receipt serial 15, definition 4, 80 damage, HP 600 to 520. The same receipt first appears at Game.log byte offsets 3128789 on server, 3561117 on ClientA and 11568098 on ClientB. |
| Dedicated owner isolation | ISOLATION_NOT_PROVEN | Build-03 evidence lacks an independently reconstructible same-attack opportunity for A, including active attack geometry, hurtbox poses and LOS for that interval. |

All recorded children signaled on their original handles with matching identities. Editor and workspace preservation passed. Earlier CONNECTION_ONLY and INVALID records are retained. Reproduction entry is python -B Scripts/U04/C1ForegroundCoordinator.py acceptance followed by a new C1-FocusedFocus numeric ID or new C1-Dedicated ID. The latter uses UDP 19642.

## Focus recheck and Build-03 isolation observability

Focus PASS in C1-FocusedFocus-2026112407. Two consecutive W-up samples preceded package launch. The same pawn/life went from accepted W and movement through inactive and active AwaitingResume, then Playing with W physically down, gateW=false and zero position change. W-up rearmed the gate. A new accepted W press moved the pawn 138.326 cm forward, and final W-up was observed while the game held foreground. Original-handle exit and preservation passed. The three prior INVALID runs remain in the previous dossier.

Dedicated replicated damage is ACCEPTED. The Build-03 owner-isolation gate is ISOLATION_NOT_PROVEN_ON_BUILD_03. The authority log contains monster B action 1 and an associated visible query and hit on B. Attack interval and geometry are observable for B. The same slice has no independently observable A hurtbox endpoints/radius or LOS for A. The encounter filter runs before span, geometry and visibility logging. The B regression verifies separate encounters and Retry preservation, with a different evidence scope.

No new trio was launched. C1 is INCOMPLETE with only owner isolation outstanding. Review decision needed on a separate opt-in diagnostic build to record both owners' hurtbox poses and obstruction evidence, keyed to the same authority attack slice. Build-03 verdicts stay tied to Build-03. Ledger, source/raw audit and SHA-256 manifest are in C1-Focus-Isolation-Review-05.
