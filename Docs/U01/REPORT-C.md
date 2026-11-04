# U01-C — Motor, sprint, nhảy và địa hình

Trạng thái: **BLOCKED ở xác nhận thao tác bàn phím/UI fixture mới trong package**. Implementation, full build, 11/11 Automation và smoke Windows3/3 đã đạt; các phép đo motor/địa hình tự động có bằng chứng. Chưa nghiệm thu C theo người dùng, chưa triển khai D. Nhánh `u01/c-motor`, không tự merge.

## Nền và phạm vi

Người dùng nghiệm thu B tại `2e0e89fdffd05b9dad86014fb3cb8ac0338ba60d` và yêu cầu ghi PASS checklist theo xác nhận người dùng, push hồ sơ, fast-forward main rồi làm riêng C. Đã commit hồ sơ `72ad2be02364ace08588bb5e78aa3a491b3f2776`, push B/main, tạo C từ đúng main này. Báo cáo B giữ rõ: AI chỉ tự kiểm build/tests/smoke; xác nhận thủ công là của người dùng, không bổ sung video/PID/giờ chơi và không xác nhận Editor gốc nạp code B.

Source build/test/package C: **`a374081a6c681662407c9024e36168a41c1e6111`**, đã push trước kiểm. Commit tài liệu sau source này không thay Source/Content/Scripts. Ngày thực hiện2026-11-04 +07; bằng chứng cuối khoảng13:30–13:39. Main vẫn72ad2be. Xem [manifest](Evidence/C-MANIFEST.json), [số đo motor](Evidence/C-MEASUREMENTS.json), [hình học sân](Evidence/C-LAB.json), [hash package](Evidence/C-ARTIFACTS.csv) và [checklist gộp](C-MANUAL-CHECKLIST.md).

Giữ runtime module/engine/plugins/renderer/template/Description. Tái dùng mannequin/AnimBP tạm của B, không tạo art/AnimBP/kiếm D. **Art anime DEFERRED**. Không damage, combat, chết/hồi sinh sản phẩm, tài khoản hoặc mạng F. Saved move/custom network data và kiểm server sprint/jump vẫn F; kết quả C chỉ standalone.

## Thay đổi

- UU01CharacterMovement giữ tốc độ500/700cm/s, chỉ sprint khi có acceleration ngang hợp lệ và không khóa. Enhanced Input thêm IA_U01_Sprint, map Ctrl trái/phải; Triggered/Completed/Canceled quản lý intent local. Đi theo yaw camera và input chéo được movement clamp về độ lớn1.
- AU01Character nhận cạnh nhấn vào FJumpWindow, nhả không hủy buffer, không tăng độ cao theo thời gian giữ. Giữ JumpMaxCount1/JumpMaxHoldTime0; engine CheckJumpInput/DoJump giữ count/OnJumped. Coyote chỉ sau rời nền ngoài ý muốn, không sau takeoff chủ động; buffer chỉ tiêu thụ một lần. Hai cửa sổ `[start,start+0.10)` dùng double/FOUNDATION helper, không epsilon.
- Clock motor theo mô phỏng movement trong world/session: seed tại BeginPlay, tích phân DeltaSeconds, input dùng thời điểm movement hoàn tất trước đó; contact dùng timestamp bên trong frame. StartFalling tính thời gian rời nền từ phần quãng đường thực; ProcessLanded ghi event time và SetPostLandedPhysics xét buffer trước phần physics còn lại. Vì vậy frame đi qua deadline không tự làm mất landing sớm. World time và motor time xuất riêng trong metrics; reset fixture xóa deadline, không dịch clock; world/pawn mới reset session. Chưa chính sách timestamp/replay mạng F.
- JumpZVelocity tính tại takeoff từ `sqrt(2*abs(GetGravityZ())*120)`. Với gravity thực−980cm/s², seed484,9742cm/s đã đạt apex trong sai số, chưa cần thêm hệ số bù tích phân.
- WalkableFloorAngle45°, MaxStepHeight45cm, gán rõ trong native và Blueprint C. Steep slope dùng physics falling/slide của CharacterMovement. Khóa là bit độc lập Control/Interacting/Defeated: xóa pending/coyote/sprint, ngừng XY/acceleration/jump, vẫn gravity. Gỡ một lý do không bỏ lý do còn lại. Camera/menu/đổi vai vẫn được phép trong Interacting/Defeated; menu/focus và cơ chế physical release B được giữ.
- Menu ở CharacterCombatLab thêm reset runway, next station, toggle Interacting/Defeated và status. Đây là **fixture Development**, không phải gameplay tương tác/chết/hồi sinh; reset chỉ pawn local trong standalone lab, không RPC/teleport thay movement replication. NetworkLab không hiện các nút trạm địa hình không có trong map. G/quest và màn hình settings/rebind E chưa làm.

Files source: U01Character.h/.cpp, U01PlayerController.h/.cpp, U01Menu.h/.cpp, U01MotorPolicy.h và Tests/U01MotorTests.cpp. Scripts CreateCAssets.py/VerifyCTests.ps1. Năm binary đổi/thêm: CharacterCombatLab, BP_U01Character, BP_U01Controller, IMC_U01_B và IA_U01_Sprint. NetworkLab/Boot và variant template không đổi; controller/input dùng chung asset đọc tĩnh, không mutate mapping khi runtime. Hồ sơ C/ROADMAP thay đổi riêng, token config ngoài index.

## Sân đo

CreateCAssets.py chỉ chạy trong clone đã full build, từ chối original/duplicate. Editor API tạo/lưu rồi đo lại transform/bounds/normal:36 hình khối,13 TargetPoint reset và nhãn. Giữ nguyên floor/thước1m/10m/spawn/camera fixtures U00/B. Không dùng geometry Editor làm số đo pawn gameplay.

| Trạm | Số đo/đặc điểm |
|---|---|
| Runway Y−4000 | Mốc0–80m; sàn9000×600cm gồm5m tăng tốc và5m phanh ngoài đoạn đo; reset X−400 |
| Dốc Y2500…6500 | Chiều dài mặt800cm, rộng400, dày20; measured normals cho30/44/45/46/60° (sai số floating point <1e−12°) |
| Bậc Y8000…9000 | Cao20/40/60cm, dài/rộng400; step motor45 |
| Trần Y10000/10500 | Mặt dưới180/260cm; mái dày20; capsule cao192cm chưa tính floor gap |
| Ledge Y12000 | Platform cao300cm, landing floor top0, hai vùng tiếp giáp tạiX400 |
| Corridor Y13500 | Hai mặt trong tường cách120cm; có góc và floor riêng |

Các trạm tách nhau, dùng menu fixture; không phải thế giới sản phẩm. TargetPoint giữ SceneComponent runtime, tag reset được cook; icon Editor không là dữ liệu vị trí. JSON C-LAB là readback Editor geometry, tách khỏi JSON Game physics.

## Build và phương pháp kiểm

Clone GitHub tại `Artifacts/U01/C/Source`, cache LFS seed từ B rồi `git lfs fsck` OK; không copy Binaries/Intermediate B. Không tuyên bố cache/DDC sạch. Full build dùng script của clone với project tuyệt đối, guard chỉ project đang mở; original Editor vẫn mở. Engine `D:/Software/UE_5.8`, UE5.8.4 CL58902052; UBT thực chọn MSVC14.51.36260 (folder14.51.36231) và WindowsSDK10.0.26100.0, Win64 Development. Không cài/nâng phần mềm.

| Kiểm tra | Kết quả / bằng chứng cuối |
|---|---|
| Full Editor/Game | PASS, ExitCode0/Succeeded; `Build-20261104-133051-539-16476e43` |
| Asset creation/compile/save | PASS, `CreateAssets.log` marker U01C_ASSETS_SUCCESS; Blueprint config được lưu, source push trước package |
| MCP Automation trên binary đĩa clone | PASS11/11, queue11 complete; `MCPTests-20261104-133626` |
| Cook/package | PASS ExitCode0/BUILD SUCCESSFUL, cook0error/0warning; `Package-20261104-133145-169-7c624294` |
| Package smoke Boot/Character/Network | PASS3/3, LoadMap + exit0, không Error/Fatal/AccessedNone; `SmokeB-20261104-133628` (tái dùng runner SmokeB) |
| Input tay/UI mới/fixture camera-menu trên package | NOT-RUN; cần xác nhận checklist C gộp, không kế thừa PASS B cho phần mới |
| FPS render30/60/120, mạng F, animation D | NOT-RUN trong C |

VerifyCTests.ps1 mở Editor clone với port18013, MCP StartServer và U01SourceSHA; gọi TestRunner.run_automation_tests filter AnimeMMORPG, poll Logs.GetLogEntries mới, kiểm đúng11 paths/Success và queue11. Chỉ QUIT_EDITOR qua endpoint clone. Bốn U00: Axes, CallOrder, HalfOpenInterval, Units. Hai B: CameraPolicy, ReleaseGate. Năm C: **FlatMovement, JumpPhysics, JumpWindows, MotorLocks, Terrain** — tất cả Success. Không lấy kết quả Live Coding hoặc log cũ để thay tests cuối.

Physics tests dùng FTestWorldWrapper của Engine tạo world **Game**, collision box thật, AU01Character/CharacterMovement thật và AIController chỉ để sở hữu pawn/input fixture (không AI gameplay). Không mesh/AnimBP trong harness này; presentation tạm có trong package, D phải đo lại sau animation riêng. Từng mẫu có PID, UTC, sourceSHA, world/context/type/net mode, pawn/controller/owner/role và motor/world clock. Đây là controlled input test, không keyboard, viewport PIE hay frame render.22 JSON measurements đủ định danh, log/hash sidecar gắn đúng source. Policy test biên dùng clock fixture, tách khỏi kiểm input UI.

## Số đo Game physics

| Phép kiểm | Thực tế / kết luận |
|---|---|
| Walk10s sau warmup1s | 5000,000261cm; target5000±50: PASS |
| Sprint10s sau warmup1s | 7000,000365cm; target7000±50: PASS; sprint thiếu hướng inactive |
| Diagonal10s | 5000,000261cm; tỷ lệ với thẳng xấp xỉ1, chênh <1%: PASS |
| Apex, bước1/30;1/60;1/120s | 119,987106;119,987106;119,994960cm; target120±5: PASS. Đây là bước mô phỏng, **không phải FPS render đo được** |
| Hold/release/double jump | Giữ/repeat command qua landing không tạo lần mới; cạnh mới trên không sau nhảy chủ động không boost velocity; count≤1: PASS |
| Clock coyote/buffer | 0/0,099 hợp lệ,0,100/0,101 hết; trước start false; lock xóa pending; new session bỏ deadline: PASS |
| Ledge/landing thật | Coyote sau rời mép ngoài ý muốn và buffer của tap đã nhả đều có takeoff: PASS |
| Buffer trong frame0,15s | Landing xảy ra trước deadline dù cuối frame đã qua; count1/vận tốc lên: PASS |
| Dốc30/44/45 | Feet cao nhất khi grounded402,149/557,866/567,768cm: đi lên được |
| Dốc46/60 | Peak feet chỉ2,15cm khi giữ input đi lên: không leo; thả từ giữa dốc không input, deltaX−309,812/−234,626cm trong1,5s: trượt xuống |
| Bậc20/40/60 | 20/40 traverse;60 chặn tạiX−42,101cm, feet không lên bậc: PASS |
| Trần180/260 | 180 chặn standing capsule;260 cho đi và cắt apex do ceiling: PASS |
| Interacting/Defeated | Hai lý do độc lập, không horizontal/jump/sprint; rơi19,600cm/0,2s với Vz−196cm/s; gỡ một lý do vẫn khóa: PASS |

Package smoke riêng: game PID13788 và16276, WorldType1=Game, NetMode0=Standalone, localPlayers1 và owner BP_U01Controller; mỗi sân39 metrics. Trạng thái AwaitingResume của smoke hidden giữ Control bit1, maxspeed0, gravity−980; seed jump484,9742, motor clock và world clock được xuất riêng. Không diễn giải các mẫu startup này thành input thật/Alt-Tab/khóa fixture đã thao tác tay hoặc dedicated server F. Editor geometry và việc tìm thấy actor không thay bằng chứng Game world.

## Lịch sử và giới hạn

- C full builds/tests không lỗi compiler/test. Sau build đầu, rà soát timestamp và bổ sung clock motor/substep để không lấy frame-end world time rồi cộng thêm cả frame; reset chỉ xóa deadlines, không shift clock. Snapshot089eb10 đã11/11, snapshotab247f3 chạy lại11/11 có thêm long-frame case. Giữ cả log cũ, không sửa threshold/luật để qua test.
- Rà soát UI cuối sửa selector trạm: reset trực tiếp (kể cả runway) đồng bộ index/canonical name để next station đi theo trạm hiện tại. Snapshot bàn giao a374081 được full build, chạy lại11/11 và package/smoke3/3; không dùng snapshot cũ thay bằng chứng mới.
- C không dùng Live Coding cho layout/reflection mới; source/native assets tạo trên clone. Lịch sử B và log người dùng cung cấp vẫn giữ: compile `Succeeded` nhưng patch `LNK2019 __imp_GetAsyncKeyState`/`LNK1120`, object U01PlayerController.cpp.obj có thể không tìm thấy (0x2) khi đổi unity/adaptive build. Không khẳng định patch đó áp vào original, không đóng/restart original để che lỗi. Muốn dùng native C trong Editor gốc cần một mốc full build/restart riêng; package C đã build độc lập.
- Compiler14.51 mới hơn preferred14.50 và C4996 engine headers còn tồn tại. Cook0/0 là cook summary; startup optional profiler DLL/audio diagnostics được giữ trong smoke report theo validator B, không bỏ lỗi game content. Không thay renderer để làm đẹp số liệu.
- Python/toolset init khi chạy Editor executable -game/-server từ A/B chưa xử lý, còn phải sửa trước nghiệm thu tích hợp và kiểm lại F. C không chạy network hoặc suy F từ hai standalone map; chưa saved move sprint/jump/custom replay/network clock.
- File config local sinh token được giữ ngoài Git. Windows checkout không unlink29 file B do ownership; đã move từng file đã đối chiếu vào Artifacts/U01/C/MergePreserve rồi fast-forward, không delete/reset metadata hoặc bỏ thay đổi người dùng. Không đổi ACL/global Git policy.
- Chưa có desktop/packaged-game input tool được xác minh; chưa tự click các nút fixture, thử Ctrl/Space/Alt-Tab hoặc có video C. Vì vậy giữ **BLOCKED ở xác nhận UI/input mới** và bàn giao checklist cụ thể, không tuyên bố người dùng đã thử C. Art anime và animation riêng vẫn DEFERRED/D.

## Bàn giao

`Artifacts/U01/C/Play-C.cmd` mở đúng package a374081, bật U01Trace/sourceSHA, log trong `Artifacts/U01/C/Review/Game.log`. Giữ nguyên cả thư mục Windows48file khi sao chép. Hash bootstrap/game/containers trong C-ARTIFACTS.csv. [Checklist C](C-MANUAL-CHECKLIST.md) gộp thao tác mới cần người dùng kiểm; các số đo tự động không cần stopwatch tay để thay thế.

Cuối kiểm còn Editor gốc PID19924, commandline đúng `D:/Data/AnimeMMORPG/AnimeMMORPG.uproject`; không dùng PID19808 của phiên B cũ làm chứng cứ hiện tại. Original chưa được xác nhận nạp native B/C mới nhất. Không thay Description, Boot, NetworkLab hoặc template trong C. Stage rõ file C/docs, không token/cache/binary/log thô.

Commit/push `u01/c-motor`, đối chiếu ref rồi dừng. Main giữ72ad2be, không merge C hoặc bắt đầu D khi chưa được giao. Chỉ khép hồ sơ C sau xác nhận cần thiết; không đánh dấu U01 tổng hợp hoặc art anime hoàn thành.
