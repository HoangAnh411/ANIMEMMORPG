# U02-E — ACCEPTED

Người dùng nghiệm thu kỹ thuật tại903e139/source1f1c359; căn cứ và quyền chuyển F ghi tại [ACCEPTANCE-E.md](ACCEPTANCE-E.md). Các kết quả/bằng chứng bên dưới giữ nguyên từ lần bàn giao, không phải chạy lại khi khép hồ sơ. Trạng thái READY_FOR_REVIEW trong manifest lịch sử phản ánh thời điểm capture/handoff; quyết định nghiệm thu ở hồ sơ này.

Branch u02/e-vitals-damage-death from D ACCEPTED main2381089. D acceptance at d0dd5b0/source82bb890, closure push and main remote verified. No D build/tests rerun for documentation closure. E native changes require isolated full Editor/Game build.

Server damage pipeline: revalidate both vital subjects/lives and ledger eligibility before a single crit roll; damage60, attack factor1, defense0, crit5% x1.5, half-up after all factors. Shield deadline/source ordering, same-source replacement. Damage mutates HP/shield synchronously; HP0 marks dead in ledger before any next sorted candidate, cancels action and locks Defeated. Action models already advanced to boundary never rewind to hit time. Gameplay death is stamped at sorted hit time, presentation cancellation uses observed model endpoint.

Lab dummy600 HP/player1000. No skill grants shields; console/native fixtures only. Reset increments generation and clears shield/action, is not product respawn. Existing U01 fixture cannot clear actual HP0 Defeated. Replicated vital snapshot supports presentation but dedicated two-client acceptance remains F. Native critical roll overrides marked on HUD/log; production defaults random5%. Debug geometry does not decide damage.

Source kiểm chứng: `1f1c35954772b075197fd225b1e7ee494b989505`. Các commit bàn giao sau source này chỉ sửa hồ sơ/công cụ; không đổi Source/Content/Config/Plugins. [Manifest](Evidence/E/MANIFEST.json) ghi SHA-256 DLL Editor, Game executable và liên kết source/package/run. [PACKAGE.csv](Evidence/E/PACKAGE.csv) chứa hash cả48 file package; [EVIDENCE-SHA256.json](Evidence/E/EVIDENCE-SHA256.json) liệt kê bằng chứng. Main vẫn ở D closure2381089. Không merge E hoặc bắt đầu F.

## Kết quả kiểm chứng thực

- Full build Editor/Game trong clone: `Build-20261106-171234-054-b4fb80ea`, đều Succeeded. Original Editor vẫn mở; không restart hoặc tuyên bố đã nạp layout mới.
- MCP Automation `MCPTests-20261106-171359`: **58/58 Success**, queue ghi58 tests performed. Toàn bộ U00/U01/U02 A–E; tên và kết quả từng test trong AUTOMATION-RESULTS/MCP-RESULTS. E thêm8 tests: formula/rounding/crit; shield replacement/order/expiry/overkill; authority dedup/one roll; same-time lethal/dead motor; reset/old life; startup cancel/active rights; hit-time expiry trước frame-end; full active ngay sau reset. Endpoint0,3/0,5 và reversed collection được kiểm riêng.
- Package Windows mới `Package-20261106-171446-457-dbe7942e`, cook đủ ba map/assets. Smoke `SmokeB-20261106-172523`: **3/3 PASS**, native map/source/owner metrics và exit code được lưu trong SMOKE.json.
- Input thật `Play-Final-Damage`: **115/115 assertions**,16 damage events:60 thường,90 crit, shield40, lethal/dead-no-hit, reset/held LMB, tường kín, nhiều target/hurtbox, hụt. [Video](Evidence/E/Input-E.mp4) dài80,833s tương ứng capture80,816s; giữ gap đúng thời gian thực, không tăng tốc. DAMAGE-TRACE.log và RUNTIME-ASSERTIONS.json liên kết IDs/life/timestamp/HP.
- Input thật `Play-Final-Controls`: **40/40 điều khiển +23/23 presentation**,871 samples: held WASD sau recovery, yaw, gravity, busy/Interacting/airborne rejection, menu/focus/Resume, montage/root-motion. [Video controls](Evidence/E/Controls-Controls-E.mp4). Authority/saved-move replay còn được kiểm bởi Automation kế thừa chạy lại trên source E. Giới hạn injected-key qua Alt-Tab của B/C vẫn giữ, không suy thành bằng chứng physical hardware key.
- Boot/Quit/reopen: hai process riêng cùng binary. Back to Boot bằng input thật, xác minh native LoadMap; Quit bằng console input ở Boot rồi mở lại, Quit bằng nút menu thật. Chỉ PASS khi handle process gốc signalled và exit code0; không suy từ cửa sổ biến mất. BOOT-QUIT-REOPEN.json và video/metadata Boot-/Reopen- lưu riêng.
- Không dùng Editor-world pawn hoặc trigger-success làm bằng chứng runtime. Config riêng giữ nguyên byte theo baseline E; không stage token.

## Sửa lỗi và lịch sử

Giữ build fail đầu tiên (QuietNaN), các run đỏ và warning gốc. Fixture whole-frame từng bị engine clamp delta; sửa cách dựng clock, không nới gameplay timing. Test đỏ `d406b3f` tái hiện hit đầu tiên sau reset bị mất do collision snapshot generation cũ; fix `1f1c359` thiết lập baseline life mới tại boundary reset đã drain. Không nối sweep qua teleport không rõ tính liên tục. Test mới cùng57 tests còn lại đều xanh trên source cuối.

Shield frame-end phải expire sau batch hit đã sắp thứ tự, để shield còn sống tại hit0,16 vẫn hấp thụ dù frame kết thúc0,5. Có regression test riêng. Reset không authority không được xóa Defeated khi HP0; chỉ reset vital hợp lệ mới mở khóa. Death vô hiệu hóa ledger ngay timestamp hit; model đã advance tới endpoint không bị quay ngược clock.

Phiên Boot cũ click sai tọa độ nút được đánh INVALID, giữ log/video/metadata lịch sử. Sửa tọa độ theo cửa sổ1280x720 thực, giữ nguyên foreground/ownership/IME guards. Capture trên source ee58d25 là lịch sử, không thay bằng chứng cuối1f1c359. RUN-HISTORY/HISTORY/WARNINGS lưu cả failed runs và giới hạn.

Warnings còn lại: toolchain VS14.51 mới hơn bản ưu tiên14.50; deprecation trong engine/API cũ; socket warning trên pawn không có mesh của Automation fixture; audio thiết bị44,1kHz so với engine48kHz dùng chuyển đổi. Giữ nguyên log, không báo zero warnings. Package/input thực có skeletal mesh và montage được kiểm riêng.

Binary SHA-256: DLL Editor `e7bcbb0849a19328a84457f63fc37a28697adef987bc461382d59dca8cf5a91d`; packaged Game executable `f08810ec88c2ad43c7480c8ffe832f8f859d21fbc888d78fb94c9e5fb5ec67ae`. Engine/toolchain/PID/executable/UTC/world/owner/roles và clock/command/action/hit/life có trong PROCESS, INPUT, LAUNCHER và raw logs. LAUNCHER xác minh đúng source/package, owned window/foreground và native runtime sau khi chạy PlayE.ps1 qua entrypoint của .cmd.

## Bản chơi và giới hạn

Chạy [Play-U02-E.cmd](../../Play-U02-E.cmd); [checklist](../../Play-U02-E-CHECKLIST.md) nằm cạnh launcher. Launcher kiểm cả48 file package và liên kết source trước khi mở. Người dùng chỉ cần báo HUD khó đọc hoặc hồi quy pose/movement/focus; không cần nghiệm thu lại cảm giác C.

Animation vẫn blockout kỹ thuật; dummy chết chưa có ragdoll/art sản phẩm. Kiếm hình ảnh chưa bị chặn theo quỹ đạo môi trường. Không mở PvP, shield skill, respawn sản phẩm, prediction trong E. Replicated vital property chưa chứng minh đồng thuận dedicated server/hai client. E đã ACCEPTED; F được triển khai riêng sau khi khép remote/main.
