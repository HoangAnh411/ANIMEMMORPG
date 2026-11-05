# U02-A — ACCEPTED

**Đã được reviewer nghiệm thu kỹ thuật tại 914f7af, source f11c944; người dùng cho phép khép hồ sơ/fast-forward main và triển khai riêng B.** [Căn cứ review](ACCEPTANCE-A.md). Không chạy lại build/tests khi khép hồ sơ; giữ nguyên manifest/binary SHA của lượt đã review.

## Hồ sơ bàn giao lịch sử tại 914f7af

Các trạng thái READY_FOR_REVIEW/chưa merge/chưa B dưới đây mô tả thời điểm bàn giao A và đã được quyết định ACCEPTED phía trên thay thế.

Đã hoàn tất riêng U02.00: hợp đồng, kiểm kê asset, model action/lifetime thuần và clock-controlled tests. **Chưa nghiệm thu, chưa merge, chưa bắt đầu B.** Không tích hợp input/combat component/motor/RPC/collision/vital/montage runtime.

## Nguồn và phạm vi diff

- Nền đã fetch/kiểm tra lại: main và origin/main `e4ab61812b5a1e3d954a1c8f3d2a1b4fb9535560`, U01-G ACCEPTED. Nhánh riêng `u02/a-contract-model` đã push.
- **Source build/test cuối: `f11c9449f9f060d13c86b3b7e25387ba01ce735f`**, đã push trước build. Commit bàn giao sau source này chỉ cập nhật hồ sơ/scripts kiểm kê/niêm phong bằng chứng, không đổi Source/Content/Config/Plugins/project; không gán SHA hồ sơ cho binary.
- Source mới chỉ `U02/U02ActionModel.h/.cpp` và `Tests/U02ActionModelTests.cpp`, trong module hiện tại. Không đổi code U01, mesh/skeleton/socket/Blueprint/map/config/plugin/module. Không GAS/framework.
- Working tree ban đầu chỉ có thay đổi riêng `Config/DefaultEngine.ini`; hash trước/sau xác nhận **nguyên byte**, không in/stage token, không restore file workspace. [Manifest](Evidence/A/MANIFEST.json) ghi kết quả đối chiếu, không lưu nội dung config riêng.
- Hồ sơ: [CONTRACTS](CONTRACTS.md), [TEST-MATRIX](TEST-MATRIX.md), [ASSETS](ASSETS.md). Xem diff bằng `git diff e4ab618..u02/a-contract-model -- Source Scripts/U02 Docs/U02`; config riêng không thuộc diff commit.

## Ba trọng điểm review

**Sweep qua toàn active:** `AdvanceAction` trả phần active đã clip ngay cả khi phase ở cuối update là Finished. Trace thực `previous=0 now=0.5 clipped=[0.16,0.22) alpha=[0.32000000000000001,0.44]`. Kiểm active-entry point0.160, end0.220 excluded, các bước1/30,1/60,1/120,0.007,0.5; discontinuity chỉ overlap current-point khi còn active, không nối teleport. Không epsilon trong gameplay comparisons. Đây là interval/alpha model; **chưa phải sweep collision hình học**. Hợp đồng D cấm broadphase chỉ lấy endpoints, cấm sweep startup/recovery, cấm bỏ cả contact interval vì contact đầu bị tường chặn.

**Resolve/death:** `FResolveLedger` kiểm alive/life/action window/dedup; comparator timestamp → source FGuid words → event ID → hurtbox ID. Test 24 hoán vị cùng tập candidate cho kết quả giống nhau: source1 giết source2 tại0.18, retaliation từ source2 bị loại ngay; duplicate hurtbox không nhân hit; source1 vẫn trúng source3 tại0.19. Death được fixture áp ngay trước event kế tiếp. Hợp đồng buộc gom toàn world trước sort, resolve batch cũ trước nhận action mới tại now, không tự resolve theo actor Tick/callback. **Chưa có HP/RNG/damage hoặc world scheduler runtime**. Reset snapshot giờ có Life riêng cả khi Idle, không dùng action đã xóa để suy lượt sống.

**Combat lock–release gate:** pure policy tách Control/Interacting/Defeated/Combat; tests dùng `FReleaseGate` thật của U01 để giữ W qua recovery, vẫn giữ menu/LMB gate tới physical release. Server combat lock không thể bị saved-combat false xóa trong replay policy. Đã chỉ rõ đường U01 hiện gán toàn LockMask trong PrepMoveFor; B phải tách quyền server khỏi replay data và mask effective intent mà không gate heldW. **Chưa sửa movement replay hoặc kiểm input Windows thật**; click Resume/held-input/focus là cổng B, không được coi model PASS là runtime PASS.

## Build và Automation thực

Engine **UE5.8.4 CL58902052**, MSVC14.51.36260/toolset14.51.36231, SDK10.0.26100.0. Full build bằng `Scripts/U00.ps1 -Task Build`, clone riêng `Artifacts/U02/A/Source`; Editor gốc PID3508 giữ mở. New plain C++ header/layout được kiểm bằng cold clone; **không dùng Live Coding để khẳng định Editor gốc đã nạp layout mới**. Khi cần sử dụng code mới trong Editor gốc phải gom full build/restart vào mốc thích hợp; A không yêu cầu restart Editor gốc.

Run cuối: **Build-20261105-195827-588-d266707a** — Generate0, Editor0, Game0. Exact commands/engine và exit codes: [BUILD-RESULTS.json](Evidence/A/BUILD-RESULTS.json); logs nguyên văn nén gzip, SHA256 cả raw/gzip: [LOGS.json](Evidence/A/LOGS.json). Compiler output kết thúc `Result: Succeeded`; không suy từ trigger.

Automation: **MCPTests-20261105-200027**, cold Editor PID trong [PROCESS.json](Evidence/A/PROCESS.json), bắt đầu2026-11-05T13:00:27.9120319Z. `VerifyATests.ps1` đọc schema clone, gọi TestRunner `run_automation_tests` filter `AnimeMMORPG.U02.A`, poll LogsToolset `GetLogEntries` và kiểm mỗi path đúng một Success cùng queue 7 tests. **7 executed, 7 Success, 0 Failed** trên source cuối; [kết quả từng test](Evidence/A/AUTOMATION-RESULTS.json), [raw MCP result](Evidence/A/MCP-RESULTS.json), [timeline](Evidence/A/TIMELINE.log).

| Test prefix `AnimeMMORPG.U02.A.` | Kết quả |
|---|---|
| PhaseDeadlines | Success |
| WholeActiveInterval | Success |
| CancellationAndAim | Success |
| IntentIdentityAndReset | Success |
| CombatLockReleaseGateBoundary | Success |
| ResolveDedupAndGeneration | Success |
| StableResolveDeathOrdering | Success |

Module Editor SHA256 `a3c6165e074e260fb8711b1b36e3d13c0b43db8dbc2e242c263c8c9dae9cddd1`; Game exe SHA256 `5bda672197817697ed7bfb00ecc3479071bf405917e709b0d541649841734952`. Full paths/hash engine exe/Git blobs nguồn trong manifest. Model tests không có Game-world pawn/owner/net roles: ghi N/A, không dùng actor Editor làm bằng chứng gameplay.

## Asset audit và lựa chọn C

Audit read-only cuối trong Editor gốc PID3508, log2026-11-05T12:56:25.828Z: **121 assets tải được**. [Metadata/hash](Evidence/A/ASSETS.json), [log audit](Evidence/A/ASSET-AUDIT-LOG.json). **109 hash khớp register template U00; 12 asset U01 khớp LFS SHA256 của main đã nghiệm thu**, 0 mismatch: [provenance](Evidence/A/PROVENANCE.json). Không cấp giấy phép mới hoặc dùng hash thay bằng chứng quyền.

Chốt **C tự tạo animation blockout trên SK_U01**. Có clip attack template nhưng chưa có clip kiếm trên SK_U01 được xác minh cho grip/timeline0.40; ba attack clip nguồn1.0s bật root motion. Không tải/mua asset, không tự nhập montage/notify template. Asset mới chưa tạo trong A nên hash/preview/cook của blockout mới còn NOT RUN ở C; art anime/carry sản phẩm DEFERRED.

## Lịch sử lỗi, warnings và giới hạn

- Build đầu `Build-20261105-194856-766-8e32f7a5`, source3c38af5, Editor exit6: `U02ActionModelTests.cpp(8,34): error C2440: 'initializing': cannot convert from 'EAutomationTestFlags' to 'const uint32'`. Đã sửa giữ kiểu enum ở af38cbd; log lỗi nguyên văn vẫn được lưu. Lượt af38cbd build Editor/Game và 7/7 tests đạt được giữ trong RUN-HISTORY, **không cộng thành 14 tests cuối**.
- Rà soát reset bổ sung `FCombatSnapshot::Life` cùng assertions tại f11c944; vì source đổi nên chạy lại build và 7 tests. Đây là lý do chạy lại, không lặp regression U01 hàng loạt.
- Preflight test cuối đã reject tracked clone config dirty vì Editor lượt trước tự sinh đúng một dòng SecurityToken. [Log reject](Evidence/A/PREFLIGHT-REJECTED.log). Không in giá trị/không bỏ guard; chỉ xóa đúng dòng tự sinh trong **clone đã xác minh đường dẫn**, clean-tree rồi chạy lại. Editor có thể lại tự sinh dòng đó lúc mở; không commit config clone. Workspace gốc nguyên byte. Không có token assignment được phát hiện trong logs chuẩn bị bàn giao.
- Asset audit đầu 120 bỏ sót class BlendSpace1D. Đã sửa filter và audit lại 121, gồm BS_U01_Locomotion; giữ log cả hai lượt, không giữ số 120 làm kết quả cuối.
- Final build/test logs không có Error; warnings còn gồm compiler newer-than-preferred, deprecated APawn::GetMovementBase và C4305 double→float tại U01AnimationTests.cpp359/362; MCP EULA warning. [Warnings exact](Evidence/A/WARNINGS.json) và full logs giữ nguyên; không mở AllToolsets để che warning. Các warning ở lượt trung gian cũng còn trong archive.

Phân loại bằng chứng: **Automation7/7**; hậu xử lý kiểm completion/identity/hash/provenance/config invariance đạt (không phải Automation tests bổ sung); **input thật/video/user-feel NOT RUN**, chưa có gameplay A để đánh giá. Windows package/cook/smoke 3 maps, dedicated server / 2 clients, collision geometry, damage/shield/crit/death runtime đều NOT RUN trong A, thuộc B–F đúng ma trận. Không tuyên bố pure model đủ nghiệm thu các cổng đó.

U01-G: 23 Automation / 3 maps / runtime là **bằng chứng kế thừa đã đọc**, không chạy lại A. Source binary/package G vẫn `5f8a6eabe103a8b31a894c82f32cffb0325474a9`; không gán SHA source A/commit hồ sơ cho binary cũ. Chưa Server đóng gói/U05/PvP tự do.

Rủi ro mở theo owner: B — heldW/menu gates, authority LockMask và yaw replay; C — carry ghi đè montage/grip/root; D — hệ tọa độ, relative sweep/obstruction completeness và global ordering; E — vital/death/reset đồng bộ ledger, HP0 không được fixture U01 bỏ Defeated; F — stale/session IDs, disconnect, source/binary/process/script paths. Đã chốt yêu cầu và tests tương lai trong CONTRACTS/TEST-MATRIX, không đánh dấu các rủi ro runtime đã đóng bằng tests A.

**Bàn giao READY_FOR_REVIEW riêng A.** Review tập trung ba đoạn trên và trace/source tương ứng. Không còn phép kiểm bắt buộc của A đang thiếu; không suy thành nghiệm thu U02. Main giữ e4ab618; không merge hoặc bắt đầu B.
