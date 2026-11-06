# Khảo sát U03 trước triển khai

Đọc trực tiếp source trên main khép U02 **33ad1f068370875440f5592ac9e2b20d938d9c7f**; sau đó main **76b627dc4ae1f6e5addd84d28d7c76e84cb2a970** đồng bộ trạng thái hợp đồng/ma trận, không đổi runtime. Nhánh hiện tại `u03/plan` chỉ chứa tài liệu. Không build/test/runtime mới;61/61,134/134 và36/36 là bằng chứng kế thừa U02-F được người dùng nghiệm thu, không phải kết quả U03. GitNexus không có tool hoặc index `.gitnexus` trong workspace; dùng `rg` và đọc source, không tuyên bố đã truy vấn đồ thị.

## Đường chạy và điểm phải mở rộng

| Điểm đọc | Hiện trạng xác minh | Việc cần làm trong U03 |
|---|---|---|
| `U01/U01PlayerController.cpp::ObservePhysicalKey` | Nhận cạnh LMB trực tiếp, một `CombatCommandSequence`, release gate chặn click Resume | Dispatcher theo binding, press/release và ưu tiên lệnh; không thêm đường input bỏ gate |
| `U02/U02CombatComponent.h/.cpp` | Attack RPC expected pawn/life, aim RPC expected pawn/life/action; chỉ một action; startup-turn deadline `.16`; phase boundaries hard-code | Definition theo action và snapshot có definition ID; buffer một slot, resource/cooldown; giữ stale/ownership validation |
| `U02/U02ActionModel.h/.cpp` | `FAttack1Definition` chỉ60/[.16,.22)/.40; busy reject, không combo/buffer | Model ba đòn và lịch chuyển tiếp; quyền cancel không được mở đại trà |
| `U02/U02CollisionWorld.cpp::DrainAt/ResolveHit` | Chụp pose, collect, sort, resolve batch; barrier drain trước mutation; vital/death trước candidate kế | Timeline phòng thủ/CC và định nghĩa immutable theo action ID; không dùng state cuối frame cho hit trước đó |
| `U02/U02VitalComponent.cpp::ApplyResolved` | Raw damage lấy trực tiếp `FAttack1Definition`; player/dummy identity cụ thể | Không chỉ đổi raw60 thành biến global; lấy đúng definition của candidate/action cũ; thêm kết quả phòng thủ trước HP/CC |
| `U02/U02Presentation.h`, `U01/U01AnimInstance.cpp` | Một montage; seek theo server time; chặn stop snapshot cũ theo pawn/life/action | Chọn clip/timeline cho từng đòn/skill, defense/dodge/CC; notify vẫn không quyết định hit |
| `U02/U02NetworkState.*` | History64 kết quả để log/HUD, không áp damage client | Outcome hit/block/parry/break/Interrupt và resource snapshots; tách diagnostic history khỏi feedback mới/HP hiện tại |
| `U01/U01Character.*`, `U01/U01NetworkMovement.cpp` | Motor/saved move giữ authority lock; tốc độ500/700; combat lock khác control gate | Dodge chuyển động do server, guard200; replay không phục hồi state cũ; không dùng ProbeSpeed làm AI production |
| Settings/control capture/menu U01 | Có nền save versioned, phím đơn/chord reject; combat còn hard-code LMB | Thêm attack/guard/dodge/X/Q/E/Tab, chuột; migration chỉ fallback phần xung đột, không autosave khi load |
| Lab/dummy/hurtbox | Dummy600 HP; world sources/adapter còn gắn `AU01Character`; dummy không có AI attack | Actor quái tham chiếu có movement300 và action source; bóc tối thiểu truy cập identity/pose/vital cho player/quái, không viết lại pawn |

## Rủi ro kiến trúc cần giải quyết ở hợp đồng A

1. **Đòn cũ, definition mới:** buffered action đổi model trước khi candidate cũ resolve có thể dùng nhầm damage70/90. Definition phải gắn immutable với action ID trong registry/candidate authority; vẫn drain interval cũ trước mutation.
2. **Hit nằm giữa frame:** parry/guard/CC phải đọc trạng thái tại timestamp hit, không đọc HP/defense/cooldown đã tiến tới endpoint. Bài học shield E áp dụng cho mọi deadline mới.
3. **Lệnh cùng timestamp:** drain hiện tại có thể đóng batch trước khi lệnh cùng world-time được nhận. Cần chốt admission cutoff/batch semantics trước dispatcher, không vá bằng epsilon hay backdate client.
4. **Frame vượt nhiều đòn:** buffer đã biết có thể khởi động đòn kế ở deadline cũ; không dùng aim/pose tương lai tại Now cho active đã qua. Một slot không được tự sinh cả chuỗi khi giữ LMB.
5. **Motor không còn chỉ khóa hoàn toàn:** guard cho bước200, dodge có sweep/nền và khóa đến.35; không sửa release gate WASD thành yêu cầu nhả sau recovery.
6. **AI chưa có nguồn action độc lập:** combat/vital/world đang cast cụ thể player/dummy. Chỉ tách điểm đọc identity/pose/definition/vital cần cho hai chủ thể thật; không thêm framework nghề/GAS.
7. **History cũ và rebind migration:** reconnect/reset không phát lại phản hồi như hit mới; rebind combat phải đi qua physical edge và UI gate hiện có.

Luật lấy từ Description4.2–4.7,6,7,15,19; phạm vi/thứ tự lấy ROADMAP U03.01–.09 và cổng U03. Không sửa Description. Các điểm chưa đủ thông số/ranh giới được đưa vào PLAN để review trước phần phụ thuộc.
