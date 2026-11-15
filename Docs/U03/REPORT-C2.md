# U03-C2 — ACCEPTED (technical)

Đã triển khai encounter cận chiến, Tab thông tin và Retry do server quyết định. Người dùng ACCEPTED về kỹ thuật tại bàn giao **`b5eed4b6fd1043eb17f4e082a95ec2b225f97203`**, source tạo binary cuối **`b43b15d7178fb5a7ca55cef667946d20fc1591d8`**, và cho phép khép tài liệu, fast-forward/push main. Nhánh `u03/c2-encounter`, main nền `8d1d2c37bc6259a58dd110a63f4fc1d3963b058f`. [Hồ sơ nghiệm thu](ACCEPTANCE-C2.md) ghi phạm vi review và ủy quyền; lượt khép chỉ đổi tài liệu, không chạy lại build/tests. Không khép toàn U03.

**Người dùng đã chơi thử C2 nhưng chưa xác nhận toàn bộ cảm giác/hình ảnh; presentation vẫn blockout.** Quái B không đánh A là đúng thiết kế encounter riêng: target/damage/kết quả/Retry cách ly, chưa phải khu quái chung. LatestReview/LatestSolo đã chuyển sang phiên chơi thử sau bàn giao; bằng chứng lịch sử công bố và manifest giữ nguyên. Các câu READY_FOR_REVIEW/chưa nghiệm thu bên dưới mô tả thời điểm bàn giao trước xác nhận này.

Chạy [Play-U03-C2.cmd](../../Play-U03-C2.cmd), [Play-U03-C2-Network.cmd](../../Play-U03-C2-Network.cmd), dừng bằng [Stop-U03-C2.cmd](../../Stop-U03-C2.cmd). Làm theo [checklist chơi thử](../../Play-U03-C2-CHECKLIST.md). Launcher dùng một clone `Artifacts/U03/C2/Source`, package cuối `Runs/Package-20261115-120335/Archive/Windows`; không cần mở Play trong Editor gốc.

## Hành vi và quyền quyết định

Quái chuyên biệt dùng motor/combat/vital/hurtbox hiện có và definition Monster: HP600/raw100, startup0,60, active[0,60;0,75), tổng1,50s. `UU03MonsterStateComponent` giữ FSM server; encounter đưa aim/LOS/range/leash/Return/death vào timestamp scheduler chung. Startup theo mục tiêu, active/recovery khóa hướng, dừng ngang vẫn giữ gravity. Đỡ/parry theo resolver chung; E chỉ Interrupt startup, Q không Interrupt. Không mở Feint/né/đỡ cho quái. Điều kiện 2m chỉ admission; hit dùng sword box và hurtbox thật.

Chase/Return dùng navigation Unreal ở300cm/s. LOS chân+90 và các biên2/10/15/0,50m được kiểm riêng. Return hủy action theo cutoff, không rechase/teleport/hồi máu sớm; vào vùng50cm mới đầy HP, life mới và collision rebase một lần. Defeated không tự hồi sinh. Hai map có đường quanh vật cản được author và kiểm path; trạm hồi quy cũ ở session riêng `?U03Regression=1`, không chạy fixture địch song song C2 mặc định.

GameMode tạo encounter riêng theo controller, immutable ID/revision, hai subject và spawn transforms. Collection lẫn resolution chỉ cho cặp player–monster cùng encounter Running. Retry đi qua PlayerController sở hữu, kiểm ID/revision/sequence và terminal state. Một transaction đóng event/life cũ, reset cả hai subject rồi publish Running. Reset HP/shield/resource/cooldown/posture/CC/slow/immunity/feedback/action/pending/combo/position/AI; giữ watermark/settings/release gate. Server giữ AwaitingResume qua Retry và từ chối control/movement packet của life cũ. Click Retry không thành đòn đánh.

Logout tìm encounter bằng owner controller kể cả khi Unreal đã UnPossess pawn, đóng ownership và invalidates nguồn damage trước hủy. Reconnect nhận encounter/pawn/life mới; không khôi phục combat và không áp chính sách reconnect đấu trường.

Tab dùng Target binding của từng LocalPlayer, không RPC combat. Chọn đối thủ sống trong20m, projected feet+90 và camera environment LOS; xếp screen-center/3D/stable ID. Toggle một edge, giữ tới30m; che khuất ẩn ngay và bỏ sau1s liên tục, thấy lại reset timer; offscreen chỉ ẩn. Death/life/revision mới bỏ chọn không thay mục tiêu. Không tự quay camera/facing, đổi hitbox hoặc quyền damage. UI hiển thị kết quả server/Retry/binding thật; quái có tư thế, mũi tên, chữ phase và sword-box cảnh báo, không dựa riêng màu. Animation/notify/root motion không quyết định damage/movement.

## Cổng cuối và bằng chứng

Tất cả hàng dưới gắn source `b43b15d`; [manifest](Evidence/C2/MANIFEST.json) chứa SHA256 DLL/Game/Engine, hai map, từng file log/video và package index48 file. [Test matrix](C2-TEST-MATRIX.md) ánh xạ luật tới đúng tầng; [contracts](C2-CONTRACTS.md) được commit trước runtime tại `6ee59a6`.

|Cổng|Kết quả và run dưới `Artifacts/U03/C2/`|
|---|---|
|Generate / Editor / Game|PASS, exit0; `Runs/Build-20261115-120024`|
|MCP Automation đầy đủ|**131 Success, 0 Failed**:117 U00–C1 +14 C2; `Runs/MCPTests-20261115-120144`. Trigger TestRunner và đọc GetLogEntries trên cold clone; mỗi test có completion riêng, không dùng PASS cũ|
|Windows package|BUILD SUCCESSFUL, exit0; `Runs/Package-20261115-120335`|
|Smoke3 map|PASS Boot/CharacterCombatLab/NetworkLab; `Runs/Smoke-20261115-120530`|
|Combat input/video|24 PASS; `Runs/InputCapture-20261115-120700`: thắng/thua/Retry, Tab death/revision clear, né/parry/Q/E, focus/menu/Resume, giữ phím qua Retry|
|Chase/Return input/video|11 PASS; `Runs/RouteCapture-20261115-120800`: vòng vật cản, Return latch, không teleport, reset HP/life một lần trong50cm|
|Tab fixture input/video|15 PASS; `Runs/TargetCapture-20261115-120830`: tie-break, hold/toggle/rebind,20/30m, offscreen, che khuất/thấy lại/reset timer|
|Hai client thật|26 PASS; `Runs/NetworkCapture-20261115-120500`: hai owner, né/E, damage/Interrupt history, Won/Lost/Retry isolation, stale/duplicate/running/unowned claims, Logout/reconnect/new identity/old claim|
|Đối chiếu độc lập|41 PASS từ snapshot đã lưu của ba PID: HP/action/AI/result/revision, defense/damage/Interrupt, resource theo authority snapshot timestamp, RetryB bất biến và reconnect mới|
|Launcher|3 refusal guard PASS; manifest/package index khôi phục byte-for-byte. Solo qua `PlayC2.ps1`: `Review-20261115-120636`; network qua `ReviewC2Network.ps1`: `Session-20261115-120356`. Ready rồi mới minimize; scoped Stop và placement restore đã kiểm|

Native C2 bao gồm before/exact/after boundaries, phòng thủ/Interrupt, reset/ownership/stale life, collection đảo và update dài/ngắn, startup aim/gravity, moving LOS, Return cutoff và lethal cùng timestamp theo resolver order. Bộ U00–C1 chạy mới giữ toàn bộ trajectory wall/StepUp/hai pawn. Không mở epsilon deadline. Hai client giữ cap60/server30 và smoothing cũ; input Windows trong video **tuần tự**, không gọi là input đồng thời. Network dùng dedicated Editor, không có Server đóng gói.

Video `.mp4`, PNG và JSON kiểm tra ở `Evidence/C2/Runs/Runs/<capture>/`. Log/text được gzip UTF-8 sau strict decode, redaction token và round-trip verification; raw nguyên bản vẫn trong Artifacts. [TEST-TRACES](Evidence/C2/TEST-TRACES.json) giữ completion/probe traces; [WARNINGS](Evidence/C2/WARNINGS.json) giữ warning/error cả run lỗi; [ENCODING-VERIFICATION](Evidence/C2/ENCODING-VERIFICATION.json) ghi kiểm encoding. Hash raw và published phân biệt rõ trong manifest.

## Điều kiện bắt đầu, lỗi đã giữ và giới hạn

Dọn dung lượng đã hoàn tất trước nhánh:162,505GiB được dọn,122635 file bảo vệ được hash-verify, main không đổi runtime. Đã thật sự chạy lại B2/C1 solo/network sau dọn: B2 `Review-20261114-175451`/`Session-20261114-175539`, C1 `Review-20261114-175514`/`Session-20261114-175640`. Raw prerequisite và audit cleanup được xuất trong `Evidence/C2/Runs/Prerequisite/`; `Preflight/RESULT.json` lưu source/hash từng session. Private `Config/DefaultEngine.ini` vẫn hash `412b42b66583f9b6e4ecdc63cd2423457bf0b1a3d192f5b0f18375ee801f8161`, không stage. Nội dung Maintenance có sẵn không bị stage hoặc xóa.

Không xóa run lỗi/invalid hoặc package trung gian. `Audit/PACKAGE-LIFECYCLE.json` ghi source/trạng thái superseded/failed/final; vẫn chỉ có một clone C2. Các PASS trước source cuối được giữ để truy vết, không thay cổng cuối. Các lỗi đáng chú ý:

- Author nav ban đầu báo success khi build còn khóa: candidate được giữ INVALID; sửa async load lock/brush/bounds. Lần dùng protected nav API không compile cũng giữ log. Path author sau đó đã PASS cả hai map.
- Moving LOS dài/ngắn ban đầu lệch do truy vấn Chaos theo frame; sửa bằng captured environment triangles của resolver. Startup aim trong barrier, gravity lúc AI stop và Retry server control gate đều có regression test sau sửa.
- Target capture hai lần lỗi hiệu chuẩn mouse và hướng WASD sau xoay camera; sửa harness, không sửa sensitivity gameplay. Capture parry trễ so với active cũng giữ failed video, sửa lịch input theo clock quan sát, không nới parry window.
- Network `NetworkCapture-20261115-115700` và `...120100` thất bại ở encounter cũ sau disconnect. Lần đầu OS kill, lần sau graceful Quit chứng minh bug Logout phụ thuộc pawn; `b43b15d` sửa theo owner. Test native mới và lượt graceful Quit/reconnect cuối đều PASS. OS kill chỉ được server nhận biết khi transport cleanup/timeout; không suy diễn việc kill PID là Logout tức thì.
- Smoke `...115100` INVALID do output tương đối; chuẩn hóa absolute path, smoke cuối PASS. Package `...120232` exit10 do `ConflictingInstance` của UBT mutex trong lúc Live Coding; thêm WaitMutex, run cuối `...120335` PASS. Không gọi lỗi này là thiếu SDK chỉ vì nhãn exit tổng của UAT.
- Có compiler warning toolchain14.51 chưa preferred, truncation float và deprecated API; native fixture có warning thiếu skeletal mesh/socket. Toàn bộ warning thực tế được giữ, không tự đổi toolchain/asset ngoài phạm vi để che warning.

Live Coding đã trigger/poll đúng AGENTS, log cuối: `Live coding succeeded, data type changes may cause packaging to fail if assets reference the new or updated data types` (2026-11-15 05:03:56 UTC). Reflection/header layout được xác minh bằng full UBT/cold clone; **Play trong Editor gốc chưa bảo đảm chạy C2**. Không save/restart Editor gốc. PID/HWND gốc từng thay đổi ngoài luồng; restore bỏ handle stale, không chạm cửa sổ thay thế, các session cuối capture/restore placement của PID10016 hợp lệ.

Đây là lab solo một encounter hoặc tối đa4 trạm, nghiệm thu network dùng2 client trên cùng máy/loopback. Chưa kiểm WAN/prediction/bù trễ, không triển khai chúng. Fixture nhiều target chỉ kiểm thông tin, không thêm encounter gameplay. Chưa có nghiệm thu cảm giác của người dùng về telegraph/chase/return/Retry; B2/C1 vẫn chưa được người dùng chơi thử. Không triển khai quest/loot/XP/boss/nghề/dungeon/PvP/hồi sinh sản phẩm/D.

## Thời gian

`Audit/TIMINGS.json` tách command wall time build, package, Automation và physical capture, kể cả failed run có đủ timestamp. Các nhóm có chạy chồng nhau nên không cộng thành thời gian lao động; run thiếu timestamp kết thúc được giữ và loại khỏi phép tổng. Cửa sổ triển khai contracts→FSM:14/11 17:58:53–20:01:19 (+07), khoảng2h02, bao gồm các lượt build/test xen kẽ; không có đồng hồ đo active coding độc lập. Các cửa sổ sửa lỗi nav/causality/aim/Retry:14/11 18:16–18:56; Logout:15/11 khoảng11:57–12:00:22. Đây là cửa sổ truy vết commit, không phải ước lượng giờ người chính xác. Không tính khoảng nghỉ qua đêm là triển khai. Build cuối khoảng2 phút, Automation cuối khoảng1 phút, package cuối gồm chờ mutex và UAT1m26s; số đo chi tiết ở JSON. Tài liệu/harness bàn giao không làm chạy lại native build/tests.

Điểm dừng bàn giao trước review là READY_FOR_REVIEW. Người dùng nay đã ACCEPTED kỹ thuật và cho phép khép tài liệu, fast-forward/push main; dừng sau xác minh SHA remote. Cảm giác/hình ảnh chưa được xác nhận đầy đủ, chưa triển khai D và chưa khép toàn U03. Runtime/config/bằng chứng giữ nguyên, không chạy lại build/tests cho thay đổi tài liệu này.
