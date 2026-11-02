# REPORT-B — U00-B

Trạng thái hiện tại: READY_FOR_REVIEW — kiểm tra baseline GitHub và clone khôi phục đã đạt ngày 2026-11-02. Không bắt đầu U00-C. Các mục BLOCKED bên dưới là lịch sử được giữ nguyên.

## Phạm vi và kết quả

Thực hiện 2026-11-02 khoảng 11:51–12:01 +07:00 tại D:/Data/AnimeMMORPG. Đã đọc lại REPORT-A, ENVIRONMENT, ASSET_REGISTER và ROADMAP; không tìm thấy AGENTS.md ở lần dò project. Lệnh giao B của người giám sát chấp nhận tiếp tục và cho phép push nguồn lên remote public; không yêu cầu xác nhận chung quyền upload nữa.

Remote chỉ định: https://github.com/HoangAnh411/ANIMEMMORPG.git. git ls-remote chạy mới, exit 0, không ref; local ban đầu chưa là repository. Danh tính Git đã có của người dùng; không đặt danh tính giả. Git LFS 3.7.1 có trên máy. Chưa chứng minh quyền ghi GitHub vì bị chặn Git local trước khi có ref để push. Không coi dry-run lỗi thiếu main là kiểm tra quyền ghi thành công. Không có lịch sử remote nào được ghép/ghi đè.

## Nguồn và phạm vi track

PowerShell Import-Csv + Get-FileHash SHA256: manifest 753 dòng, Content 753 file, mismatch 0. Nguồn khớp trong Templates theo manifest A. [EULA Epic mục 1 và 5(b)](https://www.unrealengine.com/eula/unreal), đọc lại trong lượt B, định nghĩa Examples từ Samples/Templates và cho phép phân phối Examples kể cả bản sửa đổi ở source/object code. Đây là căn cứ phân loại cho tập Content đã đối chiếu; hash chỉ là chứng cứ byte nguồn. Không gán giấy phép MIT hoặc giấy phép chung lên Epic content; giữ copyright hiện có. Không có file Content bị loại hoặc nguồn mới không rõ.

Đã kiểm danh sách Source (42 cpp, 42 h, 3 cs), Config (5 ini), Docs và file root dự kiến. Không đưa Engine source/binary, output sinh tự động hoặc .codex vào baseline. Config/DefaultEditorPerProjectUserSettings.ini hiện chỉ có ContentBrowser selected path template, không có credential được phát hiện. Build/ không tồn tại; ignore không loại toàn Build/. Các folder __ExternalActors__/__ExternalObjects__ được giữ trong Content, không bị ignore.

File thay đổi: Config/DefaultEngine.ini chỉ đặt bEnablePlugin=False trong AndroidFileServerRuntimeSettings và bỏ dòng SecurityToken. Không đổi plugin list, renderer hoặc gameplay. Không in token cũ. Thay đổi này không thu hồi token trong các bản Android đã triển khai trước đây, nếu có. Không dùng token rỗng vì có thể khiến xác thực tùy chọn. Không tạo token mới hoặc chạy Editor.

Tạo .gitignore: .vs, .codex, Binaries, Intermediate, DerivedDataCache, Saved, Artifacts, solution sinh tự động và một số loại credential local. Tạo .gitattributes: text auto; *.uasset và *.umap filter=lfs diff=lfs merge=lfs -text. Cấu hình file đã viết; LFS local install chưa thành công.

## Kiểm tra và lỗi giữ lại

| Thời điểm +07 | Lệnh/tool, nguồn | Mong đợi | Thực tế |
| --- | --- | --- | --- |
| 11:51 | git ls-remote URL remote | Kiểm tra refs | PASS: exit 0, không ref |
| 11:51 | Import-Csv + SHA256 Content | Khớp manifest A | PASS: 753/753, 0 mismatch |
| 11:52 | Quét text dự kiến track | Không credential cụ thể | PASS: 0 file khớp private-key header, GitHub/AWS token pattern, assignment SecurityToken/Password/ClientSecret/ApiKey/AccessToken có giá trị; không phải bảo đảm phát hiện mọi dạng bí mật |
| 11:52 | git init -b main | Tạo metadata local | PASS: tạo .git; chưa có commit |
| 11:52 trở đi | git remote add / lfs install | Cấu hình local | FAIL: dubious ownership, sandbox offline user sở hữu .git |
| 11:54–11:59 | Retry sandbox exec | Tiếp tục dưới owner tạo .git | FAIL: helper_unknown_error: setup refresh had errors |
| 11:56–12:00 | Git ngoài sandbox với -c safe.directory chỉ project | Ghi config | FAIL: .git/config Permission denied; không thay global safe.directory |
| 11:59 | Get-Acl .git và config | Tìm nguyên nhân | Owner CodexSandboxOffline; tài khoản kaede thiếu Modify cần thiết |
| 12:00 | icacls .git /grant kaede Modify /T được duyệt | Sửa ACL metadata vừa tạo | FAIL: Access denied, processed 0 files; không thay ACL thành công |
| cuối lượt | Đọc config trước staging dự kiến | Token vắng, AFS false | PASS; chưa stage vì metadata bị chặn |

Git push --dry-run origin main đã thử nhưng thất bại src refspec main does not match any (chưa commit), không phải bằng chứng thiếu quyền GitHub. gh không có trên PATH; không cài thêm. Không có push thật hoặc dữ liệu nào upload. Không dùng force/clean/reset, không xóa .git hoặc nội dung khác để vượt lỗi.

## Commit, staged và khôi phục

Nhánh khởi tạo dự kiến main, chưa sinh commit; origin chưa ghi được vào config. Tracked/staged: 0. Không có baseline SHA hoặc trạng thái push thành công. Danh sách file dự kiến track: Source/, Config/ đã làm sạch, Content/, Docs/, AnimeMMORPG.uproject, .vsconfig, .gitignore, .gitattributes. Chưa stage nên chưa có kết quả secret scan Git index; quét hiện tại chỉ áp tập file text dự kiến. Không có file lớn ngoài LFS trên 50 MiB trong tập text đã kiểm.

Clone GitHub/LFS fsck/hash khôi phục: NOT-RUN do chưa có baseline push. Không tạo clone local thay thế. Build/Play/Automation/gameplay/package: NOT-RUN theo phạm vi.

## Hướng dẫn khôi phục sau khi điểm chặn được xử lý

Cần chủ máy hoặc quản trị sửa quyền Modify cho tài khoản chạy Git trên .git mới tạo, hoặc khôi phục sandbox có thể chạy dưới đúng owner. Không tự xóa metadata. Sau đó tiếp tục riêng B: kiểm remote refs và Content/config lại, local LFS install, stage danh sách cụ thể, kiểm staged secret/ignore/LFS, commit rồi push main bình thường. Nếu refs remote mới có lịch sử không liên quan, dừng.

Sau push thành công, tại project chính dùng thư mục mới Artifacts/U00/RestoreCheck-<timestamp> chưa tồn tại:

```powershell
git clone https://github.com/HoangAnh411/ANIMEMMORPG.git <absolute-new-restore-directory>
git -C <absolute-new-restore-directory> lfs pull
git -C <absolute-new-restore-directory> lfs fsck
git -C <absolute-new-restore-directory> status --porcelain
git -C <absolute-new-restore-directory> rev-parse HEAD
```

So SHA256 từng Content với ASSET_REGISTER; xác nhận .uasset/.umap là binary thật, không bắt đầu bằng LFS pointer header. So Git tree/blob text với baseline và working tree sạch thay vì so byte CRLF/LF. Xác nhận token key không có trong config tracked và AFS false. Clone cùng ổ chỉ kiểm tái lập, không bảo vệ hỏng ổ; GitHub là nguồn ngoài máy. Chưa chạy những lệnh khôi phục này, không coi đã đạt.

Đề nghị giám sát xử lý quyền filesystem .git rồi giao tiếp tục B. Chưa thể READY_FOR_REVIEW cho nghiệm thu B; không khẳng định người giám sát đã nghiệm thu. Không bắt đầu C.

## Xác minh nghiệm thu bổ sung — 2026-11-02

Baseline đã tồn tại khi bắt đầu lượt xác minh: `999057852192ca51d3cf45598bf7e06cf45b8eee` (Initial commit). Không tạo lại hoặc sửa commit này. `git ls-remote origin refs/heads/main` trả đúng SHA trên; local HEAD khớp. Remote: https://github.com/HoangAnh411/ANIMEMMORPG. Lỗi quyền Git trước đây được giữ làm lịch sử; lượt này không sửa ACL.

| Kiểm tra thực chạy | Kết quả |
| --- | --- |
| Danh sách tracked baseline | 855 file; 0 file trong Binaries/Intermediate/Saved/DerivedDataCache/Artifacts/.vs/.codex |
| git lfs ls-files | 753 file; attributes uasset/umap là LFS, -text |
| Quét text từ git show HEAD:path | 0 file khớp private-key header, GitHub/AWS token hoặc assignment SecurityToken/Password/ClientSecret/ApiKey/AccessToken có giá trị; không bảo đảm phát hiện mọi loại bí mật |
| Config trong commit | Không có SecurityToken; AFS bEnablePlugin=False |
| git clone từ GitHub | Thành công vào Artifacts/U00/RestoreCheck-20261102-122426 |
| git lfs pull; git lfs fsck trong clone | Exit 0; Git LFS fsck OK |
| Content clone so manifest | Đủ 753/753; SHA-256 mismatch 0; LFS pointer còn lại 0 |
| Git tree và mọi entry blob/mode/path | Baseline và clone cùng tree de7534708d9ee1c0513fdec2aa9befd7ffc36689; khác biệt 0, bao gồm text blob |
| git status --porcelain trong clone | Rỗng, working tree sạch |

Bằng chứng máy đọc: `Artifacts/U00/verification-B.json`; thư mục Artifacts được ignore, không đưa clone/build output vào commit. Phép đọc trong sandbox có cảnh báo không đọc được global ignore tại profile; lệnh vẫn exit 0. Trạng thái clone cũng được kiểm lại ngoài sandbox trước commit tài liệu. Lượt đọc mạng đầu bị allowlist chặn; retry được duyệt thành công. Không có lỗi kiểm chứng nội dung hoặc LFS.

### Khôi phục đúng baseline đã kiểm chứng

Dùng một đường dẫn mới chưa tồn tại; không ghi đè thư mục có dữ liệu:

```powershell
git clone https://github.com/HoangAnh411/ANIMEMMORPG <absolute-new-restore-directory>
git -C <absolute-new-restore-directory> checkout --detach 999057852192ca51d3cf45598bf7e06cf45b8eee
git -C <absolute-new-restore-directory> lfs pull
git -C <absolute-new-restore-directory> lfs fsck
git -C <absolute-new-restore-directory> status --porcelain
git -C <absolute-new-restore-directory> rev-parse HEAD
```

Kiểm Content theo SHA256 trong ASSET_REGISTER.csv; đếm file và kiểm pointer như bảng trên. Để lấy tài liệu mới nhất thay vì baseline cố định, dùng main và ghi lại SHA thực tế. Clone cùng ổ là kiểm tra khôi phục từ remote, không bảo vệ hỏng ổ đĩa. Chưa build, Play, test Unreal, package hoặc bắt đầu U00-C. READY_FOR_REVIEW là trạng thái chờ giám sát, không tuyên bố đã được giám sát nghiệm thu.
