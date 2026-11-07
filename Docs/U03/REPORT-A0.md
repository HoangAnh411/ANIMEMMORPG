# U03-A0 — READY_FOR_REVIEW, bàn giao lại sau NOT ACCEPTED

Bản bàn giao tại `6abfbf4` đã bị reviewer từ chối. Không khép, không merge main, không bắt đầu A1. Báo cáo này thay bản bị mất chữ; lịch sử và failed runs vẫn giữ trong Git và raw artifacts.

Source cuối đã build Editor/Game thành công và chạy **68/68 Automation Success, 0 Failed**. Đây là bằng chứng mới của lượt sửa; kết quả66/66 trước review không dùng thay cho nó. Chưa ACCEPTED.

## Nguồn và phạm vi

Nhánh `u03/a0-contract-model`; nền main/remote vẫn `f8434d23e4f27a649dde4ea21f47dd296c0fc9ba`. Source sửa cuối `ea302cf1a829339cdfa8ee7700218f17a6bcc3dd`, đã push và đối chiếu SHA remote. Commit hồ sơ sau source này không thay Source/Content/Config/Plugins/project; không gán SHA hồ sơ cho binary.

Chỉ sửa model/tests U03, công cụ seal và hồ sơ A0. Không bind input, đổi runtime đòn 1, thêm asset/module/plugin hoặc triển khai A1. [Hợp đồng](CONTRACTS.md), [ma trận](TEST-MATRIX.md). Không dùng GitNexus. Config riêng không in/stage/restore; đối chiếu hash baseline trong manifest. Editor gốc PID12280 vẫn mở lúc kiểm tra, không dùng binary gốc làm bằng chứng mới. Quan sát PID hiện tại không chứng minh toàn bộ lịch sử thao tác; các câu về thao tác chỉ là báo cáo hành động của lượt này.

## Sửa lỗi timeline/API

`Advance` và `SubmitBatch` nhận `ITimelineResolver`, không trả cả một update đã mutate xong để caller giải về quá khứ nữa. Mỗi vòng chỉ đề xuất tới boundary gần nhất: active-start/end, action-end, TTL hoặc grace. Resolver tìm sự kiện sớm nhất trong khoảng đó qua `NextEvent`, kể cả hit tới trong startup của successor vừa tạo. Model giao interval **trước** sự kiện với endpoint loại trừ; sau đó clock tới đúng timestamp và gọi `ResolveEvent` trước sample tại timestamp, hết hạn, successor và admission.

Trong `ResolveEvent`, `CancelCurrent` chỉ làm việc tại clock hiện tại. Không advance/rewind trong cancellation. Reentrant advance bị từ chối. Resolver phải cung cấp mọi sự kiện có thể đổi model trước khi xác nhận interval, tiêu thụ sự kiện đã giao, giữ thứ tự candidate U02 và dedup. Những điều này là hợp đồng collection của resolver; barrier callback và thứ tự chuyển trạng thái được model A0 thực thi. Các helper có tên `Unopposed` chỉ dùng khi xác nhận không có world event, không phải API adapter gameplay.

Test tích hợp mới dùng timeline và ledger U02 thật: Attack1 tại0, buffer0,30, Attack2 bắt đầu0,40; sự kiện địch0,45 được resolve khi clock còn0,45 và Attack2 vẫn startup. Cả Interrupt lẫn death đều loại active Attack2 và hit nguồn đó0,60 trong cùng update tới1,0. Đảo collection không đổi kết quả; hit0,18 đã confirmed vẫn giữ. Test SubmitBatch xác nhận death được giải trước admission tại1,0 dù context caller còn cũ. Test bổ sung death đúng action-end0,40 xóa pending trước khi có thể tạo successor. Model latch death để chặn admission sau đó.

## Sửa cutoff

Interval trước event luôn loại endpoint. Cancellation được kiểm và áp trong callback tại event trước khi xuất point contact. Death/lost-ground0,18 giữ contact0,179999, loại đúng0,18; guard cancellation không hợp lệ vẫn giữ contact0,18. Hit0,17 đã confirmed và dedup không bị xóa; yêu cầu cancel lùi0,16 bị từ chối. Không epsilon nới deadline, không sửa lại interval đã publish để xóa confirmed hit.

Hai test mới là `AnimeMMORPG.U03.A0.LongUpdateResolverInterruptAndDeath` và `AnimeMMORPG.U03.A0.CutoffIntervalsAndConfirmedHits`. Năm test A0 cũ vẫn giữ; test ledger riêng không còn được dùng thay cho chứng minh timeline tích hợp. Guard gameplay vẫn chưa triển khai; ca guard sau barrier trước đây chỉ là fixture và không được coi là runtime defense.

## Sửa encoding và xuất lại bằng chứng

Báo cáo được viết trực tiếp UTF-8, không chuyển qua shell codepage. `SealA0Evidence.py` nhận diện BOM UTF-16 LE/BE, UTF-8 BOM, UTF-16 LE không BOM theo byte cấu trúc; còn lại decode UTF-8 nghiêm ngặt. Không dùng `errors='replace'`. Decode thất bại sẽ dừng seal. Redact sau decode, publish UTF-8; manifest ghi encoding nguồn/publish, hash raw và hash publish, số redaction.

Toàn bộ log/warnings/manifest cũ được xuất lại từ raw đang giữ, gồm failed run đầu tiên; không sửa/xóa raw log. Git giữ bản publish lỗi tại `6abfbf4`. Kiểm tra encoding gồm bốn roundtrip UTF-8/UTF-8 BOM/UTF-16 BOM/UTF-16 LE không BOM và hai đầu vào lỗi phải bị từ chối. Đọc đúng raw build log UTF-16 LE thấy `Result: Succeeded`. Đã đối chiếu **102/102 nội dung publish bằng raw decode/redact**, cùng hash publish; **68/68 raw file lịch sử giữ nguyên hash**. Không có ký tự replacement hoặc NUL trong publish. Báo cáo UTF-8 có0 ký tự `?` literal. [Kết quả kiểm encoding](Evidence/A0/ENCODING-VERIFICATION.json). File JSON publish ghi byte UTF-8 trực tiếp để không nhân CR khi Windows chuyển newline.

## Build/test, warning và giới hạn

Build/test mới trong clone từ source đã commit `Artifacts/U03/A0/Source`, giữ Editor gốc mở. Full UBT Editor/Game Win64 Development qua `Scripts/U00.ps1 -Task Build`; không Live Coding. UE5.8.4 CL58902052, MSVC14.51.36260/toolset14.51.36231, SDK10.0.26100.0. Automation qua TestRunner/MCP tại process clone/port18030, đọc schema tại clone, từng kết quả và queue hoàn tất; không lấy trigger-success làm PASS.

Lượt sửa đầu source `c370ddf` đã build Editor/Game thành công và đạt68/68 Success. Bản cuối `ea302cf` thêm ca death đúng action-end đã được build/test lại riêng; không cộng dồn test giữa các run. Các run66/66 trước review và nghiệm thu U00–U02 là lịch sử, không chứng minh bản sửa này. [Manifest](Evidence/A0/MANIFEST.json), [trace](Evidence/A0/TIMELINE.log), [warnings](Evidence/A0/WARNINGS.json) đã xuất lại từ raw của mọi run.

Build cuối **Build-20261107-112603-219-96b88ba5**: Generate0, Editor0, Game0; log đúng encoding có `Result: Succeeded`. [Source](Evidence/A0/Build-20261107-112603-219-96b88ba5/SOURCE.json), các command/result JSON và log.gz cạnh đó giữ lệnh thực/exit code. Full command dùng `Scripts/U00.ps1 -Task Build -ProjectPath D:/Data/AnimeMMORPG/Artifacts/U03/A0/Source/AnimeMMORPG.uproject -EngineRoot D:/Software/UE_5.8 -OutputRoot D:/Data/AnimeMMORPG/Artifacts/U03/A0/Runs`.

Automation cuối **MCPTests-20261107-112725**: **68 executed, 68 Success, 0 Failed**, gồm7 test A0 và61 test U00–U02 hồi quy mới chạy. [Từng test](Evidence/A0/MCPTests-20261107-112725/result.json), [MCP results](Evidence/A0/MCPTests-20261107-112725/mcp-results.json), [PID/command/binary hash](Evidence/A0/MCPTests-20261107-112725/process.json), schema TestRunner/LogsToolset và trigger cạnh đó. Log xác nhận queue68 hoàn tất. Bảy test A0 đều Success: AdmissionOrdering, DefinitionIdentity, ResolveBarrierAndLethal, ResourceAndCutoff, TimelineAndBuffer, LongUpdateResolverInterruptAndDeath, CutoffIntervalsAndConfirmedHits.

Editor DLL SHA256 `b9b30a3a819e9712e8cb13bf6fa20d5e2b1e7370e9dd2cc9c97ff4878f80903b`; Game exe SHA256 `f5611d73983bec1e8b55b2a83829080540ad6e9fbe399ce34aa7095d57daea02`. Manifest giữ ba source Git blobs, hash raw/publish và encoding nguồn. Hash module khớp process Automation cuối. Package N/A tại A0.

Giữ failed build `1d65b53`: helper Life/Flags va chạm unity build, đã sửa trước review đầu; không xóa log lỗi. Warning toolchain mới hơn preferred, deprecated API engine/U01 và chuyển double sang float vẫn giữ nguyên văn. Không bật AllToolsets. Binary trung gian bị thay thế trước đây không được lưu đầy đủ/hash đầy đủ; chỉ dùng binary/hash/process cuối làm bằng chứng bàn giao.

A0 chưa có runtime U03, input Windows/video, package/cook hoặc dedicated server/hai client mới. Pure model không có pawn/world/net owner/role thực, ghi N/A; model30/60/120Hz không phải FPS runtime. A1 vẫn cần collection geometry/world event toàn cục, payload và input/snapshot thực; B2 cần defense history/runtime. Kết quả A0 không tự khép các cổng đó.

**READY_FOR_REVIEW U03-A0.** Ba vấn đề reviewer nêu đã có sửa đổi và bằng chứng để review lại; chưa tự kết luận ACCEPTED. Không merge main hoặc bắt đầu A1. Không có test fail ở bản cuối; giới hạn runtime/collection nêu trên vẫn giữ để reviewer đánh giá.
