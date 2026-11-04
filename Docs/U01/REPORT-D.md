# U01-D — Hoàn thiện tư thế mang kiếm một tay

**ĐÃ NGHIỆM THU U01-D kỹ thuật/blockout theo xác nhận người dùng tại `1e46f710cec8fbb0dd9de2e6be7d35519bf45d83`.** Checklist PASS theo xác nhận đó; carry là tư thế mang kiếm tạm phục vụ U01, được thay/tinh chỉnh theo nhân vật, vũ khí và bộ động tác chính thức sau này. **Art anime và animation chiến đấu DEFERRED, chưa nghiệm thu trong D.** Nguồn runtime/asset/build/tests/package giữ nguyên **`6ef6ec3125ed455e3963a687df481eb138629df6`**; giữ lịch sử kiểm chứng phía dưới. Người dùng cho phép commit/push hồ sơ, fast-forward D vào main rồi triển khai riêng E; không cần đóng Editor gốc để khép D. D bắt đầu từ main868df83, lần carry tiếp tục từ4c8de13.

Người dùng đã xác nhận **cách nắm kiếm ổn**, nhưng chỉ rõ lỗi còn lại là quỹ đạo vai/cánh tay từ clip tay không khiến kiếm xuyên thân. Lần này sửa riêng pose mang kiếm; không coi việc socket khớp là bằng chứng hết xuyên người. Báo cáo/checklist trước giữ nguyên trong [REPORT-D-4c8-HISTORY](REPORT-D-4c8-HISTORY.md), [checklist4c8](D-CHECKLIST-4c8-HISTORY.md). Lịch sử941 và bộ bằng chứng D-Revision vẫn giữ.

## Thay đổi và phạm vi giữ nguyên

- Thêm **PA_U01_RightCarry / RightCarry** riêng dưới `/Game/AnimeMMORPG/U01/Animation`. AnimBP: selector idle/locomotion/jump/fall/land → lớp carry nhánh **clavicle_r** → lớp grip ngón tay đã được chấp nhận → output. Lớp carry blend per bone với rotation trong mesh space, weight1; giữ tư thế cánh tay phải ổn định thay vì lấy độ vung tay không. Vẫn còn chuyển động tịnh tiến nhỏ của vai theo spine/breath/bob. Đây là pose blockout chủ ý khá chắc tay, chưa phải animation mang vũ khí đã polish.
- Quan sát mesh trước sửa: component space bên phải là **−X**, hướng trước **+Y**. Shoulder nguồn khoảng(-19,−2,6,143,6)cm; wrist clip chạy quét vào X≈−8,4cm. Author pose đặt wrist **(-42,12,112)cm**, dùng elbow pole **(-55,−15,125)cm**. Giải hình học hai đoạn tay ở **Editor authoring**, lưu thành PoseAsset; không có runtime IK, constraint hoặc framework mới. Elbow tạo ra≈(-42,338,−8,635,129,797)cm; shoulder delta P/Y/R=(0,0,0). Trục lưỡi mục tiêu trong mesh space≈(-0,25;0,65;0,72), trục +X hand tham chiếu(0,0,−1), wrist component rotation≈P−44,046/Y111,038/R0 độ. [Cấu hình](../../Scripts/U01/DCarry.json) ghi rõ cơ sở số đo và giá trị authoring.
- **Giữ nguyên byte skeleton/socket SK_U01 và PA_U01_RightGrip** đã xác nhận; cả mesh, sáu clip và BlendSpace nguồn D cũng không đổi hash. Không chỉnh socket/ngón để bù quỹ đạo. Grip là lớp cuối; tests A/B xác nhận lớp grip chỉ tác động ngón, carry không tác động các xương ngoài nhánh vai phải. Các metacarpal/twist thuộc nhánh vai phải nhận pose carry, sau đó pose ngón được áp lại.
- Git diff từ4c8 tới6ef xác nhận không đổi Character/motor/controller/input, luật jump/coyote/buffer, map hay template. Lớp carry giữ nguyên root/spine/chân/tay trái trong phép so pose cùng thời điểm. Không sửa physics/collision để đẩy kiếm ra: collision/overlap/physics/nav/damage kiếm vẫn tắt. Không có animation tấn công, art anime, plugin/module runtime/IK toàn thân mới.

## Build, tests và số đo

UE5.8.4 CL58902052, MSVC14.51.36260/toolset14.51.36231, SDK10.0.26100.0. Clone `Artifacts/U01/D/Source` được fast-forward tới SHA đã push; full build từ đĩa tại `Carry/Build-20261104-215608-771-521adf60`, Editor và Game exit0. Không dùng Live Coding patch. Editor gốc tiếp tục mở.

Cold Editor clone **PID20304**, MCP TestRunner `Carry/MCPTests-20261104-215718`: **17/17 PASS**, đọc log mới tới queue empty17. U00.Foundation4/4, B2/2, C5/5, D6/6: AnimatedMotor, AssetPolicy, TransitionsAndAttachment, LandingTransitions, GripIsolationAndAttachment và **CarryTrajectory** mới. Danh sách/kết quả nguyên dòng và records tại [RESULTS.json](Evidence/D-Carry/RESULTS.json).

CarryTrajectory chạy trên **pawn Blueprint/mesh/AnimBP thật trong Game physics world**, controlled input do AIController sở hữu. Mỗi record có sourceSHA/UTC/PID/world/context/type/netMode/pawn/controller/owner/role/mesh/AnimBP. Không lấy Editor preview làm số đo gameplay. Test lấy **1.270 mẫu ở dt1/120s** qua idle → walk → sprint → jump/fall → moving land, đổi bốn hướng, dừng → stationary jump/land. Kiểm ngoài nhánh vai phải không đổi pose ở cùng thời điểm, chân vẫn có chu kỳ thực, attachment và collision giữ nguyên. Các assert yêu cầu tay phải vung như clip tay không đã được bỏ vì trái mục tiêu carry; assert chân, root và toàn bộ tests motor/landing vẫn giữ.

| Phép đo | Kết quả |
|---|---:|
| Đi10s sau tăng tốc | 5000,000260770cm |
| Sprint10s sau tăng tốc | 7000,000365078cm |
| Apex dt1/30;1/60;1/120s | 119,987106204;119,987106189;119,994960187cm |
| Gravity | −980cm/s² |
| Root drift locomotion | 0cm |
| Khoảng hở lưỡi/proxy thân-chân nhỏ nhất | **21,742434cm** |
| Bước đầu lưỡi lớn nhất giữa hai mẫu, mesh component space | 4,879416cm |
| Sai lệch attachment vị trí/hướng | 0cm /0 độ |

Proxy là các capsule theo xương pelvis/spine/neck/head và hai đùi; đoạn lưỡi có bán kính bao3,25cm. Đây là **fixture đo quỹ đạo**, không bật collision kiếm, không tuyên bố kiểm từng tam giác mesh hoặc mọi tư thế/camera có thể có. Khoảng hở dương là bằng chứng bổ trợ, còn hình ảnh thực xem trên video/package. Bước mô phỏng1/120s không là FPS render.

## Windows và bằng chứng chuyển động

Package: `Artifacts/U01/D/Carry/Package-20261104-215800-485-e6e047e7/Archive/Windows`, BuildCookRun exit0, cook summary0 error/0 warning, giữ đủ48file. [Hash package](Evidence/D-Carry/PACKAGE.csv). Smoke `Carry/SmokeB-20261104-220617`: **Boot/CharacterCombatLab/NetworkLab3/3 PASS**, lab PID21488/15188; NetworkLab chạy standalone, không phải nghiệm thu F.

- [Video chuyển tiếp/đổi hướng24s](Evidence/D-Carry/Transitions.mp4): W, Ctrl, nhảy khi sprint, W→D→S→W và nhảy lại, dừng/nhảy đứng yên; idle/đi/sprint/jump/fall/land có trong trace.
- [Video góc trước15s](Evidence/D-Carry/Front.mp4): camera yaw≈179,97° được log xác nhận, S để nhân vật đi/sprint về phía camera dọc đường thử, nhảy/đáp và D/A đổi hướng. Quan sát quỹ đạo lưỡi tách khỏi ngực; [lúc nhảy](Evidence/D-Carry/Front-4.9s.png), [sau đáp](Evidence/D-Carry/Front-5.6s.png), [đổi hướng](Evidence/D-Carry/Front-6.5s.png).
- [Preview trước](Evidence/D-Carry/Preview/Before)/[sau](Evidence/D-Carry/Preview/After) là **Editor pose diagnostic**, không gameplay/FPS: full body idle/run/đầu landing từ bốn hướng, dữ liệu arm component space/refpose. Có đèn fill tạm của công cụ chụp; không đổi renderer/map sản phẩm. Closeup theo trục hand sau xoay cổ tay có thể đi vào forearm, đã loại khỏi hồ sơ mới; không dùng ảnh bị che để xác nhận grip.

Video cuối dùng **input Windows SendInput**, kiểm đúng exe/hash/PID11332/HWND/foreground và runtime trace của pawn local sở hữu trong Game world. Có xác nhận đi500/sprint700cm/s, đủ pose indices0–4, không landing pose khi speed>3. Events/mapping camera, samples và metadata gắn source6ef trong RESULTS.json. AI đã xem các frame chuyển động/nhảy/đáp/đổi hướng trích từ video và chạy test quỹ đạo toàn chuỗi; chưa thay xác nhận cảm giác của người review.

| Capture | Hình đọc mới và ảnh khác nhau/giây | Khoảng frame lớn nhất | Frame lặp |
|---|---:|---:|---:|
| Transitions | 23,176 | 148ms | 163/720 |
| Front | 24,377 | 155ms | 84/450 |

Encoder30FPS không là capture30FPS hoặc game30FPS. Không dùng video này để khẳng định blend0,10s mượt; LandingTransitions kiểm compiled times/deadline/weights, cảm giác và độ tự nhiên của pose mang kiếm chờ review trên package. Capture tool vẫn từ chối khi mất focus, kiểm ảnh khác nhau và movement từ log. Hai lượt Transitions/Transitions2 từ chối foreground trước input; sau khi phối hợp input queue lúc startup thì Transitions3 hoàn tất. Trong lượt ghi không giành lại focus. Front đầu camera chỉ12,6° bị loại làm bằng chứng góc trước; FrontVerified dùng scale chuột đo được để đạt179,97°. Không sửa độ nhạy game để làm bằng chứng. Probe W trong menu nhận đúng, không cần đổi bộ gõ ở các lượt bàn giao cuối; trạng thái input method được giữ.

## Bàn giao và giới hạn

Chạy **Artifacts/U01/D/Play-D.cmd**, vào CharacterCombatLab của package6ef; logs ở `Artifacts/U01/D/Carry/Review`. [Checklist ngắn](D-MANUAL-CHECKLIST.md) tập trung vào tay/kiếm trong chuyển tiếp và đổi hướng; cách nắm đã được người dùng xác nhận, không tự coi D tổng thể đạt. Hash ảnh/video/asset, lịch sử và identity tại [MANIFEST.json](Evidence/D-Carry/MANIFEST.json), [EVIDENCE.csv](Evidence/D-Carry/EVIDENCE.csv). Lịch sử lỗi/kiểm chứng cũ giữ nguyên.

Compiler mới hơn preferred14.50 và các C4996 engine/C4305 của harness cũ còn trong log; không đổi engine/compiler/plugin hoặc bỏ tests. Optional profiler/audio diagnostics của smoke được phân loại theo validator B; Python/toolset init ở đường Editor -game/-server từ A vẫn phải xử lý ở F/tích hợp. Không chạy mạng F/Server packaging hoặc FPS/lifecycle10phút của G trong lần này.

MCP marker cuối UTC15:06:26.814 xác nhận **Editor gốc PID21452**, đúng project gốc, Boot0actor. AI không đóng/restart Editor gốc; native D trong đó **chưa xác nhận nạp**. Full build clone đã nạp lạnh các lớp mới; muốn dùng reflection/header mới trong Editor gốc cần mốc full build/restart riêng. Config/token local ngoài Git.

Tại bàn giao1e46f71, D chưa nghiệm thu/merge và E chưa chạy; đây là lịch sử, đã được cập nhật bằng xác nhận người dùng ở đầu báo cáo. Chỉ nghiệm thu kỹ thuật/blockout: carry tạm cầm đúng tay, tránh xuyên thân rõ rệt và hoạt động ổn khi di chuyển/nhảy. Art anime và animation chiến đấu **DEFERRED**, sẽ thay/tinh chỉnh carry sau; không coi mannequin hoặc carry hiện tại là nghiệm thu hình ảnh sản phẩm.
