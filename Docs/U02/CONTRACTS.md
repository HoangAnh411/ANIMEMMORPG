# U02 — Hợp đồng A / U02.00

Trạng thái: **A ACCEPTED tại 914f7af/source f11c944**, theo [căn cứ review](ACCEPTANCE-A.md); không là nghiệm thu U02 tổng thể. Nền main/origin/main đã fetch: `e4ab61812b5a1e3d954a1c8f3d2a1b4fb9535560`. Nguồn luật theo thứ tự: [Description](../Description.md), [ROADMAP](../ROADMAP.md), [U01 contracts](../U01/CONTRACTS.md), [closure G](../U01/G-MATRIX-CLOSURE.md). Quyết định người dùng trong kế hoạch U02 và lệnh triển khai A là ranh giới giai đoạn. Không sửa Description để xóa buffer/combo sản phẩm.

## Phạm vi, ownership và giao diện

A chỉ có value model C++ trong module AnimeMMORPG hiện có, tests và hồ sơ. Không bind LMB, thêm component lên pawn, sửa motor, RPC, map, Blueprint, montage hoặc damage gameplay. Không thêm GAS/framework/module/plugin. Giữ AU01Character, UU01CharacterMovement, controller/menu/settings, saved moves, camera; combat runtime dùng composition. Giữ Boot, trạm U01 ở CharacterCombatLab và NetworkLab; combat station/fixture bổ sung sau.

| Phần | Quyền và giao diện đã chốt |
|---|---|
| `FAttack1Definition`, `FActionModel` | Luật đòn 1, phase, deadline, admission/cancel. `SubmitAttackIntent`, `AdvanceAction`, `CancelAction`, `GetCombatSnapshot`, `ResetLabCombat` đã có model thuần. Không UObject/render/world dependency; Core math/container được phép. |
| `UU02CombatComponent` (B, chưa có) | Gắn AU01Character; server duy nhất cấp action, validate command/aim/ownership/context, gọi model, replicate snapshot. Standalone cùng authority path. |
| `FU02WorldResolver` (D, chưa có) | Một owner theo Game/PIE world; `CollectHitCandidates(FActiveSlice, previous/current collision snapshots)`; gom mọi nguồn trước sort/resolve. Không resolve trong actor Tick/overlap. |
| `UU02HurtboxComponent` (D, chưa có) | Collider → FLifeId + stable HurtboxId; chỉ cung cấp snapshot/candidate. Không sửa vital. |
| `UU02VitalComponent` (E, chưa có) | Server giữ HP/shield/damage/death/life generation; `ResolveHit` kiểm lần cuối trước mutation. `FResolveLedger` A chỉ mô hình hóa lifetime/window/dedup; không tính damage. |
| `FU02PresentationAdapter` (C, chưa có) | Chỉ đọc replicated `FCombatSnapshot` và confirmed result; điều khiển montage/HUD. |
| Lab fixture (B–F, chưa có) | Server-only `ResetLabCombat`, spawn dummy, cấp shield, RNG/cancel fixtures; không API gameplay công khai/shipping. |

Authority checks thuộc adapter, không phải bool client tự khai. Model A không là security boundary hoặc runtime implementation của các thành phần dự kiến. Tên giao diện có scope hẹp cho đòn 1, không xây framework nghề/kỹ năng tương lai.

## Action, clock và input

Đòn 1: raw60, không tốn năng lượng, không Feint; startup `[start,start+0.16)`, active `[start+0.16,start+0.22)`, recovery `[start+0.22,start+0.40)`. Đúng end là hết. Config duy nhất immutable trong adapter; `FAttack1Definition::IsValid` kiểm đúng thông số khi load, không BP override theo instance. Không epsilon trong luật. Test tolerance chỉ dành sai số tổng/tọa độ, không gia hạn deadline.

Clock double từ mô phỏng world/server, không wall clock/frame. Deadline tạo bằng `start + duration`, so sánh trực tiếp các deadline; không đổi thành số frame. World/session mới dựng model/ledger mới, xóa deadline/command/input/snapshot cũ. Reset lab cùng world giữ clock và anti-replay command, tăng generation. Model từ chối NaN/infinity/clock lùi. Snapshot chỉ đọc tại clock hợp lệ của adapter, không gọi với thời gian tùy ý từ client.

Giữ bốn mốc riêng: local input (diagnostic only), server receive, server accept/start, gameplay timestamp phase/hit. Không lấy timestamp client làm start hoặc backdate hit. Mỗi lượt update authority: advance/collect action cũ của mọi source tới server now → sort/resolve toàn batch tới now (cập nhật death/cancel ngay) → nhận intent tại now theo thứ tự server và trạng thái đã resolve → cấp action mới nếu đủ quyền. Lệnh/cancel đã đóng dấu giữa khoảng mô phỏng phải vào timeline đúng timestamp, không áp ở cuối khoảng rồi hồi tố xóa hit trước đó. Phải drain interval cũ trước thay action kể cả action đã finished theo now. Aim command được đóng dấu server; aim tới sau biên active không được thay yaw đã khóa. Khi frame vượt biên, lock dùng aim hợp lệ mới nhất trước biên, không lấy aim tương lai tại cuối frame.

LMB chỉ physical rising edge. Giữ không lặp; edge khi busy bị reject, không lưu lệnh chờ. Chỉ U03 mới buffer/combo. Reject khi airborne, Interacting, Defeated, control khác Playing hoặc busy; trả reason, không tốn tài nguyên/cấp action mới. Connection/session sequence tăng (uint64, 0 reserved); consume sequence của command đã xử lý kể cả reject, không replay sau unlock/reset. Ownership/finite validation trước mutation; client không gửi damage/HP/hit outcome. Không wrap ID: hết sequence/generation phải báo lỗi và kết thúc session, không tái sử dụng identity.

Cancel Dodge/Guard chỉ startup, qua chính `CancelAction`; fixtures dùng API này, không làm gameplay Shift/RMB. Active/recovery không voluntary cancel. Death/reset/removal/lost-ground invalidation được phép dừng phần chưa phát; menu/focus không cancel accepted action. Cancel tại t: xử lý interval trước t theo ordering, cutoff từ t (t excluded); không hồi tố xóa confirmed hit. Reset/removal/death vô hiệu candidate còn chờ đúng lifetime. Adapter phải clip trước khi gọi model cancellation, không advance sau cancel rồi kỳ vọng lấy lại interval trước đó.

## Combat lock và release gate — cổng kiến trúc B

Attack accepted dừng ngay velocity XY, acceleration và sprint; khóa move/jump/sprint, xóa jump buffer/coyote pending, giữ gravity/Z. Không biến phím WASD đang giữ thành blocked chỉ vì combat. Startup thân theo aim yaw mới nhất hợp lệ, active/recovery khóa yaw; camera tự do. Hết recovery dùng lại held WASD; locomotion quay thân lại theo movement.

`Combat` là bit riêng, không reuse `Control`, `Interacting`, `Defeated`. Local movement intent vật lý và effective motor intent là hai lớp: giữ trạng thái WASD, chỉ mask khi combat; không gọi `FReleaseGate::Lock`/`GateHeldKeys` khi attack bắt đầu/kết thúc. Sprint chỉ hoạt động lại khi có hướng và mọi điều kiện motor hợp lệ. Jump cần edge mới, không phát lại jump buffer từ trước attack.

Menu/focus/Interacting/Defeated vẫn giữ policy release gate U01. Menu/focus xóa input chờ, AwaitingResume khi mất focus; accepted action/recovery/world/gravity tiếp tục. Gate LMB vật lý cả khi UMG ăn click; hold xuyên menu/Resume/reset không sinh edge. Click Resume bị consume ở UI, phải release + press mới để attack. Nếu menu xảy ra trong attack, kết thúc combat không xóa gate menu; các lý do khóa còn lại vẫn hiệu lực.

Code U01 thực: `EU01MotorLock` mới chỉ Control1/Interacting2/Defeated4; `FSavedMove_U01::PrepMoveFor` hiện gán toàn `LockMask=SavedLocks`; `UpdateFromCompressedFlags` chỉ truyền Control bit. B phải tách authority combat mask khỏi dữ liệu saved-move client: effective combat ít nhất `AuthorityCombat || SavedCombat` khi replay, sau reconcile recompute từ snapshot action server. Client không xóa hoặc tạo server action qua flag. Không restore stale authority bits từ saved move. Đây là yêu cầu B, A chỉ test policy thuần với FReleaseGate thật của U01; chưa chứng minh replay/movement/input runtime.

Khi E có vital, U01 fixture không được clear Defeated lúc HP0; chỉ reset combat hợp lệ được phục hồi. Không gọi reset lab là hồi sinh sản phẩm.

## Collision, interval và snapshot — cổng kiến trúc D

X forward, Y right, Z up; cm world. Hộp từ feet, không capsule center: full200×120×180, half100/60/90; center `feet + yawForward*100 + worldUp*90`; yaw khóa tại đầu active. Kiếm/mesh/socket chỉ trình bày, không collision/damage.

| Đối tượng | Movement | CombatCandidate | CombatObstruction |
|---|---|---|---|
| Môi trường rắn | U01 giữ nguyên | Không target | Block |
| Body capsule | U01 giữ nguyên | Ignore | Ignore |
| Hurtbox | Không ảnh hưởng | Query, stable ID | Ignore |
| Mesh/kiếm | Trình bày U01 | Ignore | Ignore |

D dùng hai query channel riêng `U02CombatCandidate`, `U02CombatObstruction`; chọn slot trống sau kiểm config thực, không hardcode số slot trong A. Chỉ những collider môi trường rắn chủ ý mới block obstruction; ignore owner/body/hurtbox/mesh. Broadphase phải lấy mọi hurtbox có thể chạm trong interval, không single blocking sweep dừng ở target đầu. Không dựa riêng overlap ở hai endpoint để tìm target đi xuyên rồi ra.

Mỗi update xử lý giao của `[PreviousTime,Now]` với active nửa mở. `FActiveSlice` trả begin/end tuyệt đối, alpha so với **interval snapshot gốc**, và end-exclusive nếu chạm active deadline. Ví dụ prev0/now0.5 → `[0.16,0.22)`, alpha0.32/0.44, dù phase ở now đã Finished. Không chỉ kiểm `PhaseAt(Now)==Active`. Frame 0.159→0.160 kiểm overlap điểm tại0.160; now==prev không query lại. Frame 0.219→0.220 chỉ lấy trước0.220, không candidate đúng0.220. Stationary hurtbox vẫn overlap trong active.

Snapshots trước/sau gồm server time, feet world cm, hurtbox transform/shape/local binding và FLifeId + continuity epoch. Nội suy tuyến tính vị trí feet và hurtbox tại alpha đã clip; attack axes/yaw cố định trong active. D narrowphase phải tìm thời điểm tiếp xúc sớm nhất của chuyển động tương đối trong đoạn clip, không sweep từ vị trí cuối lên hộp cuối rồi suy thời gian; dựng geometry tương ứng tại candidate time. Shape/rotation dùng cấu hình hurtbox đã snapshot; thay đổi topology/shape hoặc teleport/reset tăng continuity epoch, không nối qua discontinuity. Với interval bị đứt: chỉ current-point overlap nếu now còn active; nếu now đã recovery thì không quét xuyên khoảng teleport. Không hứa phát hiện đường cong hoặc tường động giữa hai snapshot; không rewind/lag compensation. A chỉ chứng minh clipping/alpha/discontinuity policy; thuật toán collision hình học, broadphase completeness, tolerance hình học và tests world thuộc D. Hình học tiếp xúc biên được tính giao (closed spatial bounds), nhưng timestamp vẫn phải trong active half-open; numerical tolerance hình học không kéo dài active.

Tại candidate time, xét từng hurtbox giao vùng: đoạn từ **feet attacker + up90cm** tới điểm gần nhất trên hurtbox. Origin nằm trong môi trường rắn → blocked (kiểm initial overlap trước ray). Segment bị môi trường block kể cả chạm mặt tường → hurtbox invalid. Một hurtbox hợp lệ đủ; target không che target khác. Không gom target trước obstruction rồi chỉ thử một hurtbox tùy callback. Trong nhiều hurtbox chọn contact hợp lệ sớm nhất; hòa stable HurtboxId tăng. Candidate blocked/invalid không tiêu dedup. Nếu hurtbox còn giao vùng nhưng đường che khuất thay đổi trong interval do target di chuyển, D phải tìm contact hợp lệ sớm nhất trong phần giao đó; không loại cả interval chỉ vì contact đầu bị chặn. Broadphase/narrowphase phải giữ contact interval đủ để xét việc lộ ra sau vật cản, không chỉ một callback đầu. D phải kiểm riêng tường kín/góc/che một phần, target đi xuyên và teleport; model boolean A không thay bằng chứng này.

## Identity và resolver/death — cổng kiến trúc D/E

FLifeId = server `NetworkPawnId` FGuid hiện có + uint64 generation (bắt đầu1); dummy cũng cấp ID server. FActionId = source life + server action sequence (bắt đầu1 mỗi life). FHitId = action + target life; không gồm HurtboxId, để dedup mọi hurtbox của target. Candidate có HurtboxId ổn định, 0 invalid; ID từ fixture/asset registration được lưu, không lấy địa chỉ/thứ tự đăng ký collider. Session/world ID đặt ngoài ID trong envelope, không trộn events khác world. Command sequence thuộc connection/session, life reset không reset sequence. Không dùng actor display name/pointer/TSet order để sort.

Sort toàn bộ world batch: gameplay timestamp tăng → source NetworkPawnId tăng → event ID tăng. So FGuid bằng unsigned words A,B,C,D, không byte memory/chuỗi locale. Event ID so source generation, action sequence, target pawn words, target generation. Cùng hit/time hòa bằng HurtboxId. Loại nonfinite timestamps trước sort (comparator giả định finite); kiểm session/world/ownership/lifetime trước enqueue và lại trước mutation. Duplicate cùng ID mà payload mâu thuẫn phải diagnostic/reject; không nhận damage từ payload.

World resolver gom candidate từ mọi source trong cùng khoảng mô phỏng rồi resolve theo comparator, không mỗi actor resolve ngay. Không cho event mới có timestamp nhỏ hơn phần batch đã resolve; event nội sinh phải được chèn đúng sorted queue trước tiếp tục. `FResolveLedger` là primitive dùng sau sort, không tự scheduler. Nó kiểm source/target còn sống đúng generation, action registered, active/cancel cutoff, geometry/obstruction đã xác minh và per-target/action dedup. Chỉ valid hit mới mark dedup. Confirm result ID giữ nguyên FHitId, duplicate replay chỉ trả kết quả cũ, không roll RNG/trừ HP lần nữa.

Ngay sau valid hit: vital áp damage/shield và nếu HP0 phát death **đúng một lần**, mark source life chết/hủy action và pending output ngay, **trước lấy event kế tiếp**. Không trì hoãn death tới cuối Tick/batch. Hai lethal A→B và B→A cùng timestamp: source ID nhỏ hơn resolve trước; nếu B chết thì B→A bị loại, không cùng chết theo snapshot đầu batch. Tests A dùng lethal fixture và ledger, chưa có HP implementation. Hit target đã chết cũng bị loại. Removal/disconnect vô hiệu life trước resolve tiếp, không để orphan source gây damage. Death không rewind confirmed result trước đó.

Reset lab server-only: HP đầy theo fixture, shield/action/candidate/dedup cũ xóa, generation tăng, pressed input không tạo edge mới, ID cũ không tác động life mới. Ledger A xóa source windows/dedup liên quan và từ chối generation lùi/trùng; world resolver D còn phải xóa queued candidates/snapshot continuity. F kiểm disconnect/reconnect/session ID mới, ownership và pending action thực.

## Damage, trình bày và kiểm chứng các đợt sau

E: player1000HP/dummy600HP; damage = raw × attack ×100/(100+defense), defense≥0, rồi crit/block, **round-half-up sau toàn bộ hệ số**. Default attack1/defense0:60 thường/90 crit; crit server5%, ×1.5, một roll mỗi valid hit. RNG tests điều khiển; fixture tắt crit phải ghi HUD/log. Không tiêu năng lượng. Shield cùng source thay capacity/deadline, khác source cộng; expire tại đúng deadline, consume deadline sớm rồi sourceID tăng. HP clamp0; overkill/death once. Không cấp kỹ năng shield; chỉ fixture. Không triển khai đỡ/parry gameplay trong U02.

C: nguồn animation theo ASSETS; C++ giữ luật, BP chỉ asset/input/UI. Montage sections startup/active/recovery ánh xạ timeline0.40; play rate/section mapping không thay clock. Notify chỉ SFX/VFX, thiếu/lặp không ảnh hưởng hit. Snapshot trễ seek current phase/time, không replay damage; cancel/death/reset dừng đúng action ID, stale stop không dừng action mới. Carry không ghi đè tay attack; grip/socket giữ attachment. Không root-motion displacement vào capsule. Clip tự tạo kỹ thuật, anime/carry sản phẩm vẫn DEFERRED.

Mỗi đợt A→F riêng: accepted main → branch → implementation/validation → commit/push → report → stop. READY_FOR_REVIEW không là nghiệm thu; chỉ người dùng merge/giao đợt sau. E Windows package/input thật/full U00/U01/U02; F dedicated Editor server+2 clients, server0LocalPlayer, caps30/60/60 với profile U01, giữ Editor mở/minimize có identity, đọc cvar thực. Không Server target/source-engine download/U05/bad network/PvP tự do. Hai chủ thể đánh nhau chỉ fixture rõ ràng.

## Diagnostics envelope

Mỗi run: runId, UTC, sourceSHA, engine/toolchain, exe/DLL/package SHA256, PID/executable, project, world path/type/context/sessionId, map/netMode, localPlayers, pawn/owner/controller, local/remote roles. Model tests không có pawn/runtime world: ghi N/A thay Editor actor làm bằng chứng. Input/phase/hit: connectionSessionId, commandSequence, localInputTime (clock domain riêng), serverReceive/accept/gameplayTimeSeconds, FLifeId/FActionId/FHitId/HurtboxId, prev/now/clipped interval/alpha, continuity epoch, feet/locked yaw/query center/extents, obstruction endpoints/result, accepted/rejected reason, cancel cutoff, phase, lock mask/release gate, HP/shields/crit roll/result/death. Tách log intent/candidate/confirmed; server kết quả authoritative.

Giữ failed runs/reject/warnings và exact logs. Automation, hậu xử lý, input/video và user visual review là các loại bằng chứng riêng; trigger/zero-tests/compile thành công không là runtime PASS. Header/reflection/layout mới full build clone; không tự đóng Editor gốc hoặc giả định patch layout. B–F chưa chạy trong A. Không phát sinh mâu thuẫn gameplay mới âm thầm; dừng phần phụ thuộc và báo rõ nếu đối chiếu thực phát hiện xung đột.


## C revision: startup body turn

Attack aim stays server-owned. Startup following aim does not mean body equals aim in every startup frame. At acceptance preserve current body yaw. Sample shortest-arc smoothstep from segment start/body to aim by the original action active-start deadline (0.16 s). Exactly 180 degrees always takes positive yaw. Retarget during startup samples the current trajectory, starts a new segment there, and keeps the original deadline. Complete body yaw before delivering any active interval, including an update spanning all active. Active/recovery ignore new aim for body orientation. Camera stays free. No changes to timings, gravity, locks, release gates or authority.

Replicated action data includes segment start/body and target. Clients sample presentation from server simulation time; they cannot select hit yaw. No generic U01 smoothing changes. Rapid aim changes just before active may require rapid catching up; this revision removes the initial instantaneous turn and does not promise slow motion under all camera input.

Animation revision must include preparation in upper body/shoulders and feet, keep accepted grip/socket and root fixed, and return cleanly to locomotion. Existing C footage is historical and its original 30 FPS encoding played faster than wall time. Correct timestamp resampling and before/after matching views are required for review.

Required evidence: new clone Editor/Game builds, trajectory/adapter plus related regression tests, new Windows package and three-map smoke, guarded input captures with actual body/mesh/aim/action-time diagnostics, real-time videos, hashes and updated launcher/checklist. No technical PASS or user feel acceptance is inferred from the old C artifacts.
