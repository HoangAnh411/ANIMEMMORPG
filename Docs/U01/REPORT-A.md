# U01-A — Hợp đồng và phép thử khả thi

Người dùng đã nghiệm thu A tại `4216ff874872f5d7112cc792b52d008937441f7c`. Đã fast-forward/push đúng commit này vào main theo giao việc tiếp theo; không đóng Editor. Phần READY_FOR_REVIEW bên dưới là hồ sơ trước nghiệm thu. B thực hiện trên nhánh riêng `u01/b-camera`, không kế thừa nghiệm thu input/mạng F từ A.

Trạng thái: **READY_FOR_REVIEW** cho phạm vi A. Chưa nghiệm thu B–G, chưa server packaging. Nhánh `u01/a-contracts`; commit/push được xác định bằng HEAD nhánh bàn giao và ref remote, không tự merge/đi tiếp.

## Nguồn và phạm vi

Thực hiện ngày 2026-11-04, kiểm tra cuối 00:46 +07. Trước tạo nhánh đã đối chiếu `git rev-parse main` và `git rev-parse f10e925` cùng SHA đầy đủ `f10e9252767f134e8e6d5698c326a2b045b8f1d3`; `git ls-remote origin refs/heads/main` sau đó xác nhận cùng SHA. Main giữ nguyên. Đọc AGENTS.md, Description, ROADMAP, REPORT-A…F/U00, FOUNDATION, ENVIRONMENT và asset register theo tập được chọn. U00-F đã được người dùng nghiệm thu, giữ nguyên 4/4 kết quả lịch sử, không tính là tests chạy mới trong A.

Lựa chọn người dùng được ghi trong ROADMAP/CONTRACTS: kỹ thuật trước bằng mannequin/clip hiện có, kiếm hình khối, camera/chuột ưu tiên B (xoay ngay không giữ nút). Art anime DEFERRED riêng. Description/gameplay không đổi. Không triển khai Character/Controller/motor/AnimBP/settings/metrics collector hoặc gameplay B. Không cài/nâng engine/plugin, không enable AllToolsets, không sửa renderer/config/template. Config local có token trước bắt đầu vẫn ngoài commit; không stage toàn workspace.

File đổi: Docs/ROADMAP.md; Docs/U01/{CONTRACTS,TEST-MATRIX,ASSETS,REPORT-A}.md; Evidence/A-ASSETS.json và A-NETWORK.json; Scripts/U01/InspectAssets.py (đọc metadata) và ProbeNetwork.ps1 (phép thử process có giới hạn). Không asset binary/C++ mới.

Kiểm cuối: assetCount10/hashMismatch0; serverJoinCount2/processCount3; PowerShell parse0 lỗi; `git diff --check` đạt. Quét pattern credential trên đúng tập Docs/Scripts mới:0 khớp (không bảo đảm phát hiện mọi dạng secret); Description diff rỗng. MCP summary cuối vẫn Boot, PID19808 còn chạy. Config local không nằm trong danh sách stage.

Engine thực: `D:/Software/UE_5.8`, Build.version UE5.8.4 CL58902052, installed marker `Engine/Build/InstalledBuild.txt` tồn tại. Project EngineAssociation5.8. Không compile A nên không có toolchain mới được UBT chọn; mốc build U00-F dùng MSVC14.51.36260 / SDK10.0.26100.0 (lịch sử, không tái xác nhận compile A). Binary Editor/module của phép thử có SHA256 trong A-NETWORK.json; dùng binary đĩa hiện có, không chứng minh tái lập từ SHA source bằng clean build.

## Kết quả mới

| Kiểm tra / phương thức | Kết quả | Bằng chứng / giới hạn |
|---|---|---|
| Local main/base SHA và ref GitHub | PASS | SHA đầy đủ trên; không reset/merge |
| Process Editor gốc qua CIM | PASS sau retry quyền | PID19808 đúng executable/project; vẫn mở sau thử |
| MCP discovery/schema/summary | PASS | Boot `/Game/AnimeMMORPG/Maps/L_Boot.L_Boot`, 0 actor; không lấy làm pawn runtime |
| Asset metadata qua MCP + SHA256 | PASS 10/10 | A-ASSETS.json; mesh/sáu clip skeleton khớp; đi/jog root motion True được ghi thành việc cần xử lý D |
| Script network PowerShell parse + thực chạy | PASS phép thử kết nối | Không lỗi parse; launcher exit0; một server/hai client alive trước cleanup; không là test Automation |
| Dedicated Editor process + hai client join | PASS khả thi, có lỗi runtime bên dưới | A-NETWORK.json và raw logs; server listening17777, hai join và hai pawn template |
| U01 metrics world/net mode/localplayers/ownership/displacement | NOT-RUN | Đã chốt schema/nguồn world trong CONTRACTS; chưa collector; không suy runtime từ Editor actor |
| Full build/Live Coding/Automation/package/UI/input/video | NOT-RUN theo A | 0 Automation tests chạy mới; không tuyên bố U00 4/4 được chạy lại |
| Target Server đóng gói | NOT-RUN, chưa được chứng minh hỗ trợ | Không Server.Target.cs; installed configurations Win64 thấy Game/Editor, không Server; không tạo target hoặc build giả |

## Phép thử mạng thực

Lệnh chạy: `powershell -NoProfile -ExecutionPolicy Bypass -File Scripts/U01/ProbeNetwork.ps1`. Root mặc định đúng project/engine trên, port17777. Chi tiết executable/arguments/userdir/log từng PID được giữ trong [A-NETWORK.json](Evidence/A-NETWORK.json). Raw evidence local: `Artifacts/U01/A/Network-20261104-004025/{processes.json,alive.json,Server/Server.log,ClientA/ClientA.log,ClientB/ClientB.log}`. Log SHA256 có trong evidence để đối chiếu byte. Artifact bị ignore; chỉ commit trích log cần thiết đã rà soát, không toàn output có cấu hình cá nhân.

| Vai trò | PID | Đường chạy | Chứng cứ |
|---|---:|---|---|
| Server | 15820 | UnrealEditor.exe project L_NetworkLab -server -port=17777 | 17:40:34.946 UTC `IpNetDriver listening on port 17777`; connections `IsServer: YES` |
| Client A | 14100 | UnrealEditor.exe project 127.0.0.1:17777 -game | Welcomed17:40:50.954 UTC; server Join succeeded17:40:51.821 |
| Client B | 21360 | UnrealEditor.exe project 127.0.0.1:17777 -game | Server Join succeeded17:41:01.206 UTC; client Welcomed |

Server log có `BP_NetworkController_C_0 got player IpConnection_0`, `BP_NetworkController_C_1 got player IpConnection_1`, và pawn path `L_NetworkLab:PersistentLevel.BP_ThirdPersonCharacter_C_0` / `_1`. Đây là chứng cứ network join và hai pawn template, chưa kiểm mỗi client chỉ điều khiển pawn sở hữu hoặc movement replicate. Không có metrics vị trí/tốc độ nào được báo trong A. Dedicated role được xác lập từ lệnh -server và log driver phía server; giá trị `GetNetMode`, world type, local-player count0 chưa được collector đo, giữ làm cổng F.

Mỗi process có UserDir/log riêng, MCP port18110/18111/18112 để không chiếm8000. Settings isolation thực chưa kiểm. `-NullRHI -nosound -unattended` chỉ phục vụ probe headless, không đổi project renderer, không là bằng chứng render/animation/UI/FPS. Launcher chờ12s giữa process +15s cuối và chỉ Stop-Process các process tự tạo; không là Quit graceful smoke. Ba process thử đã kết thúc, Editor gốc19808 vẫn mở; không đóng/restart/save/discard Editor gốc.

## Lỗi và giới hạn còn lại

1. Cả đường game/server có Python init errors: `AttributeError: module 'unreal' has no attribute 'ToolsetDefinition'`, `'AgentSkill'`, `'PythonTestRunner'`. Ví dụ TestRunner init→toolset_registry/registration.py:14, EditorToolset blueprint_basics.py:41, ToolsetRegistry init_unreal.py:7. Không chặn hai join; không sửa dependency hoặc enable AllToolsets để che. Cần phân loại/guard editor-only init đúng scope trước khép tích hợp; chưa tuyên bố toolsets chạy trong server.
2. Server có hai warning `Accessed None trying to read (real) property CallFunc_Create_ReturnValue in not an UClass` trong BeginPlay của BP_NetworkController U00 khi tạo widget. Có hai remote controllers/pawns, nhưng server UI sạch **chưa đạt**; B phải gate local controller và F kiểm localplayers0/UI0. Không sửa U00 Blueprint trong A.
3. Installed engine chạy được **Editor executable dedicated**, không suy thành packaged Server. Hiện chỉ target Game/Editor, không Server target, không hàng Win64 Server trong installed platform config đã dò. Không phát biểu UBT đã báo lỗi Server vì chưa chạy build target đó. Server packaging ngoài cổng A/F đã chốt; nếu nhiệm vụ sau yêu cầu, cần kiểm target + engine có server artifacts, có thể cần source-built engine cùng phiên bản hoặc installed build có hỗ trợ Server. Không tải/thay engine hoặc ước đoán thời gian/chi phí chưa khảo sát. Đường Editor-server hiện khả thi nên không có điểm chặn cần engine khác cho U01 localhost.
4. Không có tool desktop input/package UI được xác minh trong phiên; A không cần input/video. B cần input thật/video và metrics camera; fixture/log không thay bằng chứng đó. Các rủi ro root motion, startup Python và UI server được chuyển thành cổng B/D/F/G cụ thể, không coi đã sửa.
5. CIM/Git metadata bị sandbox từ chối; retry được duyệt để đọc process/tạo nhánh. Đọc remote bị sandbox domain block rồi retry thành công. Có một lệnh rg wildcard kiểu Windows sai đường dẫn, đã sửa về directory search; không tính probe đó là kết quả mạng. Không đổi ACL/global Git policy.

## Bàn giao

Hợp đồng và ma trận đã đủ để review A: input/menu/focus/re-arm, camera/aim, motor/time, animation/root motion, settings validation và đo đúng world/PID/net role/pawn; asset nguồn đã xác minh; đường dedicated Editor + hai client có log thật. READY_FOR_REVIEW chỉ cho A, không đánh dấu U01 gameplay/Windows/mạng F hoặc art anime hoàn thành.

Commit/push nhánh `u01/a-contracts`, đối chiếu SHA local với ref GitHub; main không merge. Sau bàn giao dừng, chờ nghiệm thu/giao B riêng. B là ưu tiên chơi thử đầu theo người dùng, không tự bắt đầu.
