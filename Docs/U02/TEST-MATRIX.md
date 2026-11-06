# U02 — Test matrix

**A ACCEPTED tại 914f7af/source f11c944: 7/7 Automation và review evidence đạt.** [Căn cứ](ACCEPTANCE-A.md). Không chạy lại kiểm chứng để khép hồ sơ.

A là model thuần; B ACCEPTED tại95a83ca/source94ebcc7 trên source94ebcc7: full34Automation, smoke3maps, input40assertions; [REPORT-B](REPORT-B.md). C READY_FOR_REVIEW source61be83b:37Automation/3smoke/63assertions, xem REPORT-C. D–F chưa triển khai/chưa chạy. Tên dưới A là Automation tests thực đăng ký; cột evidence được khép bằng kết quả thực ở REPORT-A. Không ấn định tổng số tests tương lai.

| ID | Automation A | Nội dung và giới hạn |
|---|---|---|
| A-TIME | `AnimeMMORPG.U02.A.PhaseDeadlines` |0/0.159/0.160/0.219/0.220/0.399/0.400, exact deadlines, monotonic/finite clock, definition validation, trace phase/lock. |
| A-SWEEP | `AnimeMMORPG.U02.A.WholeActiveInterval` |0→0.5 clip toàn active/alpha, 30/60/120 và7ms/500ms bước mô phỏng, active-entry point/stationary evaluation, no zero-dt duplicate, discontinuity no connecting sweep. Chưa collision geometry. |
| A-CANCEL | `AnimeMMORPG.U02.A.CancellationAndAim` |Dodge/Guard qua CancelAction thật tại0.159, từ chối0.160/0.219/0.220/0.399; authority invalidation; startup aim/active yaw lock; menu/focus không cancel. Chưa input/runtime. |
| A-ID | `AnimeMMORPG.U02.A.IntentIdentityAndReset` |Busy reject/no buffer, duplicate/rejected command, admission context, nonfinite aim, generation reset/identity, command watermark không reset. |
| A-LOCK | `AnimeMMORPG.U02.A.CombatLockReleaseGateBoundary` |Policy combat vs control/Defeated; heldW recovery với FReleaseGate U01 thật; menu/LMB physical rearm; authority combat giữ khi replay policy. Chưa movement replay thật/click Resume. |
| A-RESOLVE | `AnimeMMORPG.U02.A.ResolveDedupAndGeneration` |Active bounds, duplicate action/hit, blocked hurtbox không dedup, nhiều hurtbox, source/target reset, death once. Geometry flag/HP là fixture, không collision/damage thật. |
| A-ORDER | `AnimeMMORPG.U02.A.StableResolveDeathOrdering` |24 permutations, timestamp/source/event/hurtbox ordering, hai lethal cùng timestamp không trả đòn từ source chết; cutoff cancel. Lethal fixture không vital runtime. |
| A-ASSET | Registry/load + SHA256 + provenance register |121 assets metadata; chọn tự author blockout C. Không asset mutation/render quality proof. |
| A-BUILD | Full Editor/Game build trong clone |Code mới build từ source SHA đã push; không coi Editor gốc đã nạp header/layout. |

| Đợt / ID | Kiểm chứng bắt buộc còn lại | Trạng thái A |
|---|---|---|
| B-ACTION |Authority component/inputLMB thật/edge/busy/clock0.16/0.22/0.40/aim/yaw, cancellation fixtures, diagnostics |PASS kỹ thuật: REPORT-B; đã nghiệm thu B |
| B-MOTOR |StopXY/gravity/move-jump-sprint lock, heldW recovery, menu/focus/Resume click suppression, lost-ground/Interacting/Defeated; saved move authority lock và U01 camera/gates regression |PASS kỹ thuật theo bằng chứng B; giới hạn injected-key qua Alt-Tab ghi REPORT-B; đã nghiệm thu B |
| C-PRESENT |Blockout/montage0.40/late seek/action IDs, notify bỏ/lặp không hit, root0displacement, carry/grip, finish/cancel/death/lost-ground, landing/locomotion, BP compile/references/cook |ACCEPTED technical blockout at cdaf102 / source 9aa7249 |
| D-GEOMETRY |Feet/world-local/center/extents; trước/sau/ngoài/chạm biên; multiple targets/hurtboxes; target không che target |NOT RUN |
| D-WALL |Kín/góc/partial hurtbox; origin inside solid; segment nearest-point; target lộ ra sau vật cản trong active; blocked candidate không consume dedup |NOT RUN |
| D-INTERVAL |Whole-active between updates, target xuyên hộp (endpoints ngoài), stationary, relative sweep clip0.16/0.22, reset/teleport no arena sweep; collider/order permutation |NOT RUN |
| E-VITAL |60/90, factors/round-half-up, shield source replacement/order/deadline/overkill; death once/immediate rejection; lethal ordering/reset old events, held input reset, cancel rights |NOT RUN |
| E-WINDOWS |Packaged input hụt/trúng/tường/nhiều hurtbox/menu/focus, smoke3maps, Boot/Quit/reopen; full U00/U01/U02 đúng binary; package hash/cook3maps |NOT RUN |
| F-AUTHORITY |Dedicated Editor server0LocalPlayer+2owned clients, confirmed action/result/HP, hụt/trúng/tường/multihurtbox/concurrent lethal, duplicate/stale/ownership/nonfinite/self-declared data, disconnect/reconnect lifetime |NOT RUN |
| F-PRESENT |Client montage phase/action, HPserver, menu/focus không pause, movement/smoothing/settings regression, profile30/60/60 actual cvars, session-safe launcher/capture/Stop |NOT RUN |
| F-CLOSURE |Source→binary/package→run→IDs→results manifest/logs/video; user checklist cảm giác/aim/3phases/kiếm/pose/movement/focus2clients; không mục bắt buộc thiếu evidence |NOT RUN |

U01 23 Automation/3 smoke/runtime là **kế thừa từ G**, không tự tính vào số đã chạy A. A chỉ cần tests liên quan; E/F mới full regression bắt buộc. Loại bằng chứng tách riêng: Automation / hậu xử lý assertions / input thật-video / user review. Không dùng model lock làm PASS motor thật; không dùng boolean obstruction làm PASS tường; không dùng lethal fixture làm PASS HP.

C startup-turn revision: StartupTurnTrajectory (shortest arc, tie, retarget/deadline, 30/60/120 Hz), ActualBodyAndSkippedBoundary (real actor yaw before full skipped active delivery), ProxySamplesActionTurn (role fixture), and inherited motor/replay/presentation tests. Final manifest/results: Evidence/C-Turn. Real input/video and actual transform traces are separate from Automation. C accepted by user at cdaf102 / source 9aa7249; remote pending.
