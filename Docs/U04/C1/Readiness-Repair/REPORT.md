# C1 readiness tooling — chờ review, chưa chạy package

Phạm vi lượt này: chỉ sửa tooling C1 và kiểm offline. Không khởi động game/Editor, không build, không Automation Unreal, không gửi input thật, không mở counter/profiling/ma trận. GATES.json giữ nguyên INCOMPLETE:0/36 timing,0/12 memory,0/3 overhead. Hai INVALID lịch sử không bị sửa hoặc chạy lại. Kết quả144 Automation và smoke trước đây không được tái nghiệm thu trong lượt này.

## Đường điều khiển để review

`C1Run.parse_args → kiểm Build-03/native inputs/hash Game → snapshot process cần bảo vệ → launch một process mới → pin creation time từ HANDLE gốc của Popen → verify identity → run_probe → select HWND → focus_once → metrics mới → Resume nếu cần → before/W/after → verify identity/stop đúng HANDLE/chờ thoát → result`.

Entry bắt buộc `--readiness-only`, chỉ nhận `--purpose readiness` và `--trace off`. Tất cả purpose cũ, kể cả `method --trace off`, bị argparse từ chối trước mọi launch. Đã bỏ toàn bộ prepare, warmup, begin, vòng combo và quit console khỏi entry. Readiness không nhận số mục tiêu/hurtbox. Không có nhánh chuyển tiếp tới profiling khi PASS hoặc INVALID; cả hai đều kết thúc ở process stop.

File mới độc lập: `C1Identity.py`, `C1Readiness.py`, `C1Win32.py`, `C1Offline.py`; sửa `C1Run.py`. Không sửa `F60Input.py`, `IdentityProcessA.py`, R1b hoặc native inputs. C1Validate/C1Export vẫn import được read/write helper nhưng không có quyền mở ma trận.

## Sáu yêu cầu và cách kiểm

|Yêu cầu|Triển khai / bằng chứng offline|
|---|---|
|Tách đường readiness|Entry success/error replay dùng launcher giả. Popen thật bị monkeypatch để phát lỗi nếu bị gọi; actual realLaunches=0. Static AST kiểm đường gọi, fake console chỉ nhận u01metrics.|
|Phân định foreground|Journal JSONL mở bằng mode x, seq tăng, monotonic, flush+fsync từng mốc. Mỗi row có HWND đích, PID kỳ vọng/thực, creation UTC kỳ vọng và FILETIME ticks thực, foreground HWND/PID, client rect/origin, errors, lastInput/held. snapshotMonotonic phân biệt snapshot gần nhất với thời điểm ghi row. Guard riêng hwnd_invalid, hwnd_pid_mismatch, process_creation_mismatch, foreground_hwnd_mismatch, foreground_pid_mismatch và window_information_error.|
|Khoanh mọi input|Không dùng Client/F60Input. Mỗi cạnh down/up, từng ký tự console, Enter, click và Ctrl/Shift qua cùng emit guard. Wait kiểm lại sau từng sleep. Latch một chiều khi lỗi; không retry focus. Cleanup không finish/release/keyup/quit/restore IME. Các cạnh chưa nhả được giữ trong journal. Nếu journal lỗi, dừng input và vẫn thử stop process sau identity verification.|
|Resume/metrics mới|Mỗi request giữ byte offset, chỉ đọc JSON hoàn chỉnh kết thúc newline mới sau offset. Bỏ line đã dở dang trước boundary; truncation/malformed line/timeout là INVALID. Chỉ một request pending. Kiểm PID, sourceSHA, Game world1, Standalone0, native runID, world/context, pawn/controller/owner và local player. Bind phiên từ mẫu mới đầu tiên, các mẫu sau phải khớp. Playing bỏ Resume. Menu/AwaitingResume cần menuVisible và Resume enabled từ diagnostics mới; tọa độ float và tọa độ sau round đều phải trong client. Chuyển sang physical pixels trong thread DPI context riêng; kiểm origin/rect ổn định, WindowFromPoint/GetAncestor đúng HWND, vị trí cursor thực trước từng cạnh click; chỉ một click. Sau đó yêu cầu metrics mới xác nhận Playing.|
|Pawn nhận W|Mẫu trước phải Playing/windowActive/gateW, không motor lock và không có vận tốc ngang trước input. Giữ offset trước W; timestamp từng cạnh, nhịp.35s và chờ.35s. Cần physical W down accepted mới và W release mới, cùng pawn/phiên/world, worldSeconds tăng, dịch chuyển ngang>=1cm theo control yaw, không chỉ Z; lateral <= max(5cm,25% forward), upper bound theo maxSpeed và world time. Đây là kiểm readiness, không nghiệm thu tốc độ sản phẩm. Chỉ toggle IME một lần nếu chính vùng log hiện tại có key=None và không có W; dòng W/None cũ không cho qua.|
|Identity/offline|Parser Windows argv so từng đối số, không substring. Kiểm full40-hex SHA, exact run ID, executable/userDir/log, map, profile và cả kế hoạch argv; duplicate hoặc argument thừa bị chặn. Quote sau dấu= và đường dẫn có khoảng trắng có roundtrip test. Dùng command fixtures của cả hai run cũ và raw command line đã ghi trong recovery. Kiểm PID reuse khác creation. Live adapter sẽ đối chiếu parser với CommandLineToArgvW; chưa gọi API đó trong lượt offline. Stop kiểm lại identity, rồi kiểm creation/executable trên cùng HANDLE sẽ TerminateProcess; chờ tối đa30s. Có replay kernel giả cho PID reuse/executable sai/timeout.|

`-U01Trace` cần cho menuButtons.Resume vì Build-03 chỉ xuất widget diagnostics khi bTrace bật. Đây là log diagnostics5Hz có sẵn, không phải Unreal Insights timing/memory trace. `-U01SourceSHA` được thêm để kiểm phiên mới. Map, cờ C1 fixture và chuỗi profile B giữ nguyên; không gọi u04c1 prepare/begin. Metrics mới chứng minh freshness/identity theo log offset và phiên; không tuyên bố là request-response có correlation ID, vì binary hiện tại không xuất ID đó và còn có metrics định kỳ.

Focus ban đầu chỉ ShowWindow + một SetForegroundWindow, kiểm ownership trước/sau; không phát Alt, AttachThreadInput hoặc vòng lấy lại focus. Bị Windows từ chối thì INVALID. Guard và SendInput là hai API riêng nên replay không chứng minh tính nguyên tử trên Windows; cần một probe thật được reviewer giao riêng. Không suy diễn nguyên nhân mất focus của hai run cũ.

## Kết quả và bằng chứng

Các suite đều **fake backend/clock/log/input/process/kernel**, không phải game runs:

- Readiness-Offline-01:72 ca,71 đạt; một ca âm UserDir không thực sự đổi đường dẫn Windows do fixture dùng dấu slash sai. Sửa fixture, thêm assert mọi mutation âm phải đổi command. Giữ nguyên suite lỗi.
- Readiness-Offline-02:76/76 đạt, thêm full entry-to-exit success/error và hash Game sai.
- Readiness-Offline-03:84/84 đạt, thêm lỗi journal, lỗi Win32 info, partial log ở boundary, log truncation và stop HANDLE giả.
- Readiness-Offline-04:86/86 đạt trên tooling cuối, thêm vị trí cursor thực bị đổi và tọa độ round ra ngoài client.

[Bảng expected/actual cuối](Evidence/Readiness-Offline-05/cases.csv.gz), [transcript cuối](Evidence/Readiness-Offline-05/transcript.txt.gz), [results cuối](Evidence/Readiness-Offline-05/results.json.gz). Manifest liệt kê hash nguồn/bản gzip, journal từng ca, snapshots entry/exit và mọi suite trước. Tất cả replay guard lỗi có số input_sent sau fault bằng0; gồm lúc console đang có key-down, LMB down, W down và Ctrl IME down. Cleanup identity sai không terminate; không có lần lấy lại focus.

[Manifest](Evidence/MANIFEST.json), [đối chiếu native/lịch sử](VERIFICATION.json). Native inputs so với13b4f34f07bd1cb8e7402984d9479fd5eb9fe2e7 không có diff; historical shared harness và GATES không đổi. Không rehash toàn evidence C1 cũ và không đối soát lại144 tests. Chỉ rehash file của hai INVALID lịch sử để xác nhận bảo toàn.

Để tái lập offline, dùng `python Scripts/U04/C1Offline.py --out <thư-mục-mới>`; script từ chối output đã tồn tại. Transcript/JSON/CSV/journal của fixture đều ghi rõ OFFLINE. Giải gzip ra bản copy để đọc, đối chiếu hash manifest. `C1Win32.Backend` thật chưa được instantiate trong lượt kiểm này; replay stop dùng __new__ và kernel giả.

## Điểm dừng

Bàn giao tooling/diff cho reviewer, chưa cấp quyền chạy package. Khi được giao riêng mới chạy đúng một readiness probe có ID mới, rehash Game Build-03 và snapshot identity hiện hành của process cần bảo vệ. PASS cần journal đầy đủ, metrics mới, W gây dịch chuyển đúng pawn và wait process exit có chứng cứ; bất kỳ thiếu dữ liệu/mất focus là INVALID và dừng. TerminateProcess có wait signaled là bằng chứng process đã thoát theo yêu cầu stop, không phải nghiệm thu clean shutdown sản phẩm.

Cả PASS lẫn INVALID của probe thật đều dừng để reviewer quyết định bước counter/phương pháp. Không tự mở36+12 lượt, overhead, C2, khép C1 hoặc merge. Tooling offline PASS chưa phải readiness runtime PASS.
