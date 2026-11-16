# U03-D — READY_FOR_REVIEW

Đã hoàn thiện trình bày/settings blockout và kiểm tích hợp U03.01–U03.09. **Chưa ACCEPTED, chưa merge main, chưa khép U03; chưa triển khai U04.** Reviewer AI đối chiếu kỹ thuật; người dùng chơi thử cảm giác/hình ảnh và cho phép khép là bước riêng.

Main nền `bc3a9955a8c0ecc1cb7f0d43dce13300c9664ac9`, nhánh `u03/d-integration`. Source runtime cuối **`9da1b43aa8ed49bd83226f76fe2b816db0d64f24`**. Các commit hồ sơ/harness sau source này không đổi `Source/` hoặc `Content/`; không chạy lại build/tests chỉ vì sửa báo cáo. [Manifest](../../Evidence/D/MANIFEST.json) giữ hash raw/published, binary, package index48 file, engine/toolchain, PID/world/owner/role và từng test. [Ma trận](../../D-TEST-MATRIX.md), [bao phủ U03](../../CLOSURE-D.md), [hợp đồng](../../D-CONTRACTS.md).

## Bản chơi

[Solo](../../Play-U03-D.cmd), [hai cửa sổ](../../Play-U03-D-Network.cmd), [Stop](../../Stop-U03-D.cmd), [checklist](../../Play-U03-D-CHECKLIST.md). Package đã xác minh tại `Artifacts/U03/D/Runs/Package-20261115-221157/Archive/Windows`; dedicated Editor và client dùng một clone `Artifacts/U03/D/Source` đúng source/binary.

Launcher giữ guard source/module/engine/package/port và PID + executable + source + **log session duy nhất**. Chỉ minimize Editor gốc sau clients ready; Stop đúng session và khôi phục placement. Settings launcher lưu riêng, ổn định dưới `Artifacts/U03/D/UserSettings/Solo` và `Network/ClientA`, `Network/ClientB`; reconnect giữ thư mục preferences của A, nhưng nhận encounter/life mới. Không đóng/restart/save Editor gốc. Play trong Editor gốc không mặc định là D.

## Thay đổi và ranh giới

Tái dùng UU01AnimInstance, U02 confirmed history, asset authoring U03 và encounter HUD. Giữ nguyên Attack1–3/Q/E, carry/grip, socket và skeleton đã nghiệm thu; thêm năm pose gốc cố định cho dodge/guard/break/hard CC/X, mười sequence/montage dưới `U03/Animation/D`. AnimBP thêm slot presentation. Asset test kiểm dependencies/root/no gameplay notify; clip và animation không dịch capsule hoặc quyết định hit.

Canvas trình bày windup/strike/recovery, hướng và sword box200×120×180cm đúng hình học hiện có; pose quái lấy server clock, không phát lại startup của snapshot muộn. Hit/block/parry/miss/break/Feint/Interrupt có nhãn/hình và tín hiệu riêng; parry giữ vòng tròn và biểu thức PCM hai nốt660→990Hz cũ. Tín hiệu mới là PCM tổng hợp blockout do project tạo, không mua/tải: hit440, block220, miss160, break110, X1320Hz, Feint chirp880 đi xuống, Interrupt330 đi lên. PCM24kHz mono16-bit/.24s; WAV bằng chứng là loopback48kHz stereo, không microphone. [Provenance/hash](../../Evidence/D/MANIFEST.json).

Mỗi event gắn subject/life/action/event serial và encounter/revision. Visual hết tại timestamp authority+1,2s; snapshot lặp không kéo dài. Audio chỉ cho event mới, thấy được, tuổi≤150ms; initial-only watermark làm history trước connection im lặng. Voice đang phát dừng khi life nguồn/đích hoặc encounter scope đổi. Dedicated server không tạo audio/UI. Overlay chẩn đoán có cờ riêng `-U03PresentationDebug`; fixture cuối kiểm với on-screen debug messages tắt.

Miss được quan sát từ **kết quả hoàn tất tự nhiên của authority timeline**, sau resolver; contact đã áp dụng gồm block/parry đều chặn miss. Cancel không thêm miss. Hook mới chỉ xuất dữ liệu, không sửa state/admission/damage/timing/motor. Các luật A0–C2, lethal cutoff, defense, dodge trajectory, authority, Retry và encounter riêng vẫn giữ nguyên. Không thêm shared monster zone, skill, balance, progression, prediction hoặc packaged Server.

HUD đọc HP/energy/posture/dodge charges/recharge/Q-E-X cooldown/CC và binding thật; không dựng tám kỹ năng. HP vừa trúng đọc confirmed history, kiểm life/revision và cửa sổ1,2s; dùng cùng projection/environment camera LOS của C2, không thay Tab target. Video ghi HP hit khi Tab tắt; camera/occlusion được kiểm bằng target fixture và helper chung. Kết quả/Retry vẫn đọc authority; giữ AwaitingResume/release gate, click Retry không attack/Resume. A/B là trạm encounter riêng, không phải quái chung.

Giữ UU01SettingsSubsystem, JSONv2 và SaveGame hiện có, không tăng schema hoặc lưu combat. Validation toàn bộ binding, conflict-closure v1/v2, file thiếu/hỏng/unsupported và no load-time rewrite có Native tests. Migration dùng slot UUID trong clone, không settings người dùng. Input thật kiểm rebind/save, giữ phím qua menu/focus/Resume/Retry; năm vòng Boot và Quit/reopen giữ preferences, không giữ HP/cooldown thành tiến trình.

## Cổng source cuối

|Cổng|Kết quả / run dưới `Artifacts/U03/D/Runs`|
|---|---|
|Generate / Editor / Game|PASS exit0; `Build-20261115-220654`|
|Full Automation MCP|**137 Success, 0 Failed**:131 định nghĩa nền chạy mới +6 D; `MCPTests-20261115-221026`; từng completion TestRunner/GetLogEntries được kiểm|
|Windows package|BUILD SUCCESSFUL exit0; `Package-20261115-221157`|
|Blueprint/references|16 Blueprint compile, không missing game reference; `Assets-20261115-221349`; audit không save asset|
|Ba map smoke|PASS Boot/CharacterCombatLab/NetworkLab; `Smoke-20261115-221300`|
|Combat input/video/audio|24 PASS; `FinalCombat-20261115-221500`; parry một cụm660 rồi một cụm990, không lặp history|
|Route/Return|11 PASS; `FinalRoute-20261115-221600`|
|Tab/visibility/rebind|15 PASS; `FinalTarget-20261116-120000`|
|Fixture presentation|15 PASS; `FinalRegression-20261116-120100`; Feint/Interrupt, block/parry/break/CC/X, held inputs, rebind; đủ dải âm, debug messages tắt|
|Boot / settings reopen|5 vòng; `FinalLifecycle-20261115-222100`, `FinalReopen-20261116-115900`; thêm kiểm ngay launcher ổn định ở `LauncherSave-20261116-121900`/`LauncherReopen-20261116-122000`, restore defaults bằng UI sau kiểm|
|Dedicated + hai client/reconnect|26 PASS +41 đối chiếu độc lập; `LauncherNetwork-20261116-122200`; HP/resource/action/result/revision, owner/proxy, Retry A không đổi B, claims cũ/lặp/unowned, logout/reconnect/new identity|
|Feedback audit|4 process; dedicated0 HUD event, client không lặp identity; audio freshness đúng; Native tests thêm late/future/initial-history/new-life scope. Không tuyên bố đã tiêm packet mạng tùy ý|
|Launcher|3 guard mismatch PASS; mở trùng Solo và port bận đều từ chối; positive Solo/Network/Stop + placement restore; preferences A/B tách biệt, reconnect dùng lại preferences A|

Native timing/model/world được kiểm tại bước30/60/120 và update dài, kể cả miss với hit/block/parry/cancel. Bộ hồi quy giữ dodge tường/StepUp/hai pawn, lethal cutoff, combat lock/focus. **Các bước model/world này không phải FPS render thực đo.**

## Profile review thực đo

Mẫu frame/tick lấy chênh lệch timestamp monotonic mỗi game/render frame, trong đoạn authority có combat và đủ hai cặp subject; giữ toàn bộ raw frames, world dt và raw game/render/GPU stats riêng. Không suy GPU cost từ cap hoặc FPS từ bước model. [Profile](../../Evidence/D/Runs/Runs/LauncherNetwork-20261116-122200/profile.json.gz).

|Process / PID|Cadence trung bình (Hz)|P99 frame/tick ms|Max ms trong mẫu|
|---|---:|---:|---:|
|Server / 18264|29.94|39.92|46.74|
|Client A / 5488|59.88|21.69|115.34|
|ClientB / 10932|60.00|20.25|21.90|
|Client A reconnect / 6588|59.61|21.73|117.40|

Giữ đúng C2: client900×540, cap60/server30, foreground idle0, screen percentage50, Lumen atlas2048, RT pool128MiB, streaming pool256MiB, Lumen diffuse/reflections0, virtual shadows0, shadow quality2, DX12/SM6. Runtime smoothing mode2/location0,1s, net update100/min2 giữ nguyên. Source không đổi cap/smoothing/input để che khựng. Có spike frame như bảng; đây là **profile review giảm chất lượng trên cùng máy, không nghiệm thu graphics/performance U04 hoặc cam kết60FPS/1080p**. Cảm giác vẫn chờ người dùng chơi thử.

## Dấu vết, lỗi giữ lại và giới hạn

C2 131 tests/package/network/video ở manifest C2 là baseline kế thừa, không tính là lượt D mới. Checkpoint D ban đầu `5cc8574` và manifest cũ giữ tại `Evidence/D/Checkpoints/INITIAL-MANIFEST.json`. Report gốc `REPORT-D.md` chỉ còn pointer tới tài liệu này, tránh hai trạng thái.

Giữ tất cả pre-final/failed/invalid runs: build đầu lỗi auto pointer/TObjectPtr (đã sửa `.Get()`); lượt build nhầm source cũ khi fast-forward bị untracked author script chặn; solo đầu thiếu history actor nên không audio (đã sửa khởi tạo); lần bấm parry ngoài cửa sổ ghi rõ guardStart/end và deadline, không đổi luật; fixture E đã Interrupt nhưng assertion dùng trace chưa xuất (harness đổi sang confirmed result); lỗi seal đường dẫn tương đối chỉ ở harness. Không đếm các lượt này vào cổng cuối. Sealer giữ raw hash, published hash, decode/round-trip và redaction; [warnings](../../Evidence/D/WARNINGS.json) giữ compiler14.51 mới hơn preferred14.50, engine deprecations, NoMesh của native fixtures, host SDK warnings và loopback warnings ở lượt cũ. Fixture loopback cuối không có discontinuity; bản thu không là nghiệm thu audio sản phẩm/latency.

Header/reflection đã qua full UBT/cold clone. Không dùng warning Live Coding05:03:56UTC của C2 làm kết quả D; yêu cầu Live Coding D trước đó không có completion mới. Source/engine/toolchain và PID được ghi theo từng run, không dùng Editor world làm bằng chứng pawn PIE. Không enable AllToolsets.

Config riêng vẫn SHA256 `412b42b66583f9b6e4ecdc63cd2423457bf0b1a3d192f5b0f18375ee801f8161`; Maintenance không chạm/stage. `.uproject` xuất hiện dirty ngoài phần D và được bảo toàn, không commit. Editor gốc đổi PID ngoài các lượt task trong khoảng gián đoạn; mỗi session chỉ minimize/restore HWND/PID hợp lệ của lượt đó. Không cộng các khoảng gián đoạn15→16/11 thành thời gian làm việc.

Điểm dừng: **READY_FOR_REVIEW U03-D**. Người dùng chỉ cần chơi theo checklist để đánh giá readability, âm/hình, grip/pose, HUD/occlusion và cảm giác Retry/focus/hai cửa sổ. AI chịu trách nhiệm kiểm kỹ thuật/hash/authority/timing; chưa tự ACCEPTED, merge, khép U03 hoặc làm U04. Art sản phẩm tiếp tục deferred.
