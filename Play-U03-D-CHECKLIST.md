# U03-D-R1 playtest

**Đã xác nhận chơi thử blockout ngày 2026-11-16.** Người dùng đã chơi D và xác nhận ổn các mục dưới đây trên bản D-R1: source `0b25523`, bàn giao kỹ thuật `a7737f9`, mốc khép kỹ thuật `89358c5`; package theo launcher/manifest D-R1 là `Artifacts/U03/D/Runs/Package-20261116-140739/Archive/Windows`. Không có mục chủ động hoãn hoặc lỗi chặn D được báo. Đây không phải bản Play trong Editor gốc.

Mở **Play-U03-D.cmd** (Solo) hoặc **Play-U03-D-Network.cmd** (hai cửa sổ). A/B là hai trạm encounter riêng, nên quái của A không chuyển sang B. Đổi focus thì chọn Resume. **Stop-U03-D.cmd** dừng đúng session và khôi phục placement Editor; Play trong Editor gốc không mặc định là D-R1.

1. Startup/active/recovery và hướng đòn có dễ đọc không?
2. Hit/block/parry/hụt/break/Feint/Interrupt có phân biệt được bằng hình/âm không?
3. Dodge/guard/CC/X có dễ hiểu; grip kiếm và tư thế có xuyên thân rõ rệt không?
4. HUD/phím/cooldown có dễ đọc? Nhãn/phản hồi đối thủ và HP phải ẩn sau vật cản; phần telegraph bị che không hiện xuyên. HP vừa trúng không tự bật Tab.
5. Won/Lost → Retry → Resume, đổi focus và hai cửa sổ có ổn không? Retry không đánh và không tự Resume.

Escape → **Open regression stations (separate run)** vào trạm fixture có nhãn. **Back to Boot** trở về. Settings lưu riêng Solo/A/B dưới `Artifacts/U03/D/UserSettings`; reconnect giữ preferences, không giữ combat progress.

Reviewer AI đối chiếu source/hash/log và bằng chứng kỹ thuật; người dùng xác nhận cảm giác và hình ảnh blockout qua chơi thử. D đã hoàn tất cổng kỹ thuật và chơi thử blockout, không phải nghiệm thu art/animation sản phẩm hay hiệu năng U04. Hồ sơ xác nhận cuối đang chờ review trên nhánh tài liệu riêng, chưa merge; chưa khép toàn U03 hoặc bắt đầu U04. Không chạy lại build/tests/package hoặc tác động Editor trong lượt cập nhật hồ sơ này.
