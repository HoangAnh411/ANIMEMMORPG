# U01-E — Checklist review package cuối

**PASS — người dùng xác nhận nghiệm thu tại cb46c52, package nguồn c8df4ff.** Giữ dấu xác nhận chơi thử của người dùng và lịch sử kiểm chứng trong REPORT-E.

Nguồn **c8df4ff2182c0006c11f65466ecec4b9223be5a3**, nhánh `u01/e-settings`. Mở `Artifacts/U01/E/Play-E.cmd`; vào sân nhân vật. Settings dùng thư mục riêng của launcher. [REPORT-E](REPORT-E.md) có build 21/21 tests, smoke3/3, video và giới hạn.

- [X] Trong Điều khiển, thử đổi các hướng, nhảy, sprint và đổi vai; phím mới dùng được, phím cũ ngừng tác dụng. Thử phím trùng/reserved và Escape hủy nhận phím. Middle/thumb mouse được hỗ trợ; LMB/RMB và cuộn dành riêng/không nhận.
- [X] Kéo sensitivity, thử đảo Y/vai mặc định và khôi phục defaults. Save/Resume, Quit và mở lại vẫn giữ thay đổi.
- [X] Giữ đi/nhảy/sprint qua Escape → Resume và Alt-Tab → trở lại → Resume: không tự chạy/nhảy lại trước khi nhả và nhấn mới. Chuột xoay trực tiếp sau Resume.
- [X] G bật/tắt fixture Interacting; fixture Defeated ở menu. Khi khóa không đi/nhảy được, vẫn xoay camera/menu và chịu gravity. Mở khóa không phát lại input đang giữ.
- [X] Về Boot và vào lại hai sân: UI/input không nhân đôi, không kẹt điều khiển. Đánh giá kích thước chữ, thao tác đổi phím và cảm giác camera có thuận tiện.

Lỗi lưu/file hỏng đã được tool kiểm trong thư mục fixture riêng, kèm ảnh/video; không cần người dùng phá file settings để lặp lại. Khi lưu thất bại, menu báo lỗi, giữ dirty và chờ Save thành công trước Resume/Boot/Quit.

D chỉ nghiệm thu mannequin/kiếm blockout và carry tạm. **Art anime/animation chiến đấu vẫn DEFERRED. Người dùng cho phép khép hồ sơ/fast-forward E rồi triển khai riêng F; chưa nghiệm thu F hoặc Server đóng gói.**
