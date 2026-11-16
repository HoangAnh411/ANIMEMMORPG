# U03-D — final test matrix

READY_FOR_REVIEW; runtime source9da1b43. 137 Success/0 Failed từ MCP cold clone. Báo cáo chính: [Docs/U03/REPORT-D](Docs/U03/REPORT-D.md); tên từng test/completion, logs, PID/world/owner/role và hash ở [manifest](Evidence/D/MANIFEST.json). C2 historical results là kế thừa; không đếm làm D mới.

|Cổng|Tầng bằng chứng|Kết quả|
|---|---|---|
|Expiry/dedup/scope|D AbsoluteFeedbackWindow, FeedbackDedupAndLateAudio; Native new-life/montage/C2 reset + live feedback audit/reconnect|PASS; 1,2s absolute, old/future/history không replay; voice scope nguồn/đích|
|Miss|AuthorityCompletedMissContactCancel, world30/60/120/long update|PASS: natural miss only; hit/block/parry/cancel không thêm miss|
|Visibility|D RecentHitVisibility predicate + shared C2 projection/LOS; target input15 + combat no-auto-Tab hit HP frame|PASS compositional coverage; không tuyên bố packet injection|
|Settings|U01 BindingValidation/PartialRecovery/SaveAndFailure/LocalMappingIsolation, A1 v1 migration, D LegacyConflictAndFutureSchema|PASS; slot UUID, no user migration/no load rewrite|
|Pose/assets|D DefensePoseAssets + existing attack/animation tests + BP16/ref audit/video|PASS; fixed root/no gameplay notify; mannequin/blockout|
|Build/package/smoke|Editor/Game/UAT +3 map processes|PASS final source|
|Input/audio|Combat24, fixture15, route11, target15; loopback parry single660→990 group + distinct signal bands|PASS; debug messages off in fixture, failed runs retained|
|Lifecycle/settings launcher|5 Boot loops, Quit/reopen; actual PlayD stable path save/reopen; defaults restored by UI|PASS|
|Network|Dedicated Editor +2 clients and reconnect,26 checks +41 independent comparisons|PASS; owner/proxy, HP/resource/result, Retry isolation/stale claims|
|Profile|Monotonic raw frame intervals during authority combat; cap60/server30, C2 quality/smoothing preserved|Measured; numeric results/limits in report; not U04 acceptance|
|Launch/Stop|Source/module/engine/package guards, occupied port/concurrent Solo refusal, unique session log identity and placement restore|PASS; Solo/A/B preferences separate and persistent|
|U03.01–09 regression|Full137 includes timing/model/world30/60/120 and long updates, wall/StepUp/two-pawn dodge, lethal cutoff, lock/focus|PASS; model rates are not render FPS|

User checklist is limited to readability, feedback/poses/grip, HUD/occlusion, Retry/focus/two-window feel. Technical verification belongs to AI. Not ACCEPTED, no main merge/U03 closure/U04.
