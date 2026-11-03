# U01 — Hợp đồng kỹ thuật

Nguồn: Description (luật không sửa), FOUNDATION U00 và giao việc U01 của người dùng. Nền main đã đối chiếu local/remote: `f10e9252767f134e8e6d5698c326a2b045b8f1d3`. A chỉ chốt tài liệu/khả thi; mọi hành vi B–G dưới đây là yêu cầu chưa triển khai, chưa PASS.

## Phạm vi và chủ sở hữu

Kỹ thuật trước: Manny Simple, clip có sẵn, kiếm hình khối; camera/chuột ưu tiên B. Art model/rig/kiếm anime DEFERRED, không coi mannequin là art sản phẩm. Không damage/combo/né/đỡ/kỹ năng/AI/tài khoản/matchmaking/thế giới đông người; G và reset chỉ là fixture.

Giữ runtime module AnimeMMORPG; C++ Character mới kế thừa ACharacter, custom CharacterMovement giữ luật tốc độ/nhảy/dốc và saved move/custom movement data. PlayerController giữ camera input, trạng thái local menu/focus/UI; Enhanced Input nhận lệnh. Blueprint gán mesh/AnimBP/input/widget. Nội dung mới dưới `/Game/AnimeMMORPG/U01`; hai lab gán cấu hình riêng, Boot giữ UI-only. Không sửa variant/template hoặc thêm GAS/framework locomotion/module mạng.

AnimBP chỉ đọc velocity, acceleration, grounded/falling và trạng thái nhảy từ movement thực. Capsule do movement điều khiển; clip in-place, không áp root motion lên actor. Bản clip/AnimBP/BlendSpace riêng; skeleton riêng U01 nếu sửa socket. Kiếm gắn tay phải, không collision/damage. Xem ASSETS.md về root motion nguồn.

## Input và trạng thái

| Lệnh | Mặc định | Điều kiện |
|---|---|---|
| Tiến/lùi/trái/phải | W/S/A/D | Vector theo yaw camera, bỏ pitch; normalize chéo |
| Look | Mouse delta | Xoay trực tiếp, không giữ nút; không nhân thêm DeltaSeconds |
| Jump | Space | Một cạnh nhấn; giữ không tăng độ cao/nhảy lại |
| Sprint | Ctrl giữ | Có hướng hợp lệ và motor được phép |
| Đổi vai | V | Giữ yaw/pitch ngắm |
| Menu | Escape | Chỉ mở; không tự Resume |
| Tương tác | G | Dành sẵn, chỉ fixture U01 |
| Reserved | Shift, LMB/RMB, Q/E/R/F/1–4/X/Tab/I/K/M | Chưa gameplay; không cho rebind chiếm |

Camera và Escape cố định. Rebind từng hướng, Jump/Sprint/Shoulder/Interact, mỗi binding một phím/nút chuột, không wheel/tổ hợp. Không tự đổi chỗ. Escape khi nhận phím hủy pending trước xử lý mở menu.

Hai trục trạng thái độc lập, không action framework: local control `Playing / Menu / AwaitingResume`; motor lock gồm lý do `Interacting / Defeated`. Khóa còn hiệu lực nếu bất kỳ lý do nào còn. Camera/menu chỉ local, không tạo UI/settings trên dedicated server.

| Sự kiện | Kết quả |
|---|---|
| Vào lab được focus | Playing, game input, cursor ẩn, capture chuột |
| Escape | Menu, nhả capture/cursor hiện; không pause world |
| Mất focus ở bất kỳ trạng thái nào | AwaitingResume, nhả chuột, khóa motor; trở lại vẫn chờ |
| Resume có focus | Playing, capture lại; motor lock khác vẫn giữ |
| Interacting/Defeated | Ngừng điều khiển ngang/nhảy, camera/menu vẫn dùng, gravity tiếp tục |

Mọi khóa xóa move intent, sprint intent, jump buffer/coyote pending; ngừng điều khiển ngang, giữ thành phần gravity. Mỗi phím đang giữ vào khóa được đánh dấu phải nhả; kể cả press lúc đang khóa không được phát lại khi Resume. Re-arm từng phím sau quan sát release vật lý; focus return không được coi là release. Không dùng Enhanced Input flush đơn thuần thay cơ chế này. Camera delta cũ bị bỏ. Khóa/đổi world xóa deadline, không đem input/session cũ sang world mới. Log transition, focus/capture, khóa/re-arm và lý do reject; tránh log delta từng frame ở sản phẩm.

## Camera

| Thông số trình bày ban đầu | Giá trị |
|---|---|
| Khoảng cách / FOV | 350 cm / 90° |
| Pivot / vai | Tâm capsule + Z70 cm; Y ±45 cm |
| Pitch | −70° đến +60° |
| Sensitivity | 1,0; UI 0,1–3,0; không đảo Y |
| Sweep | Sphere bán kính 12 cm, môi trường; ignore pawn sở hữu |
| Đổi vai | Khoảng 0,15 s; sweep liên tục |
| Ẩn gần | Owner-only mesh + kiếm khi distance pivot <80 cm; hiện lại >100 cm; giữ trạng thái trong dải giữa |

Sweep từ pivot tới vị trí camera dự kiến, thu vào ngay khi cản, trở ra mượt khi thông; không lerp xuyên vật cản, xử lý initial overlap/không gian hẹp. Đổi vai không đổi control yaw/pitch. Đứng yên look không quay thân; khi di chuyển thân theo hướng di chuyển, camera không tự kéo sau lưng. Aim ray lấy tâm camera (origin/direction world), tách khỏi thân và movement; không là quyền sửa actor khác. Thông số smoothing cụ thể được hiệu chỉnh B, đo thời gian và clearance, không đổi luật Description. Không dùng RPC mỗi frame cho camera.

## Motor và thời gian

| Luật | Hợp đồng |
|---|---|
| Walk/sprint | 500/700 cm/s; server chọn tốc độ từ trạng thái hợp lệ, client không gửi tốc độ tùy ý |
| Jump | JumpMaxCount=1, mục tiêu apex 120 cm so chân khi cất cánh; giữ Space không variable-height |
| Coyote | Chỉ sau mất nền ngoài ý muốn; `[LeftGround,LeftGround+0.10)`; không sau nhảy chủ động |
| Buffer | Cạnh nhấn sống `[Pressed,Pressed+0.10)`; consume một lần khi tiếp đất hợp lệ |
| Biên | 0,099 s hợp lệ, 0,100 s hết; không epsilon nới cửa sổ |
| Gravity | Lấy gia tốc trọng lực thực movement; seed Vz=sqrt(2*abs(GravityZ)*120), hiệu chỉnh bằng đo tích phân |
| Dốc / bậc fixture | Đi được 45°; >45° không leo bằng đi bộ, trượt; step height ban đầu 45 cm |

Clock world/session mô phỏng, server giữ quyền thời gian mạng; không wall clock/số frame. Test luật dùng clock điều khiển được, đo vật lý dùng sample time thực. Coyote/buffer không chồng thành double jump; nhảy chủ động tiêu quyền, chạm trần không reset quyền. Landing reset quyền cho cạnh mới; nhấn giữ qua landing không sinh cạnh. Khóa giữa cửa sổ xóa buffer. Frame đi qua deadline phải xét thời điểm sự kiện, không tùy callback order; deadline đúng end hết hiệu lực.

CharacterMovement replication có sẵn làm nền; saved move/custom movement data mang sprint/jump intent và dữ liệu thời điểm cần replay, không teleport thay replication, không movement RPC mỗi frame riêng. Server kiểm hướng, lock, grounded/coyote/buffer/jump count và giới hạn tốc độ; reconcile từ chối sai. Thiết kế packet/quantization chi tiết chốt ở F với tests replay/validation, không cho client tự xác nhận clock.

## Settings local và UI

USaveGame nhỏ versioned: bindings, sensitivity, invert Y, default shoulder; không account/progression. Mapping thuộc LocalPlayer, không mutate IMC dùng chung giữa client. Menu: Resume, Điều khiển, Về Boot, Thoát. Overlay chỉ thông tin cần thiết; Về Boot trong menu, không giữ cursor hiện như U00.

Sensitivity áp ngay khi kéo; lưu khi release slider/Save/Resume. Invert Y/default shoulder/restore defaults áp ngay. Thiếu file dùng defaults; trường hợp lỗi giữ phần hợp lệ và báo phần phục hồi, không tự ghi đè chỉ do load. Validate version/type/range/finite/unknown key/reserved/duplicate; phục hồi binding xung đột về default theo thứ tự action cố định W/S/A/D/Jump/Sprint/Shoulder/Interact. Khi binding hợp lệ chiếm default của action lỗi, đánh dấu nhóm xung đột liên quan và phục hồi nhóm để không tạo trùng mới; UI liệt kê mọi mục phục hồi. Không giả báo save thành công: chỉ success khi API lưu báo thành công; giữ dirty và thông báo nếu fail. File version chưa hỗ trợ phải báo rõ, không tự overwrite khi load.

## Hợp đồng số đo và bằng chứng

Mỗi sample bắt buộc: run ID, source SHA, timestamp UTC để tra log, PID, project, executable/binary hash, map package, world path/type/context ID, net mode, world/session time, pawn path/ID, controller/owner, local role/remote role và locally controlled. Vị trí ghi rõ capsule center/feet world cm; velocity cm/s; acceleration cm/s². Không dùng tên actor đơn lẻ làm ID qua process/session; liên kết mạng bằng server pawn ID/NetGUID + connection, kèm path local.

Collector tương lai B/C/F lấy world từ pawn/controller đang kiểm tra (`GetWorld()`), xác minh WorldType Game/PIE và `GetNetMode()` thực, controller possession/owner/IsLocalController và GameInstance local-player count. Loại Editor/EditorPreview/không owner hoặc nhiều world mơ hồ; trả lỗi thiếu world/pawn thay vì fallback Editor world. Dedicated sample phải chứng minh NM_DedicatedServer và local-player count=0. Client sample phải chứng minh NM_Client. Server và client có PID riêng; NetMode Standalone của PIE không thay dedicated.

Camera sample từ local PlayerCameraManager cuối frame: pivot, desired/resolved camera transform, aim ray, sweep hit/distance/clearance, side transition, owner visibility, yaw/pitch/capture/focus/menu state. Motor sample lấy CharacterMovement thực: position/velocity, movement mode, grounded, gravity, jump count/timestamps, sprint accepted/reject reason; animation sample kèm state/velocity/root displacement. U00 TestRunner hiện không expose pawn metrics; A chỉ chốt schema, chưa có collector. Không tính actor Editor hoặc ảnh là phép đo gameplay.

Mỗi đợt báo source SHA/file/asset, engine/toolchain, phương pháp (Automation/tool input thật/người dùng), pass/fail/not-run, số đo/log/video, warnings và giới hạn. B camera cần video thao tác/input thật; clock fixture không thay chuột/focus/UI. Không có tool packaged input thì chuẩn bị build xong và checklist thủ công gộp. Header/reflection mới cần full build clone và mốc restart Editor gốc gom sau chuẩn bị; không hứa Live Coding patch layout.
