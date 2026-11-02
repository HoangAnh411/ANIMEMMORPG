# U00-A — Environment

Khảo sát mới: 2026-11-02, 11:40–11:43 +07:00. Chỉ đọc ngoài ba tài liệu Docs/U00. Nguồn luật: Docs/Description.md và Docs/ROADMAP.md; không sửa checkbox. Không tìm thấy AGENTS.md trong project hoặc D:/Data và D:/; không có báo cáo đợt trước trong project. ROADMAP chứa khảo sát cũ, không dùng làm kết quả mới.

## Project và engine

Project tuyệt đối D:/Data/AnimeMMORPG/AnimeMMORPG.uproject; EngineAssociation = 5.8 (không khóa patch). Build.version tại D:/Software/UE_5.8/Engine/Build/Build.version xác nhận 5.8.4, CL 58902052, compatible CL 55116800. Editor executable D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe.

Get-CimInstance Win32_Process ban đầu Access denied; chạy lại có quyền đọc thành công: PID 7184, executable trên, command line chỉ rõ D:/Data/AnimeMMORPG/AnimeMMORPG.uproject. Không dựa recently opened. MCP log cũng trả Engine Version 5.8.4-58902052+++UE5+Release-5.8. Không có API active-project được phát hiện trong schema đã khảo sát; command line là bằng chứng thay thế.

## Baseline

Hai target Game/Editor, BuildSettingsVersion.V7, Unreal5_8 include order; một runtime module AnimeMMORPG. Dependencies: Core, CoreUObject, Engine, InputCore, EnhancedInput, AIModule, StateTreeModule, GameplayStateTreeModule, UMG, Slate. Template Combat/Platforming/SideScrolling còn nguyên.

Plugin bật trực tiếp trong uproject: ModelingToolsEditorMode (Editor), StateTree, GameplayStateTree, Terminal, ModelContextProtocol, EditorToolset, MCPClientToolset. Đây không phải danh sách mọi plugin engine tự bật.

DefaultEngine.ini: startup và game map /Game/ThirdPerson/Lvl_ThirdPerson; default game mode BP_ThirdPersonGameMode. MCP map hiện tại khớp. Có bốn map nguồn: ThirdPerson/Lvl_ThirdPerson, Variant_Combat/Lvl_Combat, Variant_Platforming/Lvl_Platforming, Variant_SideScrolling/Lvl_SideScrolling. Chưa có map Boot/lab.

Windows: Compiler=Default, DX12 mặc định (khai báo lặp), D3D12 SM6, D3D11 SM5; desktop/scalable, Lumen, ray tracing, Nanite và Substrate được cấu hình. Không thay renderer.

## Toolchain

vswhere -latest: D:/Software/Microsoft Visual Studio/18/Community, installationVersion 18.11.12315.225. VC/Tools/MSVC có 14.51.36231. Windows Kits/10/Include có 10.0.26100.0. Đường dẫn VS mặc định ở C:/Program Files không tồn tại; không kết luận thiếu VS từ phép dò đó.

.vsconfig yêu cầu workload CoreEditor/ManagedDesktop/NativeDesktop/NativeGame, Unreal IDE/debugger, .NET 4.6.2 targeting pack, VC 14.50.18.0 ATL/x86.x64, Clang, VC tools và SDK 22621. Các thư mục thực có ở trên không chứng minh toàn bộ component này đã cài. Chưa xác minh component ID riêng lẻ hoặc compiler/SDK UBT thực chọn; dành đợt C. Git LFS thực có 3.7.1.

## MCP

list_toolsets thành công. describe_toolset đọc schema EditorAppToolset, LogsToolset, SceneTools. Chỉ gọi:

- SceneTools.get_current_level {} → /Game/ThirdPerson/Lvl_ThirdPerson.
- SceneTools.find_actors {name:PlayerStart,tag:"",collision_channels:[]} → một PlayerStart trong PersistentLevel của map trên.
- EditorAppToolset.IsPIERunning {} → false.
- LogsToolset.GetLogEntries {category:"",pattern:"Engine Version:|Build:|Project Name:",maxEntries:8} → sáu dòng; có build CL và phiên bản đúng.

Đã cấu hình, kết nối và gọi đọc thành công; chưa được giám sát nghiệm thu. Không StartPIE/load/save/mutation. Chỉ đọc log lọc; không sao chép toàn bộ log.

## Git và giới hạn

git status --short → fatal: not a git repository. Không có commit/nhánh/push local. git ls-remote URL GitHub được chỉ định ban đầu bị sandbox chặn domain; chạy lại có phê duyệt: exit 0, không ref. Chỉ chứng minh truy cập đọc, không chứng minh quyền ghi hoặc LFS upload. Không init/fetch/push.

Config/DefaultEngine.ini, section AndroidFileServerRuntimeSettings có SecurityToken nghi là credential: không đưa giá trị vào báo cáo; chặn file khỏi staging cho đến khi xử lý ở B. Không sửa cấu hình trong A.

Chưa build, test, package; output/receipt cũ không được tính đạt. Giấy phép asset chưa được xác minh; xem ASSET_REGISTER.csv.

## Bổ sung A — 2026-11-02 11:44–11:47 +07:00 (kết quả mới)

Đã đọc lại Description, ROADMAP, REPORT-A và register trước thao tác. Chỉ khảo sát filesystem/web/API; không gọi Editor trong lượt bổ sung. Các kết quả Editor ở phần trước vẫn mang thời điểm lượt trước.

### Đối chiếu nguồn từng file

Lệnh PowerShell Get-ChildItem -File -Recurse + Get-FileHash -Algorithm SHA256 lập chỉ mục 3.084 file ứng viên trong bốn gốc dưới D:/Software/UE_5.8: Templates/TP_ThirdPerson/Content, Templates/TP_ThirdPersonBP/Content, Templates/TemplateResources/High và Templates/TemplateResources/Standard. So sánh mọi file Content theo hash trên toàn bộ chỉ mục (không chỉ tên/đường dẫn); nếu không khớp mới tìm ứng viên cùng filename. Không mở/chỉnh binary; không giải nén FeaturePacks/*.upack vì nguồn rời đã bao phủ đủ file hiện tại.

Kết quả: 753/753 file HASH_MATCH; DIFFERENT_CANDIDATE = 0; SOURCE_NOT_FOUND = 0. ASSET_REGISTER.csv nay chứa một dòng/file, SHA-256 project, mọi đường dẫn nguồn byte-identical, trạng thái upload riêng. Hash nguồn chính là hash project khi khớp. Khớp byte chứng minh nội dung trùng với bộ cài được khảo sát, không chứng minh lịch sử sao chép hay quyền pháp lý.

| Nhóm | File khớp |
| --- | ---: |
| Characters | 128 |
| Input | 9 |
| LevelPrototyping | 29 |
| ThirdPerson | 5 |
| Variant_Combat | 31 |
| Variant_Platforming | 11 |
| Variant_SideScrolling | 19 |
| __ExternalActors__ | 479 |
| __ExternalObjects__ | 42 |

Collections/Developers có thư mục nhưng không có file trong kiểm kê này. Không có danh sách file khác/không tìm được nguồn vì hai tập đều rỗng, không phải chưa kiểm tra. TemplateDefs.ini của TP_ThirdPerson xác nhận C++ gồm mọi variant và SharedContentPacks Characters, LevelPrototyping, Input, mức High. Đây là bằng chứng bổ sung cho shared resources.

### Tài liệu cấp phép

rg --files tìm tên EULA/Eula, License rtf/html/pdf và LICENSE/License trong bộ cài: không tìm thấy bản EULA tổng của engine hoặc license riêng cho template/shared resources trong phạm vi tên đã dò. Có nhiều giấy phép thành phần tại Engine/Source/ThirdParty/Licenses và plugin; không áp chúng cho mannequin/template. Copyright Epic trong source không phải giấy phép asset. Chưa xác minh điều khoản chủ project thực sự đã chấp thuận hoặc custom agreement.

Nguồn chính thức đã đọc ngày 2026-11-02:

- [Unreal Engine EULA, mục 1, 4, 5(b)](https://www.unrealengine.com/eula/unreal): Examples gồm code/artwork/content ở Samples và Templates của bộ cài. Game phân phối chứa Licensed Technology theo điều kiện object code gắn liền Product; mục 5(b) có ngoại lệ cho phép phân phối Examples kể cả sửa đổi ở source/object code. Vì vậy không đánh đồng mọi asset Epic với nội dung cấm chia sẻ source. File khớp nằm dưới Templates là cơ sở phân loại Examples; đây là suy luận từ vị trí + hash + định nghĩa, không phải xác nhận upload toàn project.
- [Epic Content License Agreement, mục 3–4](https://www.unrealengine.com/eula/content): nội dung thuộc hợp đồng này có thể đi trong project đóng gói theo điều kiện; chia sẻ source giới hạn cho nhóm phát triển được nêu, không suy thành quyền public upload. Private repo cũng không tự tạo quyền cấp phép. Chỉ áp khi xác định asset thuộc hợp đồng này; không mặc định áp cho Examples.

Chưa có giấy phép riêng/receipt hoặc xác nhận điều khoản áp dụng của chủ project. Cơ sở cho Examples đã tìm thấy; upload toàn bộ baseline vẫn UPLOAD_NOT_CONFIRMED. Không phủ nhận ngoại lệ 5(b), cũng không coi hash là giấy phép. Package và public source là hai phép đánh giá riêng.

### GitHub visibility

Web open GitHub/API không lấy được trang (cache/access error). Retry bằng Invoke-RestMethod GET https://api.github.com/repos/HoangAnh411/ANIMEMMORPG, không credential: thành công, full_name đúng, private=false, visibility=public. Repository PUBLIC tại thời điểm kiểm tra. Không kiểm quyền ghi; không thay visibility. Không lấy ref/push trong lượt bổ sung.

### SecurityToken — đã xác minh chức năng

Nguồn local đúng engine: Engine/Plugins/Runtime/AndroidFileServer/Source/AndroidFileServerEditor/Public/AndroidFileServerRuntimeSettings.h:25–38 (Config=Engine, DefaultConfig; trường config); Private/AndroidFileServerRuntimeSettings.cpp:14,31–36 (default [AUTO], sinh GUID rồi TryUpdateDefaultConfigFile); AndroidFileServer/AndroidFileServer_UPL.xml:10,15–16,429,470 (đọc cấu hình Engine, rỗng làm token optional, so khớp token). Phép dò nhầm Plugins/Developer ban đầu không tìm thấy; đã sửa đường dẫn khảo sát sang Runtime, không sửa project.

[Epic Android File Server, Using Security Tokens](https://dev.epicgames.com/documentation/en-us/unreal-engine/android-file-server-for-unreal-engine) xác nhận token dùng bảo vệ yêu cầu UnrealAndroidFileTool, bảo vệ cơ bản không mã hóa và không nên chia sẻ ngoài tổ chức. Đây là bí mật truy cập AFS Android, không phải GitHub token hay khóa tài khoản. Không in giá trị project. Không kiểm tra truy cập AFS thực hoặc xoay token.

Đề xuất cho nhiệm vụ được duyệt sau này: giữ mọi setting project cần thiết, chỉ loại giá trị SecurityToken khỏi cấu hình tracked. Không thay bằng chuỗi rỗng vì sẽ bỏ kiểm token; không chỉ xóa key rồi bỏ mặc vì default [AUTO] có thể sinh GUID và ghi lại DefaultEngine.ini. Cần thử cơ chế override Engine local không tracked (ví dụ Saved/Config/WindowsEditor/Engine.ini) và cách Android packaging đọc override bằng token thử dùng một lần, không log giá trị. Giữ key mẫu không bí mật/ghi chú trong tài liệu setup; kiểm tra thứ tự config và hành vi ghi lại trước khi chốt phương án. Nếu editor vẫn ghi DefaultEngine.ini, dùng bước provision local + kiểm tra staged diff để từ chối token trước commit; không ignore toàn DefaultEngine.ini, không dùng assume-unchanged làm bảo vệ. Android ngoài phạm vi U00 nên hiện chỉ đề xuất, chưa triển khai/kiểm chứng override. Không sửa config, không tắt plugin. Config SHA-256 trước/sau lượt bổ sung đều 3A7A9FF16795E261B77CD482A2A1CCEB5A119C351BE3AFB9CB94C0887CF05899.
