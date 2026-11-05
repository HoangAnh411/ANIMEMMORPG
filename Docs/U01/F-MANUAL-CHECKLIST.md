# U01-F — Checklist review

**PENDING USER REVIEW**, nguồn `df897f6088da4cca423085e9fe8e9c2869c98420`. AI đã kiểm 23/23 Automation, smoke package 3/3 và phiên dedicated Editor server/hai client; chi tiết REPORT-F. Checklist này không tự ghi PASS thay người chơi.

Người dùng đã đánh dấu các mục điều khiển dưới đây đạt; **giữ nguyên các dấu X đó, chưa nghiệm thu F** do FPS/độ trễ cần xem lại. Nguồn native/build/package revision `0f02c77bc14fc4c727ba8694223f8cfc5a655c31`; xem REPORT-F-PERFORMANCE. Launcher mới dùng profile review local4GiB: cache/pool nhỏ hơn, internal resolution50% (cửa sổ900×540), thu nhỏ Editor gốc nhưng giữ process mở, timer hint riêng cho server. Không đổi renderer backend, mạng, smoothing hoặc settings sản phẩm. Dừng bằng StopFSession sẽ khôi phục cửa sổ Editor; dùng `-OriginalQuality -KeepEditorVisible` chỉ để đối chứng.

Chạy `Artifacts/U01/F/Play-F.cmd`: mở server riêng và hai client 900×540. Chọn Resume khi đổi cửa sổ. Mỗi client mở console bằng `~`, nhập `U01NetFixture reset` để vào đường thử trống; đây là reset fixture, không hồi sinh sản phẩm. Phiên mới dùng settings riêng, mặc định W/Ctrl/Space.

- [X] A đi/sprint/nhảy; nhìn ở B thấy đúng nhân vật, animation lên/rơi/đáp và carry kiếm tạm. B làm ngược lại; chỉ pawn sở hữu nhận điều khiển.
- [X] Sprint → nhảy → tiếp đất và đổi hướng không kẹt pose; so sánh video NormalB/AttacksSettingsA nếu cần.
- [X] A mở Escape/menu; B vẫn đi/nhảy. Trở lại A phải Resume, nhả phím cũ rồi mới điều khiển.
- [X] A đổi sensitivity/phím tiến trong Điều khiển; B giữ thiết lập của B.
- [X] B Quit; A không thấy pawn B cũ. Đóng phiên bằng StopFSession rồi chạy launcher lại nếu muốn lặp (disconnect/reconnect tự động đã có video/log riêng).

Để dừng đúng process review, đọc `Artifacts/U01/F/LatestReview.txt`, chạy `Scripts/U01/StopFSession.ps1 -SessionPath <đường-dẫn-đó>`. Không cần đóng Editor gốc. Báo lại cảm giác/quan sát còn lỗi; chưa merge F/G. Cảnh báo VRAM có thể xuất hiện khi mở đồng thời Editor và hai client; không coi phiên này là nghiệm thu FPS G.

Có thể dùng `Artifacts/U01/F/Stop-F.cmd` để dừng đúng phiên mới nhất và khôi phục cửa sổ Editor. Chỉ cần review lại hai mục sau trên profile mới, không phải làm lại toàn bộ điều khiển:

- [ ] Lần lượt focus A rồi B: cửa sổ nền vẫn cập nhật chuyển động đều, không đứng hình/xem pawn kia chậm khoảng một giây. So video RepeatA/RepeatB và số đo gần30FPS ở REPORT-F-PERFORMANCE.
- [ ] Đánh giá độ nét của profile kỹ thuật50% có chấp nhận cho review cùng máy hay không. Chất lượng đồ họa gốc vẫn chưa được chứng minh ổn với ba process; không coi lựa chọn này là nghiệm thu art/FPS G.
