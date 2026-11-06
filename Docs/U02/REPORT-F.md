# U02-F — ACCEPTED về kỹ thuật

Cập nhật khép cuối: bản sửa focus **ACCEPTED32061ba**, gồm xác nhận cảm giác đổi focus “ok rồi”, theo [ACCEPTANCE-FOCUS](ACCEPTANCE-FOCUS.md). U02 A–F hoàn thành kỹ thuật, không có lỗi chặn còn mở qua lần rà soát cuối. Không chạy lại build/tests; kết quả F bên dưới giữ nguyên lịch sử.

Người dùng nghiệm thu tại **d5fb4b0436ecf5b1792eaddfffb951fef8414063**, source kiểm chứng **85806519f98ef9078c5832e6193bb3bc8d924b54**. Không phát hiện lỗi chặn trong phạm vi F. Căn cứ review ghi tại [ACCEPTANCE-F.md](ACCEPTANCE-F.md); ma trận khép kỹ thuật U02 tại [CLOSURE-F.md](CLOSURE-F.md). Bản này sửa tiếng Việt UTF-8 bị mất dấu trong báo cáo bàn giao, giữ nguyên số liệu/lịch sử; không chạy lại build/tests.

E đã được nghiệm thu tại903e139/source1f1c359; closure **e6e1e2f5cf30b713ebe560acab98b63751076493** đã push và fast-forward main trước F. Nhánh triển khai F là `u02/f-dedicated-two-clients`. Commit bàn giao d5fb4b0 không đổi Source/Content/Config/Plugins so với source kiểm chứng8580651.

[MANIFEST](Evidence/F/MANIFEST.json), [PROCESS-MANIFEST](Evidence/F/PROCESS-MANIFEST.json) và [EVIDENCE-SHA256](Evidence/F/EVIDENCE-SHA256.json) liên kết source → binary → process/session → IDs → kết quả. Trạng thái READY_FOR_REVIEW trong manifest lịch sử phản ánh lúc bàn giao; quyết định ACCEPTED được ghi riêng, không sửa bằng chứng gốc. Package Windows của E giữ source1f1c359; không gán SHA F cho binary E.

## Triển khai đã kiểm chứng

Dummy chỉ spawn trên server, replicate pawn ID/life/vital. Static lab geometry dựng cùng cấu hình/tên ổn định, net-addressable trên các process; root phải Static trước khi đăng ký collider. Không đổi thuật toán sweep, che khuất từng hurtbox, damage/shield/death hoặc timing0,16/0,22/0,40; không sửa replication/smoothing chung U01.

Một actor replicated luôn relevant trong NetworkLab giữ tối đa64 confirmed results với serial, source/life/action/target/life/hurtbox/timestamp/damage/HP/crit/death. Server duy nhất resolve và trừ HP. Client nhận history để trình bày/log, không áp damage lại; snapshot vital giữ HP/shield/death hiện tại khi reset/reconnect. HUD không dùng result life cũ ghi đè trạng thái mới. History64 là cửa sổ trình bày/diagnostics, không bảo đảm giao mọi event trong mạng xấu U05.

Attack RPC chỉ có command sequence, local diagnostic time, yaw và expected pawn/life; client không khai damage/HP/action ID. Server kiểm ownership bằng actor channel, life, watermark, finite aim và quyền action. Startup aim RPC ràng buộc pawn/life/action; aim cũ không retarget action mới. Client timestamp không backdate start/hit. Snapshot replicate counters accepted/rejected và lý do cuối; log server lưu từng quyết định.

Fixtures file/console chỉ opt-in `-U02FProbe`, non-Shipping, server NetworkLab. Concurrent fixture tạm đặt control Playing để nhận hai intent cùng boundary rồi phục hồi control lock; đây là fixture ordering riêng, không phải gameplay bỏ AwaitingResume. Các ca đánh A/B thông thường dùng LMB Windows thật. Lab gameplay chỉ đánh dummy; pawn-versus-pawn ordering tests kế thừa E là fixture native rõ ràng.

## Kết quả trên source cuối — bằng chứng kế thừa khi khép

- Full Editor/Game build trong clone: `Build-20261106-180455-913-bde29c16`; Generate/Editor/Game ExitCode0, log `Result: Succeeded`. Header/reflection mới dùng cold clone; không restart hoặc tuyên bố Editor gốc nạp layout mới.
- MCP `MCPTests-20261106-180707`, port18030: **61/61 Success**, queue61 tests performed; toàn bộ U00/U01/U02 A–F. [AUTOMATION-RESULTS](Evidence/F/AUTOMATION-RESULTS.json) và MCP-RESULTS lưu từng test.
- Ba tests F: `CommandLifeAndDuplicateAdmission` kiểm duplicate/stale/wrong subject/nonfinite và old-life/action aim; `AuthoritativeResultHistoryAndReplicationSchema` kiểm history giới hạn, publish không áp HP và wire schema; `NetworkLabStaticFloorAttachment` kiểm attachment/world transform/năm dummy/reset NetworkLab.
- Session `Session-20261106-180839`: serverPID9988, A13236, B4316; reconnect A8300. **134/134 input assertions**: ownership/roles riêng, server0LocalPlayer, đồng thuận hit/miss/wall/head-only/nhiều hurtbox/nhiều target,60/90, shield, death, reset, duplicate/stale, nonfinite aim, menu/focus, concurrent lethal. Hai nguồn concurrent đều accepted; nguồn resolve trước gây lethal mỗi target. [Network input](Evidence/F/Network-input.json).
- **36/36 kiểm tra hậu xử lý bổ sung**, controls597 samples: held WASD sau recovery, authority combat lock và hồi quy replay, sprint700cm/s, gravity/menu, Resume không attack, focus/fresh-W, settings không đổi, yaw thân thực khóa/camera tự do, montage local/proxy cùng action, root-motion ignore, server tiếp tục chạy, một RNG roll mỗi hit hợp lệ, reject đúng probe và old history không ghi đè HP hiện tại. [RUNTIME-ASSERTIONS](Evidence/F/RUNTIME-ASSERTIONS.json).
- Disconnect bằng Alt-F4 khi server đã nhận action và chưa hết0,40 giây. Native removal event có cutoff; không result từ source cũ kể từ cutoff. Reconnect ID mới, initiallife1/action0; fixture reset thànhlife2 rồi input thật tạo action1, ba process cùng HP/results. [Disconnect proof](Evidence/F/Disconnect-ASSERTIONS.json). Damage hợp lệ trước removal được giữ, không xóa ngược lịch sử.
- Profile cvars thực: client60/server30, DX12/SM6,900x540, internal50%, Lumen atlas2048, RT128MiB, texture256MiB. Trong controls: server298 frames, median33,388ms/p9534,071ms; mỗi client597 frames, median16,667ms/p9516,667ms. Profile cùng máy4GB VRAM kế thừa U01, không phải đồ họa sản phẩm1080p. Proxy smoothMode2/time0,1 đo597 samples/client trong SMOOTHING.json. Không sửa smoothing để chữa hitch.
- [Network video](Evidence/F/Network-Network-F.mp4) và [Controls video](Evidence/F/Controls-Controls-F.mp4): CFR30 theo wall timestamp, giữ ảnh cũ qua gap, không tăng tốc/nội suy. Thêm7/4 last-frame holds cho bookkeeping cuối0,23/0,12 giây; giữ bản Unpadded và metadata. VIDEO-CLOCKS tách run-start UTC có prepare với video-origin gần đúng từ nonce fixture đầu; stage UTC/IDs giữ riêng. Không dùng freeze/gap để khẳng định art mượt.
- Stop chỉ dừng PID/executable/project/userDir/hash của session, gồm reconnect. Editor gốcPID18756 còn sống, window show-state khớp trước minimize; EDITOR-RESTORED ghi xác minh thật. Config riêng giữ nguyên byte, không stage token.

## Lịch sử lỗi và giới hạn bằng chứng

Failed builds/runs, raw logs/video/metadata và warnings giữ trong Evidence/F, RUN-HISTORY và RAW-LOGS. Build đầu lỗi test symbol `Flags` trong unity và phạm vi `ForwardErrorMessages`; đã sửa test. Runtime đầu phát hiện Static collider không attach root Movable, gây rơi/reject Airborne; sửa root mobility và thêm regression fixture/world-transform. Runtime sau dừng vì reset helper E chỉ cho CharacterLab; mở đúng hai lab server-only, thêm regression reset NetworkLab. Không đổi luật hit/damage.

Hai lượt Automation trung gian bị loại:180458 vì HEAD clone đổi giữa build/test,180624 vì MCP port handover; ghi INVALID, không dùng PASS. Final180707 cold-load sau full build hoàn tất, đối chiếu lại module hash. Fixture test ban đầu rename world thay vì package nên không vào map guard; đã sửa cách dựng fixture và giữ run đỏ.

Reconnect helper từng bọc array `ConvertFrom-Json` sai trên PowerShell5 khiến guard từ chối; sửa enumeration, giữ FAILED-RECONNECT. Assertion từng đòi life1 sau chính fixture resetlife2; sửa theo initial/post-reset states, không hạ luật. Controls harness từng kết thúc sớm vì focus tốn thời gian; giữ Controls-Failed-Schedule và thu lại đủ. Assertion sprint cũ dùng >700 trong khi luật700 và float thực699,99; sửa kỳ vọng đúng config700, kiểm tốc độ thực. Một phép kiểm history từng giả định target600 khi reconnect, trong khi source cũ đã hit hợp lệ trước removal; nay đối chiếu snapshot server cùng life. Các assertions sai vẫn được giữ.

Stop guard từng từ chối vì đường dẫn slash/backslash khác nhau; chuẩn hóa `GetFullPath` trước so sánh, giữ nguyên PID/executable/hash/project/userDir guards. Không bỏ foreground/IME/AwaitingResume. Reconnect frame output của run dùng đường dẫn file A cũ từ template; phân tích lọc **PID và UTC**. Helper mới cấp Frames riêng, không trộn hai PID làm FPS evidence.

Warnings engine/toolchain/optional MCP/fixture và performance console lookup giữ nguyên; không báo zero warnings. Không dùng Editor-world actor, trigger-success, zero tests hoặc khai báo replicated properties thay bằng chứng ba process.

## Bàn giao, nghiệm thu và phần chưa xác nhận

[Play-U02-F.cmd](../../Play-U02-F.cmd), [Stop-U02-F.cmd](../../Stop-U02-F.cmd) và [checklist ngắn](../../Play-U02-F-CHECKLIST.md). Launcher kiểm source/module/engine, dùng profile review U01, đưa hai pawn tới fixture; cần Resume sau đổi focus. Launcher smoke thực session183024: server19480/A19764/B9420, guards đạt, server0LocalPlayer/đúng owner mỗi client,5 dummy life2/HP600 và crit fixture off đồng thuận. LAUNCHER/Launcher.png lưu states/ảnh; StopLatestF dừng đúng session, giữ Editor gốc.

| Binary | SHA-256 |
|---|---|
| DLL Editor | b324e86adfd91b21fa9460f370e132c464f06068ee63867f91d1bb4409b3894d |
| Engine executable | a423ab94410aa4f4cc34d99a2af75240c5d0e376a33d903a3e819fecf1177143 |
| Game build executable | 5a07966e0bde0d1d97e2f267f326746948e60e82add49ed5286fa88f4f02e725 |

Game build executable không phải package F. Reviewer đã đối chiếu149 file bằng chứng/hash DLL/Game build, remote đúngd5fb4b0 và Stop giữ/khôi phục Editor gốc. F **ACCEPTED về kỹ thuật** chỉ cho dedicated Editor server và hai client trong điều kiện đã đo. Khi nghiệm thu F ban đầu, cảm giác hai cửa sổ chưa xác nhận; sau đó bản sửa focus32061ba được nghiệm thu với xác nhận cảm giác đổi focus. Xác nhận này không được suy từ cảm giác C hoặc mở rộng thành art sản phẩm. [Báo cáo focus](FOCUS-REGRESSION.md) giữ197 file bằng chứng,71/71 input và55/55 kiểm tra bổ sung.

U02 kỹ thuật đã khép A–F và bản sửa focus, không còn tính năng U02 phải triển khai. Chưa nghiệm thu Server đóng gói, mạng xấu/bù trễ/prediction đầy đủ U05, hiệu năng sản phẩm, art anime/carry sản phẩm hoặc respawn sản phẩm. Lượt hiện tại chỉ khép hồ sơ/push/fast-forward main rồi dừng; **không triển khai U03**.
