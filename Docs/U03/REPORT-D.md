# U03-D-R1 — ACCEPTED về kỹ thuật

## Trạng thái tổng hợp U03 hiện hành

**U03 hoàn tất kỹ thuật; người dùng xác nhận chơi thử blockout tích hợp D ngày 2026-11-16**, đã ghi tại `3439fed`. U03.01–U03.09 hoàn thành theo nghiệm thu từng đợt và [ma trận CLOSURE-D](../../CLOSURE-D.md); [ROADMAP](../ROADMAP.md) đã đồng bộ. Reviewer AI đối chiếu source/hash/log, còn người dùng đánh giá cảm giác và hình ảnh blockout qua chơi thử.

Mốc không đổi: nghiệm thu D-R1 `a7737f9`, source/binary kiểm chứng `0b25523`, khép kỹ thuật D `89358c5`, xác nhận chơi thử `3439fed`. Commit tài liệu không được gán cho binary. Xác nhận D tích hợp không suy ngược rằng người dùng đã chơi các package B2/C1 cũ. Art/animation sản phẩm, hiệu năng U04, mạng xấu U05 và Server đóng gói chưa được nghiệm thu.

Hồ sơ U03 **ACCEPTED** theo reviewer tại `b2199687dba33f5348a723506169dd1cfc8628a6`, không có lỗi chặn. Ngày 2026-11-17, người dùng giao khép hồ sơ, fast-forward/push main và tiếp tục U04-A từ main mới đã xác minh. Bước khép chỉ sửa tài liệu, không chạy lại build/tests/game hoặc tác động Editor; runtime/config/launcher/manifest/bằng chứng và failed runs giữ nguyên. Commit hồ sơ không phải nguồn binary.

## Lịch sử hồ sơ đã review tại 3439fed

Các đoạn dưới giữ nội dung đã review tại `3439fed`, gồm trạng thái trước khi đồng bộ tổng hợp U03. Chúng không thay thế trạng thái hiện hành ở trên; nguồn binary và bằng chứng vẫn giữ nguyên.

**ACCEPTED về kỹ thuật D-R1 tại `a7737f9a99bfe8a8637bcf86d09c4f190add7e16`**, source kiểm chứng `0b255233df021f2cc148313e638d918d41a4a11e`, mốc khép kỹ thuật `89358c58704b194e8f00f5f504e7eeb150acafcc`. [Acceptance](ACCEPTANCE-D-R1.md). Reviewer AI đối chiếu source/hash/log; người dùng đánh giá cảm giác và hình ảnh blockout qua chơi thử. Trạng thái READY_FOR_REVIEW/chưa ACCEPTED/không merge trong phần bàn giao bên dưới là lịch sử, không thay thế các xác nhận hiện hành.

**2026-11-16: người dùng đã chơi thử D-R1 và xác nhận ổn** trên bản launcher Solo/Network ghim source0b25523, package `Artifacts/U03/D/Runs/Package-20261116-140739/Archive/Windows`. Xác nhận bao phủ đọc đòn/tư thế, phân biệt phản hồi và âm, che khuất nhãn/HP/telegraph, HUD/phím/cooldown, Retry/focus/Resume và hai cửa sổ không có khựng/lỗi trình bày rõ rệt cản trở chơi thử. Không có mục hoãn hoặc lỗi chặn D được báo. D hoàn tất cổng kỹ thuật và chơi thử blockout; chưa nghiệm thu art/animation sản phẩm hoặc hiệu năng U04.

Nhánh tài liệu xác nhận cuối từ main89358c5 **chờ review hồ sơ, chưa merge**. Lượt này chỉ sửa acceptance/report/checklist, không đổi runtime/config/launcher/bằng chứng, không chạy lại build/tests/package hoặc tác động Editor. Chưa khép toàn U03 hoặc triển khai U04; ủy quyền fast-forward trước đây chỉ thuộc lần khép kỹ thuật89358c5.

## Hồ sơ bàn giao kỹ thuật lịch sử

Phần dưới giữ kết quả và điểm dừng tại thời điểm bàn giao D-R1; trạng thái hiện hành và xác nhận chơi thử nằm ở đầu báo cáo.

Sửa lượt D bị **NOT ACCEPTED tại f6d0f68** vì nhãn/khung/âm dùng phép chiếu camera mà chưa kiểm che khuất. Source runtime cuối **`0b255233df021f2cc148313e638d918d41a4a11e`**, nhánh `u03/d-integration`; main nền vẫn `bc3a9955a8c0ecc1cb7f0d43dce13300c9664ac9`. Chưa ACCEPTED, chưa merge, chưa khép U03, chưa U04. Reviewer AI đối chiếu kỹ thuật; người dùng chơi thử cảm giác/hình ảnh và cho phép khép là cổng riêng.

## Sửa lỗi

Nhãn phase/guard/CC/dodge và phản hồi/audio tái dùng đúng projection/LOS C2: bỏ qua combat bodies, trace môi trường channel 2 từ camera của LocalPlayer tới information point và anchor nhãn. Đối thủ bị che hoặc ngoài màn hình không hiện nhãn/phản hồi, không tạo âm; voice đang phát dừng khi mất visibility hoặc đổi life/scope.

Sword box và mũi tên chuyển khỏi Canvas sang primitive world trong module hiện có: normal world PDI, `SDPG_World`, depth bias 0, không debug PDI. GPU depth-test từng pixel nên phần cạnh bị tường che bị cắt ngay cả khi anchor quái vẫn thấy. Geometry giữ nguyên 200×120×180 cm và yaw từ snapshot; component không collision/nav, không dịch capsule hoặc quyết định hit. Dedicated server không tạo component này, audio hay UI.

Capture mới còn phát hiện history có thể tới trước ước lượng clock server của client: tiêu thụ serial trước timestamp làm mất âm fresh. R1 giữ event chưa tiêu thụ tới khi chính clock đó đạt timestamp; không đổi clock, timestamp, cửa sổ 1,2 giây hoặc ngưỡng âm 150 ms. Event đủ điều kiện nhưng bị che vẫn được tiêu thụ im lặng; hiện lại không phát lại âm. Snapshot trễ chỉ còn lifetime gốc. Giữ source/target/life/action/serial/encounter revision và reconnect baseline.

Không đổi model/timing/damage/admission/defense/dodge/motor/authority/Retry, clip/carry/grip, schema settings hoặc nội dung U04. Fixture R1 chỉ bật bằng `-U03R1VisibilityProbe`, dùng camera/tường riêng sau trạm và input/combat authority thật; launcher bình thường không bật fixture.

## Cổng trên source cuối

| Cổng | Kết quả mới R1 |
|---|---|
| Editor/Game và Windows package | PASS; package index 48 file |
| Full Automation U00–U03 | **140 Success, 0 Failed**: 131 nền + 6 D + 3 R1; từng test trong manifest/log MCP |
| Timing/model/world | Nằm trong full suite: bước 30/60/120 và update dài; không gọi đó là FPS render |
| Blueprint/reference và smoke | 16 Blueprint compile, không thiếu dependency; Boot/CombatLab/NetworkLab 3/3 |
| Hai client: tường/reveal/expiry/partial telegraph | 20 kiểm tra input/video/loopback, debug overlay và stat tắt; audit độc lập 17 kiểm |
| Package Solo | Combat 24; Tab/LOS/rebind 15; fixture defense/CC/X/Feint/Interrupt/held-input 15; loopback parry 660→990 và tín hiệu tổng hợp |
| Dedicated Editor + hai client/reconnect | 26 kiểm; 41 so sánh độc lập HP/action/resource/AI/result/revision; Retry A không đổi B |
| Launcher/Stop | Guard hash package/module/source 3/3; runtime Solo/Network và scoped Stop/placement được ghi riêng |

[0b25523: ảnh phần telegraph bị che](../../Evidence/D-R1/Runs/R1/Visibility-06/ClientA-partial-depth.png), [video R1](../../Evidence/D-R1/Runs/R1/Visibility-06/Visibility.mp4), [loopback R1](../../Evidence/D-R1/Runs/R1/Visibility-06/Output-Loopback.wav), [video mạng/reconnect](../../Evidence/D-R1/Runs/R1/Network-02/Network-D.mp4). Midpoint LOS trong diagnostics chỉ giúp chọn cảnh, **không thay cho depth test từng pixel**; source proxy và ảnh/video GPU là bằng chứng cắt phần che.

## Profile và bản chơi

Combat runtime đo bằng timestamp wall mỗi frame: Server PID 13552: 29.93 FPS, p99 40.28 ms; ClientA PID 19640: 59.85 FPS, p99 22.81 ms; ClientB PID 14032: 60.00 FPS, p99 20.60 ms; ClientA PID 2408: 59.42 FPS, p99 21.14 ms. Cap client60/server30; 900×540 mỗi client, internal 50%, Lumen atlas 2048, RT minimum 128 MiB, texture pool 256 MiB và render profile giản lược giữ đúng launcher C2/D. Không đổi cap, smoothing, input để che khựng. Đây là profile review, chưa nghiệm thu đồ họa/hiệu năng U04; video encode 30 FPS là thông số khác.

[Solo](../../Play-U03-D.cmd), [Network](../../Play-U03-D-Network.cmd), [Stop](../../Stop-U03-D.cmd), [checklist](../../Play-U03-D-CHECKLIST.md). Package: `Artifacts/U03/D/Runs/Package-20261116-140739/Archive/Windows`. Một clone D duy nhất `Artifacts/U03/D/Source` ghim source trên; manifest guard source/module/engine/package/port/PID/executable/log. Chỉ minimize Editor gốc sau clients ready, scoped Stop khôi phục placement; không save/restart/đóng Editor gốc. Play Editor gốc không mặc định là D. Preferences launcher vẫn ở thư mục user riêng của Solo/A/B; kiểm migration/rebind dùng slot cô lập, không sửa settings người dùng.

## Bằng chứng, lượt lỗi và giới hạn

[Manifest R1](../../Evidence/D-R1/MANIFEST.json) giữ source/engine/toolchain/PID/world/owner/role, hash raw/published, binary/package, từng cổng và profile. [Warnings](../../Evidence/D-R1/WARNINGS.json), [matrix R1](../../D-R1-TEST-MATRIX.md), [bao phủ U03](../../CLOSURE-D.md). MSVC 14.51.36260/SDK 10.0.26100.0; engine build chính xác nằm trong manifest. Cảnh báo compiler không thuộc bản preferred, deprecation/fixture và loopback discontinuity được giữ; không khẳng định audio sample-exact.

Giữ các lượt lỗi/không hợp lệ: compile fixture thiếu `OutLifetimeProps`; camera attach xoay theo pawn; strafe/quái đuổi làm sai cảnh partial; harness đòi log cho event đã tiêu thụ; combo bấm sớm hơn buffer; phát hiện mất âm future-history; overload assertion test. Manifest phân biệt chúng với cổng cuối. Không bỏ lỗi rồi gọi toàn đợt PASS.

[Evidence D cũ](../../Evidence/D/MANIFEST.json) giữ nguyên: 534 raw + 534 published và 48 file package vẫn khớp hash. Trạng thái READY cũ là lịch sử của lượt bị từ chối, không là ACCEPTED. Clone DLL là output mutable đã được rebuild sang R1; hash DLL D cũ chỉ là tham chiếu lịch sử, không nói clone hiện còn chứa DLL cũ. Package, media, log và manifest D cũ không bị dọn/ghi đè. Năm vòng Boot/settings reopen và capture terrain D trước được kế thừa về bằng chứng; không giả ghi thành lượt R1. Tests timing/dodge wall/StepUp/two-pawn/lethal/combat lock được chạy mới trong full 140.

Runtime Editor client đã ghi lại hai `AutoSDKInfo.json` trong thư mục preferences A/B dùng chung. R1 lưu bản mới riêng, phục hồi byte gốc từ bản published đúng hash; launcher nay backup/restore riêng SDK log và không sửa preferences. Guard live-process và Stop lặp đã kiểm. Lượt guard phục hồi ban đầu từ chối cũng được giữ trong hồ sơ.

Config riêng, `.uproject`, Maintenance và Editor gốc được bảo toàn; PID gốc11880 giữ nguyên thời điểm khởi chạy. Các commit hồ sơ/harness sau source trên không đổi `Source/Content`; không build/test lại chỉ vì sửa báo cáo. Mannequin/blockout và art/animation sản phẩm vẫn deferred. **Điểm dừng: READY_FOR_REVIEW D-R1.**
