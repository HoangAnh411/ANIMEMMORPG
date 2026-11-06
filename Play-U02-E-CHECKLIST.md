# Chơi thử U02-E — một đòn có damage

Chạy `Play-U02-E.cmd`, Resume. LMB đánh, WASD di chuyển, Ctrl chạy, chuột ngắm, Escape mở menu. HP người chơi1000, dummy600; server quyết định hit/damage. Crit mặc định5%, damage thường60, crit90.

Để kiểm nhanh trong lab, mở console `~` rồi nhập `U01FixtureReset CombatD1` (hai dummy), `CombatD2` (tường kín), `CombatD3` (che body/hở head), hoặc `CombatD4` (góc tường). Nhả phím sau reset rồi bấm lại; đợi chạm đất trước khi đánh. Đây là fixture, không phải hồi sinh sản phẩm.

- Nhìn HUD: hit hợp lệ hiện CONFIRMED, target HP/shield khi có đường nhìn; hụt hiện MISS khi hết đòn. Dummy HP0 hiện DEFEATED và không nhận damage thêm.
- `U02EResetDummies` phục hồi dummy và tạo life mới. Menu “Fixture: reset runway” reset combat người chơi; không có hồi sinh tự động sản phẩm.
- Chỉ để kiểm: `U02ECrit off` tắt crit; `U02ECrit force` ép crit; `U02ECrit normal` trả5%. HUD/log ghi rõ fixture. `U02EShield 1 40 60` cấp khiên40 từ source1,60 giây cho dummy; không phải kỹ năng gameplay.

Bạn chỉ cần báo nếu HP/HUD khó đọc, kiếm/pose hoặc trở lại movement/focus có hồi quy. AI đã kiểm các phép tính, thứ tự death/reset, input và evidence bằng script/tests. Không cần nghiệm thu lại cảm giác C. Thoát bằng menu Quit để launcher khôi phục cửa sổ Editor.

E dừng READY_FOR_REVIEW; chưa merge hoặc bắt đầu mạng F. Animation vẫn blockout kỹ thuật.
