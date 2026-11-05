# U01-F — Điều tra FPS và độ trễ sau review

**?? NGHI?M THU U01-F theo x?c nh?n ng??i d?ng t?i `2bd9b565500042d25c8a8958df481f55175a753d`.** Ph?m vi: dedicated Editor server v? hai client, profile client60/server30; ch?a bao g?m Server ??ng g?i, hi?u n?ng ?? h?a s?n ph?m1080p ho?c G. Gi? native diagnostics `edf885ac79d900977a43a404019eadce0244ed47`, package ngu?n `0f02c77bc14fc4c727ba8694223f8cfc5a655c31`, to?n b? hash v? l?ch s? ki?m ch?ng. Ng??i d?ng cho ph?p kh?p h? s?/push/fast-forward F v?o main r?i tri?n khai ri?ng G trong clone, Editor g?c gi? m?. C?c tr?ng th?i ch? review b?n d??i l? l?ch s? tr??c x?c nh?n n?y.

**Cập nhật hiện tại — F60:** đã đo A–D đủ120s/lượt, đối chứng logging và kiểm liên tục300s. Chọn mặc định **hai client60 FPS / dedicated server30 FPS** trên profile review hiện tại; vẫn **READY_FOR_REVIEW, chưa nghiệm thu hoặc merge F**. Native diagnostics nguồn `edf885ac79d900977a43a404019eadce0244ed47`, package giữ nguồn0f02c77 và đã kiểm lại hash. Chi tiết ở mục F60 cuối báo cáo và [manifest F60](Evidence/F60/MANIFEST.json). Các kết quả30FPS trước đó là kết quả dưới cap30, không phải FPS tối đa của máy.

**READY_FOR_REVIEW bản sửa môi trường chạy F; chưa nghiệm thu/merge F, chưa sang G.** Giữ các mục điều khiển người dùng đã đánh dấu đạt trong checklist. Lượt review mới yêu cầu điều tra FPS thấp và cảm giác B thấy A chậm khoảng một giây; không dùng kết quả điều khiển để tự nghiệm thu phần này.

Native diagnostics/build/package nguồn **`0f02c77bc14fc4c727ba8694223f8cfc5a655c31`**; native trước đó `df897f6` và hồ sơ F cũ giữ nguyên lịch sử. Bản sửa thực thi ở scripts launcher/host, không thay motor, camera/input, saved moves, animation, attachment, tần suất replication hoặc CMC smoothing. [Manifest mới](Evidence/F-Performance/MANIFEST.json), [số đo đầy đủ](Evidence/F-Performance/RESULTS.json), CSV từng frame và video trong cùng thư mục. Main/origin main vẫn `9936322`.

## Đã phân biệt được nguyên nhân nào

**Client bị nghẽn tài nguyên đồ họa khi chạy đồng thời Editor và hai client trên RTX 3050 Ti Laptop 4 GiB.** Trạng thái thật trong runtime là `t.MaxFPS=30`, `t.IdleWhenNotForeground=0`, `r.VSync=0`, `bThrottleCPUWhenNotForeground=false`; không chỉ suy ra từ command line. Khi A foreground, B chỉ 4,63 FPS; đổi foreground sang B thì A còn 3,70 FPS. Background client có frame tới 1112 ms trong hai lượt input hợp lệ; trước đó lượt chẩn đoán chưa nhận được W còn ghi frame 2189 ms. Không đổ toàn bộ cho UE background throttle vì các gate đó thực tế đang tắt.

NVIDIA telemetry ghi VRAM resident khoảng 3,8/4 GiB và mẫu tải GPU 98%; Windows GPU Process Memory ghi shared usage (ví dụ A 546,9 MB, B 211,0 MB, Editor 250,2 MB ở lượt profile chưa thu nhỏ Editor). Đây là bằng chứng áp lực bộ nhớ cùng kết quả can thiệp, không khẳng định đã đo trực tiếp số page fault của driver. Chỉ giảm render resolution xuống 50% không sửa được; chỉ profile cache/pool cũng chưa đủ; chỉ thu nhỏ Editor với chất lượng cũ vẫn còn frame gần một giây. Tổ hợp profile bộ nhớ + internal resolution 50% + thu nhỏ Editor đã loại bỏ các frame dài trong bốn lượt kiểm cuối. Renderer vẫn **DX12/SM6/Lumen**, không chuyển backend hoặc tắt Lumen/ray tracing để lấy số đẹp; không đổi project config, preset sản phẩm hay SaveGame settings.

**Server ẩn có thêm vấn đề Windows timer.** Khi Editor thu nhỏ, server có lúc chỉ 21,3 FPS dù cap vẫn 30. Engine `WindowsPlatformMisc.cpp:1076` đã gọi `timeBeginPeriod(1)`. Dùng process-local `ProcessPowerThrottling / IGNORE_TIMER_RESOLUTION` (SDK 10.0.26100.0, processthreadsapi.h) để yêu cầu Windows tôn trọng request có sẵn, không tăng tick rate. Thử đảo A/B/A riêng trên cùng PID21756, không đổi cvar/tần suất mạng:

| Hint process server | FPS đo | Median frame |
|---|---:|---:|
| Tôn trọng timer request | 29,969 | 33,339 ms |
| Cho phép bỏ qua timer resolution | 21,333 | 46,920 ms |
| Tôn trọng lại | 29,975 | 33,357 ms |

ControlMask/StateMask, UTC và frame data có trong TimerABA/RESULTS. Đây là scope một process dedicated, giữ các power flags khác, không sửa global Windows/NVIDIA power policy, registry hoặc engine. Process kết thúc thì hint hết hiệu lực.

## Không thấy hàng đợi mạng cố định một giây

Packet simulation settings thực tế ở server và cả hai client: lag/min/max/order/dup/loss/incoming lag/loss đã đo đều bằng0 (chín trường trong RESULTS; không suy từ việc không có flag launch). Không tuyên bố có native sample riêng cho variance/jitter/buffer-bloat. ICMP localhost 4/4 phản hồi dưới 1 ms, 0 loss; đây chỉ kiểm stack localhost, không thay game RTT. Engine ping client nền trước sửa median khoảng 232–235 ms và connection AvgLag khoảng 217–250 ms, có cả thời gian client xử lý frame. Sau sửa game ping các client median khoảng 31–40 ms, connection AvgLag khoảng 31–35 ms. Không gọi đây là wire latency thuần.

Actor giữ nguyên cấu hình **NetUpdateFrequency100, Min2**, adaptive update off; actual receive coalesces theo tick/frame. CMC giữ **Exponential**, smooth location **0,10 s**, không tắt hoặc rút ngắn smoothing. Trong W-held windows, changed-position packet observations trước sửa median390–458 ms, max tới1156 ms; sau sửa median34 ms, p95 67 ms, max68–100 ms. CSV/JSON vẫn giữ cả khoảng ngừng W hai giây có chủ ý; không gọi khoảng actor đứng yên đó là mất packet. Số đo packet-change không phải số packet UDP hoặc một lời hứa actor luôn gửi100Hz.

Đo cùng input Windows thật ở ba process, chung host UTC, mỗi game frame: vị trí capsule A → authority server → replicated movement B và mesh transform B. Đổi focus dùng HWND/PID guard; không lấy Editor world làm Game world. Collector bổ sung source/PID/world/context/net mode/role/GUID từ native Game-world identity. Mesh là presentation transform trên game thread, **không phải GPU scanout/photon**. Packet receive quan sát ở frame client nên độ phân giải phụ thuộc frame; các stage bao gồm tick scheduling, không tách được UDP wire transit riêng.

## Kết quả so sánh và bốn lượt chạy cuối

| Lượt | Server FPS | A FPS | B FPS | Frame max client nền |
|---|---:|---:|---:|---:|
| Trước, A foreground | 29,82 | 29,99 | 4,63 | 443 ms |
| Trước, B foreground | 29,94 | 3,70 | 25,02 | 1112 ms |
| Sau, A foreground | 29,88 | 30,00 | 30,00 | 36 ms |
| Sau, B foreground | 29,91 | 30,00 | 30,00 | 35 ms |
| Lặp A foreground | 29,92 | 30,00 | 30,00 | 35 ms |
| Lặp B foreground | 29,96 | 30,00 | 30,00 | 35 ms |

Mỗi lượt input cuối 13 giây, đi/dừng/sprint/nhảy/tiếp đất và menu; bốn lượt tổng52giây, không gọi đây là session10phút hoặc nghiệm thu FPS G. Frame p95 server35 ms, client34–35 ms. Server headless không có foreground game viewport: foreground render test ở server là N/A; server đo liên tục khi A/B lần lượt foreground. Các lượt trung gian và can thiệp không hiệu quả vẫn có trong RESULTS. Hai phép SingleClient/Neutral không thực sự đổi focus theo native flag nên **không dùng làm chứng cứ foreground/background**. Lượt OriginalMinimizedA chứa thay đổi timer giữa lượt, không dùng làm phép so sánh timer độc lập.

| Lượt | Input→A/B owner simulation | Owner→server frame | Server→peer packet observed | Packet→mesh bắt đầu đổi |
|---|---:|---:|---:|---:|
| FinalA | 13,46 ms | 17 ms | 29 ms | cùng frame |
| FinalB | 13,39 ms | 31 ms | 28 ms | cùng frame |
| RepeatA | 1,94 ms | 8 ms | 20 ms | cùng frame |
| RepeatB | 24,32 ms | 17 ms | 10 ms | cùng frame |

Tổng input→peer mesh onset khoảng **30–72 ms** trong bốn mẫu đầu chuyển động này; “cùng frame” không có nghĩa smoothing đang bằng0. RESULTS ghi offset mesh/capsule trong lúc di chuyển; capsule proxy còn extrapolation, không dùng offset đó làm độ trễ tuyệt đối tới authority. Camera observer được xoay bằng input chuột thật ở video Repeat để nhân vật kia nằm trong FOV; lượt đầu xoay quá ít, không suy độ trễ từ thời điểm actor vừa lọt vào màn hình. Không dùng screenshot đứng yên thay video chuyển động.

Phiên cuối `Reviews/Session-20261105-132938`: server **18112**, A **15460**, B **1076**, Game world NetworkLab type1, modes1/3, source0f02c77. Server không local player/UI, mỗi client một autonomous pawn; userDir/log riêng. Input tool xác nhận W thật ở menu trước khi đo; bộ gõ ngoài từng biến W thành None ở lượt sớm, đã dùng quy trình toggle/restore có kiểm log, các lượt đó không dùng để đo đường chuyển động. Packet simulation không bật, không thêm camera RPC hoặc teleport locomotion.

## Bản sửa launcher và kiểm chứng hồi quy

`StartFSession -MemoryBudget` là **profile review cùng máy 4 GiB**, ghi rõ ra console: Lumen surface cache atlas2048, render-target pool minimum128 MiB, texture streaming pool256 MiB, internal screen percentage50% (900×540 window →450×270 internal). Đây là đánh đổi độ nét/bộ nhớ để chạy hai client cạnh Editor, **không chứng minh cấu hình đồ họa gốc đã ổn** hoặc chất lượng sản phẩm đạt. Profile chỉ per-process, không ghi settings. Giữ cap30/tần suất network/smoothing. Server được áp timer hint sau khi xác minh PID/project/userDir/role; startup lỗi dừng đúng process đã tạo, không để server ẩn treo khi retry.

`ReviewF` dùng profile trên, thu nhỏ đúng cửa sổ Editor gốc sau khi kiểm project/PID, giữ process và tài liệu mở, lưu WINDOWPLACEMENT vào session. `StopFSession` khôi phục cửa sổ sau khi kiểm HWND/PID/project. Minimize→serialize→restore đã chạy thật. `-OriginalQuality -KeepEditorVisible` chỉ dùng đối chứng, không phải profile đã đạt số đo cuối. `-Diagnostics` bật log từng frame; launcher người chơi mặc định không ghi diagnostic mỗi frame. Play-F.cmd giữ đường dẫn cũ.

Full Editor/Game build từ clone đúng native SHA: **exit0**, `Build-20261105-130401-709-c1d0b747`; UE5.8.4 CL58902052/MSVC14.51.36260/toolset14.51.36231/SDK10.0.26100.0. Lần compile diagnostics56ef988 lỗi kiểu TObjectPtr trong vòng connection đã sửa0f02c77, giữ log failed130243. Không patch/đóng Editor gốc2068 hoặc lấy Live Coding làm bằng chứng.

Cold MCP TestRunner `PerfInvestigation/MCPTests-20261105-132523`: **23/23 Success**, tên tests và số đo motor trong AUTOMATION.json; vẫn U00 4, B2, C5, D6, E4, F2 như REPORT-F. Motor/rules không đổi, regression walk/sprint/apex/landing/carry/release/settings/prediction/proxy animation đều đạt. Package Windows nguồn0f02c77 tại `Package-20261105-132600-709-df14ddc7`, BuildCookRun exit0. Smoke `SmokeB-20261105-132746`: **3/3 PASS**, Boot/CharacterCombatLab/NetworkLab exit0. Boot shutdown chờ PSO creation khoảng75s rồi thoát thành công; ghi lịch sử, không coi “đã gửi Quit” là pass. Không chạy package smoke đồng thời với các lượt đo cuối.

MCP dùng Python trong clone Editor, runtime server/game vẫn `-DisablePython` theo kết luận F trước; collector kiểm lại log cuối. Không cài/nâng engine/plugin, không commit config/token local. Phạm vi art anime/combat animation vẫn **DEFERRED**, carry blockout tạm giữ nguyên. Phần điều khiển đã được người dùng xác nhận giữ PASS; phần FPS/cảm giác độ trễ profile mới chờ người dùng xem lại theo checklist. **Chưa merge F, chưa G.**

Đã dừng phiên đo bằng StopLatestFReview, xác nhận cửa sổ Editor2068 khôi phục ShowCommand1 đúng placement đã lưu. Sau đó chạy **đúng Play-F.cmd qua cmd.exe**: phiên người chơi `Reviews/Session-20261105-134518`, server4816/A10164/B18916, cả ba ready; mặc định không bật diagnostic mỗi frame. Giữ phiên này mở để review. Có `Artifacts/U01/F/Stop-F.cmd` gọi script StopLatestFReview để dừng đúng session và khôi phục Editor, không cần nhập đường dẫn tay.

## F60 — Tách cap và đo khả năng chạy60, ngày2026-11-05

Phần trên là lịch sử revision412bc7b. Đợt mới xuất phát đúng commit đó trên `u01/f-network`, không merge main. Thêm `ClientMaxFPS`30/60 (StartFSession mặc định30), `ClientCount`1/2; server luôn30. ReviewF chọn default từ manifest sau phép đo, hiện là60. Tất cả cap và profile được đọc lại từ cvar **runtime** từng PID, không suy từ arguments. Không ghi vào project config/SaveGame.

Bổ sung diagnostics riêng trong NetworkProbe: raw CPU Game/Render/RHI và GPU từ `FStatUnitData` của viewport, đọc số của frame vừa vẽ; trạng thái async loading/shader/pipeline queue; đầy đủ packet simulation fields; tùy chọn ghi frame vào file theo lô1s thay vì UE_LOG từng frame. Đã cold build **Editor target** trong clone tại `Artifacts/U01/F/F60-Build-20261105-140722`, exit0; cold MCP TestRunner `MCPTests-20261105-140807` **23/23 Success** (U00 4, B2, C5, D6, E4, F2), tên/log/số đo motor ở [AUTOMATION](Evidence/F60/AUTOMATION.json). Header layout collector thay đổi nên không patch Live Coding vào Editor gốc. Engine/toolchain giữ nguyên UE5.8.4 CL58902052/MSVC14.51.36260/SDK10.0.26100.0.

Native chỉ đổi observability; không đổi Character/motor/replication/smoothing, mesh/animation hoặc chất lượng sản phẩm. Phép đo dùng Editor executable `-server/-game`, không cần cook lại collector cho Game package. **Tái sử dụng package nguồn `0f02c77bc14fc4c727ba8694223f8cfc5a655c31`**, kiểm lại đúng48 hash file từ PACKAGE.csv; không tuyên bố package cũ có collector mới. Không chạy build/tests/package/smoke đồng thời với bất kỳ cửa sổ đo nào.

### Giao thức và nguồn bằng chứng

Warm-up mỗi lượt ít nhất30s, ba mẫu liên tiếp xác nhận `asyncLoading=false`, `shaderJobs=0`, `pipelinePrecompiles=0`; sau đó chuẩn bị đường thử và đo **120s wall liên tục**, bao gồm đổi focus/menu/Resume. Hai client chia thành hai block60s, mỗi chiều10 lần W bắt đầu/dừng hợp lệ; S trả về vị trí ban đầu để giữ cùng đường. Case B/D một client có20 lần. Server headless không có foreground viewport; đo liên tục khi client lần lượt foreground. Native GFrameCounter liền nhau được kiểm, không mất/nhân frame; thời gian frame lấy monotonic wall, không lấy simulation dt bị clamp.

Map NetworkLab, đường fixture đã có, cửa sổ900×540 giữ nguyên. A/B/C/E dùng review profile: internal50% (450×270), atlas2048, RT pool minimum128MiB, streaming pool256MiB. D dùng cvar chất lượng gốc và internal100%; Editor cũng thu nhỏ. Mọi lượt giữ DX12/SM6/Lumen và timer hint riêng server, không đổi power policy toàn máy. D **không phải benchmark sản phẩm ở độ phân giải mục tiêu**.

[MANIFEST](Evidence/F60/MANIFEST.json), manifest từng lượt, runtime cvars, PID/world/context/pawn/source, CSV frame nén gzip và [RESULTS](Evidence/F60/RESULTS.json) có đầy đủ dữ liệu. [RAW-ARTIFACTS](Evidence/F60/RAW-ARTIFACTS.json) khóa hash log/frame/input/resource gốc. Các kích thước/render settings trong bảng áp dụng cho client; server `-NullRHI` không có cửa sổ/internal resolution. Trong vài record khởi tạo sớm có trường kích thước yêu cầu chung; arguments/runtime và role headless là nguồn xác định, writer đã sửa trường server thành N/A.

### Kết quả A–D

Đơn vị frame time là ms, bảng hiển thị **median / p95 / p99 / max**, FPS là trung bình120s.

| Lượt | Process | FPS thực | Frame time |
|---|---|---:|---|
| A: hai client, cap30, review | Server | 29,91 | 33,41 /34,42 /34,97 /41,25 |
| A | Client A | 30,00 | 33,33 /33,64 /33,92 /37,76 |
| A | Client B | 30,00 | 33,34 /33,80 /34,28 /36,64 |
| B: một client, cap60, review | Server | 29,96 | 33,34 /34,23 /34,67 /43,71 |
| B | Client A | 60,00 | 16,67 /16,95 /17,21 /18,50 |
| C: hai client, cap60, review | Server | 29,91 | 33,40 /34,62 /35,42 /42,40 |
| C | Client A | 59,96 | 16,67 /17,26 /17,84 /52,72 |
| C | Client B | 59,99 | 16,67 /17,17 /17,73 /21,26 |
| D: một client, cap60, gốc100% | Server | 29,94 | 33,37 /34,28 /34,71 /43,20 |
| D | Client A | 60,00 | 16,66 /16,95 /17,16 /18,60 |

Tách foreground/background: A cả hai client đều≈30FPS ở cả hai trạng thái. C client A foreground59,97/background59,96; client B foreground60,00/background59,99. P95 cả bốn tổ hợp C nằm17,07–17,31ms. Mẫu vượt100ms trong A–D: **0**; không chuỗi khựng kéo dài. Chi tiết p99/max riêng foreground/background ở JSON.

CPU/GPU đọc trực tiếp raw stat-unit, không suy GPU time từ FPS/cap. Ví dụ median client A/B tại C: Game3,82/3,72ms; Render6,26/6,13ms; RHI4,24/4,13ms; GPU3,37/3,24ms. Server NullRHI không có viewport stat-unit: CPU Game/Render/RHI riêng **chưa đo được**, GPU N/A; không thay bằng frame33ms. Phân bố đầy đủ từng process ở RESULTS/CSV, các timing CPU/GPU là last-drawn-frame và không cộng cơ học để suy ra wall frame.

Telemetry NVIDIA/Windows độc lập: VRAM resident median A3882MiB, B2822MiB, C3909MiB, D3114MiB trên RTX3050Ti Laptop4096MiB; GPU load median27/21/50/30%. Shared GPU memory median hai client C≈256,69/196,41MiB; toàn bộ dedicated/shared per-process có ở resource JSON. Gần đầy VRAM **không tự chứng minh đang nghẽn**: C vẫn ổn định60 trong profile này. Sampler khoảng0,7–0,8Hz, focus events đo mỗi game frame. Không gọi đây là FPS tối đa uncapped hoặc bảo đảm60 cho cảnh sản phẩm tương lai.

### Latency và lý do phần dừng tăng

Mỗi chiều A↔B tại A/C có10/10 starts và10/10 stops hợp lệ, không loại mẫu để đạt FPS. Onset lấy input thực→owner→server→peer replicated position→peer mesh. “Dừng” đòi mesh vận tốc X dưới3cm/s ba mẫu liên tiếp và báo thời điểm đầu chuỗi: gồm giảm tốc vật lý và đuôi smoothing, **không chỉ latency truyền mạng**. Không gọi các số này là độ trễ tới màn hình.

| Hướng | Bắt đầu: median /p95 A30→C60 | Dừng hẳn: mean A30→C60 |
|---|---|---|
| A→B | 47,46 /62,83 →55,57 /82,66ms | 296,55→336,53ms (+39,98) |
| B→A | 78,11 /111,52 →49,95 /82,43ms | 309,53→333,58ms (+24,06) |

Mức tăng dừng được giải thích **trước khi chọn60** bằng phân rã mean, không tắt smoothing để che:

| Thành phần tăng C−A | A→B | B→A |
|---|---:|---:|
| Input→server stop (gồm braking) | +13,38ms | +0,26ms |
| Server→peer packet stop | −4,20ms | −13,30ms |
| Peer packet→mesh dừng hẳn | +30,80ms | +37,10ms |
| Tổng | +39,98ms | +24,06ms |

Đối chiếu engine `CharacterMovementComponent.cpp:8470–8474`: Exponential khi velocity0 dùng `SmoothLocationTime=0.5*0.1=0.05s`, mỗi frame nhân offset với `1-dt/0.05`. Dữ liệu thực có177 cặp offset A và564 cặp C khi capsule đứng yên: median hệ số≈1/3 ở30 và≈2/3 ở60, sai số p95 so công thức≈3e−8. Đuôi hội tụ theo tiêu chí “dừng hẳn” vì vậy dài hơn ở60 dù giá trị smoothing không đổi. Vận chuyển packet không chậm thêm; data/phân rã/công thức nằm trong `latencyExplanation` của RESULTS. Giữ nguyên Exponential0,10s, NetUpdateFrequency100/Min2, adaptive off, mọi lag/loss/jitter/buffer-bloat đã đo bằng0. Đây là đánh đổi được báo rõ để người dùng review, không một lỗi một giây được bỏ qua.

### Logging control, lựa chọn và300s liên tục

E lặp hai client30 với collector ghi file theo lô1s, **không UE_LOG mỗi frame**. Server29,92; hai client30,00/30,00, p95 client33,93/33,63ms; A tương ứng33,64/33,80ms. Không thấy logging làm đổi kết luận đạt cap30 trong cặp đối chứng này. JSON collection và stat-unit vẫn chạy cả hai, nên đây đo ảnh hưởng log I/O, **không chứng minh overhead toàn bộ instrumentation bằng0**. Mẫu frame liên tục của E được kiểm; raw Frames.jsonl vẫn có dữ liệu từng frame, chỉ ghi theo batch.

Chọn default **hai client60 /server30**: hai client≥57, p95≤20ms; server≥28,5; không khựng dài; tăng stop latency đã giải thích bằng dữ liệu như trên. Một client review60 và một client gốc100%/900×540 đều đạt60 ở các lượt đã đo, không suy ra hai client chất lượng gốc cũng đạt.

F3 source cùng EDF, buffered diagnostics, chạy **đủ300s liên tục** gồm năm block60s, không bỏ khoảng đổi focus/menu/Resume:

| Process | FPS | Median /p95 /p99 /max frame |
|---|---:|---|
| Server | 29,89 | 33,44 /34,64 /35,36 /44,82ms |
| Client A | 59,97 | 16,67 /17,27 /17,94 /39,84ms |
| Client B | 59,96 | 16,67 /17,27 /17,88 /71,79ms |

Frame>100ms: **0**, không có nguyên nhân spike>100 cần suy đoán. A có180s foreground/120s background, B120/180; các block và focus thực ghi trong input/JSON. Đi, sprint, nhảy, V, menu/Resume được input tool thực hiện; thêm30 starts/stops A và20 B hợp lệ. Video ngắn có peer trong FOV; video mã hóa30Hz, capture thực/duplicate timing trong VIDEOS, **không dùng video30Hz để chứng nhận độ mượt60**. Số đo frame native mới xác nhận60.

Lịch sử không giấu: lượt D đầu đủ frame/input nhưng sampler lỗi cast mảng PID PowerShell, thiếu memory data nên bị loại và đã đo D lại đủ120s. Lần F3 đầu dừng trước measurement vì preflight không thấy key khi Slate chưa active; sửa input tool kích hoạt thật ở góc menu trống, kiểm native windowActive rồi mới probe/Resume; lần sau hoàn tất300s. Không sửa focus gate gameplay. Giữ lỗi ở HISTORY/artifacts. Các warning EditorDataStorageUI factory khi dùng Editor executable runtime vẫn có trong WARNINGS, không cài/tắt plugin để giấu; không có Python AttributeError/Accessed None/Blueprint Runtime Error. Runtime vẫn `-DisablePython`, MCP Editor tests giữ Python.

### Chơi thử và cổng review

`Artifacts/U01/F/Play-F.cmd` mặc định client60/server30; `Play-F.cmd -ClientMaxFPS 30` để đối chiếu. Một client: thêm `-ClientCount 1`; gốc100%: thêm `-OriginalQuality` (chỉ kết luận một client đã đo). Không hạ chất lượng dưới review profile hiện tại. Launcher bình thường không bật collector từng frame/stat-unit HUD; benchmark đã bật giống nhau để thu timing. `Stop-F.cmd` dừng đúng session, khôi phục placement Editor; đã xác minh PID2068 vẫn mở và ShowCommand khôi phục đúng sau F3.

F vẫn chờ người dùng xác nhận profile cuối về độ mượt, quan sát peer lúc bắt đầu/dừng và đổi focus/Resume theo checklist ngắn. Không khép nghiệm thu F, không merge hoặc triển khai G. Art anime/combat vẫn DEFERRED; G sẽ đo package ở độ phân giải/chất lượng mục tiêu, lifecycle dài và các FPS thực đạt.
