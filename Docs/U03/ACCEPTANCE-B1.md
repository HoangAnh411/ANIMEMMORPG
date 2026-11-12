# U03-B1 - ACCEPTED (technical)

The user confirmed technical acceptance at `4a8b7e82c10b16c31a89bb0a0c25ce06019b6cc4`, verified source `3fd6c3d82e3c85a1eda6be8d35961c863019d4f7`, and explicitly authorized documentation closure, commit/push on `u03/b1-dodge`, and fast-forward/push of main. B2 requires a separate assignment.

Accepted scope: dodge/motor integration, sequential charges, buffer/admission, startup cancellation, authority/replication, retained swept trajectory shared by geometry and commit, and relative capsule CCD. B2/C1/C2, product visuals, U05 prediction and U04 benchmarking remain outside scope. Animation/presentation are blockout and do not control gameplay.

Reviewed evidence in [REPORT-B1](REPORT-B1.md): Editor/Game and Windows package succeeded;93/93 Automation Success,0 Failed, queue complete; smoke3/3; physical input38+17; dedicated Editor plus two clients20 and reconnect2. These are existing reviewed results, not fresh runs during closure. Warnings, limits and failed/invalid runs remain recorded.

History: b2c9676/source6603c30 was **NOT ACCEPTED** because preview and commit could disagree between step endpoints. Preserve the [old review](REVIEW-B1-b2c9676.md), [old report](REPORT-B1-b2c9676.md), [B1 evidence](Evidence/B1/MANIFEST.json) and [B1-R1 evidence](Evidence/B1-R1/MANIFEST.json). R1 added trajectory/StepUp fixes and incoming-hit/lethal-cutoff/long-short-update/two-pawn regressions. Historical manifests are not rewritten to change their original status.

This closure updates documentation only. No source/assets/config changes or build/test reruns. Preserve private config bytes and the open Editor without save/restart. Stop after verifying the main remote; do not start B2.
