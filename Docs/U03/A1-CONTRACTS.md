# U03-A1 — hợp đồng triển khai

Nền main đã nghiệm thu `5f8700e69b0f381a2f6b0d158667ac9283aa98ab`; nhánh riêng `u03/a1-combo`. A0 ACCEPTED chỉ là nền model, không thay bằng chứng runtime A1. Chưa ACCEPTED A1, không merge hoặc triển khai B1.

## Phạm vi

Ba đòn raw60/70/90, active[0,16;0,22)/[0,18;0,25)/[0,26;0,36), tổng0,40/0,45/0,60. Chuỗi nối ngay220 raw/1,45s. Buffer một slot0,15s chỉ trong đánh thường; cạnh mới thay cũ, đúng expiry không consume; grace0,15s sau1/2, đòn3 nối1. Giữ nút không lặp. Menu/focus/reset/mất nền/death xóa pending theo luật, không dùng menu để hủy action đã nhận. Không đổi các luật trong kế hoạch U03.

Dispatcher dùng physical edge, release gate và binding chung. Chỉ Attack có gameplay trong A1. Guard/Dodge/X/Q/E/Target trả Unsupported, không tạo action, tiêu energy hoặc CD giả. Resource có model/snapshot và fixture native có nhãn kiểm energy/CD, không cấp kỹ năng Q/E. Save envelope giữ version1, JSON payloadv2 đọc đượcv1; load không tự save, giữ LocalPlayer isolation và phục hồi nhóm xung đột.

## Barrier và payload authority

RPC chỉ enqueue intent với identity/life/sequence/aim; thời gian client chỉ diagnostic. Scheduler authority đóng dấu accept tại lượt mô phỏng nhận được, không thêm timer/frame đệm. Trước admission, resolver drain toàn interval/action cũ và hết nhóm event cùng timestamp. Watermark chống replay giữ qua reset; command life sai không được nhận. Không có damage/hit/HP RPC do client tự khai.

World chọn boundary gần nhất của tất cả model và candidate geometry/obstruction. Mọi model tới cùng timestamp trong trạng thái barrier mở, chưa chuyển action. Resolver sort cả batch theo U02 timestamp/source/event/hurtbox, áp vital/death/cutoff trước event kế tiếp, rồi mới finish barrier và tạo successor. Phần interval còn lại được collect lại theo action mới. Ledger preview loại event đã dedup/không còn hợp lệ trước khi chọn timestamp tiếp theo; không rewind confirmed hit. Cutoff loại đúng timestamp nếu là lifecycle mutation đã biết trước contact đó. LostGround/landing đi qua barrier, latch nền không tự được clear bởi context cũ.

Candidate mang definition ID/version/raw của action đã collect, không đọc raw của action hiện tại khi resolve. Vital dùng payload authority này, giữ một đường damage/crit/shield/death. Snapshot current giữ definition/timing/resource/CD, owner-only acknowledgement giữ command/pending/expiry/admission. History64 chỉ trình bày, không cấp quyền HP/action.

## Motor và trình bày

Giữ motor500/700, gravity/jump/camera/saved-move authority. Startup xoay tới deadline riêng của mỗi đòn; active/recovery khóa thân, camera tự do, WASD đang giữ dùng lại sau recovery. Root motion bị ignore, notify không quyết định gameplay.

Attack1 giữ clip U02 đã có provenance; Attack2 chém ngược0,45s, Attack3 bổ xuống0,60s được author từ pose/skeleton U01 bằng source trong `U03AnimationEditor`, chỉ chạy trong clone A1. AnimBP A1 kế thừa graph U02, không ghi đè asset U02. HUD hiển thị phím Attack thật, action/combo, energy, pending và admission; damage/HP/feedback lấy kết quả authority. Art/âm/presentation sản phẩm đầy đủ vẫn thuộc D.

## Kiểm chứng và điểm dừng

Build/test/package từ source đã commit trong clone; không dùng Editor gốc làm bằng chứng binary mới. Process Editor gốc được kiểm thực, không kế thừa native/placement của PID12280. Không tự restart/lưu Editor. Launchers kiểm source/binary/package manifest; network giữ client60/server30,900x540/internal50%, profile render đã nghiệm thu và cvar thực; chỉ ready sau clients ready và xác minh mọi cửa sổ Editor gốc minimized. Stop theo session/PID/executable/project/userDir/hash, gồm reconnect và khôi phục placement ban đầu.

Phân biệt Automation, Game-world assertions, input Windows/video, package smoke và network process. Giữ failed/invalid runs/warnings. Không gọi raw660 là HP thực mất600, không gọi bước model120Hz là120FPS thực. Bàn giao READY_FOR_REVIEW A1, không tự ACCEPTED/merge/B1.
