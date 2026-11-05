# U01 — Ma trận nghiệm thu

**Cập nhật mới nhất:** D kỹ thuật/blockout được người dùng nghiệm thu tại1e46f71, đã khép hồ sơ/fast-forward main e867af9. Carry tạm được chấp nhận; art anime/animation chiến đấu DEFERRED. E source **c8df4ff**: full build/package, MCP **21/21 PASS**, smoke ba map **3/3**, **58 kiểm tra hậu xử lý input thật PASS**. E-REBIND/E-SETTINGS/E-ISOLATION/E-GATE có bằng chứng tại [REPORT-E](REPORT-E.md), [manifest](Evidence/E/MANIFEST.json), [checklist review](E-MANUAL-CHECKLIST.md). Hai LocalPlayer/IMC được kiểm bằng Automation; hai thư mục settings được kiểm trên các process standalone riêng, không suy thành test dedicated-server F. Các lượt input bao gồm Ctrl đơn/tổ hợp/cuộn, Alt-Tab thật, gate binding bàn phím/mouse, gravity khi khóa, save lỗi/retry, file hỏng giữ hash, reopen và năm vòng Boot. E **READY_FOR_REVIEW**, còn xác nhận người dùng, chưa merge E/chạy F–G. Những đoạn kết quả cũ phía dưới giữ lịch sử theo nguồn tương ứng.

Tất cả B–G **NOT-RUN trong A**. A không thêm C++/gameplay/test giả. Nguồn và kết quả A tại REPORT-A.md; các tên bên dưới là ID kế hoạch, không phải Automation tests đã đăng ký. Mỗi đợt riêng commit/push rồi dừng; chỉ bắt đầu từ main đã được nghiệm thu. Không tự merge.

| ID / đợt | Phép kiểm và phương thức | Tiêu chí / bằng chứng |
|---|---|---|
| A-BASE | Git local + remote, đọc U00 | Full SHA f10e925 khớp, giữ local config ngoài index |
| A-ASSET | Hash register U00 + metadata MCP | Mesh/skeleton/sáu clip tải được, nguồn hash khớp; root motion ghi rõ |
| A-NET | Ba process UnrealEditor riêng headless | Server listening, hai login/join; phân biệt packaged Server; không suy thành F |
| B-LOOK | Chuột thật ngay vào cả hai lab | Không giữ LMB/RMB vẫn xoay; cursor/capture và video; Boot UI-only |
| B-BODY | Đứng yên look; chạy đổi hướng | Thân đứng yên không quay; không tự kéo camera sau lưng |
| B-SHOULDER | V ở chỗ trống và sát góc | Aim yaw/pitch giữ nguyên, offset ~0,15 s, sweep an toàn |
| B-COLLISION | Tường/góc/hành lang/giáp trần | Không xuyên, thu vào ngay/trở ra mượt; owner mesh/kiếm <80 ẩn, >100 hiện; client khác không bị ẩn |
| B-FOCUS | Alt-Tab thật, quay lại, Resume | Cursor nhả, AwaitingResume tới click Resume; log focus/control transition |
| B-GATE | Giữ W/Space/Ctrl qua menu/focus | Resume không chạy/nhảy/sprint tới release + press mới từng phím |
| B-GRAVITY | Escape/mất focus lúc đang rơi | Pawn tiếp tục rơi, world không pause |
| C-SPEED | Movement fixture/game samples sau tăng tốc | 10 s walk 5000±50 cm; sprint 7000±50 cm; đo đoạn ổn định, không tính tăng tốc |
| C-DIAGONAL | Cùng điều kiện thẳng/chéo | Tốc độ chéo sai khác ≤1%, có vector input/velocity và thời gian |
| C-JUMP | Ground flat, jump edge/hold/release | Apex feet +120±5 cm; giữ không tăng cao/tự nhảy khi landing; không double jump sau nhảy chủ động |
| C-CLOCK | Clock fixture biên coyote/buffer | 0/0,099 hợp lệ, 0,100/0,101 hết; coyote chỉ rời mép; khóa xóa buffer; frame qua biên và session reset |
| C-TERRAIN | Tool fixture + gameplay samples | Dốc 30/44/45 đi được; 46/60 không leo và trượt; bậc 20/40/60 so step45; không suy kết quả từ geometry |
| C-LOCK | Interacting/Defeated fixtures | Không horizontal control/jump, vẫn gravity/camera/menu; log reject |
| C-LAB | Đo transform/bounds sau mở rộng | Đường 80m mốc; dốc 30/44/45/46/60; bậc 20/40/60 cm; trần 180/260; mép rơi/landing; hành lang120/góc tường; giữ thước1m/10m U00; reset chỉ fixture |
| D-STATES | Video + state/velocity samples | Idle/walk/sprint/jump-up/fall/land, rời mép, không kẹt sau landing |
| D-ROOT | Đo lại C-SPEED/C-JUMP với AnimBP | Không displacement thêm từ root motion; play rate giới hạn ghi rõ; không trượt chân rõ kéo dài khi thẳng ổn định (review video) |
| D-SWORD | Video cả move/jump/land | Kiếm theo socket tay phải, collision/damage tắt; template/skeleton chung không sửa |
| E-REBIND | Input thật từng hướng và action | Phím mới tác dụng, phím cũ ngừng; trùng/reserved/wheel/chord từ chối có lý do; Escape hủy pending |
| E-SETTINGS | UI thật + restart + file fixture | Sensitivity1 range0,1–3 ngay khi kéo, save release/Save/Resume; invert/side/defaults ngay; reopen giữ; missing/corrupt/partial/version lạ báo rõ và giữ phần hợp lệ; load không auto-save; lỗi ghi không success giả |
| E-ISOLATION | Hai local-player settings contexts | IMC riêng; đổi A không sửa B; không widget/context nhân qua Boot |
| E-GATE | Lặp B gate + G fixture | Interacting/Defeated vẫn camera/menu/gravity; input reject có lý do, không NPC/quest/chết/hồi sinh |
| F-PROCESSES | Process inventory + runtime collector | Dedicated server PID riêng, NM_DedicatedServer, localplayers0; A/B NM_Client, mỗi bên pawn/ownership riêng; log path/ID/role |
| F-MOVE | Input thật A/B, server samples/video | Server ghi walk/sprint/jump hợp lệ; client còn lại thấy movement/animation; không camera RPC/movement teleport |
| F-SECURITY | Saved-move/server validation fixture | Yêu cầu quá tốc hoặc jump thêm bị reject/correct; không điều khiển actor không sở hữu; không client tự chọn speed |
| F-LIFECYCLE | Disconnect/reconnect + menu A | Không pawn nhân đôi; menu A không pause server/B; settings/log/user dirs A/B độc lập |
| G-SOURCE | Clone SHA đã push, full build từ đĩa | Giữ Editor gốc mở; engine/toolchain/hash artifact/source SHA rõ; Live Coding không thay clean binary |
| G-AUTOMATION | MCP TestRunner + log mới/report binary | U00 Axes/CallOrder/HalfOpenInterval/Units 4/4; U01 tên/số thực chạy rõ, 0 test không PASS; không dùng log cũ |
| G-WINDOWS | Package smoke B–F, G tích hợp | Cook/load/Blueprint refs + motor/camera/menu/focus/rebind/save/reopen input thật; nếu thiếu tool, một checklist người dùng gộp sau build |
| G-LIFECYCLE | 5 vòng Boot→lab→Boot, Quit/reopen | Không nhân widget/IMC; session ít nhất10 phút không chặn điều khiển; logs/video |
| G-FPS | Game/package tại 30/60/120 FPS | Ghi FPS đo được, đo motor/camera/input/time tại mức thực đạt; mức máy không đạt ghi chưa kiểm chứng; không đổi renderer |

Mỗi phép đo dùng identity schema CONTRACTS.md. Tests luật dùng clock/input fixture; cảm giác/chuột/focus/UI phải input thật và người review. Logs gắn UTC/run/PID/source SHA. Video không thay tốc độ/độ cao. F chỉ localhost bình thường; latency/loss/jitter và combat prediction/bù trễ ở U05. G vẫn ghi art anime DEFERRED.

**F60 hiện tại (từ412bc7b):** nguồn diagnosticsEDF885A, cap client30/60 tách server30; A–D đủ120s/lượt, warm-up≥30s và runtime cvar/async/shader/pipeline readiness xác minh. C hai client59,96/59,99FPS, p95≈17,2ms; đủ10 starts/stops hợp lệ mỗi chiều. Tăng stop tail đã phân rã và khớp công thức Exponential nguyên trạng trước chọn60. Logging control E không ghi log từng frame, dữ liệu frame vẫn liền nhau. Default60/server30 chạy F3 liên tục300s đạt59,97/59,96FPS, server29,89; frame>100ms0. CPU/GPU thực đọc stat-unit khi hỗ trợ, NullRHI timing riêng ghi chưa đo được; CSV/JSON/video thực có tại Evidence/F60. Cold Editor build/MCP23/23; package0f02c77 giữ nguyên sau verify48hash. Checklist cảm giác vẫn PENDING USER, F chưa khép/merge, G chưa chạy. Các đoạn dưới giữ lịch sử revision cũ.

**F sau review FPS/độ trễ:** giữ các dấu PASS điều khiển của người dùng nhưng chưa nghiệm thu F. Nguồn0f02c77 bổ sung diagnostic từng Game frame; REPORT-F-PERFORMANCE/Evidence/F-Performance ghi actual foreground/background FPS, actual lag/loss settings, engine ping, nhịp packet-position và cùng đường owner→server→peer mesh. Sửa launcher cho workload local4GiB và timer riêng server; bốn lượt cuối đo gần30FPS cả ba process, không còn frame1s, native onset30–72ms. Profile internal50%/cache nhỏ/Editor thu nhỏ là đánh đổi có ghi rõ, không sửa renderer backend hay che smoothing bằng tắt nó; đồ họa gốc chưa đạt dưới cùng workload. MCP23/23 và smoke3/3 hồi quy; nghiệm thu cảm giác profile mới vẫn PENDING USER. Không suy thành G/FPS60/120 hoặc network scanout latency đạt.

Kết quả hiện tại: E được người dùng nghiệm thu tại cb46c52/package c8df4ff, hồ sơ/main9936322. **F nguồn df897f6 READY_FOR_REVIEW**: F-PROCESSES/F-MOVE/F-SECURITY/F-LIFECYCLE PASS theo native Game-world telemetry và input OS thật; 92 kiểm tra hậu xử lý, không cộng vào 23 Automation tests. Dedicated PID5940, A10840/B13956, reconnect8616; server không local player/UI, GUID riêng, correction actual overspeed/extra jump, foreign ownership rejected, B quit→một pawn→reconnect hai pawn không ghost, settings riêng. NormalA không quan sát được sprint edge, chứng cứ sprint A ở AttacksSettingsA; không ghi PASS cho input bị bỏ lỡ. Full build, MCP23/23 và smoke package3/3; xem REPORT-F/Evidence/F cho tên tests, số đo và capture Hz. Python/toolset errors tái hiện rồi runtime tránh bằng -DisablePython, không sửa engine. Review cảm giác còn PENDING USER; không suy thành F đã nghiệm thu, Server packaging hoặc G/FPS đã đạt. Các đoạn D phía dưới là lịch sử trước nghiệm thu D/E.

Kết quả D/source7152384: D-STATES/D-SWORD và phần số đo D-ROOT PASS bằng cold MCP14/14 (3 tests D mới), Game-world animated pawn và video input Windows27s. Kiểm chu kỳ xương ổn định và interpolation bắt được asset lỗi cũ12/14 trước khi bản sửa đạt14/14. Đánh giá foot sliding/cảm giác D-ROOT vẫn PENDING REVIEW trên video/package; D READY_FOR_REVIEW, chưa nghiệm thu/merge hoặc suy kết quả E–G. Chi tiết, identity, log và giới hạn tại REPORT-D/D-MANUAL-CHECKLIST.

Bản sửa sau review941/source819fbd0 thay kết quả bàn giao hiện tại: **16/16 PASS**, thêm LandingTransitions và GripIsolationAndAttachment. Kiểm moving landing, stationary hold/cancel, buffer/rejump/fall priority, real ledge contact, compiled blend0,100s cùng weight/deadline; layer chỉ ngón, attachment vị trí+hướng và owner-hide. Motor/apex đo lại đạt, smoke3/3. Video màn hình trước–sau có input/log thật khoảng25–26FPS; không dùng video để kết luận100ms mượt. Review cảm giác/cách cầm vẫn PENDING USER; các kết quả cũ giữ lịch sử, chưa merge/chạy E–G.

Bản carry sau review4c8/source6ef6ec3: người dùng đã xác nhận grip, chỉ quỹ đạo vai/tay/kiếm cần sửa. **17/17 PASS**, thêm CarryTrajectory1270mẫu Game-world qua sprint/jump/fall/moving+stationary land và bốn hướng, kiểm layer không đổi root/chân/spine/tay trái, proxy thân/chân clearance nhỏ nhất21,742434cm, attachment/collision nguyên vẹn. Bỏ kỳ vọng tay phải phải vung như clip tay không, giữ kiểm chu kỳ chân. Full build/package/smoke3/3; video sau/trước input Windows thật23–24FPS. Proxy không chứng minh từng tam giác hoặc độ tự nhiên; review quỹ đạo/carry trên package vẫn PENDING USER, chưa merge D/chạy E–G.
