# U00-E — Ba map và menu thử nghiệm

Trạng thái: BLOCKED kiểm chứng runtime còn thiếu. Nền 743bfaa0391b5434918da1f25aae2266a37eb8fb; nhánh u00/e-maps. Không merge, chưa bắt đầu F, không tuyên bố U00 tổng thể đạt.

## Triển khai đã lưu

Tạo bằng API Unreal Editor qua MCP, không chỉnh binary bằng text hoặc thêm C++/plugin. Engine hiện chạy 5.8.4; instance xác nhận bằng Python os.getpid là 14544, project path đối chiếu D:/Data/AnimeMMORPG/AnimeMMORPG.uproject. Thời gian lượt E: 2026-11-03 khoảng 13:52–14:12 +07:00 (log UTC 06:52–07:12).

- Maps/L_Boot: map trống, override BP_BootGameMode, pawn None; BP_BootController tạo WBP_BootMenu ở BeginPlay, cursor visible, UI-only. Ba nút Character/Network/Quit dùng OpenLevel(byObjectReference) và QuitGame, không pause world.
- Maps/L_CharacterCombatLab: sàn 40x40m, DirectionalLight/SkyLight, PlayerStart, hai thước có nhãn; BP_CharacterLabGameMode và BP_LabController kế thừa Blueprint template, giữ pawn/input.
- Maps/L_NetworkLab: sàn 20x20m, ánh sáng, PlayerStart A/B với nhãn; BP_NetworkLabGameMode và BP_NetworkController kế thừa template. WBP_NetworkOverlay là biến thể của overlay sân nhân vật.
- UI/WBP_LabOverlay và WBP_NetworkOverlay: tên sân và nút Về menu; Game-and-UI, cursor visible, không hide cursor khi capture. Camera/input là template cho phép thử U00, không nghiệm thu U01; không host/join/combat.

Tổng 12 binary mới: 3 map, 6 Blueprint GameMode/Controller, 3 widget Blueprint. Chỉ trong Content/AnimeMMORPG. Blueprint BeginPlay tạo menu một lần mỗi controller/world; không persistent UI subsystem. Tham chiếu map rõ ràng, giữ nguyên map/source template.

Map tạo bằng EditorLevelLibrary.new_level → LevelEditorSubsystem.NewLevel với bIsPartitionedWorld mặc định false (header engine LevelEditorSubsystem.h:147); không bật World Partition hoặc tạo ExternalActors cho map mới. Phép đọc world_partition bằng Python không được expose, đã ghi lỗi khảo sát thay vì suy thành kiểm chứng runtime độc lập.

Config/DefaultEngine.ini chỉ đổi hai startup/default map sang L_Boot; token local không stage. Config/DefaultGame.ini thêm PackagingSettings, ClearArray MapsToCook rồi liệt kê đúng ba map E. Không sửa renderer/plugin list. Dependencies cook theo tham chiếu. Scripts/U00/CreateLabs.py, FinalizeLabs.py, MeasureLabs.py là script tác nghiệp đã dùng trong Editor, chỉ tác động asset E; không phải framework. MeasureLabs có sửa góc Sun/nhãn trước đo, không phải script read-only. Không chạy lại script tạo trên asset đã tồn tại.

## Kiểm tra và số đo

Đọc AGENTS/Description/ROADMAP/REPORT-D trước làm. Discover list_toolsets và schema Scene/Asset/Blueprint/Object/UMG/Slate/TestRunner/EditorApp/Logs; tool runtime vẫn có nhóm aggregator từ phiên cũ, không dùng làm bằng chứng dependency sau restart. Console execute_console_command đã chứng minh gọi được Python trong Editor; không dùng ProgrammaticToolset như Python tùy ý.

| Phép kiểm, phương thức | Kết quả |
| --- | --- |
| Dirty map/content trước tạo/đổi map | Ban đầu cả hai rỗng; guard dừng một lần khi WBP_BootMenu dirty. Chỉ lưu widget E đó rồi chạy lại. Không lưu/discard package ngoài E |
| Compile Blueprint/widget qua write_graph_dsl, CompileWidgetBlueprint và BlueprintEditorLibrary.compile_blueprint | PASS 9/9 Blueprint status BS_UP_TO_DATE; không sửa template |
| AssetRegistry hard/soft dependency /Game của asset E | PASS missing list [] |
| Startup/cook | Cấu hình file đúng Boot và đúng ba MapsToCook; chưa restart Editor để kiểm startup mới; Editor đã load Boot qua thao tác tạo/đổi map |
| GameMode override từng map | PASS đo từ world settings, ba GameMode riêng đúng tên |
| PIE Boot | PASS world UEDPIE_0_L_Boot, pawn None, widget_count 1 |
| PIE từng sân | PASS BP_ThirdPersonCharacter; Character spawn (0,0,92.150003) cm; Network spawn ở X=+250 hoặc -250, Y=0, Z=92.150003 cm; một overlay/world |
| Đường nút UI 3 vòng mỗi tuyến | PASS cho activation bàn phím: focus chính nút UMG rồi Slate PressKey Enter, qua OnClicked; không gọi console Open/broadcast delegate. Character→Boot và Network→Boot đủ 3 lần, widget_count mỗi sân 1 và Boot cuối 1 |
| Click chuột thực qua Slate Click | CHƯA ĐẠT độ tin cậy: tool trả true nhiều lần nhưng không chuyển map; có lần chuyển sau chọn cửa sổ/focus. Không dùng các lượt bàn phím để tuyên bố chuột đã đạt; nút quay lại bằng chuột vẫn là cổng còn thiếu |
| Di chuyển input template sân Character | PASS hạn chế: SetFocusToGameViewport, Slate W taps; X từ 0 tới 7.406345 cm, Z giữ 92.150003; không gọi AddMovementInput/teleport. Không đo tốc độ U01 |
| Di chuyển input sân Network | NOT-RUN, không suy từ sân Character |
| Quit trong PIE bằng nút Thoát | PASS activation nút UMG + Enter, IsPIERunning false; không gọi Quit console trên Editor |
| Standalone thật | Đã launch qua menu Play Standalone Game, PID 19152, command line -game -Multiprocess đúng project/Boot. Log LoadMap Boot. Hai tuyến UI, input và Quit bằng nút trong tiến trình riêng CHƯA KIỂM CHỨNG |

Số đo numeric từ actor Transform và bounds, lưu Artifacts/U00/E/map-measurements.json:

- Floor Character: center Z=-50, scale (40,40,1), bounds 4000x4000x100 cm → mặt trên Z=0.
- Floor Network: center Z=-50, scale (20,20,1), bounds 2000x2000x100 cm → mặt trên Z=0.
- Ruler_1m: cube 100cm, scale (1,.1,.1), bounds X=100 cm.
- Ruler_10m: scale (10,.1,.1), bounds X=1000 cm.
- Network PlayerStart A=(-250,0,110), B=(250,0,110) cm; khoảng cách 500 cm, nhãn A/B. Character Start=(0,0,110). Capsule settle runtime trên mặt sàn như bảng; không rơi xuyên sàn trong các lượt quan sát.

## Lỗi, sửa và giới hạn giữ lại

1. Khảo sát Python gọi WidgetBlueprint.new_variables / unreal.WidgetBlueprintLibrary / controller.player / world.world_partition không expose hoặc protected; giữ log lỗi. Dùng unreal.WidgetLibrary đúng API và world PIE thật cho phép đọc runtime. Không dùng tool pawn metrics cũ từ Editor world.
2. Rotator positional ban đầu đã làm Sun roll -45 thay pitch -45, ảnh tối. Đã sửa script và map E sang tham số tên pitch=-45,yaw=-30,roll=0, đổi hướng nhãn, save/đo lại. CharacterLitPIE là ảnh sau sửa; ảnh đầu giữ làm fail evidence.
3. Log có lỗi InputMode:UIOnly focus vào UserWidget không focusable. Sửa BP_BootController bỏ InWidgetToFocus, vẫn UI-only/cursor visible. Lưu lần đầu fail sharing violation 32 khi Standalone giữ asset; log sau đó 07:07:11 UTC xác nhận SavePackage và kiểm cuối save_assets true. Bản sửa đã lưu nhưng chưa chạy lại vòng UI/Standalone đầy đủ sau sửa focus; không tuyên bố hết lỗi runtime cuối cùng.
4. UI-route polling ban đầu bị stale refs/timing; lưu kết quả bàn phím có snapshot chuyển sân, không dùng Click true làm đủ chứng cứ. Một probe BtnCharacter chạy nhầm lúc đã sang overlay và một probe pawn chạy trong Boot gây lỗi Python, không phải gameplay crash; giữ lịch sử.
5. Slate chỉ quan sát UI cùng process Editor, không thấy cây UI Standalone. Đã thử script input Windows nhắm đúng PID/-game/title; kiểm foreground từ chối, không gửi input. Script thử và lỗi nằm Artifacts/U00/E, không đưa thành plugin/tool mới. Không kill/đóng Editor. Standalone log ghi shutdown theo HandleExitCommand lúc 07:10:41 UTC, process sau đó không còn; không có bằng chứng AI bấm nút Quit, không gán sự kiện đó thành PASS Quit.
6. Chưa restart, full build, Foundation tests hoặc package. Không thay dependency để vượt lỗi.

Ảnh và log chỉ ở Artifacts/U00/E: BootPIE, CharacterPIE (ảnh trước sửa), CharacterLitPIE (sau sửa), NetworkPIE; keyboard-ui-routes.json; editor-evidence.json; map-measurements.json; StandaloneGame.log. Ảnh không thay phép đo transform. Chưa có video. Test route UI dùng keyboard đã đủ 3 vòng nhưng cổng chuột và Standalone vẫn thiếu; vì vậy E BLOCKED.

## Bàn giao

Commit/push riêng nhánh u00/e-maps; SHA và ref đối chiếu sau commit. Stage đúng Content/AnimeMMORPG qua LFS, ba script tác nghiệp, REPORT-E, DefaultGame và chỉ hunk hai map của DefaultEngine. Không stage token, cache/log/binary build hoặc chỉnh ngoài E. Không tự merge.

Bước còn lại để nghiệm thu E: kiểm chuột thực ổn định (đặc biệt Về menu), input sân Network, chạy lại UI sau sửa focus cuối cùng, kiểm Standalone đủ hai tuyến và Quit bằng nút với bằng chứng đúng process. Các việc này không đòi mở rộng toolset hoặc đóng Editor; chưa chọn cách vượt giới hạn hiện tại. Full build D, -Task Test binary đĩa và dependency/tool registration sau khởi động mới giữ trong checklist tích hợp riêng. Chưa bắt đầu F.

補 sung kiểm tra Git cuối: hunk startup ban đầu có CR cuối dòng bị git diff --cached --check báo trailing whitespace; baseline asset commit vẫn được lưu/push, không tính check đó PASS. Commit nối tiếp chỉ chuẩn hóa line ending index của config đã sạch token và ghi lỗi này; không stage config local có token. 12/12 asset mới đã xác minh index là LFS pointer và upload LFS thành công. Không thay nội dung asset vì lỗi line ending.
