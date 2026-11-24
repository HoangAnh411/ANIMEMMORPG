# U04-C1 ? ACCEPTED

H? s? C1 ?? ???c reviewer nghi?m thu. Ph?m vi nghi?m thu k?t th?c ? C1.

- Build-03 d?ng native `13b4f34f07bd1cb8e7402984d9479fd5eb9fe2e7` v? Game SHA-256 `282fcefc5156be5f5aa81caf2bc3a764949f2eaf76de081f9c62aa0e2e54e5a5`. Baseline 36 timing v? 12 memory thu?c Build-03. Verdict isolation l? `ISOLATION_NOT_PROVEN_ON_BUILD_03`. [Build identity](../../../../Runs/Build-03/BUILD-IDENTITY.json)
- Build ch?n ?o?n t?ch t? native Build-03, d?ng native `80858ed6f9ed1e9dc13e18fe41f42cf9e3f256dc` v? checkout `b315ad4a42eac5ec6bd2a600f91b52d380bc99ab`. Full UBT Development Editor tr?n UE 5.8.4, MSVC 14.51.36260, Windows SDK 10.0.26100.0. SHA-256 module `a644e0b4066df7d4b7f02b524ba61db379a53860eee5a1b0b49feb30dfba7145`. C?ng cu?i PASS trong `C1-Isolation-03`. [Build identity](../../../../IsolationDiagnostic-01/BUILD-IDENTITY-02.json) ? [Contact/LOS, HP v? exit proof](../../../../IsolationDiagnostic-01/contact-recheck.json) ? [Manifest](../../../../IsolationDiagnostic-01/manifest.json)

## B?o c?o l?ch s? tr??c nghi?m thu

Không READY_FOR_REVIEW. Chưa có baseline CPU/GPU/cấp phát hợp lệ; không khép U04.04. Không triển khai tối ưu, không merge, không chuyển U04-D. Ma trận36 timing +12 memory đã định trước nhưng0/48 lượt baseline được chạy.

## Điểm dừng

Cổng readiness của kiểm phương pháp thất bại trước `prepare`/`begin`; do đó chưa kiểm chứng counter hay fixture bằng gameplay. Giữ nguyên cả hai lượt, không mở toàn ma trận và không có lượt thay thế thứ hai:

|Lượt|Kết quả thực|
|---|---|
|Method-Timing-01|INVALID: guard kiểm source SHA không chấp nhận dấu ngoặc kép trong raw Windows command line; chưa ghi process.json/cửa sổ đo. Giữ command, traceback, trace startup và identity recovery. Đã xác minh executable/hash/source/run scope trước khi dừng đúng process.|
|Method-Timing-01-Replacement|INVALID: `Input focus/PID changed; abort rather than steal focus` tại `InputClient.setup → metrics → Client.console → guard`. Có process creation identity. Chưa có readiness/summary/frame CSV; không có cơ sở kết luận gameplay FAIL. Process được dừng sau kiểm identity, không retry kill/Start.|

Lỗi thứ nhất thuộc harness và đã sửa trước lượt thay thế. Nguyên nhân gốc mất foreground ở lượt thay thế chưa xác lập; không quy lỗi cho combat, GPU hay người dùng. Harness mới chưa hoàn thành kiểm chứng tương đương readiness R1b. Đây là phần C1 cần giải quyết trước khi xin review số đo; không phải đề xuất C2. Không bỏ guard, giả input hay nới điều kiện để đi tiếp. Entry baseline trong harness bị chặn khi method gate chưa PASS.

## Phần đã triển khai và kiểm tra

Nhánh `u04/c1-profiling-baseline`, clone riêng `Artifacts/U04/C1/Source`, base main `e66670fbba7f39644b0571b703bb3341ac7c0108`. Clone local độc lập, không hardlink, lấy từ clone khép B sạch cùng SHA; origin trỏ GitHub. Clone GitHub trực tiếp không nhận pack, đã dừng các process git của lượt đó; thư mục tải dở vẫn giữ trong isolation. Checkout gốc giữ `18804bfa32b14471df1ffa4bd7aeaed6cd80074c`, hai tracked modifications và hai thư mục Maintenance riêng như ban đầu.114 hash project/config/Maintenance và creation/path/command của Editor gốc17976 khớp trước/sau. Không cleanup/tải engine hoặc sửa artifact U03/A/B.

Source native cuối **13b4f34f07bd1cb8e7402984d9479fd5eb9fe2e7**, commit trước full build. Các commit sau chỉ tools/docs. UE5.8.4 CL58902052; i7-11800H8C/16T, RTX3050Ti Laptop4GiB (máy còn Intel UHD); driver/hardware đầy đủ trong host.json và runtime log. Preflight ghi ổ D còn172.51GiB sau clone/build đầu; chưa có pilot cửa sổ hợp lệ để dự toán dung lượng cả ma trận. Không suy diễn trace budget từ startup.

`Build-01` và `Build-02` Failed được giữ: member profiling trùng biến geometry cục bộ; lần sửa trung gian còn đổi nhầm local và dùng TSet với life ID không có GetTypeHash. Đã sửa trước `Build-03`. Generate/Editor/Game/package `Build-03` đều exit0, output lần lượt `Result: Succeeded` và `BUILD SUCCESSFUL`. Compiler14.51.36260 mới hơn preferred và engine deprecation warnings có trong log, không bị giấu. Editor/Game/module là cold full UBT build, không Live Coding lên Editor gốc. Header mới được full build; Live Coding không thay thế nghiệm thu layout/header.

Cook và cold test Editor tự sinh token AndroidFileServer dù plugin setting tắt. Bản phát sinh giữ riêng `Generated-DefaultEngine.private.ini`, bản công bố che token; config clone đã restore đúng commit sau mỗi bước. Diff runtime inputs với native source cuối bằng0. Generated FileOpenOrder logs giữ local, ignore cục bộ trong `.git/info/exclude`; không xóa. Package là kết quả cook thực; generated Android setting không được mô tả là input source đã commit.

Game SHA256 `282fcefc5156be5f5aa81caf2bc3a764949f2eaf76de081f9c62aa0e2e54e5a5`; Editor module `9209035a9c5abd6609767edec71e5d63fb3cf3fdc999b7bc9c6efccdc5fc6045`. Build identity có48 package files, receipts, engine/toolchain/source tree và staged Game khớp built Game. PDB Game381464576 bytes, hash `99ef5c2314ee3e022e19a4988814ee9431a7cae0ada892ab735e4946fb139943`; package/PDB đầy đủ giữ local trong `Runs/Build-03/Archive/Windows`, bản remote công bố identity/hashes và receipts thay vì upload binary1.09GB.

Instrumentation opt-in `-U04C1Profile` và fixture độc lập được thêm; không có cờ C1 trong launcher thường. Các scope/counter/điểm tăng có trong [COUNTERS](COUNTERS.md); contract/profile B trong [CONTRACT](CONTRACT.md); thứ tự48 lượt trong [MATRIX](MATRIX.json). Không đổi resolver/event admission/motor/damage algorithm. C1 tắt log collision hit/damage đồng bộ và giữ product damage records để xuất ngoài cửa sổ. Các log sản phẩm khác vẫn tồn tại; chưa đo overhead của collector/membership probes. Không tuyên bố instrumentation đã được kiểm chứng hoàn chỉnh.

Full Automation qua MCP port riêng19501: **144 expected =144 discovered =144 executed,144 Success,0 Failed**, không duplicate/extra/missing; có raw Editor log, schemas, trigger, completion và NAME-RESULTS. Ba map package `L_Boot`, `L_CharacterCombatLab`, `L_NetworkLab` load smoke exit0/PASS, không cờ C1. Đây là load smoke NullRHI, không thay focused combat/dodge/focus hay launcher rendered runtime. Các hồi quy input, dedicated Editor+hai client và media fixture chưa chạy vì dừng phương pháp. Editor kiểm thử riêng đã thoát, Editor gốc còn nguyên.

## Profiler và dữ liệu chưa có

Dùng source cài sẵn UE5.8.4 để xác định channel và CLI thật; không tải engine. Timing command `-trace=cpu,gpu,frame,bookmark,counters -statnamedevents`; script export dùng `TimingInsights.ExportThreads/ExportTimers/ExportTimingEvents/ExportTimerStatistics`. Memory script dự kiến dùng `-trace=memory,bookmark` và `MemoryInsights.ExportAllocs` với rule AaB/AfB/aAf, bookmark biên, callstack/symbol từ PDB local. Memory script chưa được nghiệm chứng.

UnrealInsights mở trace của lượt thay thế thành công, exit0; export14692 startup GPU events trên `GPU0-Graphics0` và `GPU0-Compute0`,13821 có duration>0. **Chỉ startup**, không có `U04C1_WINDOW`: không dùng chúng làm GPU frame baseline/pass cost, CPU cost hay chứng minh đủ ma trận. Trace của cả hai invalid run được giữ và hash; không ghi chúng thành valid pilot. Không có memory trace, allocation/free/size/callstack hoặc outstanding delta. Working set không được dùng thay thế.

Chưa có CPU inclusive/exclusive/frame/action, GPU frame/pass baseline, frame P50/P95/P99/max/FPS, counter deltas đúng workload, candidate/hit ratio, overhead ba cặp, allocation/sec/action hay so sánh1→10→40 và1→3 hurtbox. Warmup/start/end đúng workload chưa được tạo. Counter reset/reopen/world isolation chưa được kiểm chứng. Vì thiếu timing/stack/counter, **không xác định điểm nghẽn quan sát được và không đưa đề xuất tối ưu C2**.

## Tái lập và hồ sơ

Source/tool commands và mọi invalid run nằm trong evidence manifest. Gỡ gzip trace trước khi mở: `python -m gzip -d <capture.utrace.gz>` trên bản copy; đối chiếu raw SHA256 từ manifest. `StartupExports/commands.txt` và process record ghi đúng lệnh Insights đã chạy. Kết quả Automation kiểm lại bằng `python Scripts/U04/VerifyAutomationA.py --run <Automation-01>` trên thư mục copy vì verifier ghi output bất biến.

[Trạng thái từng cổng](GATES.json). [Manifest evidence](Evidence/MANIFEST.json). File `.private.ini` và các bản log được che token có transformation/hash nguồn và bản công bố riêng. User settings và package binary không upload; raw local vẫn giữ. Không có64-bit scanout/FPS sản phẩm/40-player hay server-capacity claim. Reviewer nhận bàn giao C1 chưa hoàn tất; chưa có baseline để lập C2 dựa trên số đo.
