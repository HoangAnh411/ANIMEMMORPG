# U01-F — Điều tra FPS và độ trễ sau review

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
