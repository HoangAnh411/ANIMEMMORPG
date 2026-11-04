# U01-B — Một phiên kiểm chứng input thật

Trạng thái: **PASS theo xác nhận người dùng khi nghiệm thu U01-B tại2e0e89f**. Cả sáu mục dưới đây được chấp nhận trên package B đã bàn giao. AI không tự chạy toàn checklist và không có video/giờ chơi/PID mới được cung cấp; không diễn giải xác nhận này thành Editor gốc đã nạp native code mới nhất. Các hướng dẫn bên dưới giữ để tái kiểm khi cần, không phải yêu cầu người dùng chạy lại.

Thực hiện trên bản Windows và source SHA ghi trong REPORT-B.md; giữ Editor gốc mở. `Artifacts/U01/B/Play-B.cmd` mở Boot, bật log trạng thái input/camera trong thư mục Review riêng. Đây là phép thử B; sprint/nhảy hiệu chỉnh/animation riêng/rebind chưa nghiệm thu ở B. Không chạy bằng patch Live Coding của Editor gốc.

Ghi một video ngắn liên tục, giờ bắt đầu/kết thúc và kết quả từng mục; giữ log Review. Không cần chạy từng checklist rời rạc hoặc gửi lại phần đã có chứng cứ đủ.

1. Từ Boot bấm sân nhân vật. Di chuột ngay, không giữ LMB/RMB: camera phải xoay, cursor ẩn. Đứng yên xoay: thân không quay. Đi rồi đổi hướng: camera không tự kéo về sau lưng. Thử pitch hai đầu, không lật camera.
2. Nhấn V ở chỗ trống rồi gần tường: vai chuyển khoảng0,15giây, hướng ngắm giữ nguyên. Tường B ở X600, góc tại Y400 và mái thấp ở X−550; đi quanh/đứng sát, xoay đủ hướng và đổi vai. Camera thu vào ngay, không xuyên; ra khỏi vật cản trở ra mượt. Khi quá gần, mesh owner ẩn rồi hiện lại ổn định; chưa có kiếm B.
3. Escape mở menu và cursor hiện. Nhấn Escape lần nữa không Resume. Bấm Resume: chuột bắt lại và xoay ngay, không cần giữ nút. Lặp khi đang đi và khi đang rơi: nhân vật phải tiếp tục rơi, menu không pause world.
4. Giữ W qua Escape→Resume: không tự đi tới khi nhả W rồi nhấn mới. Làm tương tự với Space: không phát lại cú nhảy/không tự nhảy khi đáp. Thử Ctrl giữ qua menu để đối chiếu log quarantine/re-arm; sprint thực thuộc C nên không dùng B để kết luận tốc độ sprint/replication đạt.
5. Giữ W/Space/Ctrl rồi Alt-Tab: chuột phải nhả. Quay lại vẫn có menu/AwaitingResume; không tự điều khiển. Resume trong khi giữ phím không phát lệnh cũ; nhả từng phím rồi nhấn mới hoạt động. Lặp một lần với phím nhấn trong menu và một lần nhả khi đang ở cửa sổ khác.
6. Dùng Back to Boot trong menu; vào sân mạng và lặp nhanh camera/Escape/Resume. Đi Boot→hai sân→Boot vài vòng: không nhân widget/context, Boot vẫn UI-only. Bấm Quit rồi mở lại: không mất đường vào sân; Editor gốc vẫn mở.

Log cần đối chiếu: `ControlLock` (Escape/ApplicationDeactivated/WindowDeactivated), `Resume`, `PhysicalPress` (ControlLocked/AwaitingPhysicalRelease), `PhysicalRelease/Rearm` và `Metrics` cùng PID/world/pawn/sourceSHA. Metrics có tọa độ camera cuối frame, aim/pitch, vai, hit, khoảng cách, mesh hidden, FOV, capture mode và trạng thái menu/focus. Fixture/console không thay các thao tác chuột/phím này.

Ghi PASS/FAIL từng mục, lỗi kèm thời điểm video/log. Chưa có xác nhận người dùng hoặc video thì giữ NOT-RUN, không đánh dấu nghiệm thu B. Không yêu cầu kiểm C–G, art anime hoặc mạng F trong phiên này.
