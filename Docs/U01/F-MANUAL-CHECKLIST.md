# U01-F — Checklist review

**PENDING USER REVIEW**, nguồn `df897f6088da4cca423085e9fe8e9c2869c98420`. AI đã kiểm 23/23 Automation, smoke package 3/3 và phiên dedicated Editor server/hai client; chi tiết REPORT-F. Checklist này không tự ghi PASS thay người chơi.

Chạy `Artifacts/U01/F/Play-F.cmd`: mở server riêng và hai client 900×540. Chọn Resume khi đổi cửa sổ. Mỗi client mở console bằng `~`, nhập `U01NetFixture reset` để vào đường thử trống; đây là reset fixture, không hồi sinh sản phẩm. Phiên mới dùng settings riêng, mặc định W/Ctrl/Space.

- [ ] A đi/sprint/nhảy; nhìn ở B thấy đúng nhân vật, animation lên/rơi/đáp và carry kiếm tạm. B làm ngược lại; chỉ pawn sở hữu nhận điều khiển.
- [ ] Sprint → nhảy → tiếp đất và đổi hướng không kẹt pose; so sánh video NormalB/AttacksSettingsA nếu cần.
- [ ] A mở Escape/menu; B vẫn đi/nhảy. Trở lại A phải Resume, nhả phím cũ rồi mới điều khiển.
- [ ] A đổi sensitivity/phím tiến trong Điều khiển; B giữ thiết lập của B.
- [ ] B Quit; A không thấy pawn B cũ. Đóng phiên bằng StopFSession rồi chạy launcher lại nếu muốn lặp (disconnect/reconnect tự động đã có video/log riêng).

Để dừng đúng process review, đọc `Artifacts/U01/F/LatestReview.txt`, chạy `Scripts/U01/StopFSession.ps1 -SessionPath <đường-dẫn-đó>`. Không cần đóng Editor gốc. Báo lại cảm giác/quan sát còn lỗi; chưa merge F/G. Cảnh báo VRAM có thể xuất hiện khi mở đồng thời Editor và hai client; không coi phiên này là nghiệm thu FPS G.
