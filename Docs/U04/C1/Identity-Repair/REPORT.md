# C1 identity — sửa hẹp, chờ review tooling

U04-C1 vẫn **INCOMPLETE**:0/36 timing,0/12 memory,0/3 overhead. Bản578c0e7 chưa được chấp nhận chạy readiness probe. Lượt này không chạy Build-03/game/Editor, không chọn HWND, không focus hoặc phát input. Chỉ chạy offline và kiểm Win32 identity trên child Windows vô hại đã được giao. Không khép, merge hoặc lập C2.

## Thay đổi từ578c0e7

[Diff tooling](TOOLING.patch) là unified=0; nếu áp dùng `git apply --unidiff-zero`. Diff commit có context bình thường. Chỉ sửa tooling C1 và thêm hồ sơ này; native inputs giữ nguyên13b4f34f07bd1cb8e7402984d9479fd5eb9fe2e7. GATES và các hồ sơ/suite đã bàn giao giữ nguyên.

`Backend.launch` chỉ tạo process và giữ đối tượng Popen/HANDLE gốc trước mọi thao tác đọc metadata hoặc ghi file. `capture_owned` pin PID, executable và **creationTicks nguyên100ns** từ GetProcessId/QueryFullProcessImageNameW/GetProcessTimes trên handle đó. Nếu có exception ngay sau Popen assignment, `has_owned` chỉ lấy lại chính handle trong đối tượng Popen, không tìm process khác bằng PID. Backend chỉ được launch một lần; handle đã đóng không được nhận lại.

`verify_owned` kiểm process còn sống, lấy một handle query độc lập theo PID, so PID/executable/ticks Win32 với record và handle gốc, rồi đọc command line từ CIM. Sau lần đọc CIM, kiểm lại hai handle. CIM CreationDate được giữ dưới `cimCreationUTC`, kèm delta chẩn đoán; **không dùng để quyết định identity**. Parser vẫn so đúng từng đối số, đối chiếu CommandLineToArgvW và hash binary. Thiếu Win32 ticks là lỗi; FILETIME lệch một tick vẫn là lỗi. Không làm tròn, bỏ chữ số hoặc thêm epsilon.

Guard HWND của readiness dùng trực tiếp record.creationTicks, không đi vòng qua chuỗi timestamp. `creationUTC` trong record chỉ là cách hiển thị đầy đủ FILETIME đã pin; timestamp CIM riêng không thay được giá trị đó.

`run_owned_launch` bao trùm launch, lấy identity, ghi process.json, mở/ghi journal và probe. Nhánh success và mọi nhánh lỗi đều đi qua stop bằng **handle Popen gốc**. Cleanup không phụ thuộc CIM hoặc khả năng ghi file, không OpenProcess để tìm termination target. Trong nhánh bình thường, trước terminate đọc lại PID/executable/FILETIME từ handle gốc và so nguyên ticks với pin. Khi đã có record, stop_owned cũng so record chính xác. Chỉ đóng handle sau WaitForSingleObject signaled và lấy exit code; nếu timeout thì INVALID, không retry terminate hoặc đóng handle như thể đã thoát.

Nếu API đọc metadata liên tục báo OSError, cleanup chỉ dùng chính handle trong đối tượng Popen còn mở, PID từ đối tượng đó và provenance đã giữ; không tìm handle khác bằng PID. Result vẫn INVALID, exit proof ghi identityVerifiedAtStop=false và ticks chưa pin là null. Đây chỉ là cleanup child do mình tạo, không phải nới cổng identity. RuntimeError về PID/executable/FILETIME mismatch không được catch như lỗi metadata để bỏ qua.

Probe được gọi với cleanup=False để outer lifecycle chịu trách nhiệm duy nhất. Nếu lỗi ghi launch identity vào journal, không đi tiếp vào probe/input. Result sau stop được ghi best effort; lỗi disk giả lập hoàn toàn vẫn trả proof exit trong bộ nhớ cho caller lưu khi có thể. Không có key-up, quit console, IME shortcut hoặc focus cleanup.

## Offline

Suite cuối: [Identity-Offline-05 expected/actual](Evidence/Identity-Offline-05/cases.csv.gz), [transcript](Evidence/Identity-Offline-05/transcript.txt.gz), [results](Evidence/Identity-Offline-05/results.json.gz): **86/86 PASS**. Tập86 tên ca và expected khớp suite Readiness-Offline-05 đã bàn giao; không bỏ ca. Fixture identity được bổ sung Win32 ticks; ca PID reuse cũ thay đổi ticks Win32 thay vì dùng timestamp CIM như identity. Các fixture command line lịch sử vẫn chỉ kiểm argv, không được gọi là bằng chứng FILETIME thực.

Suite bổ sung cuối: [Identity-Additional-Offline-04 expected/actual](Evidence/Identity-Additional-Offline-04/cases.csv.gz), [transcript](Evidence/Identity-Additional-Offline-04/transcript.txt.gz), [results](Evidence/Identity-Additional-Offline-04/results.json.gz): **18/18 PASS**:

- CIM delta0/1/2/6/9 ticks nhưng Win32 handle đúng: PASS.
- FILETIME của process/PID thay đổi đúng1 tick: process_creation_mismatch. Chỉ có CIM, không có Win32 ticks: bị từ chối.
- Exception giữa Popen assignment và pin metadata: còn lấy được đúng handle gốc; không tìm PID thay thế; không nhận lại handle đã đóng.
- Lỗi sau tạo process, lấy identity, ghi process.json, mở journal, verify identity, ghi dòng journal đầu hoặc disk full: INVALID, probe không được gọi, stop đúng owned handle và có proof exit khi còn ghi được.
- Stop timeout: INVALID, không ghi processExited=True và không đóng handle như đã thành công.

Các ca kernel giả vẫn cấm OpenProcess trên đường stop. 86 ca input/focus trước vẫn kiểm số input phát sau fault bằng0. Giữ tất cả intermediate suites Identity-Offline-01..04 và Identity-Additional-Offline-01..03; chỉ05/04 là suite cuối. Không sửa suite Readiness-Offline-01..05 hoặc hai INVALID lịch sử.

## Windows thật, child vô hại

`C1WindowsIdentityCheck.py` tạo Backend(input_enabled=False), không khởi tạo backend input/DPI. Chỉ khởi động Python interpreter hiện hành với mã cố định `import time; time.sleep(120)` bằng CREATE_NO_WINDOW; metadata flags trên command line được child bỏ qua. Mỗi child giữ handle Popen, kiểm argv/ticks/hash qua adapter thật, rồi dừng và chờ thoát qua chính handle đó. Các process PowerShell nội bộ chỉ đọc CIM với -NoProfile và CREATE_NO_WINDOW. Không gọi C1Run.main, không tải/chạy game hoặc engine.

Giữ Identity-Windows-01/02 và lượt cuối Identity-Windows-03. Hai lượt trước có5/5 child xác minh đúng và đã thoát. Windows-03 chạy trên adapter cuối, sau khi86+18 ca offline đạt; có5/5 child identity PASS và một child recovery cố ý gây lỗi metadata. [Bảng samples](Evidence/Identity-Windows-03/samples.csv.gz), [summary](Evidence/Identity-Windows-03/summary.json.gz) và từng Sample có command, process record, journal, check/result, exit proof. Bảng số nguyên của lượt cuối nằm trong [WINDOWS-SAMPLES.md](WINDOWS-SAMPLES.md).

Đã thu được mẫu CIM khác FILETIME thực; một mẫu bằng nhau cũng được giữ. Không thay dữ liệu CIM để tạo bằng chứng. Hai handle Win32 khớp nguyên ticks ở tất cả năm mẫu identity bình thường; CIM khác không làm hỏng identity. Năm ca này có đúng PID/ticks trong exit proof, wait=signaled, exitCode0, handleSource=original_Popen. Ca Metadata-Failure-Recovery cố ý làm capture_owned luôn báo OSError ngay sau launch: không vào probe, không có process.json/journal khởi tạo, result vẫn INVALID nhưng processExited=true và proof wait=signaled qua handle gốc; creationTicks=null, identityVerifiedAtStop=false. Caller lưu proof vào check.json/result.json khi còn ghi được. Đây là forced stop của child timer, không phải nghiệm thu clean shutdown game. Snapshot process Editor/game có sẵn trước/sau khớp; không thao tác các process đó.

## Hồ sơ và điểm dừng

[Manifest](Evidence/MANIFEST.json), [verification](VERIFICATION.json). Hash/raw bytes và bản gzip được đối chiếu; source snapshot chỉ rõ file tooling của các suite cuối. Hồ sơ cũ được giữ và kiểm hash riêng; không tái nghiệm thu144 Automation, smoke hay instrumentation.

Tái lập offline với output mới: `python Scripts/U04/C1Offline.py --out <new-dir>` và `python Scripts/U04/C1IdentityChecks.py --out <new-dir>`. Windows checker có quyền tạo child vô hại riêng, không cấp quyền chạy readiness Build-03. Không chạy lại checker chỉ vì đọc hồ sơ.

Bàn giao để reviewer xét **tooling**. Bằng chứng Windows sửa được lỗi precision giữa FILETIME/CIM; không giải thích mất focus của INVALID lịch sử, không chứng minh readiness game. Probe Build-03 vẫn cần giao riêng; nếu được giao chỉ một probe ID mới và dừng để review dù PASS hay INVALID. Không tự mở counter, overhead, ma trận36+12, C2 hoặc merge.
