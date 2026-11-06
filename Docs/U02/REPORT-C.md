> REMOTE CLOSED: C accepted and remote commit 775ce94 verified; all 816 reachable LFS objects downloaded into isolated storage and SHA-256 checked. See Evidence/C-Turn/REMOTE-VERIFIED.json. Prior pending statements below are historical; no C rebuild/retest.

> Current acceptance: technical and standing-attack turn/feel accepted by user at cdaf102, verified source 9aa7249. See [ACCEPTANCE-C.md](ACCEPTANCE-C.md). Historical review-pending statements below describe the original handoff; acceptance supersedes them. Remote delivery remains pending; no main fast-forward or D until verified.

# U02-C — ACCEPTED_LOCAL — REMOTE_PENDING

C ACCEPTED theo review nguời dùng tại cdaf102; xem ACCEPTANCE-C.md. Nhánh `u02/c-attack-presentation`; main giữ ở B ACCEPTED `34e5dd73724546deb6e9cbb410a844341fcfad3c`. Source kiểm chứng mới: **`9aa7249a38b65f8119d8c93790d73e795341324a`**. Chưa merge C hoặc bắt đầu D. Chưa xác minh bàn giao remote vì GitHub lỗi kết nối/DNS; log push được giữ trong lịch sử.

Lịch sử `39bb09c` / source `61be83b` được giữ nguyên. [Báo cáo cũ](REPORT-C-39bb09c.md) và `Evidence/C` chỉ là bằng chứng lịch sử, không chứng minh revision này. Phản hồi cần sửa: thân xoay phắt sang aim lúc nhận LMB; cần chuyển dần trong startup, bổ sung chuẩn bị bằng thân/chân, giữ grip và trả locomotion; video cũ phát nhanh hơn wall time.

## Thay đổi

`FStartupTurn` tách yaw ngắm khỏi quỹ đạo thân. Nhận đòn giữ yaw thân hiện tại; smoothstep theo simulation time và cung ngắn nhất đến aim trong startup 0,16 giây. Đổi aim bắt đầu đoạn mới từ yaw hiện tại, giữ deadline active ban đầu. Đúng 180° luôn quay chiều yaw dương. Đến active hoàn tất yaw trước khi giao interval, kể cả update vượt toàn active và recovery. Active/recovery khóa hướng; camera vẫn tự do. Timings 0,16/0,22/0,40, gravity, input, combat lock và release gate không đổi.

Snapshot có yaw bắt đầu đoạn, thời điểm đoạn và aim đích. Client lấy server simulation time để trình bày; simulated proxy được xử lý riêng vì không chạy PhysicsRotation. Không sửa smoothing chung U01 hoặc thêm quyền hit cho client. Diagnostics đo riêng transform thân, transform mesh, aim và action time. Chưa tuyên bố đồng thuận hai client mạng; đó vẫn là cổng F.

Blockout tự tạo được bổ sung chuẩn bị ở spine/clavicle và chân, không dịch chuyển root/capsule. Layer attack từ pelvis, loại nhánh upperarm_l để giữ tay trái locomotion U01; grip ngón tay vẫn sau layer attack. IK dùng chiều dài tay thực và socket đã nghiệm thu. Không đổi asset U01. Chất lượng kỹ thuật, chưa nghiệm thu art anime hoặc cảm giác người dùng.

## Kiểm chứng trên source mới

- Full build Editor/Game trong clone riêng: `Build-20261106-103506-202-75bb5d6f`, cả hai Result: Succeeded. Source C++ giống lượt compile `e1bc39f`; commit source cuối bổ sung asset đã author, build cuối xác nhận các target trên cây sạch tương ứng. [Build](Evidence/C-Turn/BUILD-RESULTS.json).
- MCP cold clone `MCPTests-20261106-103539`: **40/40 Success**, queue kết thúc 40 tests performed. Có U00/U01, A/B/C; bổ sung StartupTurnTrajectory, ActualBodyAndSkippedBoundary và ProxySamplesActionTurn. Bao phủ góc 0/±45/±90/±179/180, wrap, smoothstep, retarget, deadline, 30/60/120 Hz sampling và actual body trước interval bị vượt toàn bộ. Hồi quy saved-move authority, gravity, held intent, release gate, grip/carry/landing và montage identity đạt. [Từng test](Evidence/C-Turn/AUTOMATION-RESULTS.json).
- Windows package `Package-20261106-103646-745-f3676841`: UAT BUILD SUCCESSFUL/exit0, cook ba map và assets mới. Smoke `SmokeB-20261106-103813`: **3/3**, gồm Boot Quit rồi mở hai lab. [Smoke](Evidence/C-Turn/SMOKE.json).
- Input Windows thật `Play-Turn-Final`: **63/63 assertions**, tách khỏi Automation. Bảy accepted, ba rejected; held WASD/Ctrl tiếp tục sau recovery, Resume không attack, menu/focus không cancel, AwaitingResume, gravity, yaw lock và montage return đạt. [Assertions](Evidence/C-Turn/RUNTIME-ASSERTIONS.json), [video](Evidence/C-Turn/Input-C.mp4).
- Kịch bản chuyển hướng `Turn-After-Final`: **18/18 assertions**, 873 native samples. Thân 180°, aim 0° khi nhận đòn; có yaw trung gian, khớp aim ở active/recovery. Sai số lớn nhất giữa transform thân đo thực và quỹ đạo timestamp khoảng 5,68e-14°. Đây không phải dùng yaw đích thay transform thực. [Assertions](Evidence/C-Turn/After-TURN-ASSERTIONS.json), [trace thân/mesh/aim](Evidence/C-Turn/After-YAW-TRACE.csv).
- Launcher C đã kiểm đủ hash package, khởi chạy đúng source/Game world/owned pawn và Stop đúng session; nguyên trạng Editor gốc được khôi phục theo identity. [Launcher](Evidence/C-Turn/LAUNCHER.json).

## Trước/sau và thời gian video

[Trước sửa](Evidence/C-Turn/Before-Input-C.mp4) và [sau sửa](Evidence/C-Turn/After-Input-C.mp4) dùng cùng reset runway, camera ban đầu và kịch bản: quay lưng rồi đánh; đi ngang rồi đánh; đổi camera trong startup/active; giữ W qua recovery; menu/Alt-Tab/Resume. [Ảnh so sánh](Evidence/C-Turn/Compare.png) và [timestamps](Evidence/C-Turn/FRAMES.json).

Video sau sửa dài 14,5667 giây, capture thực 14,5469 giây; chênh dưới một output frame 30 FPS. Export giữ frame quan sát gần nhất theo timestamp, không tăng tốc hoặc tạo chuyển động giả. Capture không chứng minh render 60 FPS; các frame được giữ có thể làm video giật và không dùng để xác nhận chính xác biên 0,16. Biên gameplay dùng native traces/tests. Video cũ của hồ sơ 39bb09c được [xuất lại đúng wall time](Evidence/C-Turn/Before-Historical-Realtime.mp4), bản gốc vẫn giữ nguyên.

AI đã xem ảnh chuẩn bị/chém/thu và sau finish: tay trái về locomotion, kiếm/grip không thấy xuyên thân rõ trong các góc đã xem. Đây là kiểm hình giới hạn, không thay đánh giá cảm giác của người dùng.

## Hash và lịch sử lỗi

[Manifest](Evidence/C-Turn/MANIFEST.json), [48 file package](Evidence/C-Turn/PACKAGE.csv), [asset hashes](Evidence/C-Turn/ASSETS.json), [evidence index](Evidence/C-Turn/EVIDENCE-SHA256.json).

- Editor DLL SHA-256: `dc4d7c2a047c0caf3f045a33e38e8fd4d040fd5f8dce5911b7f2cef52759fcb4`.
- Packaged Game SHA-256: `fb4f46a6440e3d93b8101afe6804fa7ca231f24d70b340d8a8f233767e217381`.

Giữ các lượt trung gian 39/40 tests, bản mask chưa loại tay trái, lượt quay đi lùi khỏi mép runway, lượt smoke gán nhầm SHA và lượt package bị guard chặn do Editor clone đang chạy tests. Các lượt đó không thay bằng chứng source cuối. [Lịch sử revision](Evidence/C-Turn/REVISION-HISTORY.json), [warnings/logs](Evidence/C-Turn/WARNINGS.json). Không bỏ guard; chờ clone kết thúc rồi package lại. Không dùng trigger/zero tests làm PASS.

Editor gốc PID2444 được giữ mở; không restart hoặc nạp layout C qua Live Coding. Full builds/tests dùng clone, package dùng binary mới. Config riêng nguyên byte so với baseline C (SHA-256 `1A89D9B36D4C7653FE2261A9D966A59E6B4A5D26EC5F17C88C4EED1E260E556D`); không stage/in token. MSVC preference/deprecation warnings giữ trong logs. Không thêm module/plugin/framework.

## Review

Chạy [Play-U02-C.cmd](../../Play-U02-C.cmd) với [checklist ba mục](../../Play-U02-C-CHECKLIST.md): quay từ hướng ngược có còn bật người khó chịu; chuẩn bị/chém/thu và kiếm có đọc được; đánh xong tiếp tục di chuyển có tự nhiên. Nếu đổi aim rất mạnh sát active, thân phải bắt kịp trong thời gian còn lại rất ngắn; không hứa mọi thao tác đều quay chậm. Nếu cảm giác góc lớn chưa đạt, giữ C ở review, không tự đổi startup/tốc độ quay thành luật mới.

Trạng thái hiện tại: ACCEPTED_LOCAL — REMOTE_PENDING. Remote chưa được xác minh; không coi lỗi push là đã bàn giao GitHub. Không merge hoặc bắt đầu D.
