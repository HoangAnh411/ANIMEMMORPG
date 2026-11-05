# U01-F — Checklist review

**?? NGHI?M THU U01-F theo x?c nh?n ng??i d?ng t?i `2bd9b565500042d25c8a8958df481f55175a753d`.** Ph?m vi: dedicated Editor server v? hai client, profile client60/server30; ch?a bao g?m Server ??ng g?i, hi?u n?ng ?? h?a s?n ph?m1080p ho?c G. Gi? native diagnostics `edf885ac79d900977a43a404019eadce0244ed47`, package ngu?n `0f02c77bc14fc4c727ba8694223f8cfc5a655c31`, to?n b? hash v? l?ch s? ki?m ch?ng. Ng??i d?ng cho ph?p kh?p h? s?/push/fast-forward F v?o main r?i tri?n khai ri?ng G trong clone, Editor g?c gi? m?. C?c tr?ng th?i ch? review b?n d??i l? l?ch s? tr??c x?c nh?n n?y.

**PENDING USER REVIEW profile F60**, native diagnostics `edf885ac79d900977a43a404019eadce0244ed47`; package giữ nguồn `0f02c77bc14fc4c727ba8694223f8cfc5a655c31`, đã xác minh hash. AI đã đo A–D120s/lượt, logging control và300s liên tục; cold MCP23/23. Chi tiết và lịch sử df897f6/0f02c77 tại REPORT-F/REPORT-F-PERFORMANCE. Chưa nghiệm thu hoặc merge F.

Người dùng đã đánh dấu các mục điều khiển dưới đây đạt; **giữ nguyên các dấu X đó**. Default mới: **hai client60/server30**, review local4GiB, internal50% (cửa sổ900×540), atlas2048/RT minimum128/streaming pool256MiB; Editor thu nhỏ nhưng process vẫn mở, timer hint riêng server. Không đổi renderer backend, motor, replication, smoothing hoặc settings sản phẩm. Dừng sẽ khôi phục cửa sổ Editor. `Play-F.cmd -ClientMaxFPS 30` để đối chiếu; thêm `-ClientCount 1` để chạy một client. `-OriginalQuality` chỉ được đo đạt60 với một client ở900×540, chưa phải benchmark sản phẩm/G.

Chạy `Artifacts/U01/F/Play-F.cmd`: mở server riêng và hai client 900×540. Chọn Resume khi đổi cửa sổ. Mỗi client mở console bằng `~`, nhập `U01NetFixture reset` để vào đường thử trống; đây là reset fixture, không hồi sinh sản phẩm. Phiên mới dùng settings riêng, mặc định W/Ctrl/Space.

- [X] A đi/sprint/nhảy; nhìn ở B thấy đúng nhân vật, animation lên/rơi/đáp và carry kiếm tạm. B làm ngược lại; chỉ pawn sở hữu nhận điều khiển.
- [X] Sprint → nhảy → tiếp đất và đổi hướng không kẹt pose; so sánh video NormalB/AttacksSettingsA nếu cần.
- [X] A mở Escape/menu; B vẫn đi/nhảy. Trở lại A phải Resume, nhả phím cũ rồi mới điều khiển.
- [X] A đổi sensitivity/phím tiến trong Điều khiển; B giữ thiết lập của B.
- [X] B Quit; A không thấy pawn B cũ. Đóng phiên bằng StopFSession rồi chạy launcher lại nếu muốn lặp (disconnect/reconnect tự động đã có video/log riêng).

Để dừng đúng process review, đọc `Artifacts/U01/F/LatestReview.txt`, chạy `Scripts/U01/StopFSession.ps1 -SessionPath <đường-dẫn-đó>`. Không cần đóng Editor gốc. Báo lại cảm giác/quan sát còn lỗi; chưa merge F/G. Cảnh báo VRAM có thể xuất hiện khi mở đồng thời Editor và hai client; không coi phiên này là nghiệm thu FPS G.

Có thể dùng `Artifacts/U01/F/Stop-F.cmd` để dừng đúng phiên mới nhất và khôi phục cửa sổ Editor. Chỉ cần review lại ba mục sau trên default60, không phải làm lại toàn bộ điều khiển:

- [X] A rồi B đi/sprint/nhảy: độ mượt profile60 ổn, không xuất hiện chuỗi khựng dài.
- [X] Nhìn pawn đối phương lúc bắt đầu/dừng: không chậm khoảng một giây hoặc giật rõ. Đuôi dừng hẳn tại60 tăng trung bình24–40ms so30 do giảm tốc/smoothing đã giải thích trong báo cáo; xác nhận cảm giác này chấp nhận được.
- [X] Đổi focus hai chiều, mở menu và Resume: cửa sổ nền vẫn cập nhật, không tự chạy/nhảy bằng phím cũ. Không coi xác nhận này là nghiệm thu art hoặc FPS G.
