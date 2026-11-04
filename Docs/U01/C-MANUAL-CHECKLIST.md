# U01-C — Kiểm package và fixture UI trong một phiên

Chạy `Artifacts/U01/C/Play-C.cmd` (source/package ghi trong REPORT-C), giữ Editor gốc mở. Motor đã có phép đo tự động bằng input fixture trong Game world; danh sách này bổ sung xác nhận bàn phím/UI và hình học của package, không yêu cầu đo lại bằng tay các trị số đã có log chính xác.

1. Boot → sân nhân vật → Escape → **Fixture: reset runway** → Resume. Xác nhận chỉ một pawn được đưa tới đầu đường đo. W đi thường; Ctrl trái/phải + W sprint; A/D/W/S theo yaw camera và đi chéo không tăng tốc rõ. Mốc0–80m dùng đo; 5m mỗi đầu dành tăng tốc/phanh. Reset là chức năng sân thử, không phải hồi sinh sản phẩm.
2. Space nhấn/giữ/nhả: một cú nhảy mỗi cạnh nhấn, giữ không tăng cao/tự nhảy lại; rời mép và bấm gần landing thử coyote/buffer. Không dùng stopwatch tay để kết luận biên0,099/0,100s; các biên đó đã có test clock. Giữ W/Ctrl/Space qua Escape hoặc Alt-Tab rồi Resume: vẫn cần nhả phím trước lệnh mới, menu không pause rơi.
3. Menu **Fixture: next terrain station** chuyển lần lượt qua dốc30/44/45/46/60°, bậc20/40/60cm, trần180/260cm, mép rơi/landing và hành lang120cm. Tên trạm hiện trên menu. Xác nhận dốc45 đi được,46/60 không leo bằng đi bộ và trượt; bậc20/40 qua được,60 chặn; roof180 không đủ đứng,260 cho đứng nhưng chặn nhảy; camera còn tránh vật cản ở hành lang/góc. Các trạm tách nhau, dùng reset fixture để chuyển.
4. Khi đang rơi mở menu, bật **Interacting** hoặc **Defeated**, Resume: đi/nhảy/sprint bị khóa; vẫn xoay camera/đổi vai/mở menu và vẫn rơi. Bật cả hai rồi chỉ tắt một: motor vẫn khóa; tắt hết hoặc reset runway để thử tiếp. Đây chỉ là fixture, không damage/chết/quest.
5. Back to Boot → sân mạng: kiểm sprint/nhảy/menu cơ bản; không coi đây là test mạng F. Quay Boot/vào lại vài lần không nhân widget/mapping. Quit/mở lại bản Windows, Editor gốc vẫn mở.

Ghi PASS/FAIL từng mục và lỗi theo giờ/log `Artifacts/U01/C/Review/Game.log`; video ngắn nếu có. Chưa có xác nhận người dùng thì các thao tác tay này **NOT-RUN**. Không nhận kết quả B cũ làm PASS cho UI/input mới của C. Native class C trong Editor gốc vẫn cần full build/restart ở mốc riêng nếu muốn dùng trong Editor; package đã build bằng clone độc lập.
