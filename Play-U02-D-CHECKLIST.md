# Chơi thử U02-D — truy vấn hình học, chưa có damage

Chạy `Play-U02-D.cmd`. WASD di chuyển, chuột ngắm, LMB chém. HUD vàng đếm geometry hits; không có HP/damage ở D.

Bản hiện tại có debug giữ riêng action. Trong console nhập `U02CornerCase open`, đóng console rồi LMB để tái dựng tọa độ action66; `U02CornerCase blocked` chuyển attacker ra sau tường, `U02CornerCase outside` kiểm ngoài vùng. Lệnh tự chọn action kế. Dùng `U02DebugAction 0` trước đòn ở trạm khác để giữ riêng đòn đó. HUD SELECTED ghi identity và số hit của action, sphere/đường xanh là confirmed, đỏ blocked, xám outside. Nét debug foreground giúp thấy đường sau bề mặt; không có nghĩa bỏ qua tường. Hình giữ action cũ cho tới khi chọn mới, không phải hit hiện thời của animation.

Để tới trạm, Resume rồi mở console bằng phím `~`, nhập một trong các lệnh:

- `U01FixtureReset CombatD1`: hai dummy; mỗi đòn có thể thêm hai hits, giữ LMB không tự đánh tiếp.
- `U01FixtureReset CombatD2`: tường kín; không thêm hit.
- `U01FixtureReset CombatD3`: tường thấp che body; head còn hợp lệ, thêm một hit.
- `U01FixtureReset CombatD4`: góc tường; không thêm hit ở vị trí reset.

Các lệnh này chỉ là fixture lab. Reset quarantine phím đang giữ; nhả phím rồi nhấn lại. Đợi nhân vật chạm đất trước khi đánh. Ba map cũ vẫn giữ; các trạm D ở khu riêng trong hai lab.

Phép kiểm số hit/IDs/timestamp đã được script và Automation thực hiện; bạn không cần nghiệm thu lại C. Báo nếu hình query không khớp vị trí thấy được hoặc điều khiển/pose hồi quy. Thoát bằng menu Quit để launcher khôi phục cửa sổ Editor. D dừng READY_FOR_REVIEW, chưa merge hoặc triển khai E.
