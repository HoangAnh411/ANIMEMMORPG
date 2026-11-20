# U04-B-R1b — INCOMPLETE, dừng tại chuyển process

**INCOMPLETE: 23/69 PASS; chưa READY_FOR_REVIEW toàn B. Không ACCEPTED hoặc merge.** Nhánh `u04/b-r1b-fps-acceptance` bắt đầu từ `f158ce1c4c05c88c8afd590c5172b6134ca54b2c`. Native giữ nguyên `8cbcb6a6d6dfc4e29bff8731a6aaab187f887cb4`; analyzer `u04r1-entry-4` không đổi. Không dùng kết quả B/R1a cũ để cộng vào batch.

30 FPS đã hoàn thành đúng thứ tự: đi, sprint, né tiến/lùi/trái/phải mỗi ca3 PASS, combo5 PASS. Tất cả23 lượt đều đạt gameplay và cadence chính; không có FAIL, INVALID hoặc cửa sổ crash. Không thử quá số lượt cần. 60/120 FPS chưa khởi chạy; video minh họa0/21 vì batch dừng trước khi hoàn tất phần số liệu.

| Ca | 30 FPS | 60 FPS | 120 FPS |
|---|---:|---:|---:|
| Đi | 3/3 PASS | 0/3 | 0/3 |
| Sprint | 3/3 PASS | 0/3 | 0/3 |
| Né tiến | 3/3 PASS | 0/3 | 0/3 |
| Né lùi | 3/3 PASS | 0/3 | 0/3 |
| Né trái | 3/3 PASS | 0/3 | 0/3 |
| Né phải | 3/3 PASS | 0/3 | 0/3 |
| Combo | 5/5 PASS | 0/5 | 0/5 |

## Nguyên nhân dừng và giới hạn

Sau khi numeric30 trả exit0, implementer gọi `StopR1b.ps1` rồi ngay lập tức `StartR1b.ps1 ... -FPS 60` trong cùng lệnh shell. `Stop-Process` chưa bảo đảm process đã biến mất khỏi CIM khi guard Start kiểm tra. Guard từ chối với lỗi chính xác **`Another R1b package process is active`**. Kiểm tra kế tiếp xác nhận PID13764 đã thoát, không còn game R1b, không có thư mục/process numeric60 và không có cửa sổ60 được bắt đầu. Đây là lỗi orchestration/setup của implementer; không phải FAIL gameplay hoặc thiếu cadence đã quan sát ở60/120.

Theo manifest đã đóng băng (`setupError: halt; no retries`), batch đã dừng, ledger ghi lỗi setup riêng, không tính nó thành một lượt đo60. Không sửa harness/analyzer, chạy lại Start, tăng hạn mức hoặc mở batch thay thế. Evidence30 giữ nguyên. Đề xuất cho reviewer: review riêng việc bổ sung chờ process cũ thoát bằng PID+creation identity và timeout hữu hạn trước Start; chỉ sau chỉ đạo mới được đổi tool/manifest hoặc mở đợt tiếp theo. Chưa triển khai đề xuất đó.

## Identity và phương pháp

Harness/contract được commit trước capture: `7bc81afb62c3040ab523b13d695a5483fac45c77`; manifest commit `b01dbfb`. [BATCH-MANIFEST.json](BATCH-MANIFEST.json) ghim16 file runtime, binary/profile/order/budgets. Mỗi process ghi cả tool commit và repository HEAD. Analyzer working-byte SHA256 `f792caa7ca850abf333b502083d67d7c806fea159bb90d406b2cd87973cf8cd0`; manifest giữ cả hash Git bytes của bản đã được review, đối chiếu khác biệt line ending trước khi đóng băng. Native diff rỗng, không rebuild hoặc Live Coding.

Tái sử dụng nguyên package R1a `Build-R5-20261119/Archive/Windows`: Game SHA256 `915887c83acfe0d1668e1b4947807e31217452bd783f185f9f3bc63f67772e25`, Editor module `0e43d13c82f49791e2e9ee522697f200c7f7d9ab6efbe392c44c2300aac01d37`. Kiểm đầy đủ48 file package, module, Editor và commandlet engine trước launch và cuối đợt. UE5.8.4/CL58902052; kế thừa UBT thực của build R1a: MSVC14.51.36260 (directory14.51.36231), SDK10.0.26100.0. Kế thừa rõ Automation144/144 và hồi quy native R1a; không chạy lại chúng vì thay harness.

Process Solo13764 có render, viewport1280×720/internal50, đầy đủ profile/cvar đã ghim. Readiness mới kiểm source/process, Game world/pawn, thời gian tăng và Windows input tác động đúng pawn; warmup30 giây sau readiness. Numeric không import encoder/video hoặc gọi media trong cửa sổ; ảnh46 tấm ở trước/sau23 lượt. Guard50ms, native focus từng frame; events được buffer rồi ghi sau end. Clock chính duy nhất là collector entry `sampleEntryWall`, không đổi cửa sổ hoặc bỏ frame. Đây là cadence game-thread, không phải present/scanout.

Python analyzer synthetic24 nhóm và harness offline7 nhóm đạt trước batch; không thay thế gameplay thật. Không có full Automation/build/gameplay bổ sung ngoài23 lượt và readiness mới. Không lỗi build vì không build. Cảnh báo EOL khi stage source được giữ trong log thao tác; JSON/CSV/evidence có Git attributes giữ byte nguyên vẹn.

Runtime log giữ14 dòng Warning: hai dòng audio sample-rate48000/44100 và12 dòng về startup thực thi11 console commands mất41,75ms. Chúng nằm trước warmup/cửa sổ nghiệm thu; không loại sample nào vì warning. Không có dòng Error/Fatal khớp bộ lọc. Chi tiết nằm trong `RUNTIME-WARNINGS.json` và Game.log đã publish.

## Kết quả tính lại và overhead

[TRIALS.csv](TRIALS.csv) giữ từng lượt, FPS/band/percentile/max, raw SHA, sai số, admission velocity và collector cost. [MATRIX.csv](MATRIX.csv) giữ toàn bộ21 ô, gồm các ô chưa chạy. `Runs/Recomputed-20261120` là output mới: cả23 analyzer verdict và effective status khớp assertions ban đầu, không sửa raw hoặc nhãn lịch sử.

Đi/sprint mỗi lượt đo đúng10 world seconds, dịch chuyển5000/7000cm, sai số0cm; CSV giữ wall duration, path và lệch ngang. Cả12 lượt né có `velocityBeforeBatch` ngang0cm/s; snapshot gửi/nhận/model đúng hướng, quãng đường sai số tuyệt đối dưới0,001cm, trajectory0,25s và release0,35s. Cả5 combo có ba hit60/70/90, HP giảm220, crit-off cùng life, authority duration `1.4499999999999886s`.

Cadence30 của mọi lượt có100% interval trong dải±10%, FPS trung bình nằm trong cổng±5%; không interval quá hai chu kỳ. Không suy ra kết quả60/120 từ cap hoặc từ kết quả30. Raw giữ entry/world-start/core-begin/exit. Trên2192 frame nằm trong các cửa sổ được chọn, collector entry→exit P50≈0,157ms, P95≈0,233ms, P99≈0,416ms, max≈0,653ms. Collector/native buffer vẫn có allocation và input tracing; guard cũng có overhead. Không tuyên bố phép đo không có overhead. Flush native sau end, không sync log chi tiết mỗi frame do harness.

## Bảo toàn và hồ sơ

Clone/output/preferences riêng tại `Artifacts/U04/B-R1b`; không cleanup, tải engine hoặc đổi config gốc. Preflight kiểm dung lượng thực khoảng117GB trước clone; reserve25GiB. Snapshot bảo vệ34248 file gồm tracked workspace/clone lịch sử, private Maintenance, package/module/engine U03/U04. Raw/published hash và kiểm cuối được giữ trong evidence manifest.

Editor gốc PID2136/creation `2026-11-20T04:22:45.5962180Z` không bị đóng, compile hoặc đổi preference. Chỉ thu nhỏ sau fresh readiness rồi khôi phục hai HWND cùng Show=1 và normal rectangle ban đầu. So sánh toàn dictionary WINDOWPLACEMENT ban đầu không khớp trường Min do tọa độ cache minimized của Windows thay đổi; before/after và cảnh báo được giữ, không tuyên bố Min cache giống byte. Main18804bfa, trạng thái private/config/Maintenance và mọi hash được bảo vệ phải khớp kiểm cuối; không stage dữ liệu private.

[Evidence manifest](Evidence/Review-20261120/MANIFEST.json) liên kết raw và bản publish, gồm input/frame/action/hit, assertions, recompute, ảnh, readiness, identity, ledger, setup stop và protection checks. Không có video minh họa hoặc bằng chứng60/120. Chưa đủ điều kiện khép U04.03/B. Bàn giao reviewer xem lỗi chuyển process và quyết định bước tiếp theo; chưa merge hoặc U04-C/D.
