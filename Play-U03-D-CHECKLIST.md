# U03-D-R1 playtest

## Trạng thái tổng hợp hiện hành

U03 hoàn tất kỹ thuật; người dùng đã xác nhận chơi thử blockout tích hợp D ngày **2026-11-16**, ghi tại `3439fed`, với phạm vi checklist dưới đây. Reviewer AI đối chiếu source/hash/log; người dùng đánh giá cảm giác và hình ảnh blockout. Mốc giữ nguyên: D-R1 `a7737f9`, source/binary `0b25523`, khép kỹ thuật D `89358c5`; commit hồ sơ không phải nguồn binary.

Không suy ngược rằng người dùng đã chơi các package B2/C1 cũ. Art/animation sản phẩm, hiệu năng U04, mạng xấu U05 và Server đóng gói chưa được nghiệm thu. [Hồ sơ tổng hợp](CLOSURE-D.md) và [ROADMAP](Docs/ROADMAP.md) đang chờ review cuối trước merge; sau khi được review và giao khép mới lập kế hoạch U04, chưa triển khai U04.

## Checklist và xác nhận lịch sử đã ghi tại 3439fed

Giữ nguyên nội dung đã review bên dưới. Các câu “chưa khép toàn U03” mô tả thời điểm ghi nhận trước khi đồng bộ hồ sơ tổng hợp; không đổi manifest/bằng chứng hoặc tạo lượt kiểm thử mới.

**Đã xác nhận chơi thử blockout ngày 2026-11-16.** Người dùng đã chơi D và xác nhận ổn các mục dưới đây trên bản D-R1: source `0b25523`, bàn giao kỹ thuật `a7737f9`, mốc khép kỹ thuật `89358c5`; package theo launcher/manifest D-R1 là `Artifacts/U03/D/Runs/Package-20261116-140739/Archive/Windows`. Không có mục chủ động hoãn hoặc lỗi chặn D được báo. Đây không phải bản Play trong Editor gốc.

Mở **Play-U03-D.cmd** (Solo) hoặc **Play-U03-D-Network.cmd** (hai cửa sổ). A/B là hai trạm encounter riêng, nên quái của A không chuyển sang B. Đổi focus thì chọn Resume. **Stop-U03-D.cmd** dừng đúng session và khôi phục placement Editor; Play trong Editor gốc không mặc định là D-R1.

1. Startup/active/recovery và hướng đòn có dễ đọc không?
2. Hit/block/parry/hụt/break/Feint/Interrupt có phân biệt được bằng hình/âm không?
3. Dodge/guard/CC/X có dễ hiểu; grip kiếm và tư thế có xuyên thân rõ rệt không?
4. HUD/phím/cooldown có dễ đọc? Nhãn/phản hồi đối thủ và HP phải ẩn sau vật cản; phần telegraph bị che không hiện xuyên. HP vừa trúng không tự bật Tab.
5. Won/Lost → Retry → Resume, đổi focus và hai cửa sổ có ổn không? Retry không đánh và không tự Resume.

Escape → **Open regression stations (separate run)** vào trạm fixture có nhãn. **Back to Boot** trở về. Settings lưu riêng Solo/A/B dưới `Artifacts/U03/D/UserSettings`; reconnect giữ preferences, không giữ combat progress.

Reviewer AI đối chiếu source/hash/log và bằng chứng kỹ thuật; người dùng xác nhận cảm giác và hình ảnh blockout qua chơi thử. D đã hoàn tất cổng kỹ thuật và chơi thử blockout, không phải nghiệm thu art/animation sản phẩm hay hiệu năng U04. Hồ sơ xác nhận cuối đang chờ review trên nhánh tài liệu riêng, chưa merge; chưa khép toàn U03 hoặc bắt đầu U04. Không chạy lại build/tests/package hoặc tác động Editor trong lượt cập nhật hồ sơ này.
