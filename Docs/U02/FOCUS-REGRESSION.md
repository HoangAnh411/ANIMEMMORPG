# U02 — hồi quy khựng khi đổi focus

**READY_FOR_REVIEW — cổng kiểm kỹ thuật đã đạt, chờ xác nhận cảm giác chơi lại.** Mở riêng hiệu năng A ↔ B; nghiệm thu combat A–F giữ nguyên. U03 chỉ có kế hoạch trên nhánh riêng, chưa triển khai.

## Nền và phép đo

Nhánh `u02/focus-regression` từ main76b627d. Runtime clone F giữ source85806519f98ef9078c5832e6193bb3bc8d924b54 và hash DLL/Engine trong manifest F. Chỉ sửa launcher/công cụ đo, không đổi Source/Content/Config/Plugins; không build/test lại binary không đổi. Editor gốcPID18756 giữ mở, cấu hình riêng giữ nguyên byte.

Tái sử dụng ProbeGFocus và AnalyzeGFocus của U01, thích nghi guard project/hash/world/owner của F, giữ physical SendInput và click Resume. Mỗi baseline/final10 lượt gồm5 lần A→B và5 lần B→A, theo dõi từ focus-request liên tục15 giây; có W ngay sau click Resume50ms, nhả rồi S mới. Không chờ FPS ổn định sau activation. Chuẩn bị ban đầu3s để thiết lập fixture, không loại frame ở các lượt đổi focus. Fixtures dùng U01NetFixture reset trên NetworkLab để đo transform rõ, không phải đổi gameplay combat.

Thu native frames ba process, UTC/monotonic time, transform/velocity/replication/smoothing, raw game/render/RHI/GPU stat-unit, packet counters; native control samples; video15FPS theo wall time, giữ ảnh qua gap chứ không tăng tốc; ghi từng HWND Editor `IsIconic`/visible/foreground liên tục. Video15FPS không chứng minh độ trễ display hay độ mượt60FPS. Game-thread transform latency không phải present/input-to-photon. Bins0–0,5/0,5–2/2–5/5–15 giây và frame lúc activation tính cả thời gian focus/Resume, không cắt trước lúc ổn định.

## Khoanh vùng và sửa có căn cứ

- Baseline đúng Play-U02-F/ReviewFNetwork cũ, profile client60/server30, internal50%, Lumen atlas2048/RT128MiB/texture256MiB.10/10 lượt tái hiện; Editor thực tế có hai cửa sổ **không minimized suốt capture**, dù launcher đã gọi minimize trước khi clients load. Max ở hai client trong cửa sổ đo khoảng376/505ms, p95 client mới focus đoạn2–5s có lượt27–28ms, đoạn5–15s lên26ms. Render/GPU tăng hơn game thread; GPU khoảng3,9/4GB. Không quy nguyên nhân thành lỗi driver hoặc chỉ thiếu VRAM.
- Các đối chứng riêng cùng runtime: Editor hiện/thu nhỏ thật; một client; tắt diagnostics combat/MCP nhưng giữ instrumentation và native control5Hz; giảm tải Lumen/shadow. Mỗi ca ngắn2 lần là phép khoanh vùng, không thay kiểm final10 lần. Profile cap/input/motor/network không đổi. Ca một client chuyển ra/vào bằng minimize/restore chính client, không gọi nó là A↔B.
- Minimize thật sau khi clients ready cải thiện rõ, nhưng lần xác minh10 lượt chỉ sửa minimize còn một ca client nền p95 khoảng31–34ms kéo dài. Lượt này **không nghiệm thu**, giữ nguyên dữ liệu/video. Không chỉ nhìn client vừa focus để kết luận.
- Đối chứng render giảm tải giữ cả hai client gần17–18ms; vì vậy launcher review cuối vừa xác minh minimize sau ready, vừa giữ headroom: `r.Lumen.DiffuseIndirect.Allow=0`, `r.Lumen.Reflections.Allow=0`, `r.Shadow.Virtual.Enable=0`, `r.ShadowQuality=2`. Chỉ áp khi MemoryBudget của launcher review; không persist Config, không giảm cap hoặc trì hoãn input. DX12/SM6,900×540/internal50%, atlas/pool cũ giữ nguyên. Không nghiệm thu hình ảnh sản phẩm1080p.
- Lưu vị trí cả HWND đã minimized từ trước, kiểm PID/project/owner trước khi thao tác; sau khi clients ready mới minimize/xác minh từng HWND rồi báo ready. Không đóng/restart Editor, không ép minimize liên tục khi người dùng chủ động mở lại Editor. Stop dùng snapshot ban đầu/identity; nếu người dùng mở lại Editor trong lúc review, tải render có thể tăng trở lại và cần ghi trong kết quả.

Vì đối chứng đã phân biệt tải render đồng thời/placement và profile giảm tải, chưa cần quy nguyên nhân cấp driver/present hoặc lấy CPU/GPU trace sâu. Nếu final vẫn tái diễn suy giảm nhiều giây, phải lấy trace frame/CPU/GPU/present, không tuyên bố PASS bằng số trung bình.

## Lượt lỗi và giới hạn

Giữ baseline, minimized-only chưa đạt, đối chứng và final, raw logs/video cùng launcher logs. Stop F từ chối đúng vì thư mục điều tra nằm ngoài F; tạo StopFocus riêng chỉ cho Artifacts/U02/Focus, không bỏ identity guard. Ca tắt toàn bộ control telemetry khiến guard không xác minh được pawn/window nên dừng; không là bằng chứng hiệu năng. Ca DiagnosticsReduced chỉ tắt diagnostics combat/MCP/stat-unit, giữ bộ đo frame/U01FProbe và U01Trace5Hz; không gọi đây là instrumentation bằng0.

Probe/analysis giữ completed trial, không lấy trial đang chạy thiếu activatedUTC để kết luận. Không coi khoảng cách giữa UTC đầu run có prepare và video origin là cùng mốc; video.json ghi origin thực. Resources nvidia/process chỉ có trong phần phiên có sampler, không suy mẫu tài nguyên có ở toàn bộ lượt. Window samples là quan sát thực, bản ghi restore dự kiến không thay nó.

## Kết quả cuối và đối chiếu

Launcher/source scripts chức năng tại35af4ac, các chỉnh thông báo/cleanup và công cụ kiểm ởa55839e; runtime vẫn8580651. Baseline `Session-20261106-194148`; final `Session-20261106-201312`, serverPID8920/A11304/B7076. Mỗi bên10 lượt A↔B,15 giây sau focus; không chờ ổn định mới bấm Resume/input. Bộ đo/video/resource giống loại, dữ liệu thô giữ riêng theo PID/session. [Manifest](Evidence/Focus/MANIFEST.json), [đối chứng](Evidence/Focus/COMPARISON.json), [frame/input gate](Evidence/Focus/After-GATE.json), [input assertions](Evidence/Focus/After-INPUT-ASSERTIONS.json).

**71/71 input assertions và55/55 kiểm tra bổ sung đạt.** Cả hai client đạt ít nhất59 frame trong mọi cửa sổ trượt1 giây tại các lượt đo; không tái diễn suy giảm nhiều giây. P95 của cả hai client trong các đoạn0,5–2/2–5/5–15 giây đều dưới18ms; max client vừa focus18,44–20,47ms theo lượt. Không hứa tuyệt đối không có spike: tính cả client nền, max28,72ms ở0–0,5 giây. Server có spike42,95ms, p95 dưới36,7ms; giữ cap30. Các ngưỡng gate p95 client<25ms/server<40ms và rolling1s≥50 frames chỉ là tiêu chí hồi quy của phép đo này, không thay nghiệm thu hiệu năng sản phẩm U04.

Bảng dưới là **p95 lớn nhất / max lớn nhất** qua10 lượt, đơn vịms; gồm cả foreground/background của từng process, không chỉ lấy client vừa focus. Chi tiết từng lượt và frame tại activation nằm trong analysis.json.gz/SUMMARY.json. Các JSON lớn được nén nguyên nội dung; JSON-ARCHIVES ghi hash/byte trước nén để kiểm lại, không rút gọn mẫu.

| Khoảng từ focus | Process | Trước | Sau |
|---|---|---:|---:|
|0–0,5s |A |55,94 /69,00 |17,76 /28,72 |
|0–0,5s |B |63,81 /107,50 |18,26 /24,46 |
|0–0,5s |Server |37,43 /37,78 |36,64 /37,05 |
|0,5–2s |A |194,06 /357,34 |17,84 /19,11 |
|0,5–2s |B |213,34 /418,09 |17,44 /19,04 |
|0,5–2s |Server |36,24 /46,42 |35,15 /37,15 |
|2–5s |A |316,05 /375,93 |17,72 /19,59 |
|2–5s |B |373,70 /504,58 |17,53 /18,88 |
|2–5s |Server |36,65 /42,93 |35,54 /37,61 |
|5–15s |A |249,82 /358,23 |17,72 /19,26 |
|5–15s |B |308,28 /361,67 |17,48 /20,28 |
|5–15s |Server |36,70 /42,99 |35,49 /42,95 |

Phản hồi từ SendInput tới transform game-thread, ms (UTC có độ phân giải1ms, không phải display latency):

| Chủ thể quan sát | Median trước → sau | P95 trước → sau | Max trước → sau |
|---|---:|---:|---:|
|Owner |10,97 →9,92 |26,91 →15,29 |47,81 →15,43 |
|Server |32,59 →28,86 |61,91 →46,74 |72,81 →47,76 |
|Peer |114,58 →35,20 |141,41 →49,74 |213,80 →50,76 |

Resume không phát attack; nhả/nhấn mới W/S đúng;71/71 checks có native control/physical press và transform. Packet simulation không thêm lag/loss, actual inLost/outLost trong cửa sổ đo đều0. Không đổi authority, replication/smoothing, combat lock, gravity hoặc AwaitingResume. Native source/Content/Config/Plugins không đổi nên **không chạy lại full build/Automation**;61/61 của F là bằng chứng kế thừa, không được ghi thành test mới của lượt này. Có kiểm cú pháp Python/PowerShell và phép đo runtime mới.

Final có2701 samples trạng thái cửa sổ: cả hai HWND458896/393990 thuộc EditorPID18756 minimized suốt capture. Stop dừng đúng server/A/B session cuối; `STOP-VERIFIED.json` ghi Editor còn sống và cả hai show-state khớp ban đầu (floating window vốn minimized vẫn minimized, cửa sổ chính được khôi phục). Không close/restart Editor hoặc tự lưu nội dung chưa lưu. Native frame file cuối đã được cho3 giây **sau khi capture hoàn tất** để ghi buffer trước Stop; khoảng này không đổi15 giây đo, không trì hoãn input.

Đối chiếu log gốc phiên người dùng `Session-20261106-193309`, UTC12:35:05–12:35:20: max A395,259ms, B84,297ms, server34,816ms, khớp phản ánh19:35:05 giờ địa phương. Giữ ba frame logs gốc có hash, không biến chúng thành baseline10 lượt mới.

## Các lượt sau sửa chưa dùng nghiệm thu

- Minimize-only195720 đủ10 lượt nhưng client nền có đoạn p95≈31–34ms: không đạt cổng, dẫn tới profile render headroom cuối.
- Low-render200158 có kết quả frame/input tốt nhưng chỉ theo dõi HWND chính; chưa đủ chứng minh cả floating window. Snapshot theo client-rect bỏ sót cửa sổ minimized; đã đổi sang normal placement, không bỏ guard.
- Phiên200802 đã theo dõi đủ hai HWND, frame/input tốt, nhưng native file A mất phần đuôi do Stop trước flush: chỉ14,69/15s ở lượt cuối, rolling gate báo42 frame vì thiếu log. Giữ GATE lỗi và raw files; không coi nó là khựng thật hoặc dùng nó làm PASS. Phiên201312 lặp10 lượt với flush grace sau capture,55/55 gate gồm kiểm coverage đủ15s cho cả ba process đạt.
- Ca diagnostics-off đầu tiên và Stop ngoài allowed path giữ logs/ghi lý do; bộ đo không dùng dữ liệu từ lượt guard không cho chạy.

Kết luận có giới hạn: có bằng chứng placement Editor và tải render đồng thời liên quan trực tiếp, giải pháp launcher nêu trên đạt trong các lượt đo trên máy hiện tại. Không quy lỗi cho driver/OS-present/VRAM như nguyên nhân duy nhất. Không phải nghiệm thu đồ họa sản phẩm, Server đóng gói, mạng xấu/bù trễ U05 hoặc U03.

## Bản chơi lại

Chạy [Play-U02-F.cmd](../../Play-U02-F.cmd), dừng bằng [Stop-U02-F.cmd](../../Stop-U02-F.cmd), xem [checklist đổi focus](../../Play-U02-F-CHECKLIST.md). [Video trước](Evidence/Focus/Before-Focus.mp4), [video sau](Evidence/Focus/After-Focus.mp4); toàn bộ hash tại [EVIDENCE-SHA256](Evidence/Focus/EVIDENCE-SHA256.json). Runtime DLL SHA-256 giữ `b324e86adfd91b21fa9460f370e132c464f06068ee63867f91d1bb4409b3894d`; Engine `a423ab94410aa4f4cc34d99a2af75240c5d0e376a33d903a3e819fecf1177143`.

Giờ có thể nhờ người dùng xác nhận cảm giác A↔B/Resume/di chuyển ngay; chưa tự ghi người dùng đã chấp nhận. Nhánh dừng READY_FOR_REVIEW, chưa merge hoặc chuyển U03. Nếu chủ động mở Editor trong lúc chơi hai client, tải render có thể tăng; báo rõ thời điểm đó khi phản hồi.
