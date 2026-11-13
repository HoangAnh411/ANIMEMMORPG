# C1 playtest — blockout, chưa nghiệm thu cảm giác

C1 đã ACCEPTED về kỹ thuật tại bàn giao `db592ff`; người dùng chưa chơi thử B2/C1. Presentation vẫn blockout; nghiệm thu kỹ thuật không thay xác nhận cảm giác chơi, readability hoặc hình ảnh sản phẩm. Xem [hồ sơ nghiệm thu](Docs/U03/ACCEPTANCE-C1.md).

Chạy `Play-U03-C1.cmd` (package) hoặc `Play-U03-C1-Network.cmd` (dedicated Editor + hai client). `Stop-U03-C1.cmd` dừng đúng session và khôi phục placement Editor. Nút Play trong Editor gốc chưa được bảo đảm chạy C1. Giữ profile client60/server30.

- Q Hư Trảm, E Phá Thế: bấm cạnh, giữ không lặp; xem năng lượng và cooldown 4/6s trên HUD. Phím hiển thị theo binding hiện tại.
- Q rồi nhả/nhấn Q trong startup: `< FEINT >`, không hoàn năng lượng/CD. Đi bộ được; combat, sprint, jump khóa .20s. Q tại active-start không Feint.
- Đánh thường: thử Q/E nối recovery từng đòn 1/2/3. Startup/active từ chối, không tiêu. Hết skill không tự phát lại lệnh từ chối.
- Trong startup Q/E: thử né và guard. Không hủy khi active/recovery; guard đang giữ phải chủ động nhả trước skill.
- Fixture có nhãn `target-q`, `target-attack`, `target-e`, `target-block`, `target-parry`, `target-shield`, `incoming-e`: dùng input Q/E thật. E ngắt startup qua hit, không stun; block/parry chặn, shield không miễn. Q không Interrupt.
- Menu/focus: cooldown tiếp tục; Resume không phát lại phím giữ. Thử rebind Q/E rồi nhả/nhấn lại.

Ghi lại cảm giác chuyển động và tín hiệu pha/Feint/Interrupt sau khi chơi. Assertions/video kỹ thuật không thay xác nhận của người dùng. B2/C1 presentation vẫn blockout.

Solo fixture: mở console (phím dấu huyền/~) rồi nhập `U03B2Fixture target-q` (hoặc nhãn ở trên); `U03B2Fixture off` dọn fixture. Tên lệnh giữ từ B2. Trong session mạng dùng `powershell -File Scripts/U03/SetC1Fixture.ps1 -Label target-q`; kỹ năng vẫn bấm thật trên client. Fixture không phải AI/encounter C2.
