# U03-B1 — READY_FOR_REVIEW

B1 được giao riêng ngày2026-11-12, từ main **04f902e59f0c022b30b09ac9dd06a1a074be4929** đã khép A1. Nhánh `u03/b1-dodge`; source native kiểm chứng **6603c305747ea3627b7d7d85d0dceeb0394d73e4**. Các commit bàn giao sau source này chỉ bổ sung tooling/hồ sơ/bằng chứng, không đổi Source/Content/Config/Plugins. Chưa ACCEPTED, không merge main hoặc bắt đầu B2.

## Kết quả và phạm vi

- Né300cm/0,25giây, vận tốc chủ động1200cm/s, khóa đến0,35, start cách>=0,60; hai lượt hồi tuần tự2giây từ lần tiêu đầu, dùng lượt2 không reset hồi. Không tiêu energy hoặc cấp i-frame.
- Dispatcher physical edge dùng binding/gate A1; normalize WASD theo camera yaw, không hướng lùi aim, capture hướng khi nhận. Giữ Shift không loop. Buffer né một slot TTL0,15, replacement/expiry; không queue khi cạn lượt/hardCC/active hoặc recovery đánh. Né chỉ hủy startup sau khi kiểm đầy đủ điều kiện thay thế.
- Timeline sở hữu lượt/sequence/deadline; RPC chỉ enqueue. Receive groups khác thời điểm giữ thứ tự, cùng timestamp né ưu tiên trước đánh sau old-world barrier. Death/reset/lost-ground/landing/stale life giữ đường authority; saved moves không sở hữu model/lượt/deadline và không restore input jump của life cũ.
- Motor reuse `MoveAlongFloor/StepUp/FindFloor/AdjustFloorHeight`, swept capsule42/96, step45cm và slope45° U01. World chia đoạn ngang<=5cm, preview deferred/revert, collect contact trước khi commit tới event sớm nhất; lifecycle/death loại phần chuyển động sau event. Không teleport300cm/root motion, không thay smoothing hoặc dùng ProbeSpeed làm gameplay.
- HUD tên phím thật, lượt/hồi lượt và trạng thái né. Presentation dùng **locomotion blockout hiện có**; không có animation né thành phẩm, montage không quyết định gameplay. Không thêm asset/module/plugin/framework hoặc B2/C1/C2 gameplay.

[Hợp đồng](B1-CONTRACTS.md), [ma trận](B1-TEST-MATRIX.md). Diff runtime: `git diff 04f902e..6603c30 -- Source Content Config Plugins`;15 source blobs trong manifest, không đổi asset/config trong phạm vi B1. Config riêng giữ nguyên, không stage token.

## Bằng chứng mới trên source B1

Mọi build/test/package chạy trong `Artifacts/U03/B1/Source` từ commit đã ghi. Không dùng Editor gốc làm bằng chứng native mới. UE5.8.4 CL58902052; compiler Visual Studio14.51.36260, SDK10.0.26100.0; command/engine/toolchain/exit/PID/log có trong từng run.

| Loại | Run cuối | Kết quả thực |
|---|---|---|
| Generate/Editor/Game cold build | Build-20261112-144056 | cả ba exit0; Editor/Game Result: Succeeded |
| MCP TestRunner, schema và log mới | MCPTests-20261112-144222 |90 tên riêng,90 Success,0 Failed, queue90 hoàn tất |
| Windows Development package | Package-20261112-144256 | UAT exit0; archive Windows,48 file hash |
| Package smoke | Smoke-20261112-1444 | Boot/CharacterCombatLab/NetworkLab load, exit0:3/3 |
| Package physical input/video | InputCapture-20261112-1444 |38/38 checks; completed=true |
| Terrain physical input/video | TerrainCapture-20261112-1444 |17/17 checks; completed=true |
| Dedicated Editor server+hai client | NetworkCapture-20261112-1448 |20/20 checks; completed=true |
| Disconnect/reconnect | Session-20261112-144605/reconnect-result.json |2/2; pawn identity mới,HP1000,2 lượt/action0/dodge0/pending0 |

Tên folder capture là run label; UTC trong raw log/process và duration wall-clock mới xác định thời gian thực. Bằng chứng U00–A1 đã nghiệm thu là nền kế thừa;90 tests ở đây là lượt chạy mới trên binary B1, không tái dùng log A1/A0.

12 tests B1 mới, cùng78 hồi quy trong run90:

1. `ModelDeadlinesAndSequentialCharges`:0,25/0,35/0,60/2/4, buffer consume, cạn lượt không queue, hồi tuần tự và energy100.
2. `ModelBufferReplacementAndPriority`:exact expiry/replacement/control clear, hướng camera-local, cùng timestamp và duplicate.
3. `ModelStartupReplacementAndLifecycle`:trước/đúng active-start, invalid replacement không mất attack/lượt, death/lost-ground/reset và hardCC admission fixture.
4. `RuntimeSweptDistanceAndLongUpdate`:bước30/60/120Hz và update dài, actual capsule300cm±5, unlock0,35.
5. `RuntimeWallPersonAndCliff`:vật cản/người/nền hữu hạn, không xuyên/vượt mép, blocked vẫn mất lượt.
6. `RuntimeStartupCancelResetAndDamage`:startup cancel, không hit muộn, khóa sword trong né, reset giữa né.
7. `RuntimeStepSlopeAndRemovedFloor`:step30/60cm, slope30/44/46/60°, gỡ support hiện tại thật làm dừng ngang/chuyển Falling. Hồi quy U01 cũng chạy mẫu45°; không gọi mẫu44° là đã đo đúng45° riêng cho né.
8. `RuntimeNoIFrameAndDeathCutoff`:incoming geometry hit thật, mất60HP trong né; lethal tại0,16 cắt đoạn đang chạy ở192cm, không đi tiếp tới300cm trong update dài.
9. `RuntimeMenuAndStaleLife`:menu không hủy dịch chuyển đã nhận, pending bị xóa; reset/old-life RPC không tạo né hoặc mất lượt.
10. `RuntimeBatchPriorityAndRejectedReplacement`:runtime enqueue cùng timestamp né thắng attack; cạn lượt không hủy startup.
11. `RuntimeSlowMotorBudgetFixture`:hạ ngân sách đi thường/acceleration, tăng friction/braking vẫn né300cm. Đây là **fixture motor**, chưa triển khai slow effect B2. Tương tự hardCC chỉ kiểm context admission, không giả có CC gameplay.
12. `RuntimeInteractionClearsWaitingDodge`:sau khóa0,35, buffer chờ0,60 bị loại nếu nhận interaction/control lock; không tiêu lượt2, fresh press sau unlock vẫn hợp lệ. Đây là ca bổ sung khi tự kiểm source cuối, đã sửa authority lock hook và chạy lại toàn bộ bằng chứng trên source6603c30.

Tên đầy đủ có prefix `AnimeMMORPG.U03.B1`; từng test/result/queue trong result.json và Editor.log. Hồi quy mới bao gồm U00 clock/units, U01 motor/camera/jump/terrain/gate/settings/network, U02 collision/vital/identity/shield/cutoff và A0/A1 timeline/combo/presentation. Model steps không được ghi thành FPS thực.

Input package dùng SendInput với guard PID/executable/hash/source/project/world/local owner/foreground; native log xác nhận physical keys.38 checks kiểm sáu hướng gồm chéo và không hướng,300cm±5 ở vị trí nền phù hợp, energy không tiêu, held không loop, buffer/charge tuần tự, startup cancel, jump không phát lại, menu/focus/Resume và full-wall clipping.17 checks bổ sung có video/screenshot mép vực, slope30/46,step40 và corridor120. Focus gap0,6giây được ghi metadata; video lặp frame nhìn thấy cuối khi minimize, sau đó tiếp tục theo wall clock. Không tăng tốc video hoặc dùng fixture RPC thay thao tác né thật. Console fixture chỉ đặt trạm/reset, có nhãn.

Network mỗi client physical né hai lần và cạnh thử khi cạn lượt. Lấy mẫu log sau thao tác theo authority timestamp/life để tránh filesystem/PNG encoding làm trôi cửa sổ2giây. Cả ba process đồng thuận sequence/charge/restore, first dodge300cm±5 và position converge<5cm. Duplicate/stale/NaN/unowned RPC không tạo thêm action. HP1000 trong network là sample khi không có incoming attacker, **không dùng nó chứng minh no-i-frame**; bằng chứng no-i-frame là Game-world geometry fixture ở trên. Các lane/reset dùng fixture kỹ thuật U02, không phải encounter/trạm quái C2 hoặc PvP.

## Profile và giới hạn đo

Client actual cvars cap60,900×540/internal50%, Lumen atlas2048, RT minimum128MiB, texture256MiB, diffuse/reflections0, virtual shadow0, shadow2, idle0. Server actual cap30/idle0. `editorThrottle=false` được đọc trong Frames.jsonl của từng process. Không đổi smoothing, không giảm cap để che hitch.

`Session-20261112-144605/wall-frame-summary.json` dùng chênh `FPlatformTime`/`GFrameCounter`, không lấy nghịch đảo simulation dt làm FPS thực. Toàn session sau100frames đầu, gồm setup/idle/reconnect: median thực ClientA59,990, ClientB59,999, server29,969 FPS; p95 frame lần lượt17,243/17,190/34,725ms. Vẫn có hitch tối đa23,537/298,303/103,903ms; clientA reconnect có median60,020 FPS và max143,651ms. Chưa cô lập nguyên nhân hitch, không tuyên bố luôn đạt60/30 hoặc nghiệm thu hiệu năng U04. File `frame-summary.json` ở session source6c605bd trước đó chỉ thống kê dt mô phỏng; dùng bản wall-frame để nhận định FPS.

## Failed/invalid runs giữ nguyên

- Build-133150 source03cc696: compile failed do tên test `Flags` gây shadow trong unity và `Forward` chưa namespace. Sửa tên, không xóa log. Các build sau thành công; build/package cũ giữ là superseded.
- MCPTests-133715:5/6, fixture tính sai start spacing của lần né thứ hai sau startup cancel tại+0,10. Sửa fixture dùng `DodgeNextStart`; không sửa gameplay để làm test pass. Full87/87,88/88 rồi89/89 source6c605bd giữ riêng. Khi tự kiểm source cuối, phát hiện pending né có thể tồn tại qua interaction lock trong khoảng0,35–0,60; sửa hook authority control/interaction và thêm test. Run cuối source6603c30 đạt90/90; các build/package/video source6c605bd là superseded, không tính cho binary cuối.
- InputCapture-1358: helper SendInput VK Shift thiếu scan code, native ghi `None`, không kiểm được Dodge. Sửa **helper B1 riêng** gửi Left Shift scan0x2a; không nới guard U01/A1 hoặc đổi gameplay.
- InputCapture-1402:36 checks về input đạt nhưng recorder thread chết ở focus gap, nên video invalid và không tính vào PASS cuối.1405:đi ngang từ vị trí quá gần mép runway làm clip đúng luật, invalid cho mục tiêu đo nền trống.1409:recorder gặp ảnh rỗng trong transition minimize; check recording cuối fail. Sửa harness, offset điểm đo bằng đi bộ thật và kiểm recording thread còn sống/đã ghi tới cuối. Run1413 đạt38/38 trên source6c605bd; run1444 mới là bản cuối trên source6603c30.
- NetworkCapture-1412/1415:đọc log/encode ảnh trước cạnh tiếp theo khiến sample vượt mốc hồi2giây; assertion cạn lượt không còn đúng precondition. Giữ JSON/video/raw log. Run1419 đưa toàn bộ critical edges trước đọc/ghi, rồi chọn mẫu retrospectively theo authority time. Không thay binary6c605bd cho các sửa harness.

Warnings giữ đầy đủ: compiler14.51 ngoài preferred version, engine deprecation C4996, fixture actor không gán skeletal mesh phát socket warning, audio sample-rate conversion và expected unowned-RPC warning từ negative probe. WARNINGS.json gồm cả failed runs/lặp qua MCP, không phải số warning độc lập. Không tuyên bố warning-free.

## Hồ sơ, môi trường và chơi thử

[Manifest](Evidence/B1/MANIFEST.json) ghi source15 blobs, engine/Editor/Game hashes, từng raw/published artifact và encoding; [package48 files](Evidence/B1/PACKAGE.csv), [encoding verification](Evidence/B1/ENCODING-VERIFICATION.json), [warnings](Evidence/B1/WARNINGS.json), [test traces](Evidence/B1/TEST-TRACES.json). Logs decode strict BOM/UTF16LE/UTF8 trước redact và publish gzip UTF8; không dùng errors=replace để tạo bằng chứng. Raw/failed runs giữ ở Artifacts/U03/B1. Không sửa bằng chứng A0/A1.

Editor DLL SHA256 `687449197484ba5b81ccf844a6edc5008773b86fdcd8d6eb10acd8f89e55d0b8`; Game exe `3dad9516357e13590d802ac8aed3899765fcce159582cd17b10c76b53c000b96`; package CSV `665fb37d25c7c8bbf313e7bbf46db28c99331889ae56124d7460b6192ff7a186`. Commit hồ sơ không được gán cho binary source6603c30.

Editor gốc thực là PID432, creation13:06:35 ngày12/11, giữ mở, không restart/save và không xác nhận đã nạp native B1. Hai HWND được lưu placement trước launch, verified minimized sau clients ready và restored Show/normal rect sau Stop. Server/client/package/reconnect chỉ dừng theo session/PID/executable/project/userDir/source/hash; sau cùng chỉ còn Editor gốc. Private config hash khớp baseline; không stage token.

[Play solo](../../Play-U03-B1.cmd), [Network](../../Play-U03-B1-Network.cmd), [Stop](../../Stop-U03-B1.cmd), [checklist](../../Play-U03-B1-CHECKLIST.md). Launcher từ chối nếu clone source/binary/package hash không khớp manifest. Artifact package/clone hiện ở đường dẫn local trong manifest.

Cảm giác né, độ dễ đọc peer và presentation còn chờ reviewer chơi thử. Đây là blockout dùng tạm, chưa art sản phẩm; chưa CC/parry/Q/E/AI/Retry B2–C2, chưa prediction/bù trễ U05, Server đóng gói hoặc benchmark U04. Dừng tại **READY_FOR_REVIEW U03-B1**; không tự ACCEPTED/merge/B2.
