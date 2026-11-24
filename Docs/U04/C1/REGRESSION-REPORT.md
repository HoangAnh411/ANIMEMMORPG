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
