# U03-C1 — ACCEPTED (technical)

Nhánh `u03/c1-skills` từ main `f826371b9409c39453e5bd2ed8f8414749f1d34b`. Native/content source đã kiểm chứng: **`dbe10dab1cd6a9b14c28c732aba66f21d525ac69`**. Commit bàn giao sau source này chỉ thêm hồ sơ, bằng chứng và sửa harness/launcher; không thay Source/Content/Config đã build. Các câu chưa giao C1 trong hồ sơ trước là lịch sử.

**Người dùng chưa chơi thử B2/C1. Presentation vẫn blockout; chưa nghiệm thu cảm giác, readability hoặc hình ảnh sản phẩm.** Người dùng đã xác nhận ACCEPTED về kỹ thuật tại bàn giao `db592ff` và cho phép khép tài liệu, sửa lỗi dấu checklist, commit/push và fast-forward/push main; xem [ACCEPTANCE-C1](ACCEPTANCE-C1.md). Không khép U03 tổng thể hoặc triển khai C2. Các kết quả dưới đây giữ nguyên, không chạy lại build/tests và không tác động Editor trong lượt khép này.

## Runtime

Q Hư Trảm và E Phá Thế đi qua dispatcher/rebind/release gate thật. Q100 raw, .30/.40/.80s,20 năng lượng/CD4s; E80 raw,.25/.35/.75s,25/CD6s. Dùng hộp kiếm từ chân và dedup target/action hiện có. Admission kiểm quyền, năng lượng/CD trước thay action; chỉ nối recovery đánh thường, không tự nhả guard hoặc buffer skill. Chấp nhận reset combo/pending; hủy không hoàn chi phí. Regen100 tối đa,10/s sau1s kể từ lần tiêu, tích phân khoảng đủ điều kiện.

Authority phân loại cạnh Q mới trong startup Q thành Feint trước cast mới/CD. Feint cắt phần chưa phát, giữ chi phí/CD, khóa .20s và cách thành công trước1s, gắn với life. Combat/jump/sprint có khóa riêng; đi bộ vẫn chịu slow/CC/control lock. Né/guard chỉ thay startup khi replacement hợp lệ. Hết recovery tiếp tục WASD giữ; không dùng gate menu làm combat lock hoặc buffer lại jump bị khóa.

E mang Interrupt theo definition/version đã action chụp; candidate không đọc lại luật defense/Interrupt từ bảng mới. Giữ geometry → identity/dedup → defense → damage/shield → death → hiệu ứng còn hợp lệ → publish. E ngắt startup đánh thường/Q/E của target còn sống; block/parry chặn, shield hấp thụ hết không miễn, không tự stun/khóa thêm/refund. Q không Interrupt. Giữ full timestamp group/barrier, successor và cutoff; không rewind confirmed hit.

Snapshot thêm deadline/identity Feint và target action/time Interrupt; result history có life/definition version/outcome. History chỉ trình bày, không ghi ngược life mới. Một runtime module và một resolver damage; không GAS/plugin/framework/prediction/bù trễ/packaged Server.

Q/E có clip/montage blockout riêng, named phases, fixed root, không gameplay notify; seek theo authority và bỏ root motion. HUD đọc binding thật, năng lượng/CD, tên action và nhãn pha/Feint/Interrupt ngoài màu. [Provenance và payload hashes](C1-ASSET-PROVENANCE.md). Fixture B2 thêm target startup/guard/parry/shield/incoming E có nhãn, dùng action/collision/resolver thật, không AI/encounter. Q/E/Feint trong video là bàn phím thật, không fixture RPC thay thao tác.

## Cổng cuối

UE5.8.4 CL58902052, MSVC14.51.36260, SDK10.0.26100.0 theo log thực. Source đã commit trong `Artifacts/U03/C1/Source`; không lấy Editor gốc làm bằng chứng binary.

|Cổng|Run|Kết quả|
|---|---|---|
|Generate/Editor/Game|Build-20261113-181045|Exit0; `Result: Succeeded`|
|Cold MCP TestRunner + GetLogEntries|MCPTests-20261113-181220|117 Success,0 Failed; queue117 complete|
|Windows package|Package-20261113-181403|Exit0; `BUILD SUCCESSFUL`|
|Smoke Boot/CharacterCombatLab/NetworkLab|Smoke-20261113-181558|3/3|
|Input/video Windows thật|InputCapture-20261113-181656|24/24; completed=true|
|Dedicated Editor + hai client|NetworkCapture-20261113-182407|35 live +10 saved-sample comparisons độc lập|
|Né hai client hồi quy|DodgeNetworkRegression-20261113-182846|22/22|
|Reconnect, E cooldown trước disconnect|Session-20261113-181942|2/2; pawn/resource/CD/action/feedback mới|
|Sai package/module/source hash|Audit/LAUNCH-GUARDS.json|3/3 từ chối; manifest/index phục hồi nguyên byte|

117 Automation gồm107 test kế thừa U00–B2 chạy lại và10 test C1 mới; dispatcher test A1 được cập nhật từ Unsupported sang cooldown thật. Có before/exact/after các biên active/recovery, Feint, cooldown/regen; replacement/combo/pending; Interrupt/shield/block/parry/lethal, nhiều target/dedup, collection đảo và incoming E trong successor với update dài/ngắn. Wall/StepUp/two-pawn retained-trajectory regressions chạy trên binary này, không tái dùng PASS B1 cũ. [Ma trận đúng tầng](C1-TEST-MATRIX.md), [từng kết quả/traces](Evidence/C1/TEST-TRACES.json).

Input24 kiểm Q/E, Q held không lặp, Feint Q/Q, walk/no sprint/jump trong deadline, nối recovery cả ba đòn, né/guard hủy startup, nhả guard, outgoing/incoming Interrupt, menu/focus/Resume và rebind Q/E→T/Y rồi khôi phục. Actual Game-world samples có XY velocity0 trong E; W giữ bắt đầu đi lại **0.0156826s** sau recovery. Active Q/E có montage đang trình bày trong instance thực. Đây là kỹ thuật, không nghiệm thu cảm giác.

Network so pawn/life/action/definition, resource tại timestamp authority từng snapshot, CD/Feint, damage/defense/Interrupt giữa ba process. E block24/parry0 không Interrupt. Có shared-dispatcher duplicate/stale/malformed/unowned probes, reset/life, client60/server30 và né hai peer. E thật trước disconnect; reconnect nhận identity mới, energy100, CD0, không action/pending/feedback cũ. Input hai client là **tuần tự**; simultaneous-hit do Game-world fixtures, không gọi là hai client bấm đồng thời.

## Bằng chứng và chơi thử

[Manifest source/binary/hash/gates](Evidence/C1/MANIFEST.json), [package SHA-256](Evidence/C1/PACKAGE.csv), [asset payload SHA-256](Evidence/C1/ASSETS.csv), [warnings/errors](Evidence/C1/WARNINGS.json), [encoding verification](Evidence/C1/ENCODING-VERIFICATION.json).

- [Input video](Evidence/C1/Runs/Runs/InputCapture-20261113-181656/Input-C1.mp4), [Feint](Evidence/C1/Runs/Runs/InputCapture-20261113-181656/Feint.png), [E active](Evidence/C1/Runs/Runs/InputCapture-20261113-181656/E-active.png), [binding T/Y](Evidence/C1/Runs/Runs/InputCapture-20261113-181656/Rebound-T-Y.png).
- [Network video](Evidence/C1/Runs/Runs/NetworkCapture-20261113-182407/Network-C1.mp4), [10 so sánh độc lập](Evidence/C1/Runs/Runs/NetworkCapture-20261113-182407/network-independent.json.gz), [dodge regression video](Evidence/C1/Runs/Runs/DodgeNetworkRegression-20261113-182846/Network-C1.mp4).
- [WASD sau E](Evidence/C1/Runs/Runs/InputCapture-20261113-181656/movement-independent.json.gz), [animation instance thực](Evidence/C1/Runs/Runs/InputCapture-20261113-181656/animation-independent.json.gz), [reconnect](Evidence/C1/Runs/Session-20261113-181942/reconnect-result.json.gz).

Raw runs giữ tại `Artifacts/U03/C1`; manifest ánh xạ bản công bố sang raw path/hash. Text decode nghiêm ngặt, redaction token, gzip và xác minh round-trip; không xóa failures. Video30FPS encoding theo wall clock, có metadata skipped frames; không chứng minh render30/60/120FPS. Model timesteps không phải FPS.

Chạy [Play-U03-C1.cmd](../../Play-U03-C1.cmd) hoặc [Play-U03-C1-Network.cmd](../../Play-U03-C1-Network.cmd), dừng bằng [Stop-U03-C1.cmd](../../Stop-U03-C1.cmd); [checklist](../../Play-U03-C1-CHECKLIST.md). Launcher kiểm hash/source/profile và đúng session/placement. Mọi process thử đã dừng; Editor gốc vẫn mở, không tự save/restart. `Config/DefaultEngine.ini` riêng nguyên byte; thay đổi cục bộ có sẵn không vào commit. Clone chỉ còn generated FileOpenOrder logs không tracked.

**Nút Play trong Editor gốc chưa được bảo đảm chạy C1.** Có thay đổi UPROPERTY/UFUNCTION/header: Live Coding không thay full build và restart cho reflection/layout. Audit giữ các lần gọi/output thật; lần cuối ghi `Live coding succeeded`, hai lần trước cảnh báo data-type changes. Full build/cold process riêng và package là bằng chứng cuối.

## Failed/invalid/superseded và giới hạn

Giữ các lượt dưới trong manifest; FAIL/completed=false không đổi thành PASS bằng chẩn đoán.

- Author đầu log thiếu asset trước khi tạo, sau đó ghi SUCCESS. Chẩn đoán INVALID ban đầu quá sớm được đính chính; commandlet tiếp theo từ chối overwrite đúng thiết kế.
- Build guard từ chối clone INI sau cook; chỉ khôi phục token/normalization hợp lệ trong clone. Build175229 đổi checkout lúc Game build kết thúc nên không dùng làm cổng immutable-source. Build/package nguồn trước giữ là lịch sử.
- Input180329 kiểm sau Feint lock;180523 đọc nhầm stream mạng trong solo;180754 đòi speed400 quá sớm sau recovery;180958 đọc JSON đang append;181159 kiểm guard trước authority ack. Sửa harness theo deadline/complete lines/ack, không đổi motor, cap hoặc luật để PASS. Lượt cuối24/24 dùng source đúng HUD.
- Network182148 dùng dải energy cố định khi regen đã bắt đầu; thay bằng eligible integral tại timestamp snapshot. Dodge182707 đổi nhầm hằng OpenCV khi rename stage, capture worker hỏng; giữ video/log invalid rồi rerun22/22.
- Nhiều warning socket/`No SkeletalMesh` từ native fixture không mesh và deprecation/toolchain/engine được giữ trong WARNINGS/raw logs. Không bật AllToolsets hoặc che warning bằng config.

Animation/fixture/tín hiệu text vẫn blockout; chưa nghiệm thu art, âm sản phẩm hoặc feel. Feint1s test riêng ở state gate; đường cast thường còn bị Q CD4s ràng buộc. Network là localhost/profile đã ghi, không chứng minh mạng xấu U05 hoặc performance U04. C2 AI/encounter/Tab/Retry, tám kỹ năng nghề và packaged Server chưa triển khai. Trạng thái READY_FOR_REVIEW của bàn giao/bằng chứng là lịch sử trước nghiệm thu kỹ thuật; sau khép tài liệu và xác minh remote thì dừng, chưa C2.
