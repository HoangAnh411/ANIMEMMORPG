# U03-A1 — ma trận kiểm chứng

| Nhóm | Bằng chứng bắt buộc |
|---|---|
| World combo | Definition1/2/3 raw60/70/90,220raw/1,45; ba combo raw660, dummy600 chết đúng hit9, HP damage600 |
| Buffer/input | TTL/replacement/grace, held không loop; menu/focus/reset xóa pending, release gate/Resume, WASD sau recovery |
| World timeline | Update dài qua successor; hit địch Interrupt/death trong startup của successor; nhóm cùng timestamp trước chuyển action; lost-ground/landing/cutoff; giữ confirmed hit |
| Collision/vital | Tường/multihurtbox/whole-active/dedup, origin từ chân, shield deadline/rounding/death U02; payload action cũ không bị definition mới thay |
| Authority | Expected pawn/life, duplicate/stale/nonfinite/ownership; không damage RPC; owner ack và current snapshot |
| Resource/binding | Energy/CD snapshot và fixture native không tạo skill; Q/E/né/phòng thủ chưa có gameplay; binding chung, v1/v2, conflict/reserved/chord/wheel và LocalPlayer |
| Presentation | Ba clip khác nhau/đúng timing, root ignore, montage chọn theo definition, stale snapshot/history không dừng action mới |
| Build/package | Editor/Game, Automation liên quan và hồi quy U00–U03; Windows package/cook/reference/ba map smoke đúng source/hash |
| Input/video | Physical edges trên package, nhịp ba đòn/đổi hướng startup, hold/menu/focus/Resume, trở lại di chuyển; video theo wall clock |
| Network | Dedicated Editor server + hai client; action definition/HP/result đồng thuận; duplicate/stale/ownership, profile cvar và placement ready/Stop |

Các test U02 từng giả định Submit xử lý ngay phải đặt barrier tại timestamp nhận của fixture, vì RPC/runtime A1 enqueue. Busy-reject của model U02 lịch sử vẫn giữ trong test thuần; runtime normal Attack chuyển sang buffer theo luật U03. Không xóa coverage identity/collision cùng các giả định cũ. Failed runs giữ nguyên, không dùng0 tests/trigger-success làm PASS.

Kết quả thực và SHA/run/hash ghi trong REPORT-A1. Ma trận không tự cấp nghiệm thu; kết luận reviewer ghi tại ACCEPTANCE-A1.

Đối chiếu bàn giao: tám test `AnimeMMORPG.U03.A1` đều PASS trong run `MCPTests-20261107-194121`. Tổng78/78 gồm hồi quy U00/U01/U02/A0, chạy mới trên source A1. Package/smoke3/3; input46+16; network19 và reconnect2. Chi tiết từng test, failed/invalid runs và giới hạn xem REPORT-A1. **ACCEPTED về kỹ thuật tại6ae268e, source kiểm chứng0957867e**, theo [reviewer](ACCEPTANCE-A1.md). Reviewer đối chiếu source/log/hash, không chạy lại tests. Lượt khép chỉ sửa tài liệu; giữ nguyên evidence/failed runs. Animation vẫn blockout, không nghiệm thu hình ảnh sản phẩm; chưa B1.
