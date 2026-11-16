# U03-D-R1 contracts

Runtime source `0b255233df021f2cc148313e638d918d41a4a11e`. D at f6d0f68 was NOT ACCEPTED. R1 introduces no gameplay decision or authority/motor/damage change; 35 model/U02/motor/character/animation blobs match that baseline exactly, and remaining C++ edits are presentation or explicitly flagged capture fixtures.

* C2 projection and environment query are shared unchanged with Tab/HP. Canvas subject cues and event audio require the subject information point and label anchor to be on screen and clear from the LocalPlayer camera. Combat bodies are excluded from the environment trace. This does not select a target or change Tab retention.
* The entire confirmed sword box/direction is a normal world primitive with per-pixel depth test, world depth group, zero bias; no Canvas box or debug PDI.15 segments preserve the existing 200×120×180 volume/yaw. The component has no collision/navigation or authority writes; dedicated server creates none.
* Confirmed history identity remains source/target/life/action/serial/encounter/revision. Eligibility uses the existing server clock: future timestamps do not retire serials; eligible hidden events retire silently. Repeated snapshots or revealing an event never rearm sound or its absolute timestamp+1.2 lifetime. Fresh audio allowance stays150ms; initial reconnect baseline is silent, and scope/visibility loss stops active voices.
* Miss/contact/block/parry/cancel rules, animation poses, bindings/schema v2/SaveGame and all A0–C2 gameplay laws stay unchanged. Migration tests use isolated slots; no user settings rewritten for testing.
* New R1 asset inventory: no authored uasset/audio download. World line vertices are generated in U03; the opt-in fixture references the existing Engine Cube. D poses, Attack1–3/Q/E, grip/carry and synthesized PCM/parry expression are inherited unchanged and tested again.
* `-U03R1VisibilityProbe` alone enables the labelled wall/camera diagnostics fixture. Actual Windows input and ordinary authority combat produce the results. Normal Solo/Network launchers do not enable it.
* One existing D clone, immutable old D published/raw/package evidence, private config/Maintenance and original Editor are preserved. Stable launcher preferences retain their directories; new Editor SDK logs are archived separately and prior SDK logs restored at scoped Stop. No source rebuild for report-only changes.

Final gates and limits: [matrix](D-R1-TEST-MATRIX.md), [single canonical report](Docs/U03/REPORT-D.md). Stop at READY_FOR_REVIEW D-R1, never ACCEPTED/merge/U03 closure/U04 automatically.
