# Chơi thử U03-C2

Trạng thái đang triển khai; chỉ dùng launcher sau khi REPORT-C2 và manifest xác nhận đủ cổng kỹ thuật. Không xem nút Play trong Editor gốc là bản C2 đã xác minh.

- Chạy `Play-U03-C2.cmd`. Tiếp cận quái, đọc WINDUP / STRIKE / RECOVER bằng tư thế, mũi tên và vùng kiếm.
- Thử né, parry, Q và E: E trúng startup có thể Interrupt; Q không Interrupt. Đứng trong 2 m vẫn có thể đánh hụt.
- Dùng binding Target (mặc định Tab) để đánh dấu, giữ không lặp, nhấn lại để bỏ. Xoay camera ra ngoài màn hình và thử tường che; marker/HP phải ẩn đúng luật, camera và hướng đánh không tự đổi.
- Đánh thắng rồi Retry; thử đứng nhận đòn để thua rồi Retry. Retry vẫn cần Resume; giữ phím qua Retry không được tạo lệnh cũ, click Retry không được thành đòn đánh.
- Dẫn quái ra xa hoặc mất đường nhìn: quái về spawn quanh vật cản, không đổi sang chủ khác, không teleport, chỉ hồi đầy khi đã về vùng reset.
- Chạy `Play-U03-C2-Network.cmd`: hai người có trạm riêng và nhãn owner. Thắng/thua/Retry ở một trạm không đổi trạm kia. Input tự động tuần tự không được hiểu là hai người bấm đồng thời.
- Dừng bằng `Stop-U03-C2.cmd` để chỉ dừng session C2 và khôi phục placement Editor. Trạm hồi quy cũ có lối vào session riêng trong menu.

Ghi nhận cảm giác báo đòn, chase/return và vòng Retry. Assertions/video kỹ thuật không thay đánh giá này. B2/C1 vẫn chưa được người dùng chơi thử; C2 không khép toàn U03.
