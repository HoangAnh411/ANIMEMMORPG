# U01-B — Camera, chuột và menu/focus tối thiểu

Trạng thái hiện tại: **ĐÃ NGHIỆM THU U01-B theo xác nhận người dùng tại `2e0e89fdffd05b9dad86014fb3cb8ac0338ba60d`**. Checklist package ghi PASS theo xác nhận người dùng trong giao việc tiếp theo, không phải AI đã chạy input/video. Trước xác nhận này AI chỉ kiểm build/tests/smoke; không có xác nhận trước đó của AI rằng toàn checklist thực đã đạt. Không bổ sung video, thời điểm chơi, PID hoặc số đo chưa được cung cấp. Editor gốc **chưa được xác nhận nạp code B mới nhất**; giữ lịch sử lỗi Live Coding bên dưới. Người dùng cho phép commit/push hồ sơ rồi fast-forward B vào main và triển khai riêng C; không cần đóng Editor để khép B.

## Nguồn và phần triển khai

Ngày 2026-11-04 +07. Người dùng nghiệm thu A tại `4216ff874872f5d7112cc792b52d008937441f7c` và giao fast-forward/push main rồi làm riêng B. Đã thực hiện đúng; B xuất phát từ SHA này. Source build/package cuối: **`b6cf1ebfdfd34a4dbfcdb52c1507401a3096ef00`**, đã push trước build. Các commit tài liệu sau source này không thay binary/asset. Xem [manifest](Evidence/B-MANIFEST.json), [hash artifact](Evidence/B-ARTIFACTS.csv) và [checklist input](B-MANUAL-CHECKLIST.md).

Giữ runtime module; không sửa template/variant, Description hoặc project renderer/plugin/config. B thêm AU01Character kế thừa ACharacter, UU01CharacterMovement (chỉ control lock B; luật sprint/coyote/buffer C và saved move F chưa làm), AU01PlayerController, UU01Menu và hai tests policy. Dependencies tối thiểu SlateCore/ApplicationCore/Json và user32.lib trên Win64 phục vụ UI/focus/metrics. Không GAS/module mạng/framework action mới.

Nội dung dưới `/Game/AnimeMMORPG/U01`: bốn Blueprint (Character, Controller, GameMode, widget) và mười input asset (chín IA + IMC). Hai map lab đổi riêng GameMode sang BP_U01LabGameMode; Boot/ba widget Boot và template giữ nguyên. Character dùng Manny Simple và AnimBP nguồn tạm; AnimBP riêng/in-place/foot sliding/kiếm thuộc D, art anime **DEFERRED**.

Camera do local controller nhận MouseX/MouseY trực tiếp, không nhân DeltaSeconds. Yaw/pitch ngắm tách thân, pitch −70…+60; FOV90; pivot tâm capsule+Z70, arm350, vai±45 và đổi0,15s. Hai sphere sweep radius12 trên Camera channel, ignore pawn sở hữu; thu vào ngay, hồi ra FInterpTo speed8 rồi sweep lại. Owner-only mesh/attachment ẩn dưới80 và hiện trên100. Không body yaw khi đứng, không tự recenter khi chạy, không camera RPC.

Gameplay vào GameOnly/cursorẩn/permanent capture; Escape mở UIOnly/menu/cursorhiện, không Escape-to-Resume, không SetPause. Resume chỉ khi window active. Mất application/window activation vào AwaitingResume, return focus không tự Resume. Khóa xóa input engine và move/jump intent, dừng XY/acceleration nhưng vẫn PerformMovement/gravity. Slate preprocessor quan sát physical down/up trước UMG, quarantine phím giữ/nhấn khi khóa. Khi active, Win32 GetAsyncKeyState high bit xác minh phím thực đã nhả (kể cả KeyUp mất khi background); không lấy PlayerInput đã flush để giả release. Không gọi lại input cũ khi Resume. Backend OS/focus vẫn phải kiểm bằng thao tác thật.

Menu B có Resume, hướng dẫn phím, Back to Boot, Quit; chưa màn hình settings/rebind E. Controller non-local/dedicated return trước CreateWidget, Slate observer hoặc mapping registration. EndPlay gỡ widget, observer, activation delegate và đúng context riêng. Guard này được review source/compile; test server hai client F chưa chạy trong B.

Hai lab thêm ba fixture camera, giữ nền/thước/spawn U00: wall center(600,0,150), size(20,800,300)cm; corner center(400,400,150), size(400,20,300); overhang center(−550,200,220), size(400,400,20). Chưa mở rộng sân motor C. Reset fixture/G/Interacting/Defeated và settings E chưa triển khai.

## Kiểm chứng và bằng chứng

Clone GitHub độc lập: `Artifacts/U01/B/Source`. Đã LFS fsck OK; 765 asset baseline ban đầu, sau B thêm14; 16 binary đổi/thêm được LFS upload. Clone được fast-forward tới từng SHA đã push trước build, giữ log thất bại và các snapshot cũ. Không clean cache; dùng cùng engine/DDC toàn máy, không tuyên bố môi trường build trắng. Config clone sinh token sau mở Editor, giữ ngoài index như project gốc.

UE5.8.4 CL58902052 tại D:/Software/UE_5.8. UBT thực chọn MSVC14.51.36260 (folder14.51.36231), WindowsSDK10.0.26100.0, Win64 Development. Không cài/nâng engine/plugin. Binaries Editor/Game/full package lấy từ đĩa, không lấy patch Live Coding làm bằng chứng tái lập.

| Kiểm tra | Kết quả | Bằng chứng/phạm vi |
|---|---|---|
| Build Editor/Game source cuối | PASS | `Build-20261104-012408-914-500b8600`, hai result ExitCode0/Succeeded |
| Cook/package source cuối | PASS | `Package-20261104-012443-320-f0ad4b72`, ExitCode0/BUILD SUCCESSFUL; cook0errors/0warnings |
| Asset creation/compile | PASS | `CreateAssets2.log` U01B_ASSETS_SUCCESS, bốn Blueprint status up-to-date; B-Assets.json; không save asset gốc bằng patch class |
| Automation source cuối qua MCP clone | PASS 6/6 | MCPTests-20261104-012551: sáu Success, queue6 hoàn tất, đúng source/PID trong manifest |
| Smoke package source cuối | PASS 3/3 | SmokeB-20261104-012550: ba map tải/exit0, không Error/Fatal/AccessedNone; hai lab mỗi bên39metrics, đúng source/Game world/pawn local; chưa input thật |
| Chuột thật/capture/đổi vai sát tường/mesh hide/Alt-Tab/Resume/held keys/gravity khi menu | PASS theo xác nhận người dùng | Áp dụng package B đã bàn giao; không phải AI thao tác input, không có video/PID/giờ chơi mới được cung cấp |
| Server riêng hai client B/F, speed/apex/sprint/rebind/animation riêng/FPS | NOT-RUN | Ngoài B hoặc đợt sau; không kế thừa PASS mạng A |

Để chạy full build/package: `Scripts/U00.ps1 -Task Build` rồi `-Task Package`, project/output tuyệt đối như manifest. Script guard đối chiếu đúng project đang mở, cho clone khác chạy; không đóng Editor gốc. `Scripts/U01/CreateBAssets.py` chỉ chạy trong clone đã build, từ chối original/overwrite; tạo/lưu asset qua Editor API. Asset được copy về source, commit/push rồi đối chiếu clone đúng SHA trước package.

Tests trên binary clone dùng `Scripts/U01/VerifyBTests.ps1`: mở Editor clone với `-ModelContextProtocolStartServer -ModelContextProtocolPort=18012`, khởi tạo session MCP HTTP; `call_tool` TestRunner.run_automation_tests filter AnimeMMORPG; poll Logs.GetLogEntries mới rồi chỉ QUIT_EDITOR qua endpoint đó. Sáu tên: U00.Foundation.Axes/CallOrder/HalfOpenInterval/Units, U01.B.CameraPolicy/ReleaseGate. Tests B kiểm clamp/tổng mouse delta, thu camera ngay/hồi ra có giới hạn và release/quarantine độc lập; không giả test OS/UMG/collision bằng policy test.

`Scripts/U01/SmokeB.ps1` mở executable thật, DX12 cấu hình hiện có, 1280×720 windowed, log/UserDir riêng, sourceSHA và U01Trace; Boot console Quit, hai lab auto-exit sau8s bằng fixture. Metrics lấy từ pawn Game/PIE sở hữu, reject Editor/Preview/không pawn, sample sau UpdateCameraManager frame hiện tại. Có PID/world/type/context/net mode/local player/pawn/controller/owner/role, camera/aim/FOV/capture/state. Exe/module/log hash nằm sidecar manifest. Không dùng Editor world hoặc bootstrap PID thay game PID. Không gọi input/teleport để giả pass camera/UI.

Smoke cuối: game PID16092 (Character) và13100 (Network), WorldType1=Game, NetMode0=Standalone, localPlayers1, owner đúng BP_U01Controller. Camera không cản tại điểm spawn: khoảng pivot352,881cm = arm350 cùng lệch vai45; FOV90, sweep12. AwaitingResume/controlState2, cursor hiện, captureNoCapture; world clock vẫn tới8,0007/8,0065s. Đây là số đo startup/menu của smoke hidden, không phải bằng chứng Alt-Tab bằng tay, gravity khi đang rơi, camera va tường hoặc input đã đạt. Sau kiểm chỉ còn Editor gốc19808; raw log/hash và mẫu đầu/cuối trong manifest. Kiểm cuối git diff/check và quét credential chỉ trên tập tài liệu stage, không đưa Config local vào commit.

## Lịch sử lỗi và giới hạn

- Compile đầu tại source827f551 thất bại C4458 (`Children` tại U01Character.cpp:90; `Character` tại U01PlayerController.cpp:133 và các chỗ tương tự) và C3535/C2440 unwrap TObjectPtr tại controller:213/226. Sửa tên biến và `.Get()` ở6457d28; giữ LiveCoding-Initial.log và Build-20261104-005806-734-494122ad. Clone lúc đầu clone trúng SHA trước sửa nên full build thất bại cùng lỗi, không tính PASS.
- CreateAssets lượt1: `TypeError: call() takes at most 0 arguments (1 given)` ở CreateBAssets.py:56 (`unreal.Key(key)`). Sửa Key() + set key_name; lượt2 có marker thực và saves thành công. Process exit0 riêng không được tính thành công Python.
- Smoke lượt đầu dùng regex `Failed to load` quá rộng, báo fail vì aqProf/VtuneApi/VtuneApi32e/WinPixGpuCapturer DLL tùy chọn và SoundConcurrencyObject mặc định. Giữ results.json ban đầu; validator sửa chỉ phân loại đúng các thông báo cụ thể, giữ chúng trong optionalDiagnostics và vẫn fail các lỗi/missing game content khác. Reparse log cũ ghi validated-results.json riêng, không ghi đè lịch sử; smoke snapshot source cuối chạy lại bằng validator đã sửa.
- MCP clone test lần đầu thiếu `-ModelContextProtocolStartServer`, chỉ có port nên không có listener, không chạy tests; giữ MCPTests-20261104-010747. Xác minh source engine ShouldAutoStartServer rồi thêm cờ đúng. Chỉ dừng PID13456 sau đối chiếu commandline project/log của lượt đó; Editor gốc19808 không bị tác động. Các lượt sau dùng MCP thật và clone tự QUIT_EDITOR.
- MCP Live Coding có thành công ở17:58:21UTC (kèm cảnh báo data type) và18:13:31UTC (`Live coding succeeded`). Hai lượt bổ sung Win32 physical release không link được patch: `error LNK2019: unresolved external symbol __imp_GetAsyncKeyState` và `fatal error LNK1120: 1 unresolved externals` tại patch_2.exe, lần cuối18:23:21UTC. Giữ `LiveCoding/FinalAttempt.log`. Đã khai báo user32.lib; full build Editor/Game thành công, nhưng **không khẳng định patch cuối áp vào Editor gốc** và không lặp compile để che lỗi. Header/reflection mới cần full build và một mốc restart nếu muốn dùng class/asset B trong Editor gốc; lượt này tạo asset bằng clone, bàn giao package độc lập, không yêu cầu người dùng đóng Editor.
- Compiler mới hơn preferred14.50.35717 và C4996 engine headers vẫn tồn tại, không sửa engine/tắt warning. Cook summary0/0 không có nghĩa toàn startup log không có diagnostic. B không giải quyết Python ToolsetDefinition/AgentSkill/PythonTestRunner khi chạy Editor executable -game/-server từ A; còn phải xử lý trước tích hợp và kiểm lại F. Packaged runtime smoke được kiểm riêng, không suy thành lỗi server đã hết.
- Boot smoke snapshot đầu mất khoảng87s để shutdown, exit0, không gọi là phép đo FPS; có timeout120s giữ process để inspect thay kill tùy tiện. Các snapshot cũ còn trong Artifacts, không phải bản chơi thử bàn giao cuối.

## Chơi thử và bàn giao

Mở `Artifacts/U01/B/Play-B.cmd` để vào Boot bằng package cuối, bật trace và lưu Review/Game.log riêng. Exe thật và SHA256 nằm manifest; giữ nguyên toàn thư mục Windows48file khi sao chép. [Checklist gộp](B-MANUAL-CHECKLIST.md) đã được người dùng xác nhận PASS khi nghiệm thu2e0e89f. Phần NOT-RUN và giới hạn input của các lượt AI tự động vẫn là lịch sử đúng; kết quả thủ công hiện tại chỉ dựa trên xác nhận người dùng, không tạo thêm bằng chứng.

Files: Source/AnimeMMORPG/U01/*, Tests/U01CameraTests.cpp, AnimeMMORPG.Build.cs; 14asset U01 + hai lab; ba script B; ROADMAP/REPORT-A (ghi nghiệm thu A), báo cáo/checklist/evidence B. Config token local, Binaries, Intermediate, Saved, raw log/build/package đều ngoài commit. Không git add toàn bộ repo. Description/Boot/template không đổi trong commit.

Quy trình bàn giao B ban đầu đã dừng, không merge tại2e0e89f. Giao việc tiếp theo của người dùng cho phép khép tài liệu, push và fast-forward B vào main rồi tạo nhánh C riêng từ main đã merge. Art anime vẫn DEFERRED; không nghiệm thu U01 kỹ thuật tổng hợp/mạng F/Server packaging hoặc sản phẩm anime.
