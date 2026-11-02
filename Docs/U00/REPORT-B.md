# REPORT-B — U00-B

Trạng thái: BLOCKED — quyền ghi metadata Git local. Không bắt đầu U00-C.

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
