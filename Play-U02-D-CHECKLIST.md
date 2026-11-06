# Chơi thử U02-D — truy vấn hình học, chưa có damage

Chạy `Play-U02-D.cmd`. WASD di chuyển, chuột ngắm, LMB chém. HUD vàng đếm geometry hits; không có HP/damage ở D.

Để tới trạm, Resume rồi mở console bằng phím `~`, nhập một trong các lệnh:

- `U01FixtureReset CombatD1`: hai dummy; mỗi đòn có thể thêm hai hits, giữ LMB không tự đánh tiếp.
- `U01FixtureReset CombatD2`: tường kín; không thêm hit.
- `U01FixtureReset CombatD3`: tường thấp che body; head còn hợp lệ, thêm một hit.
- `U01FixtureReset CombatD4`: góc tường; không thêm hit ở vị trí reset.

Các lệnh này chỉ là fixture lab. Reset quarantine phím đang giữ; nhả phím rồi nhấn lại. Đợi nhân vật chạm đất trước khi đánh. Ba map cũ vẫn giữ; các trạm D ở khu riêng trong hai lab.

Phép kiểm số hit/IDs/timestamp đã được script và Automation thực hiện; bạn không cần nghiệm thu lại C. Báo nếu hình query không khớp vị trí thấy được hoặc điều khiển/pose hồi quy. Thoát bằng menu Quit để launcher khôi phục cửa sổ Editor. D dừng READY_FOR_REVIEW, chưa merge hoặc triển khai E.
