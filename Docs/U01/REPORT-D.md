# U01-D — Bản sửa landing và cầm kiếm (D1/D2/D3)

**READY_FOR_REVIEW**, chưa nghiệm thu D. Tiếp tục nhánh u01/d-animation từ 941bc3d3b7216355557053078c89b35a2b0a6477. Nguồn game/build/tests/package sửa: **819fbd041b8bc1f8463d6a075a4c6c29215b1f9c**. Commit hồ sơ/tool capture phía sau không đổi runtime hoặc asset của nguồn này. Main giữ 868df83e096748991ccd861da3f98b64c409dcbd; không merge D/chạy E.

Người dùng phát hiện hai lỗi sau bàn giao941: giữ pose landing khi đang di chuyển, và kiếm bám socket nhưng đặt/hướng sai, ngón tay chưa nắm cán. Lịch sử bàn giao cũ giữ nguyên tại [REPORT-D-941-HISTORY](REPORT-D-941-HISTORY.md), [checklist cũ](D-CHECKLIST-941-HISTORY.md), cùng Evidence/D-* cũ. Kết quả14/14 hoặc video cũ không thay nghiệm thu bản sửa.

## D1 — Landing

UU01AnimInstance chỉ đổi chọn pose: chạm đất với speed ngang >3cm/s vào locomotion ngay; <=3cm/s giữ landing tối đa0,25s rồi idle. Bắt đầu chạy trong hold hủy hold cùng update; nhảy lại/rơi được ưu tiên ngay. AnimBP lưu **0,100s tường minh cho cả5 pose** ở node và pin default, không dựa AddPose mặc định. Không khóa đi, sửa gia tốc/gravity/jump, coyote/buffer hoặc input để đợi animation. Git diff941→819 xác nhận các file Character/motor/input/controller, input assets, map và template không đổi.

Hai tests hồi quy mới chạy trên BP/mesh/AnimBP thật:

- AnimeMMORPG.U01.D.LandingTransitions: W–jump, W+Ctrl–jump, stationary landing, bắt đầu chạy trong hold, buffer trước touchdown, nhảy/rơi ngắt hold, đi khỏi mép collision thật tới nền thấp rồi tiếp tục chạy. Kiểm pose ngay tại contact/update; thời gian giữ <=0,25s cộng độ phân giải sample; compiled blend times đều0,100s, target chưa full ở đầu blend và full sau deadline cộng sample tolerance. Không chỉ kiểm từng thấy landing.
- AnimeMMORPG.U01.D.GripIsolationAndAttachment: pose ngón thực thay đổi; tắt/bật layer ở cùng thời điểm để so tất cả local transform ngoài15 ngón, gồm cổ tay/cánh tay, sai số0,001; attachment kiểm cả vị trí và quaternion; camera sát tường ẩn cả mesh/ba phần kiếm và hiện lại sau hết cản.

## D2 — Chẩn đoán và giá trị cuối

Đã chụp trước chỉnh trên mesh thực: socket gốc(0,0,0) ở cổ tay, lưỡi theo+X hand hướng về phía cổ tay; các ngón từ clip unarmed còn mở. Số đo hand-space cho knuckle khoảngX=-8 đến-9,5cm và ngón cái về phía+Z. Bộ ảnh trước cuối dùng byte ABP/SK của941 đối chiếu hash; không lấy attachment khớp làm chứng minh cách cầm đúng.

Giữ kích thước grip18×3×3, guard4×18×4, blade88×6×2,5cm. Socket **U01_Sword_R/hand_r** trên skeleton U01 riêng chốt **location(-6,5; 2; -0,5)cm**, **rotation Pitch90/Yaw0/Roll90 độ**. Tâm cán vào vùng lòng bàn tay, lưỡi theo+Z hand phía ngón cái, guard ngoài nắm tay. Pose riêng **PA_U01_RightGrip/RightGrip** được lưu bằng công cụ PoseAsset sẵn có, đặt sau selector với Layered Blend per Bone chỉ5 nhánh ngón01 bên phải. Không đổi cổ tay/cánh tay/metacarpal, skeleton/clip nguồn, không thêm clip chuyển động, IK toàn thân, plugin hoặc animation chiến đấu.

Các góc dưới đây là **delta Pitch/Yaw/Roll so với ref local rotation**, áp RefQuaternion * DeltaQuaternion; không phải Euler world. Chúng được chọn sau đọc hình/axes rồi quan sát candidate trên mesh idle/run/landing; giá trị đầy đủ trong [DGrip.json](../../Scripts/U01/DGrip.json).

| Ngón | Joint01 delta P/Y/R | Joint02 | Joint03 |
|---|---|---|---|
| index | 0 / -61,627 / 0 | 0 / -60,107432 / 0 | 0 / -37,483599 / 0 |
| middle | 0 / -58,427318 / 0 | 0 / -49,230790 / 0 | 0 / -40 / 0 |
| ring | 0 / -65,585518 / 0 | 0 / -56,036 / 0 | 0 / -45,832 / 0 |
| pinky | 0 / -85,166319 / 0 | 0 / -58,713001 / 0 | 0 / -50,083 / 0 |
| thumb | 12 / -18 / -10 | 0 / -25 / 0 | 0 / -35 / 0 |

Ảnh [trước](Evidence/D-Revision/Hands/Before) / [sau](Evidence/D-Revision/Hands/After) có Front/Side/Top cho idle/run/landing, thêm Palm/ThumbSide/FingerEnd để nhìn rõ khi arm/blade che góc trực diện. Ví dụ [run trước](Evidence/D-Revision/Hands/Before/Run-Front.png), [run sau](Evidence/D-Revision/Hands/After/Run-Front.png), [nắm cán](Evidence/D-Revision/Hands/After/Run-FingerEnd.png), [landing](Evidence/D-Revision/Hands/After/Land-Palm.png). Đây là **Editor pose preview**, có đèn fill tạm và sampler velocity/mode để chẩn đoán; không dùng làm số đo gameplay/FPS. Landing preview lấy đầu chuyển tiếp; thao tác landing thực kiểm riêng bằng tests/video. Một lỗi cache GPU khi chụp nhiều pose cùng frame đã được sửa bằng recreate render proxy; ảnh HandCandidate1 cũ bị thay bằng HandCandidateVerified, không dùng ảnh stale làm kết luận.

Kiếm vẫn blockout một tay, collision/overlap/physics/nav tắt, không damage. Chưa làm combat stance; clip unarmed có thể đưa kiếm qua thân ở một số góc, đúng giới hạn người dùng. Cách cầm vẫn chờ review hình ảnh trên package, không suy PASS thẩm mỹ từ sai lệch socket0.

## D3 — Kiểm chứng

UE5.8.4 CL58902052, MSVC14.51.36260/toolset14.51.36231, Windows SDK10.0.26100.0. Dùng clone riêng Artifacts/U01/D/Source, không copy binaries/Intermediate hoặc dùng patch Live Coding. GitHub có các lỗi500: phần độc lập từng build từ Git local và được ghi nguồn chưa push; **819fbd0 sau đó đã push, full build từ đĩa và cold-test**. Native rebuild Revision/Build-20261104-182743-101-c6712605; source build Revision/Build-20261104-183208-319-cbeba78e Editor/Game exit0 (asset-only change nên UBT up-to-date).

Cold clone **MCP TestRunner PID9760**, Revision/MCPTests-20261104-183218: **16/16 PASS**, đọc log mới tới queue-empty16. U00.Foundation4/4 (Axes/CallOrder/HalfOpenInterval/Units), B2/2 (CameraPolicy/ReleaseGate), C5/5 (FlatMovement/JumpPhysics/JumpWindows/MotorLocks/Terrain), D5/5 (AnimatedMotor/AssetPolicy/TransitionsAndAttachment/LandingTransitions/GripIsolationAndAttachment). Kỳ vọng cũ giữ landing chỉ còn ở ca đứng yên; ca đang chạy bắt buộc locomotion. [Kết quả và record identity](Evidence/D-Revision/RESULTS.json).

Fixture spawn pawn BP có AnimBP/mesh thật trong **Game physics world**, AIController cấp controlled input; mọi record có UTC/sourceSHA/PID/world/context/type/netMode/pawn/controller/owner/roles/mesh/anim class. Không dùng Editor world hoặc suy PIE từ tên actor.

| Đo lại với animation/grip | Kết quả |
|---|---:|
| Đi10s sau tăng tốc | 5000,000260770cm |
| Sprint10s sau tăng tốc | 7000,000365078cm |
| Apex dt1/30;1/60;1/120s | 119,987106204;119,987106189;119,994960187cm |
| Gravity | -980cm/s² |
| Hold stationary quan sát ở dt1/120 | 0,250000089s (sai số float/sample) |
| Target weight sau blend deadline | 1,000000 |
| Attachment max position/angle error | 0cm /0 độ |
| Root drift locomotion | 0cm |

Độ phân giải tích phân không là FPS render. Owner-hide cả mesh/kiếm đã assert hide/restore trong test mới. Package cuối Artifacts/U01/D/Revision/Package-20261104-183402-258-c983dd92/Archive/Windows: BuildCookRun exit0, đủ48file, [hash package](Evidence/D-Revision/PACKAGE.csv). Smoke Revision/SmokeB-20261104-184708: Boot/CharacterCombatLab/NetworkLab **3/3 PASS**, lab PID19712/3400; NetworkLab ở đây standalone, không nghiệm thu F.

## Video input thực và giới hạn capture

[Trước sửa11s](Evidence/D-Revision/Before.mp4) / [sau sửa11s](Evidence/D-Revision/After.mp4) dùng cùng timeline W–Space, rồi W+Ctrl–Space. [Ca mở rộng25s](Evidence/D-Revision/Coverage.mp4): đứng yên đáp, bắt đầu chạy trong landing, thử buffer/nhảy lại, chọn fixture Ledge rồi tiếp tục chạy. Raw events, identity và samples trong RESULTS.json. Log trước thực ghi pose4 ở500/700cm/s; log sau không có pose4 khi speed>3, có locomotion tại touchdown. Ledge sau có fall rồi locomotion, không ascent giả. Biên buffer/coyote chính xác do Automation chứng minh; video/trace5Hz không đo được thời điểm0,099s.

Capture dùng **SendInput Windows**, khóa đúng exe/PID/HWND/foreground, xác minh W/sprint từ log. UniKey từng biến W thành None; tool mới probe W trong menu đang khóa, chỉ chuyển tạm nếu cần và khôi phục nếu đã đổi. Các lượt bàn giao cuối probe nhận W đúng sẵn, không cần đổi mode. Không sửa input game. Capture cuối là screen BitBlt giới hạn vùng client, kiểm cả số ảnh khác nhau; không dùng window-client DC giữ ảnh menu cũ.

| Clip | Frame đọc mới/giây và ảnh khác/giây | Khoảng frame lớn nhất | Frame lặp để giữ thời gian |
|---|---:|---:|---:|
| Before | 25,869 | 131ms | 45/330 |
| After | 25,919 | 137ms | 44/330 |
| Coverage | 24,866 | 149ms | 128/750 |

File encoder30FPS **không có nghĩa capture30FPS hoặc game30FPS**. 285/286/622 ảnh khác nhau được xác nhận và ảnh trích đã xem. Không dùng các video này hoặc video10Hz cũ để khẳng định blend100ms mượt; test compiled graph kiểm deadline, người review đánh giá cảm giác trên package cuối. Các lượt capture cũ đã loại vì W=None, Resume chưa thực hiện, readback<1Hz, hoặc DC stale dù metadata đọc50–60Hz. Raw logs/metadata giữ trong Revision, không sửa thành PASS. [Manifest và lịch sử](Evidence/D-Revision/MANIFEST.json), [hash ảnh/video](Evidence/D-Revision/EVIDENCE.csv).

Compiler vẫn mới hơn preferred14.50; các C4996 engine và warning diagnostic API giữ trong log. Các lỗi compile/link helper pose riêng (private accessor/export/editor-only accessor) đã sửa, không bỏ tests. Optional profiler/audio diagnostics của smoke được giữ theo validator B. Không đổi renderer, engine hoặc cài plugin. Tồn tại Python/toolset của đường Editor -game/-server từ A vẫn để F/tích hợp; không giả báo đã xử lý trong D.

AI không đóng/restart Editor gốc. Cuối kiểm **PID20412, project gốc, Boot0actor**, marker MCP UTC12:09:56.665; native D mới trong Editor gốc **chưa xác nhận**. Header/UFUNCTION mới cần full build/restart trước dùng ở Editor đó, package clone đã nạp lạnh. Config/token local ngoài Git.

Art anime **DEFERRED**. Chưa nghiệm thu D tổng thể, chưa E/F/G, Server packaging hoặc combat. Chạy **Artifacts/U01/D/Play-D.cmd** để vào Boot của package819fbd0, logs ở Artifacts/U01/D/Revision/Review; giữ nguyên thư mục Windows48file khi sao chép. [Checklist ngắn](D-MANUAL-CHECKLIST.md) chỉ còn cảm giác chuyển động/cách cầm trên bản cuối; dừng chờ review, không tự merge.
