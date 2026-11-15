# U03-D test matrix

Status: planned, no new D gate claimed. Inherited C2: 131 Success / 0 Failed at source b43b15d; see Docs/U03/Evidence/C2/MANIFEST.json. Documentation-only main base does not constitute a D run.

| Gate | Coverage / method | D status |
|---|---|---|
| D.1 | Trace Description/ROADMAP U03.01–09, source, asset inventory, frozen gameplay contracts | Initial audit recorded; exhaustive audit pending |
| Feedback | Timestamp expiry at/exactly after 1.2s; duplicate/stale/late/future packets; new subject/life/encounter revision; reconnect; audio dedup | Pending implementation/tests |
| Authority miss | Completed with no contact; hit/block/parry suppress miss; cancellation suppresses miss; long update crosses completion | Pending audit/tests |
| Visibility | LocalPlayer projection, viewport boundary/offscreen, environment occlusion, immediate hide, life/revision invalidation; no Tab mutation | Pending tests/input video |
| Settings | Single key/mouse, duplicate/canonical modifier/wheel/chord/reserved; v1/v2 conflict closure; missing/truncated/corrupt/unsupported; load preserves bytes; isolated save/reopen | Existing coverage to audit, D pending |
| U03.01/.02 | Combo timing/priority/resource/cooldown; model/world updates 30/60/120 and long steps | Pending final regression |
| U03.03 | Dodge charges/trajectory, wall/StepUp/two pawns; no animation capsule motion | Pending final regression |
| U03.04/.08 | Guard/parry/break/hard CC/X, lethal cutoff and focus/control lock | Pending final regression |
| U03.05/.09 | Q/E/Feint/Interrupt, monster startup direction/box, authority cutoffs | Pending final regression |
| U03.06 | Clip/pose/grip/readability, HUD actual bindings/resource/CC, independent recent-hit HP; no debug overlay dependency | Pending final inspection/video |
| U03.07 | Won/Lost/Retry authority; release gate/AwaitingResume, owner isolation, no combat persistence | Pending final regression |
| Full Automation | MCP TestRunner filter AnimeMMORPG; GetLogEntries completions; actual total and per-test status | Initial HUD source5cc8574:134 Success/0 Failed; final D source pending |
| Build/assets | Editor + Game; Windows package; Blueprint compile/references; Boot/CharacterCombatLab/NetworkLab smoke | Initial HUD source5cc8574 Editor/Game PASS; package/assets/smoke and final D pending |
| Input/video | Combo,Q/E/Feint/Interrupt,dodge,guard/parry/break, labelled CC/X; win/loss/Retry; Tab/HP occlusion; rebind/save/load; held keys through menu/focus/Resume | Pending final source |
| Loopback audio | Parry 660→990 sequence, distinct Feint/Interrupt; duplicate snapshots silent; event timestamp correlation | Pending final source |
| Lifecycle | Five Boot→arena→Boot loops; Quit/reopen isolated settings | Pending final source |
| Network | Dedicated Editor + two clients: identity/owner/proxy, HP/resource/result agreement, Retry A leaves B, stale/duplicate/late data, disconnect/reconnect | Pending final source |
| Profile | Exact inherited resolution/pool/render, client60/server30 with runtime combat; measured render FPS distinct from model steps; no cap/smoothing/input workaround | Pending profile audit and final measurement |
| Delivery | One clone, guarded launchers/hash/port/process, placement restoration, manifest all retained failures/warnings, commit/push/remote SHA | Pending |

AI owns technical verification; user checklist covers readability, distinct audiovisual feedback, poses/grip, HUD/occlusion and Retry/focus/two-window feel only. Product art and U04 graphics/performance acceptance remain deferred.
