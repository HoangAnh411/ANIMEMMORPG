# U01 — Ma trận nghiệm thu

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

Kết quả D/source7152384: D-STATES/D-SWORD và phần số đo D-ROOT PASS bằng cold MCP14/14 (3 tests D mới), Game-world animated pawn và video input Windows27s. Kiểm chu kỳ xương ổn định và interpolation bắt được asset lỗi cũ12/14 trước khi bản sửa đạt14/14. Đánh giá foot sliding/cảm giác D-ROOT vẫn PENDING REVIEW trên video/package; D READY_FOR_REVIEW, chưa nghiệm thu/merge hoặc suy kết quả E–G. Chi tiết, identity, log và giới hạn tại REPORT-D/D-MANUAL-CHECKLIST.
