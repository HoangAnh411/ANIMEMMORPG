# U01-G — Checklist chơi thử gộp

Trạng thái: CHỜ XÁC NHẬN NGƯỜI DÙNG; G chưa nghiệm thu/merge. Chạy Play-G.cmd (mặc định cửa sổ1280x720, cap60; tùy chọn -MaxFPS30/60/120). Launcher kiểm SHA256 toàn bộ package, dùng thiết lập review riêng. Source package:5f8a6eabe103a8b31a894c82f32cffb0325474a9; xem Evidence/G/MANIFEST.json và PACKAGE.csv.

Chỉ đánh dấu sau khi chơi package cuối:

- [ ] Boot → CharacterCombatLab: chuột xoay ngay, không cần giữ nút; đứng yên xoay không kéo thân, đổi vai không đổi hướng ngắm; camera tránh tường và ẩn/hiện cả mesh/kiếm khi sát người.
- [ ] Đi/sprint/nhảy, giữ hướng khi tiếp đất và nhảy lại: chuyển động ổn, không trượt pose landing; carry blockout không xuyên thân rõ rệt, nắm tay giữ đúng.
- [ ] Escape/menu khi rơi: thế giới tiếp tục; Alt-Tab/trở lại chờ Resume. Giữ W/Space/Ctrl qua khóa không tự chạy/nhảy khi Resume trước khi nhả phím.
- [ ] Điều khiển: đổi từng phím, trùng/reserved bị từ chối, Escape hủy; sensitivity/đảoY/vai/default áp dụng đúng. Quit/mở lại giữ thiết lập, lỗi lưu có phản hồi.
- [ ] Fixture Interacting/Defeated khóa motor, giữ gravity/camera/menu. Năm vòng Boot → sân → Boot và Quit/mở lại không nhân UI/input.
- [ ] Đánh giá độ mượt ở FPS máy thực đạt và cảm giác camera/menu. Cap120 chỉ đo được89.52FPS trong lượt1080p; không yêu cầu xác nhận máy đã đạt120FPS.

Bằng chứng tự động/tool: full build đạt, Automation23/23, smoke3/3; phiên600.23giây với263input và10lần đổi focus. Lượt534giây bị gián đoạn được giữ riêng, không tính hoàn tất10phút. Checklist này không thay các phép kiểm kỹ thuật còn đang hoàn thiện trong REPORT-G.

Art anime/animation chiến đấu DEFERRED; carry hiện tại chỉ là tư thế kỹ thuật/blockout. Không nghiệm thu Server đóng gói.
