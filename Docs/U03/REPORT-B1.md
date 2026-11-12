# U03-B1 R1 — READY_FOR_REVIEW

Nhánh `u03/b1-dodge`; source native kiểm chứng **3fd6c3d82e3c85a1eda6be8d35961c863019d4f7**, sửa từ b2c9676. Main giữ04f902e. B1 cũ **NOT ACCEPTED** do đường preview/commit khác nhau giữa bước; [review](REVIEW-B1-b2c9676.md), [báo cáo gốc](REPORT-B1-b2c9676.md) và Evidence/B1 giữ nguyên. Bản này chưa tự ACCEPTED, không merge/B2.

## Sửa runtime

Geometry và commit dùng **cùng retained swept trajectory**, có knot timestamp cho sweep/slide/StepUp, không còn chord hai đầu rồi chạy lại partial walking solve. Native StepUp scope loại rollback/search excursions; chỉ thay bằng chord khi capsule sweep riêng xác nhận chord đó thông. World chia tại mỗi knot trước collect; commit áp đúng prefix đã collision-solve, ETeleportType::None, không solve lại hoặc teleport300cm.

Quantum ngang1/240giây giữ qua endpoint update; cache bị loại khi life/action, actual pose, nhóm pawn đang né hoặc scene geometry đổi. Đường phẳng bị chặn đi theo distance/1200 rồi đứng yên; ramp/StepUp phân thời gian quantum trên các đoạn hợp lệ. CMC authority không chạy thêm walking solve làm đổi pose đang thuộc trajectory. Falling/gravity vẫn native; smoothing và luật timing/charges/buffer/cost/hướng giữ nguyên.

Hai pawn active được giải continuous relative capsule collision trên cùng đoạn, clip cả hai trước collect hit; không dùng transform cũ của peer làm blocker tĩnh. Pair order ổn định theo identity, xét contact sớm nhất và giải lại sau clip. Skin hình học0,01cm không mở rộng deadline. [Hợp đồng R1](B1-R1-CONTRACTS.md).

Không kết luận lỗi giữ W vẫn lùi: luật không WASD=lùi theo aim giữ nguyên; input thật kiểm vector W/A/S/D/chéo/không hướng riêng. Presentation vẫn locomotion blockout/HUD, chưa art sản phẩm, không điều khiển hit/motor. Không thêm asset/module/plugin/framework hoặc B2/C1/C2.

## Bằng chứng mới

Cold build/test/package tại clone `Artifacts/U03/B1/Source`, commit3fd6c3d; không dùng Editor gốc làm chứng cứ binary mới. UE5.8.4 CL58902052, VS14.51.36260, SDK10.0.26100.0. Source mới chỉ đổi7 files dưới Source so b2c9676; không đổi asset/config. Commit hồ sơ sau source này chỉ là tooling/docs/evidence.

| Cổng | Run source R1 | Kết quả |
|---|---|---|
| Generate/Editor/Game | Build-20261112-161120 |exit0; Editor/Game Result: Succeeded|
| MCP TestRunner/schema/log/queue mới | MCPTests-20261112-161254 |93 tên riêng,93 Success,0 Failed, queue93 hoàn tất|
| Windows Development package | Package-20261112-161409 |UAT exit0,48 package files|
| Package smoke | Smoke-R1-20261112-1616 |3/3: Boot/CharacterCombatLab/NetworkLab load và exit0|
| Package physical input/video | InputCapture-R1-20261112-1620 |38/38, completed=true|
| Terrain physical input/video | TerrainCapture-R1-20261112-1620 |17/17, completed=true|
| Dedicated Editor+hai client | NetworkCapture-R1-Final |20/20, completed=true|
| Disconnect/reconnect | Session-20261112-183400 |2/2, live PID/exe/module/source/world/owner guards; fresh identity,2 lượt, không replay|

93 tests gồm90 hồi quy chạy mới và3 test R1:

- `RetainedWallSlideAndStepPrefixes`:nhiều timestamp giữa bước tường/slide/StepUp, actual committed transform khớp PositionAt(t); không giữ failed search excursion thành đường đi thật.
- `IncomingMidWallAndStepLethal`:incoming geometry hit giữa bước bị tường chặn và đoạn lên bậc, nonlethal/lethal, long/short update. Hit **đúng** S+0,16; wall pose(0,532;0;97,296), stair pose(3,523;0;99,470) ở fixture này. Pose thực tại callback khớp đường xét hit; lethal ngăn mọi phần dịch chuyển sau đó. Long/short cho cùng timestamp và vị trí, không chỉ cùng endpoint. Trace `U03B1_R1_MID` có số đầy đủ.
- `SimultaneousPawnCCD`:hai actor thật trong Game-world né đối đầu/cùng hướng, không overlap/xuyên hoặc bị chặn bởi stale transform; đảo collection và partition update vẫn cùng kết quả. Đây là fixture authority, không giả làm input hai client đồng thời.

Phân biệt tầng: model/Game-world assertions chứng minh timing, geometry, actual transform/cutoff; physical input/video chứng minh keys/gate/HUD; network process chứng minh authority/replication. Reviewer còn phải đánh giá cảm giác/độ dễ đọc. Không dùng90 tests hoặc video source6603c30 thay cho R1.

## Failed runs và giới hạn

Giữ log source8959290 build fail vì dùng `.IsValid()` trên raw pointer API ignore-actor; đã sửa kiểu dữ liệu. MCPTests-155640 có incoming fixture fail và phát hiện trace giữ native StepUp search;160246 bắt failed search excursion còn sót. Bổ sung override StepUp để giữ survivor validated. MCPTests-160833 chỉ còn assertion fixture đặt hit trước đoạn thật sự đi lên; đổi setup stair sang2ms trong quantum và dùng equality timestamp chính xác. Run cuối93/93, không xóa các lượt fail.

InputCapture-R1-1616 có cạnh buffer đến muộn thành fresh admission sau0,60; giữ là invalid cho phép đo nối đúng deadline. Harness cuối gửi cạnh sớm hơn và replacement, vẫn giữ assertion start đúng0,60; không đổi binary hoặc nới gameplay window. Lịch sử B1 gốc/failed runs vẫn ở báo cáo gốc và Evidence/B1.

NetworkCapture-R1-1626 đã đạt20 checks; phép kiểm live reconnect của session162238 bị guard từ chối vì process đã thoát trước lúc xác minh, không tính PASS reconnect. Raw/log/invalid record giữ nguyên. Phiên183400 được chạy lại và kiểm live/cleanup trong cùng pipeline; không dùng sample sau khoảng ngắt dài để kết luận FPS/focus regression.

Warnings đầy đủ trong manifest/log: compiler ngoài preferred version, engine deprecation, fixture không gán mesh/socket, audio conversion và expected unowned RPC warning. Không tuyên bố warning-free. Profile review client60/server30,900×540/internal50%, Lumen atlas2048/RT128/texture256, diffuse/reflections0, virtual shadow0/shadow2, idle0; xác minh cvar thực và editorThrottle=false. FPS thực lấy wall/GFrameCounter trong wall-frame-summary, không lấy simulation dt làm FPS; không benchmark U04 hoặc tuyên bố mọi frame đạt cap.

Phiên cleanup183400 có median FPS thực A59,966/B60,015/server29,917; p95 frame17,450/17,745/35,004ms; max47,611/106,542/113,874ms, gồm setup/reconnect. Không dùng phiên162238 có khoảng ngắt dài để kết luận performance/focus. Source/pawn/world/role/owner/receive/action/life/hit timestamp trong raw logs; video là wall-clock30FPS, không suy120FPS từ model step.

## Hồ sơ và môi trường

[Manifest R1](Evidence/B1-R1/MANIFEST.json), [package hashes](Evidence/B1-R1/PACKAGE.csv), [strict encoding](Evidence/B1-R1/ENCODING-VERIFICATION.json), [warnings](Evidence/B1-R1/WARNINGS.json), [test traces](Evidence/B1-R1/TEST-TRACES.json). Decode BOM/UTF16LE/UTF8 nghiêm ngặt trước redact/gzip, không errors=replace. Raw lịch sử không xóa; public Evidence/B1 không sửa. Clone/binaries hiện theo source R1; manifest lịch sử giữ binary identity đã review, package cũ còn riêng trong archive.

Editor gốc PID432 giữ mở, không restart/save hoặc xác nhận đã nạp R1. Config riêng so baseline nguyên byte; không stage/in token. Launcher lưu mọi HWND, verified minimized sau clients ready; Stop đúng PID/exe/project/userDir/source/hash, gồm reconnect và restore placement. Launcher B1 hiện kiểm manifest R1; [solo](../../Play-U03-B1.cmd), [network](../../Play-U03-B1-Network.cmd), [Stop](../../Stop-U03-B1.cmd), [checklist](../../Play-U03-B1-CHECKLIST.md).

Điểm dừng cuối **READY_FOR_REVIEW U03-B1**, chưa khép/merge hoặc triển khai B2.
