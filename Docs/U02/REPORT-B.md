# U02-B — ACCEPTED

**Người dùng xác nhận nghiệm thu kỹ thuật tại95a83ca/source94ebcc7; [căn cứ và Editor refresh](ACCEPTANCE-B.md). Các trạng thái chờ dưới đây là lịch sử bàn giao đã được quyết định này thay thế.**

B triển khai riêng action/input/motor, chưa nghiệm thu hoặc merge. Main đã khép A tại `0550254e702e406dcef6731900541a625dafb915`; nhánh B `u02/b-action-input-motor`. **Source build/tests/package/runtime cuối: `94ebcc73b27dc0d40b0f818491caef6217469e4c`**. Các commit bàn giao sau đó chỉ scripts/hồ sơ, không đổi Source/Content/Config/Plugins/project. Không gán SHA hồ sơ cho binary.

## Kết quả và quyền runtime

`UU02CombatComponent` composition trên AU01Character dùng model A; server cấp action/life identity và replicated snapshot. Standalone cùng authority path; LMB physical rising edge trước UMG, giữ không lặp, busy reject không buffer. Ctrl đang sprint vẫn nhận attack. Không gameplay montage/hit/damage; C–F chưa nghiệm thu. HUD trace chỉ phase/action/lock, kiếm vẫn pose U01.

Adapter advance/deliver interval cũ trước replacement/cancel/reset, cancel cutoff excluded. `BeforeActionMutation` là barrier để resolver world D gom/resolve batch trước mutation; B chưa có resolver/damage và delegate này chưa bind gameplay. Test thực kiểm interval → barrier → mutation, kể cả frame vượt toàn active. Không tuyên bố barrier B tự chứng minh ordering/death world D/E.

Combat bit8 giữ ngoài replayed LockMask; compressed flags không có quyền xóa/tạo combat action. Saved move không combine qua action/life/lock transition; replay không resurrect stale combat, không kéo dài deadline, không phục hồi jump/sprint qua khóa authority. Interacting/Defeated authority bits cũng không bị PrepMoveFor ghi đè. Actual `FSavedMove_U01` và CharacterMovement được kiểm trong Game world, không chỉ policy A. Full network integration/security/disconnect đồng thuận hai client vẫn thuộc F.

Accepted attack dừng XY, khóa move/jump/sprint, giữ gravity. Startup cập nhật aim hợp lệ; active/recovery khóa body yaw, camera vẫn tự do; remote aim RPC không bị controller rotation cũ ghi đè. Lost-ground hủy phần chưa phát qua API cancel, không ngừng rơi. Menu/focus giữ action/world clock, Control và AwaitingResume U01; không dùng combat để gate WASD. Recovery trả held movement intent. Resume click ở UI không thành attack; Dodge/Guard chỉ test qua CancelAction thật, chưa Shift/RMB gameplay.

## Kiểm chứng nguồn cuối

Engine UE5.8.4 CL58902052; MSVC14.51.36260/toolset14.51.36231, SDK10.0.26100.0. Full Editor/Game build clone riêng đạt, run `Build-20261105-205203-468-c36b4343`; Generate/Editor/Game exit0 và exact `Result: Succeeded`. New reflected component/header/layout kiểm bằng full build/cold clone; không coi Live Coding là đã nạp layout vào Editor gốc. Không đóng/restart Editor gốc; PID hiện8396 (PID3508 ở đầu đợt là lịch sử, không giả định liên tục).

Cold MCP `MCPTests-20261105-211013`: **34/34 Success, Failed0**, có `Automation Test Queue Empty 34 tests performed`. Gồm U00/U01 23, U02-A7, U02-B4. [Từng test](Evidence/B/AUTOMATION-RESULTS.json), [raw MCP](Evidence/B/MCP-RESULTS.json), [build](Evidence/B/BUILD-RESULTS.json). B tests: AdapterDrainBeforeMutation, AuthorityLockSavedMoveReplay, MotorGravityAndHeldIntent, AdmissionCancelAndYaw. Tests chạy fixtures Game physics/clock; không tự gọi đó là input Windows/network3process.

Package `Package-20261105-211051-062-781bdf0f` thành công, full cook ba map; **smoke3/3** `SmokeB-20261105-211152` trên đúng source94. [Smoke](Evidence/B/SMOKE.json), [package48file/hash](Evidence/B/PACKAGE.csv). Build/tests/package nguồn94 được tái sử dụng sau đối chiếu hash, không chạy lại vì capture/script sửa. [Manifest source/binary/process](Evidence/B/MANIFEST.json), [logs nguyên văn gzip và raw hash](Evidence/B/LOGS.json). Lượt nguồn2e06309 trước sửa Ctrl+LMB chỉ giữ lịch sử, không dùng thay binary cuối.

## Input Windows thật và video

Session `Play-Evidence94`, capture14.5s,871mẫu owned Game world/Standalone/1LocalPlayer; exact PID/exe/hash/world/owner/foreground guards. Windows SendInput chuột/phím thật, probe IME rồi phục hồi; thực dùng UI reset runway trước quay. **40/40 assertions hậu xử lý đạt** (không cộng vào34Automation). [Assertions](Evidence/B/RUNTIME-ASSERTIONS.json), [timeline input/frame timestamps](Evidence/B/INPUT.json), [video](Evidence/B/Input-B.mp4). Video341frames lưu30FPS nhưng capture thực khoảng23.5frames/s; video phát nhanh hơn wall time, phải dùng frame timestamp array trong INPUT để liên kết log, không suy video frame index là gameplay clock/FPS sản phẩm. Không dùng video xác nhận cảm giác thay người dùng.

Các checks thực gồm: sprint700 trước attack; LMB trong Ctrl-sprint dừng XY; held WASD/Ctrl chạy lại sau recovery không release; hold LMB chỉ một action; busy/new edges reject; jump không buffer trong action; active/recovery yaw cố định khi camera quay; menu giữ recovery tới finish; Resume không tăng accepted count; focus mất vào AwaitingResume, action hoàn tất lúc nền; focus return không tự Playing; Resume không tự movement, cạnh W mới chạy; Interacting/airborne reject; gravity tiếp tục trong menu khi rơi. Bảy action accepted, ba rejected. Từng action có gameplay phase timestamps chính xác start+0.16/+0.22/+0.40 từ log, observed frame time tách riêng.

Giới hạn input: injected W có thể bị Windows re-arm khi đổi input mode/focus. Runtime chứng minh **heldW trong combat→recovery** và **không replay movement sau menu/Resume**, không chứng minh hardware W giữ liên tục qua Alt-Tab. GateW đã quan sát true trong đoạn menu sau synthetic transition; không đổi log hoặc ép bit để đạt. Assertion ban đầu yêu cầu gate bit false bị giữ FAIL trong lịch sử; assertion cuối chỉ phát biểu hành vi thực đo. Release-gate policy có tests U01/A, replay có test B thật; đây không là phép nghiệm thu lại mọi input case U01. Không bỏ AwaitingResume hoặc foreground guard.

## Lỗi giữ lại và giới hạn

- Hai compile lỗi đầu: trùng tên delegate `FU02ActiveInterval` với test A trong unity build; macro DOREPLIFETIME cần tên tham số `OutLifetimeProps`. Đã sửa, giữ raw logs. Warnings compiler newer-than-preferred/UE deprecated/U01 conversion còn trong WARNINGS/full logs.
- Input runtime nguồn2e06309 bắt lỗi chặn LMB khi Ctrl modifier; đã sửa tại94ebcc7, rebuild34tests/package/smoke đúng nguồn. Không hạ assertion để che lỗi gameplay này.
- Capture foreground bị chặn, helper HWND/message-loop, IME probe và log-reader đọc toàn file gây delay được giữ theo run. Game khác hoạt động khiến guard dừng; sau người dùng tắt game mới thu tiếp. Reader cuối chỉ tail250KB, không bỏ guard. Lượt timing dồn action không PASS. Separate owned focus helper được xác minh PID/HWND, không gửi gameplay input sang app khác.
- Smoke preflight nhập nhầm chuỗi SHA bị guard reject trước chạy; retry dùng SHA thực. Script seal đường dẫn tương đối lỗi đã sửa resolve, không đổi binary. Clone Editor tự thêm SecurityToken: chỉ xóa đúng dòng tự sinh trong clone sau đối chiếu; không in giá trị hoặc sửa config riêng workspace.
- Failed runs/logs/video/metadata được giữ trong Artifacts và bản archive bàn giao; xem FAILED-RUNS.json. Không xóa failure hoặc cộng dồn tests nhiều nguồn thành số cuối.

Config riêng `DefaultEngine.ini` nguyên byte theo hash trước/sau đợt, không staged/token/restore. Main giữ0550254; không merge B hoặc bắt đầu C. C++ layout mới chưa xác nhận nạp Editor gốc; bản chơi dùng package riêng. Art anime/carry/montage, collision/hurtbox/sweep geometry, damage/death/shield và confirmed network outcomes chưa thuộc B.

## Review chơi thử

Chạy [Play-U02-B.cmd](../../Play-U02-B.cmd): launcher kiểm48package hashes, dùng userDir riêng và khôi phục Editor windows hợp lệ sau khi game thoát. Chỉ cần đánh giá: cảm giác dừng/tiếp tục movement khi LMB, startup aim/body yaw sau active, camera/menu/focus/Resume. B chưa có animation chém C hoặc damage D/E nên không yêu cầu review mỹ thuật/kiếm chém. Chưa giả định người dùng PASS; **READY_FOR_REVIEW riêng B**.
