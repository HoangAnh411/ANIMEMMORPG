# U00-C — Compile baseline

Trạng thái: READY_FOR_REVIEW. B được người giám sát nghiệm thu và giao C từ 8addcb9c3e224d0e2997b7aa3df1b15f4806d2c0. Nhánh u00/c-build, không merge main. Không đánh dấu U00 tổng hợp.

## Thực hiện và nguồn

Ngày 2026-11-02, khoảng 18:57–19:01 +07:00. Project tuyệt đối D:/Data/AnimeMMORPG/AnimeMMORPG.uproject; engine D:/Software/UE_5.8, Build.version 5.8.4 CL 58902052. Đọc Description, ROADMAP, REPORT-B; không tìm thấy AGENTS.md trong project ở phép dò. HEAD trước tạo nhánh khớp đầy đủ SHA nền. Editor cũ đã đóng theo người dùng và Get-Process xác nhận không còn UnrealEditor. Đã bỏ riêng dòng SecurityToken được cho phép; git diff sau đó không có khác biệt nội dung config với nền. Không restore toàn file.

Tạo Scripts/U00.ps1: giao diện -Task Build -ProjectPath -EngineRoot -OutputRoot. Kiểm đường dẫn tuyệt đối, file tồn tại, engine/CL và Editor đóng; mỗi lượt output riêng có timestamp/GUID; gọi Build.bat tuần tự generate, Editor, Game; ghi command JSON, log và exit code riêng; dừng khi lỗi. Không tải/cài, clean/delete. Chưa thêm Test/Package/Verify thuộc đợt sau. Không đổi source gameplay, plugin list, renderer hoặc dependency.

## Lệnh và kết quả thực tế

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Scripts/U00.ps1 -Task Build -ProjectPath D:/Data/AnimeMMORPG/AnimeMMORPG.uproject -EngineRoot D:/Software/UE_5.8 -OutputRoot D:/Data/AnimeMMORPG/Artifacts/U00
```

Script gọi Engine/Build/BatchFiles/Build.bat với từng bộ args (đường dẫn project được truyền thành một argument):

1. -projectfiles -project=D:/Data/AnimeMMORPG/AnimeMMORPG.uproject -game -rocket
2. AnimeMMORPGEditor Win64 Development -Project=D:/Data/AnimeMMORPG/AnimeMMORPG.uproject -WaitMutex -NoHotReloadFromIDE
3. AnimeMMORPG Win64 Development -Project=D:/Data/AnimeMMORPG/AnimeMMORPG.uproject -WaitMutex -NoHotReloadFromIDE

| Lượt/bước | Kỳ vọng | Thực tế |
| --- | --- | --- |
| Build-20261102-185734-704-28a2bd3b trong sandbox | Generate/build | FAIL exit 1 ngay generate, output chỉ tới gọi UBT, không có chẩn đoán cụ thể; giữ log/command, chưa có result JSON bước con |
| Build-20261102-185750-912-255eb25c, tài khoản chủ máy | Generate | PASS exit 0, 18:58:03 +07; .sln/.slnx sinh thành công |
| cùng lượt, Editor | Compile Win64 Development | PASS exit 0, 18:58:28 +07; compile/link module, Result Succeeded |
| cùng lượt, Game | Compile Win64 Development | PASS exit 0, 18:59:34 +07; UHT/PCH/module/link AnimeMMORPG.exe, Result Succeeded |
| ParseFile script sau bổ sung catch lưu failure.json | Không lỗi cú pháp | PASS 0 parse errors; đường thành công đã chạy, nhánh catch bổ sung chưa gây lỗi có chủ ý để thử |

Bằng chứng dưới Artifacts/U00/<lượt>: Generate/Editor/Game.command.json, .result.json và .log; lượt fail giữ nguyên. Bổ sung script ghi failure.json khi gặp exception sau lượt fail, không làm lại/ghi đè chứng cứ cũ. Không khẳng định nguyên nhân lượt fail đầu đã được chẩn đoán; retry chạy ngoài sandbox thành công.

UBT thực chọn Visual Studio toolchain 14.51.36260 tại VC/Tools/MSVC/14.51.36231 và Windows SDK 10.0.26100.0. DotNet bundled 10.0 win-x64. Warning compiler mới hơn preferred 14.50.35717; không đổi/cài toolchain. Compiler warning C4996: Editor 1, Game 20 (header engine, deprecated APIs); không có lỗi compile/link, không sửa engine chỉ để xóa warning. Đây là build thông thường trên workspace có Binaries/Intermediate/cache cũ; không clean và không tuyên bố build từ clone sạch (đợt F). Không dựa Live Coding/receipt cũ.

## Mở Editor và module

Start-Process đúng UnrealEditor.exe + project tuyệt đối + -abslog=<lượt thành công>/EditorStartup.log -NoSplash, không Play. PID 15712. Get-CimInstance xác nhận executable và command line đúng; Get-Process.Modules xác nhận DLL runtime D:/Data/AnimeMMORPG/Binaries/Win64/UnrealEditor-AnimeMMORPG.dll được nạp. Log đúng engine 5.8.4 CL 58902052, Engine initialized và Total Editor Startup Time 12.470s; quét Error/Fatal/missing modules/could not be loaded không có kết quả. EditorVerification.json lưu tóm tắt đã lọc. Không dùng screenshot thay build.

Editor hiện để mở, không tự đóng/kill/discard nội dung. Khi khởi động, AFS tự sinh lại dòng SecurityToken dù bEnablePlugin=False; diff local chỉ thêm dòng đó. Không in giá trị, không stage config, commit config vẫn giữ bản nền sạch và AFS false. Không thu hồi token Android cũ. Đây là thay đổi runtime local cần xử lý trước đợt tiếp theo, không phải thay đổi build source. Không che bằng assume-unchanged.

## Git, bàn giao và giới hạn

Chỉ commit Scripts/U00.ps1 và Docs/U00/REPORT-C.md trên u00/c-build; SHA commit và kết quả push đối chiếu bằng git log/ls-remote sau commit. Config local có token tự sinh được giữ ngoài index. Không git add toàn workspace; Artifacts/log/binary không commit. Git sandbox không ghi được index.lock nên thao tác nhánh/commit dùng tài khoản chủ máy với safe.directory giới hạn từng lệnh, không đổi global policy/ACL.

Không chạy Automation test (đợt D), Play hoặc package. Chưa nghiệm thu U01/gameplay, U04/performance hoặc U05/network. Đề nghị giám sát review C, xử lý config local khi cần, merge vào main sau nghiệm thu rồi mới giao D từ commit đã merge; không tự bắt đầu D.

## Điều chỉnh quy tắc Editor sau nghiệm thu C

Theo chỉ thị mới của người dùng: đọc/MCP/tài liệu/review/commit không yêu cầu đóng Editor; asset giữ Editor mở và lưu trước commit. Build đầy đủ module Editor mới yêu cầu đóng Editor của đúng project. Scripts/U00.ps1 nay đọc command line qua Win32_Process và so khớp đường dẫn project tuyệt đối, không chặn chỉ vì Editor của project khác đang chạy. Nếu không đọc được process/command line, báo lỗi không xác định được project thay vì kết luận mọi Editor đều xung đột. Không tự đóng tiến trình.

Token AFS local được giữ ngoài commit khi làm việc; không yêu cầu đóng Editor/xóa token cho mỗi commit. Việc nhỏ riêng chưa triển khai: điều tra và ngăn AFS tự ghi token vào tracked config dù đã tắt AFS, dựa source config lifecycle; tiêu chí là mở lại Editor không thêm secret vào tracked config, không làm xác thực optional và không đổi plugin/renderer ngoài nhiệm vụ được giao. Không sửa config trong lượt điều chỉnh này. Commit 2e3547c đã nghiệm thu được giữ nguyên; sửa script là bổ sung cần review, không tuyên bố build lại.

## Bổ sung guard fail-closed sau review 337f538

Sửa Assert-EditorProjectSafe: chỉ cho qua khi command line nhận diện duy nhất một project qua positional argument hoặc -project, đường dẫn tuyệt đối tới file .uproject tồn tại và Resolve-Path khác project mục tiêu. Cùng project yêu cầu lưu/đóng đúng PID. Command line rỗng, chỉ tên project, đường dẫn tương đối, không có project, đường dẫn không tồn tại hoặc đầu vào mơ hồ báo Cannot identify project kèm PID; không mặc định là project khác. Không log toàn command line hoặc tự đóng tiến trình.

Kiểm tra thực chạy 2026-11-02: powershell -NoProfile -ExecutionPolicy Bypass -File Scripts/Tests/U00.EditorGuard.Tests.ps1, exit 0. Tám ca PASS: cùng project đường dẫn tuyệt đối có dấu cách; project khác; command line rỗng; đường dẫn tương đối; tên project; -project với cùng project; file tuyệt đối không tồn tại; không có project. Test chỉ trích xuất function từ AST, không chạy nhánh build; fixture mới nằm ở temp. Parse script không lỗi. Không build lại C++; nghiệm thu compile 2e3547c giữ nguyên. Phần guard bổ sung READY_FOR_REVIEW, chưa tự merge hoặc bắt đầu D. Config token local không sửa/không stage.
