# Hợp đồng nền U00-D

Thiết kế dùng mét và giây; Transform Unreal dùng centimet: 1 m = 100 cm. Góc tính độ. Hệ trục Unreal: X tiến, Y phải, Z lên; yaw +90° quay +X về +Y. World space là tọa độ chung của world; local space tương đối transform cha. TransformPosition áp xoay/scale/dịch; hướng dùng phép biến đổi vector (không dịch), không cộng vị trí vào hướng. Chuyển đơn vị tại ranh giới dữ liệu thiết kế/Transform, không chuyển hai lần.

Vị trí actor/capsule center khác chân. Với capsule đứng thẳng, chân = tâm - Up * capsule half height đã scale; công thức này giả định hướng capsule thẳng đứng. Không mặc định actor origin là chân. Hướng thân, hướng di chuyển và hướng ngắm là ba dữ liệu riêng, không tự suy ra chúng bằng nhau.

Thời gian theo world/session (giây), không theo đồng hồ hệ điều hành hoặc số frame. Now/Start/End phải cùng world/session và cùng miền clock. Khoảng hiệu lực [start,end): đúng start còn hiệu lực, đúng end hết hiệu lực; start >= end luôn false. Khi thay world/session phải bỏ deadline cũ và tạo lại theo clock mới. Helper không quản lý lifecycle: caller chịu trách nhiệm không tái sử dụng deadline qua session. U00 không tạo clock subsystem/network sync.

Helper thuần trong namespace AnimeMMORPG::Foundation: MetersToCentimeters(double), CentimetersToMeters(double), IsWithinHalfOpenInterval(Now, Start, End). Không trạng thái global, không đọc clock. Đầu vào theo hợp đồng là số double hữu hạn; không cam kết domain vô hạn/NaN. Tests truyền thời gian trực tiếp. Round-trip kiểm các giá trị đã liệt kê với sai số tuyệt đối <= 1e-9; hướng/vector qua FTransform giữ tolerance 1e-9; FRotator::RotateVector dùng tolerance thành phần 1e-6 vì đường SIMD ma trận dùng DEG_TO_RAD kiểu float. Test ghi vector thực; ngưỡng này vẫn phân biệt rõ sai trục/dấu. Không áp epsilon vào biên [start,end).

Automation prefix AnimeMMORPG.U00, bốn tests Units/Axes/HalfOpenInterval/CallOrder; chỉ biên dịch dưới WITH_DEV_AUTOMATION_TESTS trong runtime module hiện có. Không thêm module/plugin, map hay gameplay. CallOrder kiểm helper stateless theo thứ tự đảo và xen kẽ; không phụ thuộc thứ tự framework chạy test.
