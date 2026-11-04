# ANIMEMMORPG — ROADMAP UNREAL ENGINE

## 1. Mục tiêu và hiện trạng

Project chính: `D:\Data\AnimeMMORPG`; engine mục tiêu Unreal Engine 5.8.4. Thiết kế tại [Description.md](Description.md), lịch sử và lưu ý chuyển engine tại [UNITY_REFERENCE.md](UNITY_REFERENCE.md).

Baseline khảo sát 2026-11-02: project Third Person C++ có ba variant Combat/Platforming/SideScrolling; EngineAssociation ghi 5.8. Lịch sử khảo sát lưu tại [REPORT-A](U00/REPORT-A.md) và [ENVIRONMENT](U00/ENVIRONMENT.md). Hiện U00 đã được người dùng nghiệm thu sau lượt F: clone GitHub/LFS, compile Editor/Game, 4/4 Automation tests trên binary đĩa, tool registration sau khởi động mới, package Windows và kiểm tra thủ công packaged game đủ 5 vòng, Thoát/mở lại đều đạt. Nguồn build `9d6a81b24c9dbf75ad8fcf4c47de78c72f95eb80`; UE 5.8.4 CL 58902052; UBT chọn MSVC 14.51.36260, SDK 10.0.26100.0. Xem [REPORT-F](U00/REPORT-F.md), [manifest](U00/F-MANIFEST.json) và [hash artifact](U00/F-ARTIFACTS.csv). Không kế thừa nghiệm thu Unity; U01-A đã nghiệm thu tại 4216ff874872f5d7112cc792b52d008937441f7c; B đã nghiệm thu trên package tại2e0e89f theo xác nhận người dùng; Editor gốc chưa xác nhận nạp code mới.

Bản thử kín: Kiếm Vũ và Cơ Xạ, một trung tâm nhỏ, một vùng, dungeon bốn người, PvP 1v1 không xếp hạng, tiến trình lưu được cấp 1–10. Đích đầy đủ: sáu nghề, cấp 50, raid tám người, phân khu 40 người, PvP 1v1/3v3.

Mỗi đợt bàn giao có commit, test, nguồn/build, bằng chứng và giới hạn; dừng để giám sát trước đợt kế tiếp. Không tự thêm tính năng, đổi cân bằng, mua asset hoặc đăng ký dịch vụ. C++ giữ luật; Blueprint cấu hình asset/UI/trình bày. Animation không xác nhận damage. Chỉ qua cổng khi đạt hoặc có lý do chấp nhận lỗi còn lại. Không hứa lịch phát hành trước khi đo năng lực thực tế.

## 2. Các giai đoạn

### U00 — Công cụ và nền project

- [x] U00.01 Xác nhận Editor 5.8.4, toolchain C++, compile và Windows packaging. Bằng chứng: [C](U00/REPORT-C.md), [F](U00/REPORT-F.md).
- [x] U00.02 Gọi tool/MCP đọc project/map/actor/log thật; phân biệt cấu hình, kết nối và gọi thành công. Bằng chứng: [A](U00/REPORT-A.md), [D](U00/REPORT-D.md), [F: đăng ký sau khởi động mới](U00/REPORT-F.md).
- [x] U00.03 Git/LFS/ignore, quyền phân phối asset, cấu hình máy và khôi phục. Bằng chứng: [B](U00/REPORT-B.md), [kiểm kê asset](U00/ASSET_REGISTER.csv), [F: clone và hash](U00/REPORT-F.md). Phân loại/quyền giữ theo nguồn và phạm vi đã ghi; không áp giấy phép chung lên asset Epic.
- [x] U00.04 Khảo sát template hiện có; tổ chức C++/Blueprint/data/UI/test, không xóa source tùy tiện. Bằng chứng: [A](U00/REPORT-A.md), [D](U00/REPORT-D.md), [E](U00/REPORT-E.md).
- [x] U00.05 Map khởi động, sân nhân vật/combat, map thử mạng và menu chuyển map. Bằng chứng: [E](U00/REPORT-E.md), [F: packaged game, xác nhận thủ công người dùng](U00/REPORT-F.md).
- [x] U00.06 Chốt đơn vị/hướng/clock; test tự động và build Windows tối thiểu. Bằng chứng: [hợp đồng Foundation](U00/FOUNDATION.md), [D](U00/REPORT-D.md), [F: 4/4 tests và build](U00/REPORT-F.md).

U00 đã nghiệm thu theo xác nhận người dùng. Kết quả packaged UI là xác nhận thủ công, không phải AI điều khiển input. Giữ lịch sử lỗi/warning trong báo cáo; camera template cần giữ chuột là giới hạn U00, không nghiệm thu điều khiển U01, hiệu năng U04 hoặc mạng U05.

Phạm vi U00: giữ một runtime module hiện có; chỉ tạo nền tối thiểu, không triển khai điều khiển U01, combat, backend hoặc framework dự phòng. Giữ template làm baseline; chỉ xóa/di chuyển sau kiểm tra tham chiếu và có nhiệm vụ riêng.

Thứ tự các đợt U00 và bằng chứng:

| Đợt | Công việc | Nghiệm thu và bằng chứng |
| --- | --- | --- |
| A | Ghi project/engine/toolchain thực tế; xác minh active project và các phép đọc MCP; kiểm kê nguồn gốc asset | Báo cáo môi trường, kết quả gọi thật, danh mục asset và quyền phân phối còn thiếu; không coi tên plugin là kết nối |
| B | Git/LFS trước lần add đầu, ignore, baseline và khôi phục | Commit giữ Source/Config/Content/Docs; `.uasset`/`.umap` qua LFS; cache không tracked; phục hồi thử nguồn và LFS từ bản sao |
| C | Generate project files; compile Editor và Game Win64 Development bằng engine đã khóa | Exit code thành công, log compiler/SDK thực chọn, mở không thiếu module; chưa dựa vào Live Coding |
| D | Tổ chức phần mới trong Source/AnimeMMORPG theo Foundation/Bootstrap/Tests và Content/AnimeMMORPG theo Maps/Blueprints/UI/Data/Tests; chỉ tạo thư mục/asset thực dùng | Quy ước đơn vị/hướng/clock và Automation tests chuyển đơn vị, hướng, biên deadline đạt; không chuyển hàng loạt template |
| E | L_Boot, L_CharacterCombatLab, L_NetworkLab; menu chọn sân/quay lại; cấu hình startup và danh sách cook | Boot vào từng sân và quay lại đúng map/player; sân có nền, ánh sáng, PlayerStart, thước 1 m/10 m; map mạng có ít nhất hai điểm spawn; log và ảnh/video |
| F | Script compile/test/package có tham số project/output; package Windows và tái lập từ checkout sạch có LFS | Executable ngoài Editor vào được hai sân và thoát; test thực chạy, không chấp nhận 0 test; log, report, manifest commit/engine/toolchain và SHA-256 build |

Ignore `.vs`, Binaries, Intermediate, DerivedDataCache, Saved, solution sinh tự động và output package. Giữ `__ExternalActors__`, `__ExternalObjects__` và tài nguyên Build viết tay. Không commit bí mật/cấu hình cá nhân; bằng chứng cần giữ phải đưa ra khỏi thư mục bị ignore. Chọn nơi sao lưu/remote với chủ project trước khi sử dụng dịch vụ.

Quản lý asset: ghi nguồn/giấy phép; quy ước tên và đường dẫn; kiểm tra Blueprint compile/missing reference. Đổi tên/di chuyển qua Editor và kiểm tra redirector. Cook rõ các map cần dùng, kiểm tra asset trong package; nội dung Editor/test chỉ được đóng gói khi có mục đích thử được ghi rõ. Không dựng hệ thống quản lý asset tổng quát tại U00.

Cổng: mở, compile, test và packaged Windows vào được sân thử từ nguồn quản lý phiên bản. Tên plugin không chứng minh kết nối.

### U01 — Điều khiển, camera, animation và mạng cơ bản (kỹ thuật)

Phụ thuộc: U00.

U01-A bắt đầu từ main U00 `f10e9252767f134e8e6d5698c326a2b045b8f1d3`. Quyết định người dùng: kỹ thuật trước bằng mannequin/clip hiện có và kiếm hình khối; camera/chuột là ưu tiên chơi thử đầu tiên, di chuột xoay ngay không giữ nút. Nghiệm thu kỹ thuật tách khỏi art sản phẩm. Model/rig/kiếm anime **DEFERRED**, chưa hoàn thành và không chặn cổng kỹ thuật. Không sửa luật gameplay trong Description. Hợp đồng, asset và ma trận tại [Docs/U01](U01/CONTRACTS.md), [báo cáo A](U01/REPORT-A.md).

Mỗi đợt riêng trên `u01/<tên-đợt>` từ main đã nghiệm thu; commit/push, bàn giao rồi dừng, không tự merge hoặc chuyển đợt: A hợp đồng/khả thi → B camera/chuột/menu tối thiểu → C motor/sân đo → D animation/kiếm thử → E rebind/settings/khóa → F server riêng/hai client → G Windows tích hợp. B–F có smoke packaged phần mới; G full build/Automation/package từ clone SHA đã push, giữ Editor gốc mở.

B đã triển khai trên `u01/b-camera`: [báo cáo](U01/REPORT-B.md), [checklist chơi thử](U01/B-MANUAL-CHECKLIST.md). Full build, 6/6 Automation và smoke Windows ba map đạt từ source `b6cf1ebfdfd34a4dbfcdb52c1507401a3096ef00`; checklist package **PASS theo xác nhận người dùng tại2e0e89f**. Người dùng cho phép khép B/fast-forward main và bắt đầu riêng C; chưa nghiệm thu U01 tổng hợp. Native class mới chưa được coi là đã nạp tái lập trong Editor gốc qua patch; bản package độc lập dùng để chơi thử.

C triển khai trên `u01/c-motor` từ main `72ad2be02364ace08588bb5e78aa3a491b3f2776`: [báo cáo](U01/REPORT-C.md), [checklist C](U01/C-MANUAL-CHECKLIST.md). Source `a374081a6c681662407c9024e36168a41c1e6111` full build, 11/11 tests và smoke Windows3/3 đạt; motor/slope đo bằng input fixture trong Game world. Checklist package C PASS theo xác nhận người dùng tại0cba933; đã cho phép khép hồ sơ/fast-forward main và triển khai riêng D. Editor gốc chưa xác nhận nạp native code mới. Các bước mô phỏng1/30–1/120s không là FPS render đã đo.

- [ ] U01.01 Chốt mannequin/clip nguồn theo register U00 cho phép thử kỹ thuật. Model/rig/kiếm anime hợp giấy phép: **DEFERRED**, nghiệm thu art riêng.
- [ ] U01.02 Character/CharacterMovement và Enhanced Input: đi 5 m/s, sprint 7 m/s, nhảy 1,2 m, dốc 45°, đi chéo không nhanh hơn.
- [ ] U01.03 Camera tự do/đổi vai/tránh vật cản, tách hướng thân/di chuyển/ngắm.
- [ ] U01.04 Skeleton/retarget/socket kiếm, Animation Blueprint idle/đi/chạy/nhảy/rơi/tiếp đất; motor giữ quyền dịch chuyển.
- [ ] U01.05 Menu/focus/Resume, rebind/settings; camera dùng được khi khóa hành động, xóa lệnh cũ.
- [ ] U01.06 Sân dốc/bậc/trần/vực/hành lang/vật cản có số đo; Windows chơi được với mannequin kỹ thuật.
- [ ] U01.07 Chốt chính sách root motion cho bộ clip đầu: CharacterMovement giữ quyền dịch chuyển cơ bản, AnimBP trình bày; không để root motion và code cùng dịch chuyển một hành động. Ghi rõ ngoại lệ nếu có và kiểm thử displacement thực.
- [ ] U01.08 Thử kỹ thuật bằng UnrealEditor.exe -server và hai client riêng localhost ngay từ A; phân biệt với target Server đóng gói, không mặc định installed engine hỗ trợ. Nếu không chạy được, bàn giao lỗi và phương án engine, không tự tải source/nâng engine. F kiểm spawn/possess/ownership, server ghi nhận đi/sprint/nhảy, hai client thấy di chuyển/animation, reconnect và settings độc lập; log từng PID/world/net mode/pawn. Chưa prediction combat hoặc mạng xấu U05.

Cổng kỹ thuật: Windows điều khiển được, chuột xoay ngay, menu/focus/Resume/settings đúng; motor và animation đo theo Description, không trượt chân nghiêm trọng. U00 Foundation 4/4 và ma trận U01 thực chạy, có source SHA/log/video; server riêng/hai client đạt trước U02. Art anime vẫn DEFERRED, mannequin không là nghiệm thu hình ảnh sản phẩm. Xem [ma trận](U01/TEST-MATRIX.md).

### U02 — Một đòn đánh hoàn chỉnh

Phụ thuộc: U01, gồm thử server/hai client. Thực hiện U02.00 trước U02.01–05, sau đó U02.06.

- [ ] U02.00 Bàn giao hợp đồng một action: chủ sở hữu trạng thái/quyền sửa, clock/deadline, thời gian nhận lệnh và xử lý, ID chủ thể/action/event ổn định, thứ tự resolve theo Description. Chốt xử lý frame đi qua cả đầu/cuối active và nguồn dữ liệu animation. Đánh giá giải pháp action tối thiểu; chỉ thử framework/GAS nếu có yêu cầu cụ thể và phép so sánh, không mặc định cài thêm. Test bằng clock điều khiển được trước khi nhân rộng.

- [ ] U02.01 Action instance/deadline/phase/quyền hành động, đòn 1 theo Description.
- [ ] U02.02 Montage theo phase, không dùng notify làm nguồn quyết định hit.
- [ ] U02.03 Hurtbox/query/sweep/tường/chống trùng/thứ tự resolve ổn định.
- [ ] U02.04 HP/damage/crit/khiên/death, hình nộm/reset, HUD/log tối thiểu.
- [ ] U02.05 Test biên active, hủy startup, nhiều collider, chết đồng thời; Windows một đòn chơi được.
- [ ] U02.06 Một đòn qua server riêng/hai client: server nhận và kiểm tra lệnh, quyết định hit/HP; client hiển thị kết quả xác nhận. Thử đánh hụt/trúng/tường và gửi lặp cùng action ID; không nhân hit, hai client đồng thuận HP. Bàn giao log có ID lệnh/action/hit, lý do từ chối và video; chưa nghiệm thu bù trễ hoặc prediction đầy đủ.

U02.03 phải bàn giao collision matrix/profile trong Config và fixture: môi trường/thân nhân vật/hurtbox; vị trí chân khác tâm capsule; kích thước đầy đủ khác half extent API; world/local space; tường chặn nhưng cơ thể đối thủ không tự chặn kiếm; nhiều hurtbox vẫn một hit/mục tiêu/action. Query/sweep phải kiểm chứng khi khoảng active nằm giữa hai lần cập nhật, không chỉ kiểm tra phase tại cuối frame.

Cổng: đúng active, không xuyên tường hoặc nhân hit, một đòn được server xác nhận và hai client thống nhất; không sao chép giả định FixedUpdate/PhysX Unity.

### U03 — Combat Kiếm Vũ đầy đủ

Phụ thuộc: U02. Bàn giao lần lượt A–D.

- [ ] U03.01 A: ba đòn 60/70/90, buffer 0,15 giây, chuỗi 1,45 giây, quyền hủy/hướng.
- [ ] U03.02 A: năng lượng/cooldown, ưu tiên lệnh/reset combo.
- [ ] U03.03 B: né hai lượt 3 m/0,25 giây, hồi tuần tự, chặn tường/người/vực, không i-frame.
- [ ] U03.04 B: đỡ/parry/thế đỡ/phá đỡ, CC/chống khóa/X tại timestamp hit.
- [ ] U03.05 C: Q Feint/E Interrupt, quái báo đòn phát hiện 10 m/leash 15 m, Tab, thắng/thua/thử lại.
- [ ] U03.06 D: animation/kiếm/VFX/âm/HUD, kết quả/rebind/save/load và sân thử.
- [ ] U03.07 Retry reset sân thử, không thay hồi sinh sản phẩm; giữ trạm hồi quy U01.

Cổng: luật Description được kiểm chứng trên Unreal (G02 A–E chỉ là tham chiếu lịch sử). Các đợt A–D giữ quyền quyết định trên server và chạy hồi quy hai client ở mạng cục bộ cho hành động vừa thêm; bàn giao log trạng thái/HP thống nhất. Chưa nghiệm thu hiệu năng đầy đủ hoặc mạng xấu U05.

### U04 — Windows và hiệu năng

Phụ thuộc: U03.

- [ ] U04.01 Hồi quy luật/tích hợp/camera/input dưới tải, giữ mọi lượt fail.
- [ ] U04.02 Build đúng nguồn/hash; input Windows, xác nhận đúng map/player/tick trước đo.
- [ ] U04.03 FPS thực 30/60/120: đi/sprint 50/70 m trong 10 giây mô phỏng sau tăng tốc (±0,5 m), né 3 m ±0,05 m; combo 1,45 giây/220 damage với fixture riêng tắt crit.
- [ ] U04.04 Profiler CPU/GPU/cấp phát, 1/10/40 mục tiêu × 1/3 hurtbox, kiểm chứng counter, tách warmup/debug.
- [ ] U04.05 Combat thực ≥10 phút, 10 Retry, 5 vòng map, Alt-Tab giữ input, Quit/mở lại settings, nghe/xem trực tiếp.
- [ ] U04.06 XML/log/CSV/profile/video/checksum, phân biệt phương pháp, giữ dữ liệu người dùng.

Bàn giao theo thứ tự: A — U04.01–02 xác minh binary/hồi quy; B — U04.03 tính đúng ở các FPS; C — U04.04 profiling và sửa điểm nghẽn; D — U04.05 soak/input/vòng map. U04.06 áp dụng mỗi đợt, giữ cả lượt fail. Benchmark 40 mục tiêu/hurtbox đo truy vấn combat, không chứng minh tải 40 người chơi/server. Ghi cấu hình máy và FPS đo thực; không đạt FPS yêu cầu thì báo thiếu bằng chứng, không thay bằng giá trị cap.

Cổng: không lỗi chặn gameplay; số đo đạt trên binary thực. Cap/filename/vòng lặp mô phỏng/soak đứng menu không thay bằng chứng gameplay. Mạng cơ bản đã thử từ U01–U03; qua U04 mới nghiệm thu ma trận mạng xấu U05.

### U05 — Kiểm chứng combat qua mạng

Phụ thuộc: U04. Không sản xuất thêm nghề trước khi qua giai đoạn này.

- [ ] U05.01 Dựa trên server/hai client U01–U03, đo hạn chế replication và prediction bằng thử nghiệm nhỏ; chốt giải pháp bổ sung sau khi xem giấy phép, chi phí và bằng chứng. Không trì hoãn xác minh đường build server đến giai đoạn này.
- [ ] U05.02 Một server riêng, hai client; quyền quyết định không nằm ở máy người chơi chủ phòng.
- [ ] U05.03 Đồng bộ di chuyển, hướng ngắm, đòn, HP, né, khống chế và chết.
- [ ] U05.04 Prediction, sửa sai và làm mượt nhân vật từ xa.
- [ ] U05.05 Tách animation khỏi quyền quyết định sát thương; kiểm chứng projectile bằng súng thử.
- [ ] U05.06 Chốt chính sách bù trễ sau đo; không mặc định đảo ngược sát thương đã xác nhận.
- [ ] U05.07 Ngắt/kết nối lại, yêu cầu sai thứ tự và gửi lặp.
- [ ] U05.08 Chặn client tự khai tốc độ, damage, hồi chiêu hoặc quyền dùng kỹ năng.

Ma trận: RTT 0/60/120/200 ms, mất gói 0/1/3%, có jitter; ngắt khi startup/active/né/chết; hai người đánh hoặc CC gần đồng thời.

Cổng: hai client thống nhất HP/chết, không nhân đôi hit; RTT 120 ms vẫn đọc và điều khiển được. Nếu phải đổi cấu trúc combat, sửa tại đây trước khi mở rộng nội dung.

### U06 — Kỹ năng và hai nghề bản thử

Phụ thuộc: U05.

Trước U06.01, review cách quản lý action/ability/effect đã có với nhu cầu hai nghề. Chỉ đổi kiến trúc/GAS khi thử nghiệm nhỏ chứng minh lợi ích, có chi phí chuyển đổi và hồi quy U02–U05; không tự thay framework rồi sản xuất kỹ năng hàng loạt.

- [ ] U06.01 Dữ liệu kỹ năng, tài nguyên, hiệu ứng, vùng đánh và quyền hủy.
- [ ] U06.02 Thiết kế 10 kỹ năng mỗi nghề, chọn tám ô.
- [ ] U06.03 Hai Biến Thức mỗi nghề; mỗi hướng thay ít nhất hai kỹ năng với đánh đổi rõ.
- [ ] U06.04 Kiếm Vũ: áp sát, áp lực, phản công và thoát vị trí bất lợi.
- [ ] U06.05 Cơ Xạ: bắn, đạn/nạp đạn, cơ động, bẫy và kiểm soát đường đi.
- [ ] U06.06 Bộ kỹ năng, tooltip, màn hình nghề và đổi nghề tại thành phố.
- [ ] U06.07 Ghi rõ điều chỉnh PvE/PvP nếu khác; không sửa ngầm theo chế độ.

Cổng: hai nghề có cách đối phó lẫn nhau; đổi build không để sót skill/buff; mỗi lựa chọn công cụ có chi phí ô kỹ năng hoặc đánh đổi.

### U07 — Tài khoản và lưu dữ liệu

Phụ thuộc: U06.

Trước U07.01, chốt ranh giới game server, xác thực và lưu dữ liệu; hợp đồng API/quyền truy cập, lỗi và giao dịch. Chọn backend theo yêu cầu đã đo; không mặc định UObject replication là lưu bền hoặc client được ghi tài sản trực tiếp.

- [ ] U07.01 Tài khoản thử kín theo lời mời, xác thực và quản lý phiên.
- [ ] U07.02 Tạo nhân vật, tên, ngoại hình tạm và nghề.
- [ ] U07.03 Lưu cấp/XP, điểm, build, đồ, tiền, nhiệm vụ và điểm hồi sinh.
- [ ] U07.04 Tách dữ liệu thiết kế với tài sản sở hữu; một phiên hoạt động mỗi nhân vật.
- [ ] U07.05 Giao dịch nguyên tử và mã chống thực hiện lặp cho tiền/đồ.
- [ ] U07.06 Version dữ liệu, migration, sao lưu và khôi phục.
- [ ] U07.07 Công cụ nội bộ tra lịch sử tài sản và lỗi; bí mật chỉ ở server.

Cổng: tắt server giữa lúc thưởng, đăng nhập lại và gửi lại yêu cầu không mất/nhân tài sản; khôi phục thành công một bản sao lưu thử.

### U08 — Vòng PvE đầu tiên

Phụ thuộc: U07.

- [ ] U08.01 Một trung tâm, một vùng nhỏ, ba quái thường cận chiến/tầm xa/cơ động và một tinh anh.
- [ ] U08.02 Sáu nhiệm vụ giới thiệu di chuyển, đánh, phòng thủ, kỹ năng, trang bị và tổ đội.
- [ ] U08.03 Tiến trình cấp 1–10, XP, lên cấp và nâng kỹ năng.
- [ ] U08.04 AI phát hiện, tiếp cận, đánh, rút về/reset.
- [ ] U08.05 Drop, nhặt đồ, kho và kho nhận thưởng khi đầy.
- [ ] U08.06 Checkpoint, chết/hồi sinh và chia sẻ mục tiêu nhiệm vụ đúng điều kiện.
- [ ] U08.07 UI lỗi rõ khi thiếu điều kiện, đầy kho hoặc mất mạng.

Bàn giao: vòng nhận mục tiêu → đánh → thưởng → chỉnh build → thử thách mới. Cổng: người mới hoàn thành chuỗi, thoát/vào vẫn tiếp tục được, không cần lệnh quản trị.

### U09 — Dungeon bốn người và PvP 1v1

Phụ thuộc: U08.

- [ ] U09.01 Mời/rời/giải tán tổ đội, instance và kết nối lại đúng phiên.
- [ ] U09.02 Dungeon 15–20 phút: nhóm quái, tinh anh, boss ba cơ chế; không bắt buộc nghề chưa có.
- [ ] U09.03 Cứu đồng đội, checkpoint, wipe/reset và thưởng cá nhân đúng một lần.
- [ ] U09.04 Bản cốt truyện một người, chỉnh encounter/phần thưởng.
- [ ] U09.05 Ghép 1v1 không xếp hạng, chuẩn hóa build, cấm đồ ngoài trận.
- [ ] U09.06 Bắt đầu/kết thúc/hòa/chết đồng thời/bỏ trận/reconnect.
- [ ] U09.07 Ngăn buff/chỉ số PvE lọt vào PvP; bảng kết quả dễ hiểu.

Cổng: bốn client hoàn thành dungeon, thưởng đúng; mọi trận 1v1 kết thúc và trả nhân vật về trạng thái hợp lệ.

### U10 — Bản thử kín

Phụ thuộc: U09.

- [ ] U10.01 Build Windows có phiên bản, kiểm tra tương thích server và truy cập giới hạn.
- [ ] U10.02 Báo lỗi kèm phiên bản/phiên chơi/log phù hợp.
- [ ] U10.03 Hướng dẫn trong game, cài đặt hình/âm và thoát an toàn.
- [ ] U10.04 Mời 4–8 người trước, tăng theo sức tải đo được.
- [ ] U10.05 Đo FPS, memory, thời gian khung server, băng thông, lệch vị trí và lỗi lưu.
- [ ] U10.06 Quan sát đọc đòn, latency, camera, nguyên nhân thua và khả năng tự học.
- [ ] U10.07 Thông báo dữ liệu có thể xóa; không nhận tiền hoặc hứa giữ tiến trình.

Cổng: không lỗi tài sản/quyền tài khoản nghiêm trọng đã biết; không lỗi chặn dungeon; hai nghề đối phó được; người mới hoàn thành hướng dẫn không cần giải thích trực tiếp. Bàn giao báo cáo sửa ưu tiên. Sửa combat/mạng trước mở rộng thế giới.

### U11 — Sáu nghề và chiều sâu build

Phụ thuộc: U10. Thứ tự: Phá Trận → Hộ Ước → Ấn Sư → Ảnh Quyền, lần lượt kiểm chứng tầm dài, hỗ trợ/khiên, vùng tác dụng và bắt/quật.

- [ ] U11.01 Mỗi nghề đi qua thiết kế, hoạt ảnh, mạng, PvE và PvP.
- [ ] U11.02 Kiểm tra tương tác CC, khiên, projectile, bẫy và vùng kỹ năng.
- [ ] U11.03 Kiểm tra 21 cặp nghề tính cả cùng nghề.
- [ ] U11.04 Hoàn thiện Biến Thức, ghi nhận đóng góp nghề hỗ trợ.
- [ ] U11.05 Công cụ tạo kỹ năng/encounter và kiểm tra dữ liệu tự động.

Cổng: thêm nghề không sao chép toàn bộ combat; không khóa vô hạn hoặc bộ kỹ năng vô hiệu hóa hoàn toàn nghề khác.

### U12 — Cấp 50, trang bị và kinh tế

Phụ thuộc: U11.

- [ ] U12.01 Các dải 1–10, 11–20, 21–35, 36–50; chốt XP/chỉ số/vật liệu trước sản xuất hàng loạt.
- [ ] U12.02 Sáu phẩm chất, bộ 2/4/6, ngọc, nâng +10.
- [ ] U12.03 Chế tạo theo ngân sách thuộc tính và danh sách hiệu ứng hợp lệ.
- [ ] U12.04 Tháo đồ, kho thành phố, giao dịch trực tiếp.
- [ ] U12.05 Nguồn tạo và tiêu tiền/đồ; ngăn vòng lặp kiếm tài sản vô hạn.
- [ ] U12.06 Kiểm thử đổi nội dung sau xác nhận, gửi lặp, mất mạng giữa giao dịch.
- [ ] U12.07 Ngưỡng thưởng boss ghi nhận cả damage, hồi máu và bảo vệ.

Cổng: lên cấp/đổi build không ngõ cụt; kinh tế không có lỗi nhân tài sản hoặc công thức tạo tiền vô hạn.

### U13 — Thế giới 40 người, raid và PvP đội

Phụ thuộc: U12.

Trước U13.01, chốt vòng đời instance/phân khu, nơi giữ quyền sở hữu nhân vật khi chuyển khu và ngân sách tải bằng thử nghiệm đo được; không mặc định một map lớn hoặc số kết nối tương đương sức tải MMORPG.

- [ ] U13.01 Phân khu 40 người, ưu tiên tổ đội cùng nơi, đồng bộ theo phạm vi quan tâm.
- [ ] U13.02 Chuyển khu không mất/nhân nhân vật; boss thế giới và thưởng cá nhân.
- [ ] U13.03 Raid tám người, nhiều cấu hình nghề, xử lý bỏ dở/reconnect.
- [ ] U13.04 PvP 3v3; xếp hạng 1v1/3v3 riêng, chuẩn hóa sức mạnh.
- [ ] U13.05 Ghép theo trình độ, vùng mạng và thời gian chờ; xử lý bỏ trận/thông đồng.
- [ ] U13.06 Bạn bè, bang hội, chat, tìm nhóm, chặn/báo cáo và công cụ xử lý vi phạm.

Cổng: 40 nhân vật thật sự di chuyển và chiến đấu trong phân khu, không chỉ 40 kết nối đứng yên; raid/trận đội và chuyển khu có kết quả nhất quán.

### U14 — Nội dung và hình ảnh sản phẩm đầy đủ

Phụ thuộc: U13; art được sản xuất từng phần từ trước khi cơ chế tương ứng ổn định.

Ngân sách nội dung đầu: một thành phố, bốn vùng theo dải cấp, bốn dungeon, một raid, hai boss thế giới, hai bản đồ đấu trường, sáu nghề tối thiểu 10 kỹ năng/nghề chọn tám và hai Biến Thức.

- [ ] U14.01 Tuyến chính nối đủ cấp 1–50, nhiệm vụ phụ theo nhu cầu XP/khám phá.
- [ ] U14.02 Thay asset tạm bằng bộ thống nhất và có quyền phân phối.
- [ ] U14.03 Animation, VFX, âm thanh, UI; kiểm tra lại hit khi thay model/clip.
- [ ] U14.04 Tối ưu texture/mesh/ánh sáng/hiệu ứng/số đối tượng.
- [ ] U14.05 Trang phục không giấu tín hiệu nghề hoặc tạo lợi thế thị giác.

Cổng: đi từ tạo nhân vật tới cấp 50 bằng nội dung có mục đích, không lặp vô lý để bù khoảng thiếu.

### U15 — Alpha đầy đủ và beta

Phụ thuộc: U14.

- [ ] U15.01 Vòng tài khoản → cấp 50 → PvE endgame → PvP → kinh tế.
- [ ] U15.02 Lỗi server/mạng trong mọi giao dịch nhạy cảm; yêu cầu giả, spam và dữ liệu sai.
- [ ] U15.03 Kiểm tra quyền quản trị, logging và bảo vệ thông tin nhạy cảm.
- [ ] U15.04 Tăng người chơi theo đợt có giới hạn; chốt cấu hình PC tối thiểu qua đo.
- [ ] U15.05 Tải combat, thưởng/chuyển khu đồng thời, thử dài hạn phát hiện leak.
- [ ] U15.06 Vá phiên bản, bảo trì, migration và khôi phục.
- [ ] U15.07 Chính sách tài khoản, riêng tư, hỗ trợ, phát hành; thời điểm wipe cuối trước cam kết giữ tiến trình.

Cổng: không còn lỗi nghiêm trọng tài sản/bảo mật/tiến trình/kết thúc trận; quy trình khôi phục đã thử thành công.

### U16 — Phát hành và vận hành

Phụ thuộc: U15.

- [ ] U16.01 Khóa release candidate, chỉ nhận sửa lỗi cần thiết; rà quyền phân phối asset.
- [ ] U16.02 Cài/cập nhật, thông báo bảo trì, hỗ trợ và giới hạn người chơi theo tải/ngân sách.
- [ ] U16.03 Cảnh báo lỗi server/lưu, tải, đăng nhập và giao dịch bất thường.
- [ ] U16.04 Rollback code và khôi phục dữ liệu có quy trình riêng; không coi chúng là cùng một việc.
- [ ] U16.05 Ưu tiên lỗi tài sản/kết nối/tiến trình trước thêm nội dung.
- [ ] U16.06 Theo dõi kinh tế, cân bằng, ghép trận và chi phí/người chơi đồng thời.
- [ ] U16.07 Nội dung mới đi qua thiết kế → thử kín → kiểm thử → phát hành.

Cổng nền tảng: game vận hành ổn định, dữ liệu được bảo vệ, có quy trình hỗ trợ và khôi phục. Game online vẫn cần bảo trì liên tục.

## 3. Hợp đồng và ranh giới hệ thống

| Nhóm | Nội dung thống nhất |
| --- | --- |
| Lệnh | Số thứ tự, hành động, hướng và thời gian; server kiểm tra quyền |
| Nhân vật | Vị trí, hành động, HP, tài nguyên, CC, cooldown và phiên bản trạng thái |
| Kỹ năng | ID ổn định, nghề, các pha, chi phí, mục tiêu, vùng đánh, hiệu ứng, quyền hủy |
| Vật phẩm | Tách định nghĩa món và bản thể sở hữu; không dùng tên hiển thị làm ID |
| Combat | Nguồn/đích, kỹ năng, thời gian, hit, damage, lý do từ chối |
| Tiến trình | XP/cấp, build, nhiệm vụ, checkpoint, phiên bản dữ liệu |
| Tài sản | Mã giao dịch duy nhất, nguyên tử, lịch sử và chống gửi lặp |
| Instance | Thành viên, vòng đời, kết quả, quyền thưởng |

Luật combat không nằm trong animation/UI. Server không tin damage, tiền hoặc kết quả hit tự khai từ client. Chi tiết thư viện/schema được chốt trong nhiệm vụ tương ứng trước khi nhân rộng, không chọn chỉ vì đã có tên package trong project.

Hợp đồng nền chốt tại U00, cụ thể hóa action/collision tại U02:

- Dữ liệu thiết kế dùng mét/giây; transform Unreal dùng centimet, 1 m = 100 cm. Đổi tại ranh giới, tên trường ghi rõ Meters/Cm/Seconds; test phép đổi và round-trip.
- X tiến, Y phải, Z lên; góc dùng độ. Ghi rõ world/local, vị trí chân/tâm capsule, hướng thân/di chuyển/ngắm; không suy ra từ orientation của mesh nhập vào.
- Clock gameplay theo mô phỏng world/session, không dùng giờ hệ điều hành hoặc số frame. Khi chạy mạng, server giữ quyền thời gian; đồng bộ/bù trễ hoàn thiện ở U05. Test dùng clock điều khiển được.
- Khoảng thời gian nửa mở `[start,end)`, đúng deadline là hết hiệu lực; frame vượt biên vẫn phải xét phần khoảng thời gian liên quan. Thứ tự sự kiện cùng thời điểm theo Description; không dựa vào thứ tự callback collider.
- Menu không pause thế giới theo luật sản phẩm. Chính sách reset clock khi đổi world/session phải được ghi rõ; không dùng deadline cũ sang phiên mới.
- Montage/notify phục vụ trình bày; không xác nhận hit/damage. Luật sở hữu action; animation phản ánh phase và kết quả đã xác nhận.

## 4. Kiểm thử xuyên suốt

- Luật: damage, timing, buffer, charge, CC, XP và ngọc.
- Tích hợp: vào trận, thưởng, đổi nghề, save/load và migration.
- Mạng: latency/jitter/loss, reconnect, sai thứ tự và gửi lặp.
- Nội dung: dữ liệu thiếu, Blueprint/asset mất tham chiếu, vùng đánh sai, nhiệm vụ không hoàn thành được.
- Hiệu năng: build thực, máy mục tiêu, phiên dài và combat đông người.
- Người chơi: học điều khiển, đọc đòn, hiểu thất bại và động lực chơi tiếp.

Mỗi U01–U03 có smoke test packaged Windows ngoài Editor cho nội dung vừa thêm, kiểm tra Blueprint compile, missing reference và map cook. Mỗi báo cáo ghi nguồn/commit, engine/toolchain, lệnh, exit code, số test pass/fail và giới hạn; không coi 0 test là đạt. U04 giữ vai trò nghiệm thu hiệu năng đầy đủ. Bằng chứng kỹ thuật không thay kiểm tra cảm giác điều khiển và khả năng đọc đòn.

Công cụ theo nhu cầu: sân combat, hiển thị vùng đánh/trạng thái/cooldown, tạo build thử, giả lập mạng xấu, kiểm tra dữ liệu, nhật ký tài sản và phục hồi tài khoản thử. Chức năng debug không cấp quyền cho client phát hành.

## 5. Kiểm soát phạm vi và rủi ro

Bản thử kín chưa làm bốn nghề còn lại, raid, thế giới 40 người, xếp hạng, giao dịch, bang hội đầy đủ, kinh tế cấp 50 hoặc art riêng hàng loạt. Đây là hoãn theo giai đoạn, không tự xóa mục tiêu sản phẩm.

Không thêm gacha, cửa hàng, thú cưỡi, lãnh thổ hoặc tính năng ngoài Description vào đường phát triển chính.

| Rủi ro | Cách xử lý |
| --- | --- |
| Combat không vui | Thử từ U03/U06/U10; sửa trước mở nội dung |
| Mạng buộc viết lại | Server/hai client từ U01, một đòn qua server ở U02, hồi quy U03; mạng xấu U05 trước sản xuất nghề hàng loạt |
| Khối lượng art vượt sức | Asset hợp giấy phép, rig/bộ hình thống nhất, thay dần |
| Mất/nhân tài sản | Giao dịch nguyên tử, chống lặp, log và thử khôi phục |
| Không đủ tải hoặc tiền | Giới hạn thử, đo chi phí trước mở rộng; không hứa số CCU toàn hệ |
| AI tạo thay đổi khó kiểm soát | Nhiệm vụ nhỏ, review diff, kiểm tra nghiệm thu và commit có thể hoàn tác |

## 6. Bước bắt đầu và cập nhật lịch

Đường phụ thuộc: U00 → U01 → U02 → U03 → U04 → U05 → U06 → U07 → U08 → U09 → U10 → U11 → U12 → U13 → U14 → U15 → U16.

Thứ tự đầu: quản lý phiên bản → build sạch/sân thử U00 → nhân vật và server/hai client U01 → hợp đồng action/collision và một đòn qua server U02 → combo/phòng thủ U03 → Windows/hiệu năng U04 → mạng xấu U05. Mốc kiểm chứng MMORPG quan trọng nhất là combat hai client qua server dưới mạng xấu; phép thử mạng cơ bản không được bỏ qua để chờ U05.

Cuối mỗi phiên ghi việc hoàn thành, bằng chứng, lỗi mới và nhiệm vụ tiếp theo. Cuối mỗi giai đoạn cập nhật thời gian thực tế, backlog và phạm vi. Lập lịch tuần sau U05 dựa vào năng lực thực tế, không quy đổi một câu trả lời AI thành thời gian sản xuất nội dung đã hoàn thành.

## 7. Bổ sung combat: Parry, Counter, Feint và Interrupt

Các nhiệm vụ này bổ sung vào giai đoạn hiện có, không chờ tới giai đoạn mới sau phát hành.

- [ ] U03.08 Parry qua nút đỡ: cửa sổ 0,12 giây, khoảng cách mở 0,60 giây, một hit/cửa sổ; giữ nút thành đỡ thường, không tự phản đạn, gây choáng hoặc bất tử.
- [ ] U03.09 Hạ tầng Feint/Interrupt bằng kỹ năng thử: Feint đúng startup, ưu tiên trước combo, khóa 0,20 giây và giới hạn 1 giây; Interrupt đúng hit/pha và không hoàn tài nguyên.
- [ ] U05.09 Xác minh parry theo thời gian, hướng và thứ tự hit máy chủ; không nới cửa sổ theo ping. Thử RTT 0/60/120/200 ms, mất gói 0/1/3%, jitter và phản hồi dự đoán bị từ chối.
- [ ] U06.08 Chốt đòn nghề có Feint, pha bị ngắt và kỹ năng khai thác parry. Kiếm Vũ thiên phản công, Hộ Ước bảo vệ; không tự cấp parry cho Cơ Xạ/Ấn Sư.

Cổng U03 bổ sung: thử parry tại 0, ngay trước/đúng 0,12 giây; mở lại trước/đúng 0,60; sai hướng, hết thế đỡ, giữ nút, đòn bắt/xuyên đỡ, đòn không parry được nhưng đỡ được, nhiều hit/người tấn công đồng thời. Xác nhận parry không tự counter và không ngắt boss. Thử Feint ngoài startup, khi đang hồi, ưu tiên lệnh với combo; ngắt không tự gây choáng. Chạy biên thời gian ở 30/60/120 FPS.

Cổng U05 bổ sung: hai client đồng thuận kết quả parry/đỡ/trúng; không lợi dụng gửi lặp hoặc thời gian client để mở thêm cửa sổ. Cổng U06 bổ sung: phản công có điều kiện/đánh đổi rõ, không bảo đảm trúng và không tạo chuỗi hủy vô hạn.
