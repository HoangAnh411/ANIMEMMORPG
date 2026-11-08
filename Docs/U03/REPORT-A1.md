# U03-A1 — ACCEPTED về kỹ thuật

Triển khai riêng combo, dispatcher và resource runtime từ main đã nghiệm thu `5f8700e69b0f381a2f6b0d158667ac9283aa98ab`, nhánh `u03/a1-combo`. Source native/content kiểm chứng **0957867e11193081fb26b732864ccc006ffc975a**; commit bàn giao sau đó chỉ bổ sung scripts/hồ sơ/bằng chứng. **ACCEPTED về kỹ thuật tại `6ae268e0a19c385b9a2b573acb3e6be3080aac72`**, không phát hiện lỗi chặn A1. Người dùng đã giao khép tài liệu và fast-forward/push main rồi dừng; chưa giao B1. A0 đã khép là nền kế thừa, không thay thế bằng chứng runtime dưới đây. [Kết luận nghiệm thu](ACCEPTANCE-A1.md).

## Thay đổi

- A0 timeline vào combat component và world resolver; RPC enqueue, global cooperative barrier đưa mọi model tới cùng timestamp, giải hết nhóm collision/lifecycle trước completion/successor/admission. Candidate giữ immutable definition/raw. Death/Interrupt/lost-ground và stale life không phát hit muộn.
- Ba đòn raw60/70/90, duration0,40/0,45/0,60, buffer/grace0,15. Hurtbox mới sau reset có `AvailableFrom`, không được hồi tố vào active trước khi life đó tồn tại. Giữ geometry/obstruction/dedup và damage/shield/death U02.
- Dispatcher dùng physical edge/release gate, chung namespace binding15 controls, migration v1 sang payloadv2. Console/menu/focus consume cạnh và xóa pending; action đã nhận tiếp tục. Chỉ Attack hoạt động; các command tương lai trả Unsupported. Energy/CD có model/snapshot/fixture, chưa có skill gameplay Q/E.
- Hai clip mới tự author từ rig/grip/carry U01 và montage riêng, ABP_U03 chọn ba montage theo definition; root motion ignore. HUD phím thật/action/energy/pending/admission và feedback damage hiện có. Không thay clip đòn1 hoặc art U02. Public DefaultGame chỉ thêm cook directory U03; private DefaultEngine không sửa.

Diff đầy đủ: `git diff 5f8700e..0957867 -- Source Content Config`. Các test U02 runtime từng giả định RPC thực thi ngay được chuyển sang drain barrier tại receive timestamp trong fixture. Không bỏ coverage identity/collision; model U02 lịch sử giữ luật cũ. [Hợp đồng](A1-CONTRACTS.md), [ma trận](A1-TEST-MATRIX.md).

## Bằng chứng mới

Tất cả build/test/package trong clone `Artifacts/U03/A1/Source` từ commit đã ghi; không dùng Editor gốc làm bằng chứng binary mới. UE5.8.4 CL58902052; command, toolchain/compiler output, exit code, PID/project/world/role/owner nằm trong raw/published log và process JSON.

| Loại | Run cuối | Kết quả |
|---|---|---|
| Generate/Editor/Game cold build | Build-20261107-194009-997-544b1dcf | Cả ba exit0; Editor/Game Result: Succeeded |
| MCP TestRunner, đọc schema tại clone và log mới | MCPTests-20261107-194121 | 78 tên riêng, 78 Success, 0 fail; queue78 hoàn tất |
| Windows package | Package-20261107-194150-892-b3ba9ae7 | UAT exit0; archive Windows,48 file hash trong PACKAGE.csv |
| Package smoke | Smoke-20261107-1944 | Boot/CharacterCombatLab/NetworkLab đều load, exit0:3/3 |
| Package physical input/video | InputCapture-20261107-1959 | 46/46 checks, completed=true |
| Ba clip/startup-turn/camera | TurnCapture-20261107-2005 | 16/16 checks, completed=true |
| Dedicated Editor + hai client, input thật | NetworkCapture-20261107-2026 | 19/19 checks, completed=true |
| Disconnect/reconnect | Session-20261107-200144/reconnect-result.json | 2/2: identity mới, HP1000, action/pending0, không replay |

Tên folder capture là run label; thời gian thực lấy từ log UTC và metadata, không suy từ nhãn folder.

Tám test A1 mới (cùng78 test trong run cuối): `WorldComboAndNineHitDeath`, `RuntimeBufferExpiryReplacementAndControl`, `ResourceSnapshotAndUnsupportedDispatcher`, `GeometryIncomingInterruptAndDeathDuringSuccessor`, `WorldTimestampGroupBeforeSuccessor`, `LostGroundLandingResetAndStaleLife`, `AuthoredThreeClipsAndDefinitionClock`, `BindingFoundationAndV1Migration`. Tên đầy đủ và từng PASS có trong result.json và Editor.log. Các test model A0, U00/U01/U02 cũng chạy lại trên binary mới; không dùng lại kết quả70/70 cũ.

Game-world fixture kiểm update dài qua toàn active/nhiều boundary, successor Attack2 tại0,40 rồi hit địch thật tại0,45 Interrupt/death trước active0,58, nhóm cùng timestamp và đảo collection, deadline/cutoff, buffer/expiry/replacement, lost-ground/landing/reset/stale life, payload definition. Fixture resource tiêu Q/E kiểm snapshot nhưng không tạo skill. Hồi quy bao gồm collision/tường/từng hurtbox/dedup/shield/rounding/identity và motor/settings/gate.

Package input dùng SendInput có guard PID/exe/hash/project/source/world/local owner/foreground. Chín action cho ba chuỗi raw660, dummy600 chết đúng hit9, actual HP damage600; không gọi raw660 là HP thực mất. Tám lần nối kế tiếp đúng duration, held LMB không loop, pending thật bị menu/focus xóa, Resume và giữ W hồi lại500 trên runway; tường chặn damage. Clip bổ sung kiểm cả ba startup-turn, body khóa active/recovery, camera tự do và montage đúng đòn. Video30 FPS theo wall clock, có metadata các sample/gap; không dùng tốc độ video làm clock gameplay, không tuyên bố120FPS thực.

Network có server authority và hai client độc lập, mỗi bên physical combo1/2/3. So sánh toàn bộ result serial/source/life/action/target/definition/raw/damage/HP giữa ba process; no friendly fire, các playerHP1000. Đây là fixture kỹ thuật dùng dummy gần nhau, mỗi đòn có thể trúng hai dummy; chưa phải encounter/trạm quái C2. Duplicate/stale/NaN và RPC trên pawn không sở hữu không thêm action/damage. Reconnect thay pawn identity, không nhận action/pending cũ. Client actual cvars60FPS cap,900×540, internal50%, Lumen atlas2048, RT minimum128MiB, texture256MiB, diffuse/reflections0, virtual shadow0, shadow2, idle0; server cap30/idle0. Frames.jsonl giữ số đo FPS thực; cap không được coi là benchmark hay chứng minh60FPS mọi thời điểm.

## Failed và invalid runs giữ nguyên

- MCPTests-192315: crash test fixture U02 đọc index0 trước queued command được drain; sửa fixture admission barrier, không che crash.
- MCPTests-193145:76/78, hai lỗi reset life/revalidation do hồi tố hurtbox mới vào active cũ. Sửa runtime `AvailableFrom`; full78/78 ở193546 rồi full78/78 source cuối194121. Build/package cũ vẫn giữ, đã superseded.
- InputCapture-1947: W bị tường fixture cản; chuyển phép đo W sang runway. 1949: cạnh vật lý đến sau action-end tạo grace successor, không đạt mục tiêu đo queued timing. 1952/1955: minimize xảy ra sau successor vì harness chậm; giữ precondition/timestamp. TurnCapture-2003: sample camera trước khi OS xử lý mouse; thêm chờ sample và bỏ encode PNG trong cửa sổ ngắn. Không đổi native source cho các sửa harness này.
- NetworkCapture-2011/2014 dùng nhầm local clock;2016/2019/2022 chịu trễ snapshot/capture nên không chứng minh đủ chuỗi chính xác. Harness cuối dùng actionSeconds authority và recording thread riêng, physical edges thay slot; các JSON/video/raw log không bị xóa. Lệnh reconnect kiểm đầu tiên giả định fresh connect bắt buộc Resume đã bị loại: luật đó thuộc focus/Retry, không áp cho fresh connect. Kết quả đúng chỉ kiểm identity/state mới, không tự đổi gameplay.
- `editor-after-stop.json` chụp quá sớm còn Show2. Đã restore lại đúng HWND/PID và đọc sau500ms: `editor-restored-verified.json` có cả hai cửa sổ PID13168 Show1 và normal rect khớp baseline. Giữ snapshot sớm để không che lịch sử.

## Hash, logs và khôi phục môi trường

[MANIFEST](Evidence/A1/MANIFEST.json) ghi SHA256 binary Editor/Game, engine executable, source blobs, từng raw/published artifact và encoding. [PACKAGE.csv](Evidence/A1/PACKAGE.csv) ghi48 package files; launcher kiểm từng file trước chạy. Published logs được decode BOM/UTF16LE/UTF8 nghiêm ngặt, redact credential rồi gzip UTF8; không dùng errors=replace. [Encoding verification](Evidence/A1/ENCODING-VERIFICATION.json), [warnings](Evidence/A1/WARNINGS.json), [test traces](Evidence/A1/TEST-TRACES.json). Raw giữ dưới Artifacts/U03/A1, không xóa failed runs. Evidence A0 không thay đổi.

Editor DLL SHA256 `cb9da76ba00b08b75bf5d1480a03209235a3d3d62b7ef6720b620f6be50cfa08`; Game exe `98459264f4c43b1d48ba3a240ff1543d5562486bc0048aa765edebfffffd7900`. Package CSV SHA256 `1de25faab9656a3751fd0d67cfbc35a65681d13fb25590b896511ff84546ca97`. Hash đầy đủ và nguồn binary trong manifest, không chỉ dựa vào tên file.

Original Editor PID13168 giữ mở, không restart/save; không xác nhận đã nạp binary A1. Launcher ghi placement mọi HWND trước minimize và xác minh minimized sau clients ready. Stop chỉ PID/exe/project/userDir/source/module hash của session, gồm client reconnect, sau đó restore placement. Private config hash so baseline, không stage/in giá trị token. Main giữ5f8700e; chỉ push nhánh A1.

Warnings không bị lọc bỏ: phần lớn là `GetSocketInfoByName: No SkeletalMesh` của actor fixture không gán mesh (có cả bản log và MCP log lặp), không phải package thiếu mesh. Còn compiler14.51 không thuộc preferred toolchain, engine header deprecation C4996, audio48000/44100 chuyển sample rate và unowned RPC warning cố ý từ negative probe. Danh sách đầy đủ gồm cả failed runs trong WARNINGS.json; không tuyên bố build sạch warning.

## Chơi thử và giới hạn

Chạy [Play-U03-A1.cmd](../../Play-U03-A1.cmd), [Network](../../Play-U03-A1-Network.cmd), [Stop](../../Stop-U03-A1.cmd); [checklist](../../Play-U03-A1-CHECKLIST.md). Package/clone là artifact local ở manifest; launcher từ chối nếu source/hash không khớp.

Chưa triển khai né/phòng thủ/CC/X/Q/E/AI/Tab/Retry gameplay; settings hoàn thiện D, Server đóng gói ngoài phạm vi. Animation là blockout dùng tạm để kiểm nhịp/hướng chém/đọc đòn: đòn1 giữ clip U02, đòn2–3 có clip riêng. Animation đẹp hơn sau này phải giữ timing gameplay; montage không quyết định hit/damage. ACCEPTED kỹ thuật A1 không phải nghiệm thu hình ảnh sản phẩm. Không tuyên bố benchmark U04 hoặc prediction U05.

## Khép hồ sơ sau review

Reviewer chỉ đọc source và đối chiếu bằng chứng đã bàn giao:165/165 artifact,147 bản text decode/redact và34 source blob khớp; không vừa chạy lại build/tests. Trạng thái READY_FOR_REVIEW trước đó và các failed/invalid runs giữ trong Git/bằng chứng gốc. Lượt khép chỉ cập nhật tài liệu, không sửa source/asset/config và không chạy lại build/tests. Không gán SHA khép hồ sơ cho binary nguồn0957867e. Editor hiện tại được giữ mở; xác nhận PID13168 phía trên chỉ thuộc lịch sử lượt triển khai, không kế thừa cho process mới. Dừng sau khép/merge A1; chưa B1.
