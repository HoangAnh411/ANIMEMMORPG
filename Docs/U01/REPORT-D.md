# U01-D — Animation in-place và kiếm blockout

**READY_FOR_REVIEW**, chưa phải xác nhận nghiệm thu D của người dùng. Nhánh `u01/d-animation`, từ main `868df83e096748991ccd861da3f98b64c409dcbd`. C đã khép REPORT-C/checklist theo xác nhận package tại `0cba933aa56379b1be064be40aaa0d9b3dbddb59`, commit/push hồ sơ và fast-forward main tới 868df83 trước khi tạo D. Nguồn build/test/package D cuối: **`715238443e33e1a2760ea3d89f4d1698f092e511`**. Commit bàn giao tài liệu phía sau không thay binary/asset nguồn này. Không merge D hoặc bắt đầu E.

## Thay đổi

- Bộ riêng `/Game/AnimeMMORPG/U01/Animation`: skeleton SK_U01, mesh SKM_U01, sáu sequence, BS_U01_Locomotion và ABP_U01. BP_U01Character gán mesh/AnimBP và Cube cho kiếm. Không sửa map, Description, template/variant, mesh/skeleton/clip nguồn. Hash11 asset thay đổi và diff template tại [D-ASSETS.json](Evidence/D-ASSETS.json).
- UU01AnimInstance đọc velocity ngang/dọc, acceleration, grounded/falling và sprint từ motor thực. AnimBP blend5 pose: idle, locomotion BlendSpace, jump-up, fall-loop, land. Rời mép đi thẳng vào fall; landing giữ0,25s rồi thoát; tái kích hoạt child reset thời gian clip. Animation không ra lệnh đi/nhảy, teleport hoặc đổi movement mode.
- Walk nguồn có root speed300cm/s; jog600,340651cm/s. Mẫu BlendSpace: idle0/rate1, walk300/rate1, jog500/rate0,832860, jog700/rate1,166005. Giới hạn kiểm rate0,6–2,5. Lệnh “đi”5m/s dùng chu kỳ jog đã chỉnh tốc độ; walk nguồn tham gia ở giai đoạn tăng tốc thấp hơn. Đây là bộ kỹ thuật hiện có, không chọn thêm art.
- Sequence bản sao bật extraction, ForceRootLock/AnimFirstFrame; AnimBP IgnoreRootMotion. Root track nguồn còn dữ liệu, nhưng pose trình bày in-place và motion bị discard, không cộng lên capsule. Mesh riêng bỏ post-process AnimBP của skeleton nguồn; không thêm foot IK/framework.
- Socket `U01_Sword_R` trên `hand_r` của skeleton riêng. Kiếm gồm ba Cube native components: grip18×3×3cm, guard4×18×4cm, blade88×6×2,5cm; Blueprint gán mesh. Collision/overlap/physics/navigation tắt, không damage. Cơ chế owner-hide gần camera của B áp dụng cả kiếm là con mesh. Clip unarmed chưa có pose nắm kiếm sản phẩm.
- File native: U01AnimInstance, U01AnimationEditor, U01Character, U01PlayerController metrics, U01AnimationTests và Build.cs. Helper authoring chỉ chạy trong Editor clone D; rebind FK ControlRig của clip bản sao trước validation, không sửa nguồn. Thêm dependency editor có sẵn để author graph, không cài/bật plugin mới hoặc tạo runtime module mới. Scripts CreateDAssets/FinalizeDAssets, VerifyDTests, CaptureDPlay, SummarizeD/RecordDEvidence giữ phép kiểm tái đọc được.

## Build, Automation và số đo

UE5.8.4 CL58902052, MSVC14.51.36260 (thư mục toolset14.51.36231), SDK10.0.26100.0. Clone GitHub tại `Artifacts/U01/D/Source`, seed cache object LFS từ C rồi fsck OK; không copy Binaries/Intermediate. Clone ban đầu ở source đã push, sau đó fast-forward đến7152384. Full native rebuild ở `Build-20261104-144328-366-7006a6c3`; sau commit chỉ sửa asset BlendSpace, UBT Editor/Game tại `Build-20261104-144803-468-388ab013` đều exit0/up-to-date từ đĩa. Không dùng patch Live Coding làm bằng chứng.

MCP TestRunner trên **cold clone Editor PID22856**, `MCPTests-20261104-144814`, đọc log mới đến “14 tests performed”: **14/14 PASS**. Tên/kết quả nguyên dòng trong [D-RESULTS.json](Evidence/D-RESULTS.json):

| Nhóm | Tests thực chạy |
|---|---|
| U00.Foundation —4/4 | Axes, CallOrder, HalfOpenInterval, Units |
| U01.B —2/2 | CameraPolicy, ReleaseGate |
| U01.C —5/5 | FlatMovement, JumpPhysics, JumpWindows, MotorLocks, Terrain |
| U01.D —3/3 mới | AssetPolicy, AnimatedMotor, TransitionsAndAttachment |

D tạo **Game physics worlds**, spawn BP_U01Character có mesh/AnimBP D thật, AIController sở hữu để cấp input fixture; không lấy Editor world làm số đo. Mỗi record có sourceSHA, UTC, PID, world/context/type, net mode, pawn/controller/owner/roles, mesh và anim class. Đây là input fixture, tách khỏi input Windows của video. Kết quả:

| Phép đo với animation | Kết quả |
|---|---:|
| Đi ổn định10s | 5000,000260770cm |
| Sprint ổn định10s | 7000,000365078cm |
| Apex dt1/30s | 119,987106204cm |
| Apex dt1/60s | 119,987106189cm |
| Apex dt1/120s | 119,994960187cm |
| Gravity | −980cm/s² |
| Root pose drift trong chu kỳ locomotion | 0,000000000cm |
| Sai lệch vị trí SwordRoot với socket | 0,000000000cm |
| Biên thay đổi xương tay/chân khi đi ổn định | 72,493673 /106,318791cm |
| Biên thay đổi xương chân khi sprint ổn định | 91,656429cm |

Các biên xương chứng minh pose chạy qua nhiều frame, không là phép đo foot sliding. Test còn kiểm idle/move/jump/fall/land/idle, không kẹt landing, rời mép không jump-up giả, capsule42/96cm và kiếm không collision/physics. Bước tích phân1/30–1/120s **không phải FPS render đã đo**.

## Windows và input thật

Package cuối `Artifacts/U01/D/Package-20261104-144914-755-2b8e3bc6/Archive/Windows`, BuildCookRun exit0; cook summary0 error/0 warning. Giữ đủ48 file; hash từng file ở [D-ARTIFACTS.csv](Evidence/D-ARTIFACTS.csv). Smoke `SmokeB-20261104-145341`: Boot/CharacterCombatLab/NetworkLab **3/3 PASS**, exit0, lab PID4592/17960 có sourceSHA và mesh/AnimBP D đúng. NetworkLab ở smoke là standalone, không phải kiểm mạng F.

[Video D27 giây](Evidence/D-PLAY.mp4), [ảnh đi](Evidence/D-WALK.png), [sprint](Evidence/D-SPRINT.png), [nhảy](Evidence/D-JUMP.png), [tiếp đất](Evidence/D-LAND.png). Video gốc và log tại `Artifacts/U01/D/PlayCaptureFinal`; bootstrapPID14268, gamePID**22692**, HWND/đường dẫn exe/hash được khóa trước input. CaptureDPlay dùng **Win32 SendInput** cho click Reset/Resume, W/Ctrl/Space/Escape và mouse delta; dừng nếu mất foreground, nhả phím trong finally. Không gọi AddMovementInput để thay input trong video. Log nhận PhysicalPress accepted=1 và reset đúng fixture Runway/Ledge.

27,0036s, 270 frame ở10Hz, có18 frame lặp để giữ thời gian thực khi capture chậm; **10Hz không là FPS của game**. D-RESULTS giữ137 samples đúng Game world/type1, net mode0, owned local pawn và source7152384. Đoạn đi/sprint ổn định trong log đúng500/700cm/s; đủ pose indices0–4. Ở fixture Ledge, log ghi fall với velocityZ âm rồi land, không jump-up; sau đó trở lại idle. AI đã xem các ảnh mẫu pose và attachment, video dành cho người review đánh giá chuyển động/trượt chân. Chưa tự đánh dấu xác nhận thẩm mỹ hoặc toàn bộ checklist người dùng PASS.

## Lịch sử lỗi và giới hạn

1. Compile đầu lỗi API extraction context/FindFProperty/TObjectPtr; Game build kế tiếp lỗi accessor chỉ có trong Editor. Đã sửa, các log Build-* lỗi vẫn giữ; không đổi compiler/engine hoặc bỏ test.
2. Authoring đầu `Authoring-20261104-142401` báo FK rig bản sao còn bound SK_Mannequin. Giữ file lỗi trong PreservedAssets, sửa binding chỉ nested rig bản sao; authoring sau `Authoring-20261104-142947` SUCCESS. ConditionalPostLoad import-data warnings của lần duplicate còn trong log, không che lỗi binding.
3. Source07fbb3e đạt14/14 tests ban đầu nhưng **video PlayCapture/Run3 phát hiện pose locomotion đứng cứng**: thiếu dữ liệu nội suy đã bake của BlendSpace. Lượt này bị loại, không dùng làm bằng chứng đạt. Bổ sung assert lấy sample runtime và chu kỳ xương ở tốc độ ổn định; `MCPTests-20261104-144514` chạy asset cũ đạt12/14, đúng hai test AssetPolicy/TransitionsAndAttachment FAIL. Sau ResampleData/save,7152384 cold-load đạt14/14 và video mới có locomotion. Lịch sử này giữ trong manifest, không suy thành kiểm chứng hình ảnh từ lượt PASS cũ.
4. Capture setup Run1 lỗi BOM trước input; Run2 từ chối foreground trước input. Dùng attach input queue một lần lúc startup để xin foreground; trong lượt ghi vẫn abort khi mất focus, không giành lại focus liên tục. Capture cuối hoàn tất.
5. Compiler14.51 mới hơn preferred14.50 và C4996 engine header còn; smoke giữ optional profiler DLL/audio diagnostics đã phân loại theo validator B. Không thay renderer để làm số đo đẹp. Python/toolset init ở đường Editor executable -game/-server từ A vẫn để xử lý trước F/tích hợp; D không giả báo đã sửa tồn tại đó.

Editor gốc vẫn mở **PID19924**, MCP summary Boot/0actor. Marker LogPython mới UTC07:56:22.230 xác nhận project gốc. **Chưa xác nhận nạp native B/C/D mới trong Editor gốc**; reflection/layout mới cần cold build/restart trước khi dùng lớp mới ở đó. Không yêu cầu đóng Editor để khép C, build clone hoặc bàn giao package D.

Art anime **DEFERRED**. Chưa chạy E/F/G, Server packaging, mạng hai client, các mức FPS render30/60/120 hoặc phiên10 phút của G. Chưa có damage/combo/né/đỡ/skills/AI chiến đấu. Không đổi luật Description.

## Bàn giao

Chạy `Artifacts/U01/D/Play-D.cmd` để vào Boot của đúng package7152384, chọn CharacterCombatLab; local logs/settings ở `Artifacts/U01/D/Review`. Có thể sao chép nguyên thư mục Windows48file sang máy khác. [Checklist review D](D-MANUAL-CHECKLIST.md) chỉ còn xác nhận chuyển động/foot sliding và trải nghiệm kiếm trên package. Source/binary/video hashes, đường dẫn log và lỗi lịch sử ở [D-MANIFEST.json](Evidence/D-MANIFEST.json). D được push riêng để review, main giữ868df83; chờ người dùng nghiệm thu trước merge/chuyển E.
