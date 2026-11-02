# U00-D — Foundation và Automation

Trạng thái: BLOCKED phần kiểm chứng Automation C++; phần triển khai và kiểm tra script sẵn sàng review. Không báo đạt 0 test. Full build được người dùng dời sang nghiệm thu tích hợp riêng và không là lý do yêu cầu đóng Editor trong lượt này.

## Nguồn và phần thực hiện

Project D:/Data/AnimeMMORPG/AnimeMMORPG.uproject; commit nền 6f042e9c9942a3cbe0aff852f6ffae070fe5c108, nhánh u00/d-foundation. Đọc Description/ROADMAP/REPORT-C và quy tắc U00 trong giao việc; không tìm thấy AGENTS.md ở phép dò project. Token AFS local tiếp tục ngoài commit; không sửa Config, không đóng/kill Editor, không bỏ nội dung chưa lưu. Không thay luật Description để làm test đạt.

FOUNDATION.md chốt mét/giây, centimet Transform, độ, trục X/Y/Z, world/local space, vector/position, chân khác capsule center, ba hướng riêng, khoảng [start,end), clock world/session và reset deadline qua world/session. Không clock subsystem hoặc sync mạng.

Source/AnimeMMORPG/Foundation/UnitsAndTime.h thêm ba helper thuần constexpr double trong namespace AnimeMMORPG::Foundation: MetersToCentimeters, CentimetersToMeters, IsWithinHalfOpenInterval(Now,Start,End); khoảng rỗng/đảo false. Không giữ trạng thái, không đọc clock. Source/AnimeMMORPG/Tests/FoundationTests.cpp khai báo bốn Automation tests dưới WITH_DEV_AUTOMATION_TESTS, prefix AnimeMMORPG.U00.Foundation: Units (0/1/10/âm, hai chiều, round-trip <= 1e-9), Axes (tiến/phải/lên, yaw +/-90 và local-to-world position), HalfOpenInterval (trước/start/trong/end/sau, rỗng/đảo), CallOrder (đảo/xen kẽ lời gọi không đổi kết quả). Một runtime module giữ nguyên; không thêm dependency/plugin/asset/map/gameplay.

## Script và kiểm chứng thực chạy

Scripts/U00.ps1 thêm -Task Test. Test chạy UnrealEditor-Cmd.exe riêng với -ExecCmds="Automation RunTests AnimeMMORPG.U00", -TestExit="Automation Test Queue Empty", -ReportExportPath, -abslog, -unattended -NullRHI; không gọi Build, không dùng guard đóng Editor trong nhánh Test. Mỗi lượt tạo output mới, lưu command/result/log/report. Timeout 600 giây trả lỗi và giữ tiến trình để kiểm tra, không kill. Đây là test binary trên đĩa, KHÔNG dùng patch Live Coding của Editor đang mở; cần binary tích hợp tests trước khi chạy script này.

Không dựa riêng exit code: yêu cầu index.json, đúng tập bốn test, mỗi state Success, summary không failed/notRun/inProcess, tổng success khớp và log có queue completion với số test >0 khớp report. Nhánh không có report, 0 test hoặc chưa hoàn tất không thể PASS. Không gọi Task Test trên binary cũ để giả định tests mới có sẵn.

Thời điểm kiểm tra 2026-11-02 khoảng 19:17–19:19 +07:00; nguồn chính là working tree D, không dùng receipt C thay chứng cứ D.

| Lệnh/tool | Mong đợi | Thực tế |
| --- | --- | --- |
| git rev-parse HEAD trước tạo nhánh | Nền đúng SHA được giao | PASS khớp đầy đủ |
| AST ParseFile Scripts/U00.ps1 | Không lỗi cú pháp | PASS |
| powershell -NoProfile -ExecutionPolicy Bypass -File Scripts/Tests/U00.EditorGuard.Tests.ps1 | Guard không hồi quy | PASS 8 ca, exit 0 |
| powershell -NoProfile -ExecutionPolicy Bypass -File Scripts/Tests/U00.AutomationReport.Tests.ps1 | Report validator từ chối kết quả sai | PASS 7 ca, exit 0: success; zero; fail; incomplete; thiếu test; thiếu completion; summary lệch |
| git diff --check | Không lỗi whitespace | PASS |
| Discovery ALL_TOOLS lọc unreal/live coding | Có công cụ kích hoạt compile/test trong Editor | Không có tool Unreal/MCP hoặc Live Coding được expose trong phiên này |
| Đọc log local Saved/Logs/AnimeMMORPG.log lọc LiveCoding | Phân biệt khởi tạo và compile | Có Successfully initialized, chưa có bằng chứng compile D; không suy thành tests đã chạy |
| Live Coding compile D | Compile/apply patch mới | NOT-RUN: không có công cụ gọi trong phiên; không bấm phím vào cửa sổ chưa xác minh |
| Automation C++ D trong Editor | >0 tests thực chạy và tất cả đạt | NOT-RUN, executed 0; chưa phải đạt |
| Full build D | Nghiệm thu tích hợp riêng | DEFERRED theo chỉ thị mới; không chạy Build.bat |

Bằng chứng tóm tắt máy đọc: Artifacts/U00/D-Static-20261102-191907/verification.json. Không có log compile hoặc Automation report thật của D để bàn giao; không tạo report giả từ fixture. Fixtures PowerShell chỉ kiểm validator, không thay thế Automation tests C++. Source engine AutomationControllerManager.h/AutomationCommandline.cpp được đọc để đối chiếu fields report và completion marker, không sửa engine.

## Điểm chặn còn lại và bàn giao

Cần phiên có công cụ Editor hoặc một lượt người giám sát chạy Live Coding và Automation prefix AnimeMMORPG.U00 trong đúng Editor để có bằng chứng tests mới đã được đăng ký/thực chạy. Nếu Live Coding không nhận translation unit/test mới, ghi kết quả đó và để phần kiểm chứng C++ sang lượt tích hợp đã lên lịch; không yêu cầu đóng Editor ngay trong vòng D này. Sau đó chạy Task Test bằng binary đã tích hợp, đối chiếu report, số test và trạng thái. Chưa xác nhận Script Test với report thật engine hoặc compile C++ D.

Chỉ stage helper/tests, FOUNDATION.md, Scripts/U00.ps1, test validator và REPORT-D.md; không git add ., không đưa Config/token/log/binary vào commit. Commit/push nhánh D, không merge. Commit SHA và push kết quả bàn giao sau commit. Chưa bắt đầu E, chưa tạo map, chưa Play/package hoặc triển khai gameplay. Đề nghị review phần độc lập D và lên lịch kiểm chứng còn thiếu, không tự đánh dấu D hoàn thành.
