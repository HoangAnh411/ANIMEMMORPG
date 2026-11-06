# Chơi thử mạng U02-F

Chạy `Play-U02-F.cmd`: cửa sổ trái A, phải B, cùng dedicated Editor server. Đổi cửa sổ thì bấm Resume; không dùng click Resume làm đòn đánh. WASD di chuyển, Ctrl chạy, chuột ngắm, LMB đánh, Escape menu. Lab vẫn chỉ đánh dummy; không mở PvP.

- Kiểm A/B nhìn cùng một action và target HP; đòn thường60, crit90, một hit/target/action dù nhiều hurtbox.
- Xem startup/chém/thu kiếm có đọc được ở cửa sổ bên kia, kiếm/pose có hồi quy không.
- Menu hoặc mất focus A không pause B/server; đánh xong có tiếp tục movement đúng, Resume có cần thao tác bất thường không.

HUD ghi rõ FIXTURE CRIT OFF/FORCED khi fixture đang điều khiển RNG. Shield/reset chỉ là lab, không phải kỹ năng hoặc hồi sinh sản phẩm. AI tự kiểm phép tính, ownership, commands và IDs bằng logs/tests; người dùng chỉ cần đánh giá hình ảnh/focus/cảm giác hai cửa sổ.

Chạy `Stop-U02-F.cmd` để dừng đúng các process của session và khôi phục cửa sổ Editor còn hợp lệ. Không đóng Editor gốc. F chưa merge; chưa Server đóng gói hoặc U05/U03.
