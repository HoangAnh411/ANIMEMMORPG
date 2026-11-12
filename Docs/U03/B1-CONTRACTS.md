# U03-B1 — hợp đồng né/motor

B1 được giao ngày2026-11-12 từ main04f902e. Các câu chưa giao B1 trong hồ sơ A1 là lịch sử. Chỉ né/motor: chưa B2/C1/C2, không thêm module/plugin/framework hoặc prediction U05.

Né300cm trong[0;0,25), vận tốc chủ động1200cm/s; khóa action/jump/guard/interaction đến0,35. Hai start cách>=0,60. Hai lượt, hồi tuần tự2giây từ lần tiêu đầu, dùng lượt tiếp không đổi deadline hồi. Không tiêu energy, không i-frame/Perfect Dodge/tự chọn hướng. Normalize WASD local camera yaw, không hướng thì lùi aim; capture hướng tại admission, slow không tác động vận tốc né. Chỉ cạnh nhấn thật, giữ Shift không lặp.

Slot né TTL0,15 riêng với slot đánh; chỉ nhận khi đang né/chờ0,60 và còn lượt. Không nhận lúc hết lượt/hardCC/airborne/active hoặc recovery đánh. Cạnh mới thay slot cũ, exact expiry không consume. Menu/focus/reset/lost-ground/death xóa pending; menu không hủy dịch chuyển đã nhận. Né hợp lệ hủy startup đánh và reset combo, mọi điều kiện thay thế phải hợp lệ trước khi hủy. Cạnh tại active-start bị từ chối. Tại cùng timestamp, né trước đánh, sau barrier collision/lifecycle cũ; invalid command không tiêu lượt.

Model timeline sở hữu lượt, deadline, sequence và hướng. Server RPC chỉ enqueue identity/life/sequence/aim/WASD, không nhận vị trí/damage/lượt/cooldown tự khai. Snapshot replicate trạng thái né cùng resource/action; watermark giữ qua reset life. Saved moves không sở hữu model/lượt/deadline, không restore jump của life cũ. Smoothing và network correction giữ nguyên A1.

Motor dùng walking sweep capsule/MoveAlongFloor/StepUp/FindFloor/AdjustFloorHeight hiện có, góc45°, step45cm U01. Chia đường thành các slice không quá5cm. Probe support ở tâm điểm tới để không bước qua vực. Preview bằng deferred scoped movement, revert transform và overlap chưa publish; không phát impact gameplay. World collect geometry theo đường preview trong slice, arrive mọi model ở event sớm nhất, commit walking tới event đó rồi resolve cả nhóm trước transition/admission. Không teleport300cm hoặc root motion. Khi nền hiện tại mất thật, dừng né và chuyển Falling; charge không refund khi bị chặn.

Presentation/HUD có thể blockout, luôn lấy state authority; montage không quyết định né/hit/damage. Package/client60/server30 và placement/Stop giữ quy tắc A1, với đường dẫn/manifest/session riêng B1. Editor gốc/config riêng giữ nguyên. Source/header thay đổi được cold build và test trong clone, không Live Coding/restart Editor gốc.

Bàn giao READY_FOR_REVIEW B1 với build Editor/Game, Automation/hồi quy, package/smoke3map, input/video thật và dedicated Editor+hai client; lưu failed/invalid runs/hash/warnings. Không tự ACCEPTED/merge/B2.
