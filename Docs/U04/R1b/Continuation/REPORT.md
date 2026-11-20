# U04-B-R1b — tổng hợp phần kế thừa30 và tiếp tục60/120

**Post-review: U04-B technically ACCEPTED at `251335895394c5ddb260d875a05d26462fbd1d70`, with no blocking findings in scope. Closure/merge authorized2026-11-20. [Acceptance B](../../ACCEPTANCE-B.md). READY_FOR_REVIEW below records the handoff; manifests/ledger/raw/CSV/verdicts remain unchanged. Native/package/analyzer unchanged; no build/gameplay/Automation or Editor action for closure. C/D remain unstarted.**

**READY_FOR_REVIEW.** Đủ69/69 PASS theo21 ô ma trận và21/21 video minh họa riêng. Reviewer quyết định ACCEPTED và quyền khép U04-B; chưa merge hoặc triển khai U04-C/D.

Đợt tiếp tục được giao từ `e1ba0d6cc2d1d8c6acdc4f329c82c68eba5e4b24`, trên nhánh `u04/b-r1b-fps-acceptance`, clone/output riêng `Artifacts/U04/B-R1b-C1/Source` và `Runs`. Không mở lại hoặc sửa manifest/ledger/evidence của batch R1b cũ đang halted. Kế thừa đúng23 PASS30 FPS đã hoàn thành trong R1b; không cộng bất cứ kết quả B cũ, repro R1a hoặc idle nào.

| Ca | 30 FPS, kế thừa | 60 FPS, mới | 120 FPS, mới |
|---|---:|---:|---:|
| Đi5000cm/10 world seconds | 3/3 PASS | 3/3 PASS | 3/3 PASS |
| Sprint7000cm/10 world seconds | 3/3 PASS | 3/3 PASS | 3/3 PASS |
| Né tiến300cm | 3/3 PASS | 3/3 PASS | 3/3 PASS |
| Né lùi300cm | 3/3 PASS | 3/3 PASS | 3/3 PASS |
| Né trái300cm | 3/3 PASS | 3/3 PASS | 3/3 PASS |
| Né phải300cm | 3/3 PASS | 3/3 PASS | 3/3 PASS |
| Combo1–2–3 | 5/5 PASS | 5/5 PASS | 5/5 PASS |

69 cửa sổ bắt đầu và69 PASS, gồm23 kế thừa và46 mới. Không FAIL/INVALID/crash hoặc lần thử vượt số cần ở phần số liệu. Ledger mới không có setup error, timeout, identity mismatch hoặc retry Start. Lỗi chuyển process cũ vẫn nằm nguyên trong ledger/evidence cũ và được liên kết dưới đây.

## Nguồn từng trial và hai chuỗi manifest

[BATCH-MANIFEST.json](BATCH-MANIFEST.json) mới SHA256 **`6134a608be951604abd80e1ff464024fe063a227f3f895f24a6fdffd2af5be32`**, commit đóng băng `0618637`. Tool orchestration đã commit trước capture: **`a201b850c9f90a07703a64116d2afe4bf6e322ab`**. Manifest pin18 file runtime, cùng native/package/analyzer/profile/case limits/window rules như manifest cũ; order numeric mới chỉ60→120. Ledger/initial snapshot mới ở Runs, tách khỏi old halted ledger.

23 trial `r1b-fps30-*` được liệt kê nguyên trong trường inheritance, trỏ raw/assertions ở `B-R1b/Runs/Numeric-fps30-20261120`. Manifest cũ SHA256 **`2668ba4aff505a5094ec887811a1995803a98c1ddc44dea255318d35fb820cba`**; halted ledger SHA256 **`46bdd285f600db97ccc172596b170490feaf20cc11851c8364fef611524bbc08`**; evidence manifest cũ SHA256 **`7e20e62a742ad2f37e937840e3ff11cd61a5f250d27159f32e7dd4ba6b69aa2f`**. Không sửa nhãn hoặc cửa sổ của chúng. 46 trial `c1-r1b-fps60-*`/`c1-r1b-fps120-*` thuộc manifest tiếp tục, raw ở Runs mới. [TRIALS.csv](TRIALS.csv) ghi `sourceBatch`, `inherited`, `sourceManifestSHA256`, raw/assertions SHA cho từng trial; [MATRIX.csv](MATRIX.csv) giữ đủ21 ô và số lần thử.

## Lỗi cũ và sửa orchestration

Lỗi cũ xảy ra trước cửa sổ60: Stop-Process trả về nhưng PID13764 chưa biến mất khỏi CIM, Start kế tiếp bị guard chặn `Another R1b package process is active`. Batch cũ vẫn halted/INCOMPLETE, không tính lỗi setup này thành lượt đo60. Người dùng cho phép tiếp tục bằng manifest/ledger mới và giữ23 PASS30.

Sửa tool giữ executable/hash/command scope và PID+creation identity trước Stop, pin OS handle, gửi tối đa một yêu cầu rồi kiểm identity mỗi250ms, deadline30s. Không lặp kill. PID tái sử dụng, mismatch, timeout hoặc session khác còn sống đều cấm Start và lưu lỗi. Nếu đã thoát trước Stop, ghi ALREADY_EXITED không kill. Start bắt buộc proof thoát thành công, rehash process record, kiểm PID cũ vắng và guard session R1b. So handle creation với CIM tại đúng độ chính xác microsecond của CIM; không đổi bất kỳ timestamp/epsilon gameplay nào.

Offline7 ca qua helper production đạt: thoát ngay/chậm/đã thoát, PID tái sử dụng trước/trong chờ, timeout và session khác còn sống; thêm kiểm độ chính xác timestamp handle/CIM. Bảy kiểm harness offline hiện hành đạt. Không rebuild, UE Automation hoặc gameplay hồi quy vì thay orchestration. Input/session/client/analyzer không đổi; đổi prefix trial và điều kiện order tiếp tục chỉ để tách provenance/cho phép media sau60→120.

Proof00 xác nhận PID13764 đã thoát,0 Stop. Năm process mới mỗi process có đúng1 Stop và EXIT_CONFIRMED, thời gian hoàn tất khoảng1,03–1,27s. Không có retry Start/kill hoặc tác động PID tái sử dụng. Toàn bộ proof lưu ở Runs/Lifecycle và được publish.

## Binary, process và phương pháp giữ nguyên

Native **`8cbcb6a6d6dfc4e29bff8731a6aaab187f887cb4`**, analyzer **`u04r1-entry-4`**, working-byte SHA256 **`f792caa7ca850abf333b502083d67d7c806fea159bb90d406b2cd87973cf8cd0`**. Tái sử dụng R1a Build-R5-20261119 sau full48-file package/module/engine/commandlet hash checks trước từng process và cuối đợt. Game SHA256 **`915887c83acfe0d1668e1b4947807e31217452bd783f185f9f3bc63f67772e25`**; Editor module **`0e43d13c82f49791e2e9ee522697f200c7f7d9ab6efbe392c44c2300aac01d37`**. Editor module là provenance build kế thừa; process package dùng Game PE ghi riêng. UE5.8.4/CL58902052; UBT thực kế thừa MSVC14.51.36260 (directory14.51.36231), SDK10.0.26100.0. Không build mới/Live Coding. Kế thừa rõ144/144 Automation cùng hồi quy native combat/dodge/focus/settings/ba map/dedicated Editor+hai client của R1a đã được chấp nhận.

Numeric60 PID10636 và numeric120 PID4564 là hai process Solo rendered lạnh riêng. Ba process media riêng chạy30/60/120 sau toàn bộ số liệu. Mỗi process có readiness mới: exe/source/native module provenance, Game world/map/pawn, clock tăng, Windows input tác động đúng pawn, cvar/viewport thực; warmup30 giây sau readiness, vượt cap stable tối thiểu10 giây. Process records pin source/tool/repository HEAD, creation identity, command, preferences/output mới và previous-stop-proof hash.

Profile giữ1280×720/internal50, VSync0, background idle0, Lumen atlas2048, RT minimum128MiB, streaming256MiB, Lumen indirect/reflections0, virtual shadows0, shadow quality2. Dilation1, fixed timestep/frame tắt, smoothing giữ nguyên. Không hạ chất lượng hoặc thay motor/collision/damage/cooldown/input delay. Windows input có PID/focus guard50ms; telemetry native focus mỗi frame. Reset/prepare ngoài cửa sổ; lượt số liệu không grab ảnh/convert/encode/video trong cửa sổ, ảnh trước/sau và flush sau end.

Clock chính duy nhất **`sampleEntryWall` tại post-actor collector entry**; world-start/core-begin/collector-exit chỉ để đối chiếu. Đây là cadence game-thread của package có render, không phải GPU present/scanout hoặc nghiệm thu1080p. FPS = số interval/tổng wall time, không trung bình FPS tức thời. Cổng nguyên ±5% mean, ≥95% interval trong±10% period, max≤2 period, liên tục frame/clock và nguyên focus/config/source. Không lọc frame hoặc chọn lại timestamp/window sau kết quả.

Đi/sprint: raw entry-4 chọn vận tốc500/700cm/s ổn định0,5 world seconds, sau đó nội suy đúng10 world seconds: alpha=(biên−worldLeft)/(worldRight−worldLeft), position=left+alpha×(right−left). Assertions giữ hai sample kẹp mỗi biên, CSV giữ wall duration/path/lateral. Cả18 lượt đi/sprint sai số0cm, path5000/7000cm, lệch ngang0.

Né: 36 lượt đều edge hướng trước Dodge trong batch SendInput có thứ tự, đúng command/pawn/life qua intent→receipt→admission→trajectory; authority `velocityBeforeBatch` ngang0cm/s. Snapshot gửi/nhận/model đúng hướng. Sai số quãng đường lớn nhất toàn bộ khoảng0,000545cm, trajectory0,25s, release deadline0,35s. Receipt-origin và cadence tới release gate cùng các frame kẹp biên giữ nguyên entry-4. Không dùng frame trước thay admission.

Combo: cả15 lượt đúng ba action liên tục, ba hit riêng60/70/90, HP giảm220, cùng target life và crit-off; Windows edges/admission/buffer được kiểm bằng analyzer nguyên bản. Authority duration mọi lượt `1.4499999999999886s`, sai số nhỏ hơn1µs; không nới theo observation frame.

| FPS | Mean FPS min–max từng lượt | In-band thấp nhất | Max interval lớn nhất |
|---:|---:|---:|---:|
| 30 | 29,9874–30,0538 | 100% | 35,7695ms |
| 60 | 59,9322–60,1264 | 100% | 18,1775ms |
| 120 | 119,8168–120,0856 | 95,3488% | 9,5482ms |

Đây là min/max để đọc nhanh, không thay dữ liệu từng trial. CSV/JSON giữ FPS, in-band, P50/P95/P99/max, histogram, sample biên và sai số từng lượt. Output tính lại mới `Runs/Recomputed-Combined-20261120` đối chiếu toàn69 raw SHA, stored assertions và verdict; tất cả khớp, không thay kết quả lịch sử.

Collector entry→exit trên15133 frame của cửa sổ được chọn: P50≈0,1873ms, P95≈0,2623ms, P99≈0,3470ms, max≈0,6527ms. Collector/native buffer vẫn có allocation, input tracing và guard có overhead; không tuyên bố đo không overhead. Native flush ngoài cửa sổ; giữ raw clocks để reviewer tính lại.

## Media, warnings và bảo toàn

21 video là bảy ca mỗi mức30/60/120, cùng binary/profile/fixture trong process riêng sau số liệu. Tất cả label ILLUSTRATIVE ONLY, video30FPS; không tuyên bố chúng đồng thời với số liệu hoặc chứng minh game120FPS. MEDIA-CHECKS kiểm21 file giải mã được frame giữa,1280×720,30FPS và frame count khớp recorder. Raw/input/ảnh trước-sau của media được giữ riêng, acceptance=false. Không ca gameplay bị dừng nên không có video phải bỏ qua.

Runtime năm process mới có58 dòng Warning,0 Error/Fatal theo bộ lọc: audio48000/44100 và startup thực thi ExecCmds trước warmup; chi tiết RUNTIME-WARNINGS.json và Game.log được giữ. Hai dòng audio ở media60,14 dòng ở mỗi process còn lại. Build không chạy nên không có build lỗi mới. Lỗi chuyển process cũ và các warning lịch sử không bị xóa/đổi nhãn.

Dung lượng thực trước clone tiếp tục khoảng111GB; sau clone preflight khoảng105GB, reserve25GiB. Không cleanup, tải engine, sửa config/private/Maintenance hoặc artifact cũ. Snapshot bảo vệ42232 file, mở rộng thêm source/run R1b cũ. Kiểm cuối phải khớp mọi hash và private status trước publication.

Editor gốc PID2136/creation `2026-11-20T04:22:45.5962180Z` không đóng/compile/đổi preference. Thu nhỏ sau fresh readiness, khôi phục sau process cuối. HOST-PROTECTION xác nhận creation/exe/HWND, show/normal rectangles và toàn dictionary placement khớp trước đợt; không còn game R1b. Main18804bfa và R1a f158ce1c được giữ nguyên. Không stage dữ liệu riêng.

## Replay và điểm dừng

[Evidence manifest](Evidence/Review-20261120/MANIFEST.json) liên kết raw/published mới và chain manifest cũ. Có ledger toàn bộ attempts, initial ledger, process/build identity, Windows events, raw frame/action/hit, per-trial assertions, recompute mới, CSV/matrix, lifecycle proof/tests, video/ảnh đúng vai trò, warning và protection checks. Old evidence vẫn được verify riêng, không republish hoặc rewrite.

Trên capture host: `python Scripts/U04/RecomputeContinuationR1b.py --manifest Docs/U04/R1b/Continuation/BATCH-MANIFEST.json --out <thư-mục-mới>`; verify cả manifest evidence bằng VerifyEvidenceB.py. Trên host riêng: verify published-only, giải gzip raw nguyên byte theo manifest, chạy AnalyzeR1.py entry-4 với case/FPS tương ứng; raw SHA bảo đảm cùng đầu vào. Các sample gốc và công thức đủ để reviewer tính lại, không chỉ summary.

Chỉ bàn giao READY_FOR_REVIEW sau khi69 PASS,21 illustrations, source/package/process identity, recompute, raw/published hashes và bảo toàn cuối đều đạt. Chưa ACCEPTED, merge, khép B hoặc U04-C/D. Báo cáo/manifest cũ tiếp tục phản ánh trạng thái halted lịch sử; kết luận tổng hợp thuộc đợt tiếp tục này.
