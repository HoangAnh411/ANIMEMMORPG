# U01-E — Đổi phím, thiết lập local và khóa điều khiển

**READY_FOR_REVIEW. Chưa nghiệm thu/merge E; chưa bắt đầu F.** D kỹ thuật/blockout đã được người dùng nghiệm thu tại `1e46f710cec8fbb0dd9de2e6be7d35519bf45d83`. Hồ sơ D được commit/push tại `fc5a43b155eb4da120f7b963e484a1d0489e2976`, bổ sung digest tại `e867af97c53bbf11ea141fe5f8f21efc1e31200a`, rồi fast-forward/push vào main. Nhánh `u01/e-settings` bắt đầu từ main `e867af97c53bbf11ea141fe5f8f21efc1e31200a`.

Nguồn full build, tests và package E cuối: **`c8df4ff2182c0006c11f65466ecec4b9223be5a3`**. Commit hồ sơ bàn giao sau nguồn này không thay runtime/package. [Manifest](Evidence/E/MANIFEST.json) ghi đường dẫn artifact, phiên bản, PID và nguồn; [checklist chơi thử](E-MANUAL-CHECKLIST.md).

## Thay đổi và phạm vi

- Menu có trang Điều khiển: đổi riêng tám hành động tiến/lùi/trái/phải/nhảy/sprint/đổi vai/tương tác. Nhận một phím hoặc middle/thumb mouse; từ chối trùng, reserved, trục/cuộn/gamepad và tổ hợp; không tự đổi chỗ. Escape hủy nhận phím. Ctrl trái/phải thuộc một binding Ctrl.
- `UU01SettingsSubsystem` thuộc LocalPlayer, giữ bản mapping context riêng; không sửa IMC asset dùng chung. Camera mouse/Escape giữ cố định. `UU01ControlSave` có version, payload JSON kiểm kiểu/range/finite/binding, vỏ file kiểm version/độ dài/checksum trước deserialize SaveGame. Lưu local, không có tài khoản/tiến trình nhân vật.
- Sensitivity 0,1–3,0 áp dụng khi kéo, lưu khi thả/Save/Resume; đảo Y, vai mặc định và defaults áp dụng ngay. File thiếu dùng defaults; lỗi từng trường giữ phần hợp lệ, khôi phục nhóm binding xung đột và báo các mục phục hồi. Nạp không tự ghi đè. Lỗi ghi giữ dirty và thông báo; Resume/Boot/Quit chờ lưu thành công, có thể thử Save lại sau khi sửa lỗi ghi.
- Gate input dùng binding hiện tại, kể cả nút chuột; input giữ qua menu/focus/fixture phải nhả trước khi dùng lại. G chỉ bật/tắt fixture Interacting trong CharacterCombatLab. Fixture Defeated vẫn ở menu sân kiểm tra. Camera/menu được phép khi hai lý do khóa motor này hoạt động; gravity tiếp tục. Controller không local/dedicated server không tạo UI/mapping/capture.
- Thay asset: `BP_U01Controller` gán action mới `IA_U01_Interact`. Thay native: Settings mới, Controller/Menu, thêm setter vai mặc định ở Character; tests và scripts E. **Không đổi luật motor C, AnimBP/clip/skeleton/grip/carry D, map hay template.** [Recorder kiểm phạm vi](../../Scripts/U01/RecordE.py) và tests hồi quy xác nhận. Kiếm vẫn blockout, collision/physics/damage tắt.

Carry D là **tư thế mang kiếm tạm** cho bản kỹ thuật, đã được chấp nhận trong phạm vi đó. **Art anime và animation chiến đấu DEFERRED**, sẽ thay/tinh chỉnh theo nhân vật, vũ khí và bộ động tác chính thức; không nghiệm thu hình ảnh sản phẩm trong E.

## Build và Automation

UE **5.8.4 CL58902052**, MSVC **14.51.36260**, toolset **14.51.36231**, Windows SDK **10.0.26100.0**. Clone riêng `Artifacts/U01/E/Source` được checkout SHA đã push, kiểm LFS; không copy Binaries/Intermediate từ project gốc. Full build từ binary đĩa tại `Build-20261104-232437-531-46c7d54a`: **Editor và Game exit 0**.

Native E có lớp/property phản chiếu mới nên dùng cold build/Editor clone, không lấy Live Coding làm bằng chứng. **Editor gốc PID21452 vẫn mở tại Boot, 0 actors, MCP đã đối chiếu sau kiểm chứng; chưa xác nhận nạp native E.** Không yêu cầu đóng/khởi động lại Editor gốc. Local config/token không đưa vào commit.

Cold Editor clone **PID4444**, [AUTOMATION.json](Evidence/E/AUTOMATION.json), MCP TestRunner `MCPTests-20261104-232558`: **21/21 PASS**, đọc log mới đến `Automation Test Queue Empty 21 tests performed`.

| Nhóm | Tests thực chạy, đều Success |
|---|---|
| U00.Foundation (4) | Axes, CallOrder, HalfOpenInterval, Units |
| U01.B (2) | CameraPolicy, ReleaseGate |
| U01.C (5) | FlatMovement, JumpPhysics, JumpWindows, MotorLocks, Terrain |
| U01.D (6) | AnimatedMotor, AssetPolicy, CarryTrajectory, GripIsolationAndAttachment, LandingTransitions, TransitionsAndAttachment |
| U01.E (4) | BindingValidation, LocalMappingIsolation, PartialRecovery, SaveAndFailure |

E kiểm đổi từng action, Ctrl alias, duplicate/reserved/chord/mouse; mapping hai LocalPlayer/template không lẫn; partial recovery/type/version và nhóm trùng ba binding; SaveGame round-trip, file không tự đổi khi load, version lạ, file rỗng/sai header/cắt/sai checksum/quá kích thước; đường dẫn lưu bị chặn thực sự trả thất bại. Đây là tests data/fixture, không coi là input chuột/focus thật.

Hồi quy trên pawn/mesh/AnimBP thật trong **Game physics world**, không lấy Editor world: đi 10s **5000,000260770 cm**, sprint **7000,000365078 cm**; apex dt1/30, 1/60, 1/120 nằm **119,987–119,995 cm**. Records có PID/world/context/net mode/pawn/controller/owner/role/source SHA; đầy đủ 32 dòng đo C/D trong AUTOMATION.json. Không suy controlled input fixture thành FPS renderer.

## Package và input thật

Package cuối `Package-20261104-232646-531-8bba7fa6/Archive/Windows`, BuildCookRun exit 0, **48 files** có [hash manifest](Evidence/E/PACKAGE.csv). Smoke **Boot/CharacterCombatLab/NetworkLab 3/3 PASS**, exit 0, không thiếu asset/lỗi runtime mới; [SMOKE.json](Evidence/E/SMOKE.json). Boot thoát lần đầu chờ PSO khoảng 90s rồi exit bình thường, không đổi renderer hoặc tính thành PASS trước khi process hoàn tất.

Win32 SendInput vào đúng HWND/PID/executable, guard foreground, capture client bounds; metadata có binary SHA256, event UTC và capture rate thật. Các phiên cuối PID **18956** (đổi phím/locks), **21596** (mở lại/lifecycle), **9408** (lỗi ghi/phục hồi), **20936** (file hỏng), đều standalone Game world. **58 kiểm tra hậu xử lý PASS** tại [CHECKS.json](Evidence/E/CHECKS.json); đây không phải 58 Automation tests bổ sung.

| Kiểm chứng bằng input thật | Kết quả và bằng chứng |
|---|---|
| Tám binding, duplicate/reserved/Escape, slider/invert/vai/Save | PASS; [video Rebind](Evidence/E/Rebind.mp4), [metrics/events](Evidence/E/Rebind.json). Phím mới đi/nhảy/sprint/đổi vai/tương tác hoạt động; W/Space/Ctrl cũ hết tác dụng sau đổi. |
| Ctrl đơn, tổ hợp Ctrl+T và cuộn chuột | PASS; [CaptureEdges](Evidence/E/CaptureEdges.mp4). Ctrl đơn chờ nhả mới gán; tổ hợp/cuộn bị từ chối và giữ binding cũ. [Video trước sửa](Evidence/E/History/CtrlBefore-b8bda58.mp4) tái hiện lỗi Ctrl+T bị nhận thành Ctrl ở b8bda58. |
| Menu, giữ phím/nút chuột và Alt-Tab thật | PASS; [MotionLocks](Evidence/E/MotionLocks.mp4). AwaitingResume khi trở lại; Resume vẫn chặn input đang giữ đến nhả/nhấn mới; sau nhấn mới đạt 500/700 cm/s. Gravity tiếp tục trong menu. |
| Interacting/Defeated | PASS; [MotionLocks](Evidence/E/MotionLocks.json), [DefeatedRestore](Evidence/E/DefeatedRestore.mp4). Khóa đi/nhảy, vẫn rơi/tiếp đất, camera/đổi vai/menu dùng được; mở khóa không tái phát input giữ. |
| Restore, Quit/mở lại | PASS; [Persist](Evidence/E/Persist.mp4). Binding H, sensitivity **1,587111**, invert Y và vai trái được giữ; hash file không đổi chỉ do load/Resume. |
| Năm vòng Boot → sân → Boot | PASS; bốn CharacterCombatLab và một NetworkLab, [Lifecycle](Evidence/E/Lifecycle.mp4), [NetworkReturn](Evidence/E/NetworkReturn.mp4). Sáu runID gồm phiên mở lại ban đầu; mapping active luôn 1, UI không chồng thêm, input/camera tiếp tục dùng được. |
| Save lỗi và retry | PASS; UserB có thư mục `.sav` chặn ghi, [thông báo lỗi](Evidence/E/SaveFailure-save-failed-resume.png), [video](Evidence/E/SaveFailure.mp4). Dirty còn, không báo thành công, Resume chưa rời menu. Bỏ vật cản ghi, [SaveRecovered](Evidence/E/SaveRecovered.mp4) lưu được và chơi tiếp. UserB ban đầu vẫn defaults; file UserA không đổi. |
| File nhị phân hỏng | PASS; [Corrupt](Evidence/E/Corrupt.mp4), [ảnh thông báo](Evidence/E/Corrupt-corrupt-file-message.png). Dùng defaults, có feedback; hash giữ nguyên qua load/Resume/Quit khi chưa sửa thiết lập. Partial recovery từng trường được kiểm riêng bằng Automation. |

Video target encode 30Hz nhưng capture duy nhất thực đo khoảng **21–25Hz** ở các phiên chính; metadata từng video ghi đầy đủ. Không dùng video này khẳng định blend 0,10s mượt, hoặc nghiệm thu 30/60/120 FPS của G. Cảm giác điều khiển và dễ dùng của menu vẫn chờ người dùng review trên package cuối.

## Lịch sử, tồn tại và bàn giao

- Giữ build lỗi đầu tại `Build-20261104-224237-479-3c19440b` và `Build-20261104-224554-126-ae80a97e`: cờ Automation UE5.8, namespace `Forward` trong unity, biến che thành viên controller và API metrics protected. Đã sửa, không bỏ test. Cảnh báo engine API deprecated, float trong tests D và compiler mới hơn preferred còn trong log; không cài/nâng toolchain.
- Nguồn thử đầu `1cca45f`, 21/21 PASS/package/input tại `Artifacts/U01/E/Play` giữ lịch sử. Lượt đi đầu chạm vật cản spawn nên không dùng để kết luận sprint; lượt cuối reset runway trước đo. Sau bổ sung vỏ SaveGame kiểm hỏng binary, full build/tests/package/input đều được chạy lại tại **c8df4ff**; chỉ kết quả cuối ở Evidence/E là bàn giao hiện tại.
- Lượt `b8bda58` đã kiểm checksum và input cơ bản, nhưng rà soát cuối phát hiện Ctrl đang rảnh bị gán ở key-down trước khi biết tổ hợp. Input thật tái hiện Ctrl+T → Ctrl, giữ tại `Artifacts/U01/E/FinalPlay/CtrlBefore` và Evidence/E/History. **c8df4ff** thêm policy nhận phím trì hoãn Ctrl đến key-up, hủy khi có phím thứ hai/Escape/focus reset; mở rộng BindingValidation và kiểm thật CaptureEdges. Build/tests/package/smoke và toàn bộ các lượt input được chạy lại, dữ liệu cuối tại `Artifacts/U01/E/Play-c8df4ff`.
- Lịch sử lỗi Live Coding B vẫn giữ trong REPORT-B; không suy full build clone thành Editor gốc đã cập nhật. Authoring Python ở clone E đã tạo/compile/save hai asset thành công; chưa lấy điều này để khép vấn đề Python/toolset/network còn phải kiểm ở F/tích hợp.
- Chưa chạy F/G, server/two-client, loss/latency, kiểm FPS tích hợp hay phiên tích hợp 10 phút. Không nghiệm thu packaged Server, anime art hoặc combat. Các trạng thái fixture không phải chết/hồi sinh/quest.

Chạy **`Artifacts/U01/E/Play-E.cmd`** để mở Boot của package cuối. Launcher [PlayE.ps1](../../Scripts/U01/PlayE.ps1) dùng settings riêng `Artifacts/U01/E/PlayerSettings`, log mới ở `PlayerLogs`, không dùng thư mục thử lỗi. Có thể truyền `-Map L_CharacterCombatLab` hoặc `-Map L_NetworkLab`. Nhánh E sẽ commit/push hồ sơ và dừng chờ review; **không merge E hoặc bắt đầu F**.
