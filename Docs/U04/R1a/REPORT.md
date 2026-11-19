# U04-B-R1a — bàn giao review input và phương pháp

**R1A_REVIEW_PENDING. U04-B vẫn INCOMPLETE. R1b chưa chạy; không ACCEPTED, merge hoặc khép U04.03.**

Nhánh `u04/b-r1-input-measurement` bắt đầu đúng diagnostic `88f07b01e045a36b9922d3f3988c5d483aa11cbd`. Main nền `18804bfa32b14471df1ffa4bd7aeaed6cd80074c`; B cũ `3f1867ec41768cc836a198c8d865df6de6990c18`. Clone và runs mới nằm riêng tại `Artifacts/U04/B-R1a/Source` và `Artifacts/U04/B-R1a/Runs`.

Nguồn native được build và dùng cho toàn bộ capture: **`8cbcb6a6d6dfc4e29bff8731a6aaab187f887cb4`**. Game SHA-256 **`915887c83acfe0d1668e1b4947807e31217452bd783f185f9f3bc63f67772e25`**; Editor module **`0e43d13c82f49791e2e9ee522697f200c7f7d9ab6efbe392c44c2300aac01d37`**. Selected full Editor/Game/package: `Build-R5-20261119`. UE **5.8.4 / CL58902052**; UBT thực ghi MSVC **14.51.36260**, directory **14.51.36231**, SDK **10.0.26100.0**. Build identity giữ checksum package, receipts, engine, command/log và native Git tree; process records tách PID, creation, executable/module và source/tool identity. Các process đo đều cold; không dùng Live Coding.

## Sửa input và bằng chứng repro

Đường production vẫn là physical preprocessor → controller → interface intent → RPC/authority queue → model. Chỉ nguồn hướng của Dodge đổi sang `ObservedDodgeDirection`: boolean hợp lệ của mỗi binding qua `PhysicalKeys`, `ObservedKeys` và `ReleaseGate`, rồi lấy hiệu hai phía của trục. Snapshot được lấy ngay tại cạnh Dodge. Alias đóng góp một boolean, không cộng hai lần. Các lệnh khác giữ nguyên `IsInputKeyDown`; không đổi reconciliation phím nhả, RPC/settings schema, dispatcher, priority, motor, retained trajectory, epsilon, damage, cooldown hay release gate. OS held-state tiếp tục chỉ là diagnostic/quarantine hiện hành, không quyết định thứ tự cạnh cho Dodge.

Full Automation kiểm helper production: thứ tự cạnh/repeat, bốn hướng/chéo/đối nghịch/thả đối nghịch, rebind/alias, production release-gate policy qua các chuyển trạng thái, snapshot sau gửi và hai controller gắn hai LocalPlayer thật với bộ trạng thái riêng. Hồi quy Windows kiểm thêm đường menu/focus/settings/Retry hiện hành.

**24/24 repro đạt tiền điều kiện input và đúng hướng, hai lượt mỗi ca mỗi cap, đều trong hai lần thử đầu; không có FAIL gameplay hoặc lượt thay thế.** Các batch phím đầu dùng một `SendInput` có thứ tự; raw physical edges/frame/serial mới là bằng chứng cùng frame.

| Chuỗi | Mỗi cap 30/60/120 | Snapshot gửi/nhận | Model | Vận tốc admission |
|---|---:|---|---|---|
| W↓ → Shift↓ cùng frame | 2 | `(1,0)` | tiến | 0 cm/s |
| Shift↓ → W↓ cùng frame | 2 | `(0,0)` | fallback lùi | 0 cm/s |
| W↓ → W↑ → Shift↓ cùng frame | 2 | `(0,0)` | fallback lùi | 0 cm/s |
| W được quan sát qua frame trước → Shift↓ | 2 | `(1,0)` | tiến | được phép có vận tốc; chỉ đối chứng |

[REPRO-MATRIX.csv](REPRO-MATRIX.csv) giữ từng lượt, tốc độ admission, observed/engine-held/gate, snapshot gửi/nhận, model, displacement từ receipt và model origin, duration, FPS/band/max của toàn trace, PID/source/raw SHA. JSON assertions giữ toàn bộ edge/admission/commit và các frame giữ W trước Dodge. Commit trajectory thực đi đúng chiều; số liệu quãng đường ở đây là chẩn đoán, không tính nghiệm thu né.

**Chỉ 2/24 toàn trace repro đạt cadence; 22/24 không đạt cổng cadence và vẫn được công bố INVALID ở cột cadence.** Trace repro bao gồm cả tương tác console mở/kết thúc và mọi frame của buffer; không cắt lại cửa sổ sau khi xem dữ liệu. `PASS` trong assertions repro có scope `REPRO_ONLY`, `acceptance=false`: đó là kết quả input/model, không phải chứng minh gameplay đạt FPS nghiệm thu. Không cộng các lượt này hoặc kết quả B cũ vào R1b.

Hai client Editor thật đều gửi `(1,0)`; server nhận nguyên `(1,0)` trên đúng pawn/life/command và ghi admission Accepted với authority=true. Client không có authority admission. `Network-Direction-Capture-20261119` giữ input Windows, trace độc lập từng process và correlation; network vẫn server30/client60, không thành ma trận mạng mới.

## Phương pháp cadence và capture

Mốc chính cố định là **`sampleEntryWall` tại entry post-actor collector**, lưu đúng một lần; `Event` không ghi đè trường này. `worldBeginWall`, `frameBeginWall`, `collectorExitWall` và legacy `wall` chỉ để đối chiếu. Đây là **cadence game-thread của package D3D12/SM6 có render**, không phải GPU present/scanout. Native raw kiểm đúng Solo Game world, một sample mỗi frame, continuity/counter alignment, clock đơn điệu, focus, source/pawn/reset và cấu hình thực.

Giữ profile1280×720/internal50%, atlas2048, RT minimum128 MiB, streaming256 MiB, Lumen indirect/reflections0, virtual shadows0, shadow quality2, background idle0, VSync0; dilation1 và fixed timestep/frame tắt. Không thay smoothing. Actual cvars và viewport nằm trong từng frame. Chỉ cap30→60→120 thay giữa các process số liệu.

FPS = số khoảng frame / tổng wall interval. P50/P95/P99 nội suy rank `(n-1)*p`. Cổng không đổi: mean ±5%, ≥95% interval trong ±10% chu kỳ, không interval >2 chu kỳ. Cửa sổ idle đã được script chốt trước capture: first sample worldTime+1.5 đến +16.5, giữ sample kẹp trái/phải; nội suy `alpha=(t-left.worldTime)/(right.worldTime-left.worldTime)`. Sleep Python chỉ giữ đủ acquisition, không định nghĩa15 giây đo.

**9/9 idle15-world-second windows đạt cadence chính**, không video; [COLLECTOR-MATRIX.csv](COLLECTOR-MATRIX.csv) và raw JSON có toàn bộ percentile/histogram, wall duration, biên và sample gốc.

| Window | FPS thực GT | Trong dải ±10% | Max interval ms | Collector P95 ms |
|---|---:|---:|---:|---:|
|30-1|30.000749|100.0000%|35.3863|0.2509|
|30-2|30.000512|100.0000%|34.6254|0.2460|
|30-3|29.999499|100.0000%|35.1087|0.2171|
|60-1|59.999455|100.0000%|17.4172|0.2079|
|60-2|59.999677|100.0000%|17.5061|0.2060|
|60-3|59.998712|100.0000%|17.6475|0.2069|
|120-1|119.990458|99.8334%|9.3410|0.2300|
|120-2|119.993691|99.9445%|9.0577|0.2318|
|120-3|119.991686|99.8890%|9.2344|0.2252|

CSV/JSON dùng cm và giây; bảng trên đổi thời gian sang ms. Chi phí collector entry→exit bao gồm tạo JSON objects/arrays/strings, getters, đọc cvar/viewport/input diagnostics, duyệt history, stamp/event và buffer growth. Exit được stamp sau chèn buffer; chi phí stamp cuối/return không nằm trong con số. Ngoài collector vẫn còn product input/movement/render, log key edges và metrics `U01Trace` khoảng5 Hz với serialization/logger calls; không tuyên bố zero allocation, zero log I/O hoặc zero overhead. Native frame/action/hit không được serialize/flush chi tiết đồng bộ mỗi frame; buffer serialize/file flush sau end.

Numeric path không gọi ImageGrab, chuyển màu, encoder, screenshot hoặc video writer trong cửa sổ; ảnh chụp trước begin/sau end. Guard HWND/PID/focus mỗi50 ms; native focus mỗi sample. Một process minh họa riêng dùng cùng package/profile/fixture tại target120, video1280×720/30FPS/60 frames có nhãn `ILLUSTRATIVE ONLY`. Ảnh và video đã xem kiểm tra cảnh lab có render. Video không chứng minh cadence hoặc gameplay120 của bất kỳ lượt số liệu nào.

13 nhóm synthetic đạt: cap120/thực60, FPS count/total thay vì mean instantaneous FPS, missing/duplicate/long frames, immutable entry/no clock fallback, percentile/threshold boundaries, interpolation/boundary selection, config/source/focus/reset, hit trùng/sai life/action/crit/HP và phân biệt valid buffered combo FAIL với lỗi input ngoài buffer. Candidate analyzer **`u04r1-entry-2`** còn dùng đúng `Received.receivedPosition` cho origin né và lấy khung bao từ receipt qua release gate; synthetic kiểm origin model khác receipt và thiếu receipt. Cadence/repro/idle tính lại khớp assertions lưu; thay đổi candidate không đổi nhãn hoặc timestamp của B cũ và chưa chạy nghiệm thu gameplay R1b.

## Hồi quy và bảo toàn

Cold-clone MCP Automation **144/144 Success**, exact expected/discovered/executed names (baseline140 +4 mới), actual loaded DLL khớp selected build. Smoke **3/3 map**. Windows regression: combat24, defense15, dodge/focus38, movement26, settings Save/Quit5 và cold reopen2 — tất cả đạt. Dedicated Editor +2 clients: direction transport/admission cả hai đạt, network26, independent comparisons41 và reconnect feedback watermark đạt. Các capture hồi quy có video là hồi quy thường, không được dùng cho cadence matrix.

Native source cuối không khác selected build. Normal package processes không bật fixture B; opt-in chỉ qua cờ `-U04BFPSFixture`, không thêm vào launcher/menu thường. Handoff có audit args/source/render/imported guards. Source/tool identity được tách: capture đầu dùng tool e972d00, resume/video dùng fb4eec1; native/binary không đổi. Actual imported helper byte hashes được giữ riêng; một helper có CRLF/LF khác giữa original/fresh clone nhưng code chuẩn hóa giống nhau.

**4.493 protected file/artifact hashes đạt**: workspace/private preflight, launcher và bằng chứng/package U03/U04-A, B/diagnostic lịch sử, module/engine và package mới. B seal391 và diagnostic seal197 được kiểm riêng. Original main vẫn giữ dirty/untracked state ban đầu; không stage nội dung dữ liệu riêng. Editor gốc PID4296, creation `2026-11-19T04:32:06.6244960Z`, executable và hai HWND/show/normal rectangles khớp preflight sau khôi phục. Không save/close/restart Editor gốc; không còn process Editor/Game R1a. Dung lượng thực trước clone100897087488 bytes; không cleanup hay tải engine.

## Lỗi và warning giữ nguyên

- Ba build Editor đầu lỗi trong test mới (shadowing/namespace `Flags`/`Forward`, rồi accessor qualification); log/commands/results và các commit sửa đều giữ. R4 full build không được chọn vì trace authority cần correlate command ID thay vì trajectory sequence; sửa read-only trước R5. Package R4 vẫn giữ và có index hash riêng. Tất cả gameplay captures chỉ dùng R5.
- Remote clone ban đầu được ngắt khi chưa quan sát object transfer; dùng local clone `--no-hardlinks` từ diagnostic đúng SHA và đặt origin về GitHub. Warning preflight và partial directory nếu có được giữ; không sửa clone diagnostic.
- UBT cảnh báo MSVC14.51 mới hơn preferred14.50; các C4996/deprecation và test-world mesh/socket warnings giữ trong log. Không đổi engine/toolchain để che warning.
- Idle120-1: đọc file khi native writer đang flush gây `PermissionError`. Ledger aborted không bị sửa; original raw có end marker đầy đủ và đạt cùng cửa sổ đã chốt. Phân tích lại buffer đã đóng; chỉ capture idle2/3 chưa từng chạy. Chờ closed-buffer nay nằm sau end. Không có control thay thế hoặc lượt chọn thêm.
- Restore ban đầu để một floating HWND còn minimized dù rectangle đúng. Giữ observation thất bại; identity-guarded SW_RESTORE riêng HWND lệch và original placement đã khôi phục đúng cả hai cửa sổ. Helper mới giữ cách phục hồi này. `FINAL-HOST.json` và `RESTORE-RECOVERY.json` xác nhận trạng thái cuối.
- 22 whole-trace cadence INVALID của repro vẫn hiện rõ; không nới ngưỡng, bỏ frame xấu hoặc dùng world-start thay primary entry.

## Hồ sơ và điểm dừng

[Contract](CONTRACT.md), [repro từng lượt](REPRO-MATRIX.csv), [collector từng cửa sổ](COLLECTOR-MATRIX.csv), [manifest R1b đề xuất](PROPOSED-R1b-MANIFEST.json), [manifest R1a](Evidence/Review-20261119/MANIFEST.json). Seal giữ raw input/frame/action/hit, assertions/CSV, process/build/tool identities, media đúng vai trò, mọi aborted/failed observations và SHA-256 raw/published. Dữ liệu account/token riêng được redact trong bản công bố, có khai báo transformation; raw gốc giữ tại host. Các raw gameplay samples không bị summarize thay thế.

Reviewer có thể chạy `VerifyEvidenceB.py <manifest> --published-only`, rồi `RecomputeR1a.py --published Docs/U04/R1a/Evidence/Review-20261119 --out <new-directory>` để tính lại từ gzip raw. Hai CSV trực tiếp là bản sao byte của `Analysis-Review-20261119`; final gates giữ hash liên kết. Các analysis versions trước vẫn còn, không xóa.

Đề nghị reviewer xem riêng bản sửa input và phương pháp, bao gồm scope PASS repro/cadence và các recovery warnings. **Dừng tại review R1a. R1b chỉ được khởi động khi được giao sau khi reviewer chấp nhận; B chưa READY_FOR_REVIEW toàn bộ. Không merge, C/D, tối ưu renderer, mạng xấu hoặc Server đóng gói.**
