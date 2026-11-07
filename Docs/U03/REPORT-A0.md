# U03-A0 — ACCEPTED về kỹ thuật

Reviewer đã nghiệm thu tại **32603b1**, source kiểm chứng **c33f2fc**, không phát hiện lỗi chặn còn lại trong phạm vi hợp đồng/model A0. [Căn cứ nghiệm thu](ACCEPTANCE-A0.md). Người dùng giao khép hồ sơ và fast-forward main rồi dừng, chưa giao A1. Lượt khép chỉ sửa tài liệu, không chạy lại build/tests và giữ nguyên bằng chứng gốc.

Nghiệm thu chưa bao gồm gameplay, input, collision adapter hoặc hai client U03; các cổng đó thuộc A1 trở đi. Các trạng thái chưa ACCEPTED/READY_FOR_REVIEW bên dưới là lịch sử tại lúc bàn giao32603b1, đã được quyết định nghiệm thu phía trên thay thế.

## Hồ sơ bàn giao lịch sử tại32603b1

Hai lần bàn giao trước tại `6abfbf4` và `6f7b7b7` đều NOT ACCEPTED. Lượt này chỉ sửa riêng hai boundary mới trong A0; chưa khép, chưa merge main, chưa A1. Bản sửa cuối build Editor/Game thành công và đạt70/70 Automation Success,0 Failed. Không dùng kết quả68/68 cũ thay cho bản sửa; chưa tự kết luận ACCEPTED.

## Nguồn và thay đổi

Nhánh `u03/a0-contract-model`; nền main `f8434d23e4f27a649dde4ea21f47dd296c0fc9ba`. Source sửa cuối `c33f2fc9aac3be7c64c75fa0680b2785ec2079fd` đã commit/push. Commit hồ sơ sau source này không đổi Source/Content/Config/Plugins/project; không gán SHA hồ sơ cho binary.

Chỉ sửa `U03ActionModel.h/.cpp`, `U03ActionModelTests.cpp` và hồ sơ A0. Không đổi input hoặc runtime đòn1, không thêm asset/plugin/module, không triển khai A1. [Hợp đồng](CONTRACTS.md), [ma trận](TEST-MATRIX.md). Diff review: `git diff 6f7b7b7..c33f2fc -- Source`.

**Nhóm event cùng timestamp:** sau mỗi `ResolveEvent`, model gọi lại `NextEvent` với horizon đúng `Now`, lặp tới khi không còn event tại timestamp hiện tại. Nhóm này bao gồm event vừa được callback phát hiện. Chỉ sau khi cả nhóm hết mới sample endpoint, xử lý action-end/TTL/grace/successor hoặc admission. Điều này áp dụng cả khi `Now == T`, không phụ thuộc vòng lặp update dài còn chạy hay không. Resolver cung cấp thứ tự ổn định U02; mọi event đã giao phải được tiêu thụ. Timestamp trả về sai trong nhóm làm advance thất bại thay vì cho admission đi tiếp.

**LostGround đúng action-end/grace:** transition lifecycle xóa pending/combo/grace và latch mất nền trước khi xét action cũ còn cancellable hay không. Vì vậy LostGround vẫn được nhận tại action-end hoặc khi action đã hết trong grace. Natural completion không được tái tạo grace hoặc successor khi đã mất nền/dead. Context admission cũ ghi grounded không xóa latch này. Chỉ `SetGroundedCurrent(true)` từ một authority resolver event xác nhận landing; landing tự nó không tạo action hay phục hồi combo/buffer cũ. Command mới sau landing bắt đầu Attack1.

## Regression tests mới

`AnimeMMORPG.U03.A0.TimestampGroupBeforeTransitionAndAdmission` kiểm16 tổ hợp: event tại0,18 hoặc action-end0,40; endpoint ngắn hoặc update tới1,0; Advance hoặc SubmitBatch; collection thuận hoặc đảo. Fixture dùng ledger/comparator U02, nguồn2 đánh không lethal, nguồn3 lethal, callback đầu phát hiện thêm nguồn4 cùng timestamp. Trace/assertions buộc thứ tự2/3/4, cả ba callback xong trước return, nguồn4 không damage lại người đã chết, không sample endpoint và không tạo successor giữa nhóm. Death đứng sau hit đầu vẫn chặn admission/pending successor.

`AnimeMMORPG.U03.A0.LostGroundAtActionEndAndGrace` kiểm4 tổ hợp: Attack1 tại0/buffer0,30/LostGround0,40, hoặc không buffer rồi mất nền0,45 trong grace; mỗi ca chạy endpoint ngắn và update dài. Kiểm transition được nhận, không successor, admission với stale grounded context bị Locked, không thể tự xác nhận landing ngoài callback, command mới sau landing bắt đầu Attack1.

Bảy test A0 cũ giữ nguyên, gồm update dài với Interrupt/death tại0,45, cutoff loại trừ, giữ hit đã confirmed, definition/resource/buffer/admission. Các test này không bị thay bằng fixture ledger độc lập. Pure model fixture chưa là bằng chứng gameplay runtime.

## Kiểm chứng và bằng chứng

Build/test trong clone từ source đã commit: `D:/Data/AnimeMMORPG/Artifacts/U03/A0/Source`. Full UBT Editor/Game Win64 Development qua `Scripts/U00.ps1 -Task Build`, không Live Coding. UE5.8.4 CL58902052, MSVC14.51.36260/toolset14.51.36231, SDK10.0.26100.0. TestRunner/MCP port riêng18030, đọc schema tại process clone, trigger filter `AnimeMMORPG`, đọc từng result và queue hoàn tất. Mỗi run giữ source, command/exit, process/binary/log hashes.

Build cuối **Build-20261107-121809-999-441fb921**: Generate0, Editor0, Game0; cả ba log đọc đúng encoding có `Result: Succeeded`. [Source](Evidence/A0/Build-20261107-121809-999-441fb921/SOURCE.json), command/result JSON và log.gz cạnh đó giữ nguyên lệnh/exit code. Full command: `Scripts/U00.ps1 -Task Build -ProjectPath D:/Data/AnimeMMORPG/Artifacts/U03/A0/Source/AnimeMMORPG.uproject -EngineRoot D:/Software/UE_5.8 -OutputRoot D:/Data/AnimeMMORPG/Artifacts/U03/A0/Runs`.

Automation cuối **MCPTests-20261107-121928**, PID14680: **70 test riêng,70 Success,0 Failed**, queue xác nhận70 tests performed. Gồm9 test A0, trong đó2 regression mới của lượt này, và61 test U00–U02 hồi quy mới chạy. [Từng test](Evidence/A0/MCPTests-20261107-121928/result.json), [MCP results](Evidence/A0/MCPTests-20261107-121928/mcp-results.json), [PID/command/hash](Evidence/A0/MCPTests-20261107-121928/process.json), schema/trigger và log Editor cạnh đó. Cả TimestampGroupBeforeTransitionAndAdmission và LostGroundAtActionEndAndGrace đều Success; trace ghi thứ tự nhóm, event còn lại, admission, successor và landing.

Editor DLL SHA256 `9637e940b92ed809e3c3b820fd6edc6671ce1b4d59aef8dbffd76e8c3aee6303`; Game exe SHA256 `27c57e2e37a9339e5ebb70862e160d38e2c35b319f27212cd0636a05a6c1bc5d`. Module hash khớp process Automation; manifest giữ ba source Git blobs. Package N/A trong A0.

Lượt trung gian `95095b7` cũng build/test70/70 trước khi bổ sung guard natural completion không tái tạo grace/successor sau lifecycle invalidation. Source cuối `c33f2fc` đã build/test lại riêng như trên; không cộng dồn thành140 tests.

Hồ sơ raw/publish dùng decoder nghiêm ngặt đã sửa ở lượt trước: nhận diện UTF-16/UTF-8 trước redact, publish UTF-8, không replacement decoding. [Manifest](Evidence/A0/MANIFEST.json), [timeline](Evidence/A0/TIMELINE.log), [encoding verification](Evidence/A0/ENCODING-VERIFICATION.json), [warnings](Evidence/A0/WARNINGS.json). Đã kiểm136/136 nội dung publish bằng raw decode/redact và hash publish;102/102 raw file lịch sử tại bản bàn giao6f7b7b7 giữ nguyên hash. Publish không có replacement character hoặc NUL. Không xóa raw hoặc failed runs; Git giữ các bản bàn giao bị từ chối. Báo cáo được viết UTF-8, không qua shell codepage.

## Giới hạn và điểm dừng

Các run66/68 trước đây là lịch sử; nghiệm thu U00–U02 là kế thừa. Chỉ kết quả run cuối của source mới là bằng chứng mới cho sửa đổi lần này; không cộng số test giữa các run. Các warning compiler newer-than-preferred, API deprecated của engine/U01, double sang float vẫn giữ nguyên văn. Failed build đầu do helper Life/Flags va chạm unity build vẫn còn. Binary trung gian cũ không được lưu/hash đầy đủ; chỉ dùng binary/hash/process cuối để bàn giao.

Pure model không có pawn/world/net owner/role thực: N/A. Không chạy input Windows/video/package/cook/dedicated+hai client mới; A0 chưa có gameplay U03. Các bước30/60/120Hz model không phải FPS runtime. A1 vẫn phải cung cấp collection geometry/world event toàn cục theo hợp đồng resolver và input/snapshot thực; B2 cần defense history/runtime. Không mở AllToolsets hoặc GitNexus.

Config riêng giữ nguyên, không in/stage/restore token. Editor gốc không được restart/lưu bởi lượt này; trạng thái process tại cuối chỉ chứng minh lúc kiểm tra, không chứng minh toàn bộ lịch sử. Header/model mới kiểm bằng clone cold build, không khẳng định Editor gốc nạp native mới.

**READY_FOR_REVIEW U03-A0.** Không còn test fail trong lượt cuối; hai lỗi chặn được sửa và có regression evidence để reviewer đánh giá lại. Chưa ACCEPTED, không merge main, không bắt đầu A1.
