# REPORT-A

Trạng thái: BLOCKED — khảo sát kỹ thuật đã bàn giao; quyền phân phối asset chưa có bằng chứng. Không tuyên bố giám sát nghiệm thu.

Mục tiêu: riêng U00-A, xác minh baseline hiện tại bằng thao tác chỉ đọc. Đã tạo ENVIRONMENT.md (kết quả/lệnh/giới hạn), ASSET_REGISTER.csv (mọi nhóm Content cấp đầu, chưa xác minh quyền), REPORT-A.md (bàn giao). Không sửa source, config hoặc asset.

## Kiểm tra và bằng chứng

Tất cả phép đọc thực hiện 2026-11-02 khoảng 11:40–11:43 +07:00 trên D:/Data/AnimeMMORPG; chi tiết nguồn/lệnh ở ENVIRONMENT.md.

| Phép kiểm | Mong đợi | Thực tế | Trạng thái |
| --- | --- | --- | --- |
| Get-Location, uproject, target/module/config | Đúng project và baseline | Project chính, một module, hai target | PASS |
| Build.version và MCP log | UE 5.8.4 CL 58902052 | Khớp cả hai nguồn | PASS |
| Get-CimInstance process | Command line active project | Lượt đầu Access denied; lượt được duyệt PID 7184 đúng project | FAIL rồi PASS |
| MCP discovery/schema và bốn call đọc | Map/actor/log/PIE thật | Map ThirdPerson; một PlayerStart; log đúng engine; PIE false | PASS |
| vswhere, MSVC/SDK directory | Ghi thành phần thực có | VS 18.11, MSVC 14.51.36231, SDK 26100; component riêng chưa kiểm đủ | PARTIAL |
| git status | Xác định trạng thái local | Chưa là repository | PASS baseline |
| git ls-remote GitHub | Ref hiện tại hoặc lỗi rõ | Sandbox chặn lần đầu; retry exit 0 không ref | FAIL rồi PASS đọc |
| Kiểm kê asset và license filenames | Chứng cứ nguồn/quyền | Có nhóm asset; không tìm thấy file LICENSE trong project qua rg | BLOCKED quyền |
| Compile / Automation / Package / executable | Ngoài phạm vi A | Không chạy | NOT-RUN |

Không có commit, nhánh hoặc push; chưa init Git. Không có build sạch hay nghiệm thu compile/package. Báo cáo không chứa giá trị token; Config/DefaultEngine.ini có trường SecurityToken cần chặn staging và xử lý trước baseline B.

Giới hạn: nguồn gốc asset mới là giả thuyết theo cấu trúc template, chưa có giấy phép/receipt/manifest chứng minh. Chưa audit từng asset. Toolchain chỉ xác minh installation/path, không chứng minh tương thích UBT. Không cài/nâng phần mềm hoặc plugin.

Đề nghị: giám sát xem xét A, cung cấp chứng cứ nguồn và giấy phép asset cần phân phối, quyết định xử lý trường credential. Chỉ giao U00-B sau nghiệm thu A; không tự bắt đầu B. Không đánh dấu U00 hoặc gameplay U01, hiệu năng U04, mạng U05 đạt.

## Bàn giao bổ sung A — 2026-11-02 11:47 +07:00

Trạng thái hiện tại: BLOCKED baseline; khảo sát kỹ thuật bổ sung HOÀN TẤT, nguồn gốc byte đã đối chiếu, quyền upload toàn baseline CHƯA XÁC NHẬN. Phần này cập nhật các giới hạn nguồn gốc của báo cáo ban đầu; giữ phần cũ để bảo toàn lịch sử kiểm tra.

- PASS: hash 753 file Content với 3.084 ứng viên template/variant/shared resources trong engine khóa. 753 khớp; 0 khác; 0 không tìm được nguồn. Chi tiết từng file và SHA-256 trong ASSET_REGISTER.csv. Empty Collections/Developers không có file để hash.
- PASS: tìm/đọc nguồn Epic chính thức, phân biệt game đóng gói, Examples source exception và Licensed Content source restrictions. Không thấy license template riêng trong phép dò bộ cài; không kết luận mọi nội dung được upload. Điều khoản chủ project chấp thuận/custom agreement chưa xác minh.
- PASS: GitHub API GET read-only xác nhận public (private=false); web open trước đó lỗi, đã giữ ghi nhận trong ENVIRONMENT.md. Không chứng minh quyền push.
- PASS: source AFS engine và tài liệu Epic xác nhận chức năng token. Có đề xuất loại secret khỏi tracked config nhưng chưa thử override; không sửa config/rotate token. Hash config trước/sau khớp.
- NOT-RUN theo phạm vi: init/stage/push, build/test/package/Play, chỉnh asset/config, cài đặt. Không có commit/nhánh/push mới.

Ba file thay đổi: ENVIRONMENT.md bổ sung phương pháp/kết quả/nguồn/giới hạn; ASSET_REGISTER.csv thay bảng nhóm bằng kiểm kê từng file cùng hash và nguồn khớp; REPORT-A.md bổ sung bàn giao này. Không sửa Description hoặc ROADMAP.

Điểm chặn baseline: cần giám sát xem xét căn cứ Examples và xác nhận điều khoản áp dụng/quyền upload cho tập nguồn dự kiến; giải quyết SecurityToken trước stage. Repository là public nên không thể dựa vào giả định private. Không còn điểm chặn thiếu nguồn byte đối với 753 file Content hiện tại; chưa kiểm secret toàn baseline thay cho B.

Đề nghị tiếp theo: nghiệm thu phần A bổ sung và quyết định hai điểm chặn trên, sau đó giao B riêng nếu được chấp nhận. Đã dừng; không bắt đầu U00-B, không tuyên bố giám sát nghiệm thu.
