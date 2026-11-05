# U01-F — Dedicated Editor server và hai client

**READY_FOR_REVIEW; chưa nghiệm thu hoặc merge F.** E được người dùng nghiệm thu tại `cb46c520469807004b101c1b98ac4bdfdad70d84`, package nguồn `c8df4ff2182c0006c11f65466ecec4b9223be5a3`. Hồ sơ E đã cập nhật, commit/push và fast-forward main tại `99363222895b0069b3afdab2b103bfc81c68af6b`. Nhánh `u01/f-network` bắt đầu từ main đó.

Nguồn native/build/package F: **`df897f6088da4cca423085e9fe8e9c2869c98420`**, đã push trước khi build clone riêng. [Manifest](Evidence/F/MANIFEST.json), [kiểm chứng runtime](Evidence/F/CHECKS.json), [checklist review](F-MANUAL-CHECKLIST.md). Commit hồ sơ sau nguồn này không thay binary. Art anime/animation chiến đấu **DEFERRED**; carry một tay D vẫn là tư thế tạm cho blockout.

## Triển khai

`U01NetworkMovement.cpp` dùng saved move và CMC prediction/replication sẵn có. Compressed flags mang sprint intent, jump-held và control gate; server dựng cạnh nhảy theo movement clock đã được CMC chấp nhận. Không nhận tốc độ tùy ý hoặc timestamp nhảy tùy ý từ client. Replay khôi phục snapshot cửa sổ nhảy/lock/sprint; không combine qua thay đổi intent. Server tắt client-authoritative position và không bỏ kiểm tra correction. Motor C vẫn 500/700 cm/s, jump 120 cm, coyote/buffer nửa mở 0,10 s.

GUID pawn do server cấp và replicate; sprint replicate cho simulated proxies. AnimInstance của simulated proxy đọc vận tốc trong replicated movement packet để trình bày nhảy/rơi, thay vì vận tốc extrapolation có thể bỏ qua pha lên. Owner/authority giữ velocity thực. Không sửa clip, skeleton, grip/carry, template hoặc luật motor; animation không dịch chuyển capsule.

`U01NetworkProbe` chỉ opt-in Development/Game-world, ghi mỗi 0,2 s world/context/PID/net mode/local players, ownership/role/GUID, vị trí/vận tốc, pose và correction. Fixture tạo nền kiểm tra replicated từ server; reset đặt vị trí chỉ là lệnh sân thử rõ ràng, không thay replication locomotion bằng teleport. Các probe speed/jump/foreign-pawn là fixture Development, không phải API gameplay hoặc RPC mỗi frame. Camera/UI/settings vẫn local; dedicated không tạo UI.

Các file thay đổi gồm Character, MotorPolicy, PlayerController, AnimInstance; thêm NetworkMovement, NetworkProbe, NetworkTests và scripts StartFSession/CaptureFPlay/VerifyFTests/RecordF/ReviewF/StopFSession. Xem git diff từ base để đối chiếu đầy đủ; không có module mạng/GAS/plugin mới.

## Build, tests và package

UE **5.8.4 CL58902052**, MSVC **14.51.36260**, toolset **14.51.36231**, Windows SDK **10.0.26100.0**. Cold clone `Artifacts/U01/F/Source` đúng SHA trên. Editor và Game build exit 0 tại `Build-20261105-120525-295-b4be0b5d`. Không lấy Live Coding làm bằng chứng; native/reflection mới cần full build và restart khi muốn nạp vào Editor gốc. Editor gốc **PID2068 vẫn mở**, chưa xác nhận nạp F, không dùng làm bằng chứng Game world; token/config local không commit.

MCP TestRunner trong cold Editor **PID7304**, `MCPTests-20261105-120700`: **23/23 Success**, đọc log mới đến queue empty 23 tests performed. [Danh sách/log đo](Evidence/F/AUTOMATION.json):

| Nhóm | Tests thực chạy |
|---|---|
| U00 Foundation (4) | Axes, CallOrder, HalfOpenInterval, Units |
| B (2) | CameraPolicy, ReleaseGate |
| C (5) | FlatMovement, JumpPhysics, JumpWindows, MotorLocks, Terrain |
| D (6) | AnimatedMotor, AssetPolicy, CarryTrajectory, GripIsolationAndAttachment, LandingTransitions, TransitionsAndAttachment |
| E (4) | BindingValidation, LocalMappingIsolation, PartialRecovery, SaveAndFailure |
| F (2) | SavedMoveReplay, ProxyAnimation |

SavedMoveReplay kiểm flags/combine/replay, jump windows, authority lock/speed và correction dù không còn saved move để replay. ProxyAnimation dùng pawn/mesh/AnimBP thật trong Game fixture: packet velocity quyết định pose proxy, owner/authority vẫn dùng movement thực; không đổi capsule. C/D regression đo lại walk **5000,000261 cm/10 s**, sprint **7000,000365 cm/10 s**, apex nằm trong ngưỡng **120±5 cm** đã nghiệm thu; toàn bộ số đo có trong AUTOMATION.json. Fixture clock không phải chứng nhận FPS renderer.

Package Windows Development: `Package-20261105-120856-201-0ffc4cbc/Archive/Windows`, BuildCookRun exit 0; [digest 48 file](Evidence/F/PACKAGE.csv). Smoke package `SmokeB-20261105-121748`: **Boot, CharacterCombatLab, NetworkLab 3/3 PASS**, exit 0 [SMOKE.json](Evidence/F/SMOKE.json). Đây là Game package smoke; **không build/nghiệm thu packaged Server target**.

## Phép thử mạng thật

Run `Session-20261105-120906`, localhost bình thường. [Process inventory](Evidence/F/PROCESSES.json) có executable/arguments/userDir/log/source/UTC. Server **PID5940**, A **10840**, B **13956**, B reconnect **8616**. Cả ba chạy UnrealEditor.exe riêng: server `-server`, hai client `-game`; không listen-host PIE. Native collector xác nhận Game world type 1, server net mode 1, client mode 3; dedicated có **0 local player, 0 menu**, mỗi client một autonomous pawn và remote simulated pawn.

| Pawn | Server GUID |
|---|---|
| A | C5796E1B4190B2A1CEDF52BB0F6DB9F2 |
| B cũ | 1720536F49D66975EFCA93B07C535416 |
| B reconnect | 23AAC0F3444C214114FF0CA62FA502F4 |

Input Win32 SendInput thật, có kiểm HWND/PID/foreground và metadata UTC, quay đồng thời hai client. NormalA chứng minh đi/nhảy, Ctrl edge ở lần đó không được quan sát thành sprint; **sprint A lấy từ AttacksSettingsA trước probe** (cả server/owner/observer đạt 700). NormalB và ReconnectBOnRunway có walk500/sprint700/jump. Các bên trở về grounded/idle, vị trí dừng khớp authority trong 5 cm; pawn còn lại không bị điều khiển. Observer có jump/fall/land trong AttacksSettingsA. Không gán PASS cho lần input thiếu edge.

Speed fixture thực sự đẩy dự đoán client vượt giới hạn: **904,831 cm/s**, trong khi authority toàn phiên không vượt **700 cm/s**, correction A tăng **3→13**; claim 2000 bị reject. Probe thêm jump trên không bị reject tại falling/count1; correction **1→3**, server không có lần lên thứ hai, apex vẫn trong motor bound. Target GUID pawn khác bị reject theo ownership. [Server events](Evidence/F/Server-events.log), JSON/video SpeedA và AttacksSettingsA ghi cả input, dự đoán và authority; không chỉ dựa vào một dòng reject RPC.

Menu A không pause server hoặc B: B tiếp tục sprint trong MoveQuitB, A đứng yên. A lưu Forward=H, sensitivity≈1,962; B và B reconnect vẫn W/1,0, mỗi bên một mapping context [SETTINGS.json](Evidence/F/SETTINGS.json). UserDir/log riêng. B Quit qua UI, server còn đúng A một pawn; reconnect tạo GUID mới, cuối phiên đúng A+B mới hai pawn, không GUID B cũ. Test processes đã dừng bằng kiểm tra PID/project/userDir, Editor gốc giữ mở.

## Python/toolsets và lịch sử

Đã tái hiện lỗi A không mitigation tại `PythonBefore-20261105-105711` (nguồn 97400db): cả server/client A/client B đều có ba AttributeError liên quan ToolsetDefinition, AgentSkill, PythonTestRunner — editor-only reflected types. Đối chiếu engine PythonScriptPlugin.cpp xác nhận flag **`-DisablePython`**. Launcher runtime dùng flag đó; phiên F cuối không AttributeError, Accessed None hoặc Blueprint Runtime Error. Cold Automation Editor vẫn bật Python/MCP. [PYTHON-REGRESSION.json](Evidence/F/PYTHON-REGRESSION.json). Lỗi đường chạy không flag vẫn được ghi nhận; không tuyên bố đã sửa engine/plugin hoặc editor toolsets chạy được trên server.

Giữ artifacts/log lịch sử: compile declaration/alias fixes trước 97400db; readiness ban đầu nhầm Zen listening nên không tính PASS, đã dùng IpNetDriver; throttle ini ban đầu sai file, sửa thành override EditorSettings từng process; nền fixture movable tạo local riêng gây proxy Falling, sửa replicated server base tại 0166d6f; proxy animation velocity sửa b1c3ed0; Space quá ngắn có thể lọt trong cùng frame chậm, phép thử normal giữ thật 0,6 s, không đổi jump law. Counter cũ chỉ đếm replay bỏ sót correction không saved move; df897f6 đếm received adjustment và kéo speed probe 2 s để đo actual correction. Không bỏ test để qua cổng.

## Bằng chứng và giới hạn bàn giao

Video trong Evidence/F giữ hai vùng client 900×540, chỉ bỏ khoảng desktop giữa chúng; giữ frame order/duplicate timing frames và cảnh báo trong game, không nội suy. Metadata từng case ghi capture Hz thực, raw/export SHA; encoder 30 Hz không phải FPS game. Máy báo vượt VRAM khi giữ Editor gốc và hai rendered client; renderer giữ nguyên. Không dùng video để nghiệm thu độ mượt/FPS tích hợp G. [Manifest](Evidence/F/MANIFEST.json) ghi Hz thực từng video; [EVIDENCE.csv](Evidence/F/EVIDENCE.csv) khóa digest.

Mở `Artifacts/U01/F/Play-F.cmd` để review lại server + hai client từ clone đúng source. Launcher đã smoke thật tại `Reviews/Session-20261105-122649` (server3696/A18608/B14760), readiness đạt, cleanup kiểm identity đúng; script PowerShell/Python syntax PASS. [Checklist ngắn](F-MANUAL-CHECKLIST.md) chỉ còn cảm giác/quan sát người dùng; kiểm chứng tự động và input tool đã hoàn tất. F chỉ localhost, chưa latency/loss/jitter/U05, chưa Server packaging, chưa G hoặc U02. **Không merge F cho tới nghiệm thu.**
