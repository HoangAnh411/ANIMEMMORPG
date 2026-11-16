# U03-D — bao phủ READY_FOR_REVIEW

Ma trận nghiệm thu kỹ thuật để reviewer AI kiểm; chưa ACCEPTED và chưa khép U03. Source runtime9da1b43; tất cả cổng cuối và manifest tại [REPORT-D](Docs/U03/REPORT-D.md). Baseline A0–C2 được kế thừa về triển khai, nhưng131 tests nền được chạy mới cùng6 tests D, tổng137/137. User feel/art vẫn là cổng riêng.

|ID|Nền giữ nguyên|Bằng chứng D mới / trạng thái|
|---|---|---|
|U03.01|Combo A0/A1|PASS coverage: Full137: timing/priority + combat combo video; clip1–3 giữ nguyên|
|U03.02|Resource/cooldown|PASS coverage: Full137 + HUD energy/Q/E, rebind persistence|
|U03.03|Dodge B1|PASS coverage: Native wall/StepUp/two-pawn + physical dodge/pose; không animation authority|
|U03.04|Defense/CC/X B2|PASS coverage: Full137 +15 fixture checks/audio/pose/held-input|
|U03.05|Skills/monster/Tab C1/C2|PASS coverage: Route11, target15, combat24, network26+independent41|
|U03.06|Presentation/settings D|PASS coverage: Canvas/history/scoped audio, ten pose assets, BP16/package/smoke, save/reopen|
|U03.07|Authority Retry C2|PASS coverage: Won/Lost/Retry release gate + owner isolation/reconnect; không product resurrection|
|U03.08|Parry B2|PASS coverage: Native boundaries + real parry ring/660→990 loopback, no repeat|
|U03.09|Feint/Interrupt C1|PASS coverage: Native boundaries + physical labelled fixture/confirmed result + distinct chirps|

“PASS coverage” không là ACCEPTED từng hạng mục hoặc cho phép merge. Không mở shared monsters/skills/balance/progression/prediction/packaged Server/U04. Profile review không là nghiệm thu graphics/performance. [Manifest](Evidence/D/MANIFEST.json), [matrix](D-TEST-MATRIX.md), [checklist](Play-U03-D-CHECKLIST.md).
