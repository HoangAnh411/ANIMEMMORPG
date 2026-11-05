# U01-G — Checklist chơi thử gộp

Trạng thái: PASS theo xác nhận người dùng tại9c89d08, gồm sửa focus A/B; hồ sơ khép kỹ thuật sau đối chiếu ma trận. Chạy Play-G.cmd (mặc định cửa sổ1280x720, cap60; tùy chọn -MaxFPS30/60/120). Launcher kiểm SHA256 toàn bộ package, dùng thiết lập review riêng. Source package:5f8a6eabe103a8b31a894c82f32cffb0325474a9; xem Evidence/G/MANIFEST.json và PACKAGE.csv.

Các mục dưới đây PASS theo xác nhận người dùng trên bản bàn giao9c89d08; không gán thành thao tác tự động của AI:

- [x] Boot → CharacterCombatLab: chuột xoay ngay, không cần giữ nút; đứng yên xoay không kéo thân, đổi vai không đổi hướng ngắm; camera tránh tường và ẩn/hiện cả mesh/kiếm khi sát người.
- [x] Đi/sprint/nhảy, giữ hướng khi tiếp đất và nhảy lại: chuyển động ổn, không trượt pose landing; carry blockout không xuyên thân rõ rệt, nắm tay giữ đúng.
- [x] Escape/menu khi rơi: thế giới tiếp tục; Alt-Tab/trở lại chờ Resume. Giữ W/Space/Ctrl qua khóa không tự chạy/nhảy khi Resume trước khi nhả phím.
- [x] Điều khiển: đổi từng phím, trùng/reserved bị từ chối, Escape hủy; sensitivity/đảoY/vai/default áp dụng đúng. Quit/mở lại giữ thiết lập, lỗi lưu có phản hồi.
- [x] Fixture Interacting/Defeated khóa motor, giữ gravity/camera/menu. Năm vòng Boot → sân → Boot và Quit/mở lại không nhân UI/input.
- [x] Đánh giá độ mượt ở FPS máy thực đạt và cảm giác camera/menu. Cap120 chỉ đo được89.52FPS trong lượt1080p; không yêu cầu xác nhận máy đã đạt120FPS.

Bằng chứng tự động/tool: full build đạt, Automation23/23, smoke3/3; phiên600.23giây với263input và10lần đổi focus. Lượt534giây bị gián đoạn được giữ riêng, không tính hoàn tất10phút. Đối chiếu kỹ thuật đã hoàn tất trong G-MATRIX-CLOSURE.md và CLOSURE-AUDIT.json.

Art anime/animation chiến đấu DEFERRED; carry hiện tại chỉ là tư thế kỹ thuật/blockout. Không nghiệm thu Server đóng gói.

Focus-switch follow-up (use Play-G-Network.cmd, not the standalone launcher):

- [x] A→B: chọn Resume rồi đi ngay; pawn của B phản hồi ổn ngay từ đầu, không chậm rồi mới mượt. Quan sát riêng nhân vật A.
- [x] B→A: lặp lại, đi/sprint/nhảy ngay sau Resume; phân biệt pawn mình và đối phương.
- [x] Không tự Resume khi trở lại cửa sổ; phím giữ qua khóa phải nhả trước khi dùng lại.
- [x] Stop-G-Network.cmd dừng cả ba process kiểm thử và trả cửa sổ Editor về trạng thái trước khi chạy. Editor vẫn mở.

Đã đo5lần mỗi chiều trước/sau; sửa launcher đưa trạng thái Editor về đúng profile F. Chi tiết và giới hạn phép đo trong REPORT-G, mục Focus-switch regression. Người dùng xác nhận PASS tại9c89d08; không thay đổi phạm vi kỹ thuật/blockout.
