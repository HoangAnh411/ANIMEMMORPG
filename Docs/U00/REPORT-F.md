# U00-F — Windows package và kiểm chứng tích hợp

Trạng thái: **BLOCKED — chỉ còn kiểm chứng thao tác UI/input trên packaged game**. Build, Automation, dependency sau khởi động mới và package đã PASS. Chưa đề nghị nghiệm thu toàn U00; chưa merge F hoặc bắt đầu U01.

## Nguồn và phạm vi

E đã được người dùng nghiệm thu theo xác nhận thủ công, cập nhật REPORT-E và push commit b281662d31a4c5df29730c75213fda52b7b3131b trên u00/e-maps. Main đã fast-forward tới cùng SHA và đối chiếu ref GitHub. Không bổ sung số vòng/PID/video/log cho xác nhận E.

Nhánh F: u00/f-package, từ SHA trên. Script được commit/push **9d6a81b24c9dbf75ad8fcf4c47de78c72f95eb80 trước khi clone**. Đây là SHA nguồn thực sự build/test/package. Commit bàn giao tài liệu sau đó không thay binary; xem lịch sử Git nhánh F để xác định commit tài liệu. Remote: https://github.com/HoangAnh411/ANIMEMMORPG.

Clone GitHub độc lập: `Artifacts/U00/F-20261103-191300/Source`. Không build vào project gốc. Dùng engine và cache toàn máy, không tuyên bố cache sạch. Engine UE 5.8.4 CL 58902052 tại D:/Software/UE_5.8; UBT thực chọn MSVC 14.51.36260, Windows SDK 10.0.26100.0; Win64 Development. Windows/hardware và hash nằm trong F-MANIFEST.json.

## Phương thức và kết quả — 2026-11-03, giờ +07

Gọi script **trong clone**:

```powershell
& ./Scripts/U00.ps1 -Task Verify -ProjectPath 'D:/Data/AnimeMMORPG/Artifacts/U00/F-20261103-191300/Source/AnimeMMORPG.uproject' -EngineRoot 'D:/Software/UE_5.8' -OutputRoot 'D:/Data/AnimeMMORPG/Artifacts/U00/F-20261103-191300/Evidence'
```

Mọi đường dẫn bằng chứng dưới đây tương đối với `Artifacts/U00/F-20261103-191300`. Thư mục lượt Verify: `Evidence/Verify-20261103-191513-678-5b1c4f1f` (gọi tắt V).

| Phép kiểm, nguồn/tool | Kỳ vọng | Thực tế và bằng chứng |
|---|---|---|
| Git clone từ GitHub, LFS pull/fsck, trước chạy | Đúng SHA, sạch, đủ asset | PASS: SHA 9d6a81b; 765 LFS files; fsck OK; working tree sạch, chưa có Binaries/Intermediate. ClonePreflight.json |
| SHA-256 Content so với nguồn đã chốt | Không khác, không pointer | PASS: 765/765 khớp, 0 mismatch, 0 pointer. AssetVerification.json |
| Generate project files; Build.bat Editor/Game, 19:15–19:18 | Hai target Succeeded | PASS: Generate và hai build exit 0, log Succeeded. V/Build-20261103-191514-226-d18c989f; command/result/log từng bước |
| U00.ps1 -Task Test trên binary vừa build, 19:18–19:19 | Đủ 4 tests Success và queue hoàn tất | PASS: exit 0, succeeded=4, failed/notRun/inProcess=0, queue `4 tests performed`. V/Test-20261103-191831-311-7f76f053/Report/index.json và Automation.log |
| Editor clone khởi động mới, khoảng 19:24 | Đúng project, module/toolset đăng ký thật | PASS: PID 20184, native ToolsetRegistry xác nhận TestRunnerTools, AutomationTestToolset và EditorAppToolset; Python module TestRunner đến từ clone. EditorRegistration2.json/.log/.command.json. MCP riêng 18002, không chiếm 8000; tiến trình kiểm chứng tự thoát sau script |
| RunUAT BuildCookRun, 19:19–19:27 | Cook/package/archive thành công | PASS: exit 0, BUILD SUCCESSFUL, cook 0 errors/0 warnings. V/Package-20261103-191930-356-0536b45e chứa command/result/log và Archive |
| Executable thật, direct map URL + ExecCmds Quit, 19:28–19:30 | Ba map tải và thoát không crash/missing map | PASS: Boot, CharacterCombatLab, NetworkLab đều LoadMap confirmed, exit 0; không thấy Error:/Fatal/BlueprintRuntimeError/missing-map trong log lượt này. Smoke-20261103-192818/results.json, command JSON và từng log |
| Click menu, di chuyển, quay menu, Quit bằng nút trong packaged game | Đủ tuyến và input thật | **NOT-RUN**, cần checklist gộp bên dưới. Direct map URL/console Quit không thay bằng chứng nút UI |

Bốn tests thực chạy: AnimeMMORPG.U00.Foundation.Axes, AnimeMMORPG.U00.Foundation.CallOrder, AnimeMMORPG.U00.Foundation.HalfOpenInterval, AnimeMMORPG.U00.Foundation.Units — tất cả Success. Full build D, Test trên binary đĩa và đăng ký dependency sau khởi động mới được khép PASS bằng lượt clone này; không dựa vào Live Coding cũ.

## Script và package

Scripts/U00.ps1 giữ Build/Test, thêm Package/Verify. Verify gọi Build → Test → Package và dừng ở exit code lỗi đầu tiên. Mỗi lượt có thư mục mới, lệnh, exit code và log riêng. Test kiểm tra đủ đúng bốn tests, trạng thái report và completion log; không chấp nhận 0 test. Guard phân biệt project clone với Editor project gốc. Test dùng port 18001 khi cần; lượt Editor kiểm dependency dùng 18002.

Package gọi RunUAT.bat BuildCookRun với `-noP4 -platform=Win64 -clientconfig=Development -build -cook -stage -pak -archive -unattended -utf8output -nocompileeditor`, project/archive tuyệt đối, danh sách map đọc từ config và kiểm tra đúng ba map E: L_Boot, L_CharacterCombatLab, L_NetworkLab. Không đổi plugin/renderer; không Shipping, installer, ký số hay Release. Script không clean/delete; UAT tự quản sandbox cook mới của clone. AST và tám kiểm tra guard, bảy kiểm tra validator report đã đạt; không cố ý gây một build/compiler failure mới để thử exception.

## Artifact và hướng dẫn chạy

Executable bootstrap (chạy bình thường, không thêm ExecCmds Quit):

`Artifacts/U00/F-20261103-191300/Evidence/Verify-20261103-191513-678-5b1c4f1f/Package-20261103-191930-356-0536b45e/Archive/Windows/AnimeMMORPG.exe`

Giữ nguyên toàn bộ thư mục Windows khi sao chép/chạy. SHA-256 bootstrap: `DE088F5191B0CDBA77E47F71FBAE8321FE128C6EDDE75975A34037F432A5272E`; binary game tại Windows/AnimeMMORPG/Binaries/Win64/AnimeMMORPG.exe: `7F9D8F7D3A1E743F04E3D075766681EA8B6D038AF00152A769A81DA3B607C630`.

F-ARTIFACTS.csv ghi 48 file đóng gói và SHA-256, loại Saved sinh khi chạy. F-MANIFEST.json gắn source SHA, engine/toolchain, máy chạy, đường dẫn, hash manifest và kết quả. Package/log/clone chỉ giữ dưới Artifacts, không commit/LFS.

## Lịch sử, warning và giới hạn

- Lượt EditorRegistration đầu dùng callback chờ frame nhưng ExecutePythonScript tự kết thúc Editor trước callback; **chưa kiểm chứng**, không tính PASS. Giữ VerifyCloneEditor.py và EditorRegistration.command.json/.process.json/.log. Lượt 2 kiểm tra đồng bộ bằng native registry, không import module để giả đăng ký; đã PASS. Chỉ tiến trình clone tự thoát; Editor người dùng PID 13444 vẫn mở ở lần đối chiếu 19:32.
- UBT cảnh báo compiler chưa thuộc bản preferred; C4996 trong engine headers: Editor 30, Game 20 theo CompilerWarnings.json. Không thay engine/toolchain để che warning. Cook summary 0 errors/0 warnings.
- Smoke có warning audio engine 48000 Hz/device 44100 Hz, dùng sample-rate conversion. Lượt Boot đầu thoát sau khoảng 77 giây; không coi đây là đo hiệu năng. Cả ba process thoát bình thường; không kill.
- Sau chạy, clone phát sinh token AFS trong Config/DefaultEngine.ini và tài nguyên Build/. Không stage chúng; trạng thái sạch chỉ được xác nhận **trước** chạy. Config local project gốc giữ ngoài commit, không xuất giá trị token. Không sửa asset/source gốc hoặc đóng Editor người dùng.
- Discovery công cụ phiên này không có desktop mouse/keyboard hoặc tool điều khiển widget của packaged executable. MCP của Editor không thay thế input trên game đóng gói. Xác nhận thủ công E không được tái sử dụng làm PASS cho packaged game F.

## Một checklist thủ công gộp — đúng bản đóng gói trên

1. Mở bootstrap exe từ thư mục Windows; xác nhận Boot/menu xuất hiện.
2. Bấm sân nhân vật/combat, dùng input template di chuyển, bấm Về menu. Bấm sân mạng, di chuyển và bấm Về menu.
3. Thực hiện tổng tối thiểu năm vòng Boot → sân → Boot, luân phiên hai sân; kiểm tra không nhân widget/mất nút. Camera giữ chuột là giới hạn template đã chấp nhận.
4. Bấm Thoát; xác nhận game đóng và Editor gốc vẫn mở. Mở lại executable, xác nhận Boot. Gửi kết quả từng mục và lỗi nếu có; chưa có xác nhận/số vòng/video/PID nào được tự ghi nhận trước khi người dùng cung cấp.

Sau xác nhận packaged UI mới cập nhật kết luận nghiệm thu. Hiện bàn giao nhánh F để review với trạng thái BLOCKED tại cổng input/UI thủ công duy nhất; không tự merge F, không nghiệm thu U01, hiệu năng U04 hoặc mạng U05.
