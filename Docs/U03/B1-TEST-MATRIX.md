# U03-B1 — ma trận kiểm chứng

| Nhóm | Kiểm chứng |
|---|---|
| Model deadline/charges |0,25/0,35/0,60/2/4; hồi tuần tự không reset; không tiêu energy; update dài|
| Buffer |TTL0,15, replacement, exact expiry, hai lượt cạn không buffer; menu/focus/reset clear; hold không lặp|
| Replacement/priority |hủy startup sau kiểm điều kiện; exact active-start từ chối; cùng timestamp né trước đánh sau old-world barrier|
| Motor |300cm±5 trên nền trống; capsule sweep tường/người/góc; nền/step45cm/dốc45°/vực; mất nền thật chuyển Falling; slow không đổi né|
| Lifecycle |death/reset/lost-ground/landing, stale life/duplicate/nonfinite/ownership; saved move không tái tạo action/lượt hoặc jump cũ|
| Regression |U00–A1 phù hợp, collision/dedup/cutoff/whole-active/update dài, camera/gravity/gate/WASD/motor500/700|
| Package/input |Editor/Game cold build, Windows package/cook/smoke3map; physical Shift/WASD/no-direction, held, startup cancel, wall/cliff, menu/focus/Resume; video wall-time|
| Network |dedicated Editor+2clients: authority/admission/charges/position, peer presentation, duplicate/stale/ownership/reconnect; cvar thực và placement ready/Stop|

Kết quả thực, giới hạn và failed runs ghi trong REPORT-B1. Tài liệu này không tự xác nhận PASS hoặc ACCEPTED; A1/A0 nghiệm thu là nền kế thừa, không thay bằng chứng B1.

Bàn giao **READY_FOR_REVIEW**, source6603c30:12 test B1 cùng78 hồi quy chạy mới, tổng90/90 Success,0 Failed, queue hoàn tất. Build Editor/Game và Windows package thành công; smoke3/3; package input/video38 checks và terrain17; dedicated Editor+hai client20 và reconnect2. Chi tiết tên test/run/hash, phần fixture slow/hardCC, các lượt failed/invalid và giới hạn FPS/presentation trong [REPORT-B1](REPORT-B1.md). Chưa ACCEPTED/merge/B2.
