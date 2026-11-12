# U03-B1 R1 — retained swept trajectory

Reviewer NOT ACCEPTED bản bàn giao b2c9676 (source6603c30): preview chord và walking solve khi commit có thể khác nhau tại timestamp giữa bước. Bằng chứng cũ vẫn hợp lệ cho các ca đã chạy; giữ nguyên Evidence/B1 và raw lịch sử. Bản sửa không đổi timing/cost/charge/buffer/cancel rules và chưa B2.

## Một đường cho geometry và commit

- Native walking collision solve chạy trong scope preview để lấy các đoạn capsule sweep thực: ramp, slide và StepUp. Override MoveUpdatedComponentImpl ghi phần đi được; override StepUp loại scope rollback/search excursion. Chỉ rút gọn sang đoạn thẳng khi capsule sweep độc lập xác nhận đoạn đó không bị chặn.
- Đường được giữ thành các knot có timestamp, không chỉ hai đầu. Trên đường phẳng bị chặn, thời gian đi bằng quãng đường/1200, phần còn lại đứng yên. Ramp/StepUp chia thời gian quantum ngang1/240giây theo độ dài các đoạn hợp lệ; tối đa5cm ngang mỗi quantum. Không thêm thời gian khóa hoặc nới deadline.
- World phải chia tại mọi knot và capsule-contact boundary trước collect. Trong mỗi đoạn, geometry và commit dùng cùng hàm PositionAt(t). Commit phát lại đúng prefix đã sweep/CCD, bằng movement update ETeleportType::None; không chạy lại sweep/StepUp/slide cho partial timestep và không teleport300cm. Native sweep/CCD quyết định đường trước khi commit, không animation/notify.
- Quantum cache giữ qua endpoint update và hit boundary; một update dài và nhiều update ngắn dùng cùng prefix. Cache bỏ khi life/action, vị trí thực, nhóm pawn đang né hoặc scene geometry thay đổi. Trong đoạn đường còn hiệu lực, authority CMC không được chạy thêm walking solve ngoài world scheduler; Falling vẫn dùng gravity native.
- Khi lethal/lifecycle cắt ở giữa đoạn, actor đã commit đúng PositionAt(hit), phần còn lại không chạy. Confirmed hit không rewind. Khoảng thời gian vẫn nửa mở, không epsilon mở rộng action/buffer.

## Pawn va chạm đồng thời

Preview không dùng vị trí cũ của pawn đang né cùng batch làm blocker tĩnh. World giải continuous relative collision giữa các capsule thẳng đứng trên từng đoạn, cắt cả hai đường tại contact sớm nhất trước khi collect hit; phần còn lại quantum đứng yên. Pair order ổn định theo identity, xét lại sau mỗi clip. Trường hợp đứng yên/đuổi cùng hướng/đối đầu không được xuyên nhau hoặc bị chặn bởi transform cũ của peer. Skin0,01cm và tolerance hình học chỉ phục vụ collision, không phải tolerance thời gian gameplay.

## Regression/cổng review

R1 bắt buộc prefix ở tường/slide/StepUp; incoming hit trong bước tường và đoạn lên bậc, contact timestamp và actual transform tại callback, lethal cutoff; so long/short update; hai pawn né đối đầu/cùng hướng, đảo collection. Giữ hồi quy U00–B1; cold Editor/Game, MCP Automation đúng process clone, package/smoke, input/video và dedicated Editor+hai client/reconnect trên source mới. Không lấy90 tests/video cũ làm bằng chứng binary R1. Bàn giao READY_FOR_REVIEW, chưa tự ACCEPTED/merge/B2; Editor/config riêng giữ nguyên.
