"""Write only review documents after the R1 sealer has verified the gates."""
import json
from pathlib import Path
r=Path(__file__).resolve().parents[2];m=json.loads((r/'Evidence/D-R1/MANIFEST.json').read_text());assert m['status']=='READY_FOR_REVIEW';g=m['gates'];source=m['source'];short=source[:7]
def write(name,text):(r/name).write_text(text.strip()+'\n',encoding='utf-8')
profile=g['network']['profile']['processes'];fps='; '.join(f"{p['role']} PID {p['pid']}: {p['measuredFPS']:.2f} FPS, p99 {p['frameMsP99']:.2f} ms" for p in profile)
audit_count=g['network']['feedbackChecks']
vis=g['visibility']['run'].replace('Artifacts/U03/D/','Evidence/D-R1/Runs/');net=g['network']['run'].replace('Artifacts/U03/D/','Evidence/D-R1/Runs/')
write('Docs/U03/REPORT-D.md',f'''
# U03-D-R1 — READY_FOR_REVIEW

Sửa lượt D bị **NOT ACCEPTED tại f6d0f68** vì nhãn/khung/âm dùng phép chiếu camera mà chưa kiểm che khuất. Source runtime cuối **`{source}`**, nhánh `u03/d-integration`; main nền vẫn `bc3a9955a8c0ecc1cb7f0d43dce13300c9664ac9`. Chưa ACCEPTED, chưa merge, chưa khép U03, chưa U04. Reviewer AI đối chiếu kỹ thuật; người dùng chơi thử cảm giác/hình ảnh và cho phép khép là cổng riêng.

## Sửa lỗi

Nhãn phase/guard/CC/dodge và phản hồi/audio tái dùng đúng projection/LOS C2: bỏ qua combat bodies, trace môi trường channel 2 từ camera của LocalPlayer tới information point và anchor nhãn. Đối thủ bị che hoặc ngoài màn hình không hiện nhãn/phản hồi, không tạo âm; voice đang phát dừng khi mất visibility hoặc đổi life/scope.

Sword box và mũi tên chuyển khỏi Canvas sang primitive world trong module hiện có: normal world PDI, `SDPG_World`, depth bias 0, không debug PDI. GPU depth-test từng pixel nên phần cạnh bị tường che bị cắt ngay cả khi anchor quái vẫn thấy. Geometry giữ nguyên 200×120×180 cm và yaw từ snapshot; component không collision/nav, không dịch capsule hoặc quyết định hit. Dedicated server không tạo component này, audio hay UI.

Capture mới còn phát hiện history có thể tới trước ước lượng clock server của client: tiêu thụ serial trước timestamp làm mất âm fresh. R1 giữ event chưa tiêu thụ tới khi chính clock đó đạt timestamp; không đổi clock, timestamp, cửa sổ 1,2 giây hoặc ngưỡng âm 150 ms. Event đủ điều kiện nhưng bị che vẫn được tiêu thụ im lặng; hiện lại không phát lại âm. Snapshot trễ chỉ còn lifetime gốc. Giữ source/target/life/action/serial/encounter revision và reconnect baseline.

Không đổi model/timing/damage/admission/defense/dodge/motor/authority/Retry, clip/carry/grip, schema settings hoặc nội dung U04. Fixture R1 chỉ bật bằng `-U03R1VisibilityProbe`, dùng camera/tường riêng sau trạm và input/combat authority thật; launcher bình thường không bật fixture.

## Cổng trên source cuối

| Cổng | Kết quả mới R1 |
|---|---|
| Editor/Game và Windows package | PASS; package index {m['packageFiles']} file |
| Full Automation U00–U03 | **140 Success, 0 Failed**: 131 nền + 6 D + 3 R1; từng test trong manifest/log MCP |
| Timing/model/world | Nằm trong full suite: bước 30/60/120 và update dài; không gọi đó là FPS render |
| Blueprint/reference và smoke | 16 Blueprint compile, không thiếu dependency; Boot/CombatLab/NetworkLab 3/3 |
| Hai client: tường/reveal/expiry/partial telegraph | 20 kiểm tra input/video/loopback, debug overlay và stat tắt; audit độc lập {audit_count} kiểm |
| Package Solo | Combat 24; Tab/LOS/rebind 15; fixture defense/CC/X/Feint/Interrupt/held-input 15; loopback parry 660→990 và tín hiệu tổng hợp |
| Dedicated Editor + hai client/reconnect | 26 kiểm; 41 so sánh độc lập HP/action/resource/AI/result/revision; Retry A không đổi B |
| Launcher/Stop | Guard hash package/module/source 3/3; runtime Solo/Network và scoped Stop/placement được ghi riêng |

[{short}: ảnh phần telegraph bị che](../../{vis}/ClientA-partial-depth.png), [video R1](../../{vis}/Visibility.mp4), [loopback R1](../../{vis}/Output-Loopback.wav), [video mạng/reconnect](../../{net}/Network-D.mp4). Midpoint LOS trong diagnostics chỉ giúp chọn cảnh, **không thay cho depth test từng pixel**; source proxy và ảnh/video GPU là bằng chứng cắt phần che.

## Profile và bản chơi

Combat runtime đo bằng timestamp wall mỗi frame: {fps}. Cap client60/server30; 900×540 mỗi client, internal 50%, Lumen atlas 2048, RT minimum 128 MiB, texture pool 256 MiB và render profile giản lược giữ đúng launcher C2/D. Không đổi cap, smoothing, input để che khựng. Đây là profile review, chưa nghiệm thu đồ họa/hiệu năng U04; video encode 30 FPS là thông số khác.

[Solo](../../Play-U03-D.cmd), [Network](../../Play-U03-D-Network.cmd), [Stop](../../Stop-U03-D.cmd), [checklist](../../Play-U03-D-CHECKLIST.md). Package: `{m['packageRelativePath']}`. Một clone D duy nhất `Artifacts/U03/D/Source` ghim source trên; manifest guard source/module/engine/package/port/PID/executable/log. Chỉ minimize Editor gốc sau clients ready, scoped Stop khôi phục placement; không save/restart/đóng Editor gốc. Play Editor gốc không mặc định là D. Preferences launcher vẫn ở thư mục user riêng của Solo/A/B; kiểm migration/rebind dùng slot cô lập, không sửa settings người dùng.

## Bằng chứng, lượt lỗi và giới hạn

[Manifest R1](../../Evidence/D-R1/MANIFEST.json) giữ source/engine/toolchain/PID/world/owner/role, hash raw/published, binary/package, từng cổng và profile. [Warnings](../../Evidence/D-R1/WARNINGS.json), [matrix R1](../../D-R1-TEST-MATRIX.md), [bao phủ U03](../../CLOSURE-D.md). MSVC 14.51.36260/SDK 10.0.26100.0; engine build chính xác nằm trong manifest. Cảnh báo compiler không thuộc bản preferred, deprecation/fixture và loopback discontinuity được giữ; không khẳng định audio sample-exact.

Giữ các lượt lỗi/không hợp lệ: compile fixture thiếu `OutLifetimeProps`; camera attach xoay theo pawn; strafe/quái đuổi làm sai cảnh partial; harness đòi log cho event đã tiêu thụ; combo bấm sớm hơn buffer; phát hiện mất âm future-history; overload assertion test. Manifest phân biệt chúng với cổng cuối. Không bỏ lỗi rồi gọi toàn đợt PASS.

[Evidence D cũ](../../Evidence/D/MANIFEST.json) giữ nguyên: 534 raw + 534 published và 48 file package vẫn khớp hash. Trạng thái READY cũ là lịch sử của lượt bị từ chối, không là ACCEPTED. Clone DLL là output mutable đã được rebuild sang R1; hash DLL D cũ chỉ là tham chiếu lịch sử, không nói clone hiện còn chứa DLL cũ. Package, media, log và manifest D cũ không bị dọn/ghi đè. Năm vòng Boot/settings reopen và capture terrain D trước được kế thừa về bằng chứng; không giả ghi thành lượt R1. Tests timing/dodge wall/StepUp/two-pawn/lethal/combat lock được chạy mới trong full 140.

Runtime Editor client đã ghi lại hai `AutoSDKInfo.json` trong thư mục preferences A/B dùng chung. R1 lưu bản mới riêng, phục hồi byte gốc từ bản published đúng hash; launcher nay backup/restore riêng SDK log và không sửa preferences. Guard live-process và Stop lặp đã kiểm. Lượt guard phục hồi ban đầu từ chối cũng được giữ trong hồ sơ.

Config riêng, `.uproject`, Maintenance và Editor gốc được bảo toàn; PID gốc11880 giữ nguyên thời điểm khởi chạy. Các commit hồ sơ/harness sau source trên không đổi `Source/Content`; không build/test lại chỉ vì sửa báo cáo. Mannequin/blockout và art/animation sản phẩm vẫn deferred. **Điểm dừng: READY_FOR_REVIEW D-R1.**
''')
write('REPORT-D.md','''# U03-D report location

The single current report is [Docs/U03/REPORT-D.md](Docs/U03/REPORT-D.md), now U03-D-R1. D at f6d0f68 was NOT ACCEPTED.

Historical evidence remains at [Evidence/D](Evidence/D/MANIFEST.json); current evidence is [Evidence/D-R1](Evidence/D-R1/MANIFEST.json). This root file remains a pointer, not a second competing report.
''')
write('CLOSURE-D.md',f'''# U03-D-R1 — coverage READY_FOR_REVIEW

Source `{source}`. Chưa ACCEPTED/merge/khép U03/U04. Full 140 chạy mới; các capture D trước chỉ là bằng chứng kế thừa và đã bị từ chối ở cổng presentation occlusion. [Báo cáo chính](Docs/U03/REPORT-D.md), [manifest mới](Evidence/D-R1/MANIFEST.json).

| ID | Nền giữ nguyên | Bao phủ R1 mới / kế thừa rõ ràng |
|---|---|---|
| U03.01 | Combo A0/A1 | Full140 mới + package combat/fixture; clip1–3 kế thừa |
| U03.02 | Resource/cooldown | Full140 mới + HUD/resources/rebind trong package/mạng |
| U03.03 | Dodge B1 | Full140 mới wall/StepUp/two-pawn/timing + input dodge; terrain video D kế thừa |
| U03.04 | Defense/CC/X B2 | Full140 + fixture/audio/held-input mới; pose assets giữ nguyên |
| U03.05 | Skill/monster/Tab C1/C2 | Full140 + Tab15/combat24/network26 + independent41 mới; route D kế thừa |
| U03.06 | Presentation/settings D | Shared C2 LOS; depth-tested world telegraph; R1 two-client20 + audit{audit_count} + future-clock test; BP16/package/smoke mới |
| U03.07 | Authority Retry C2 | Full140 + Won/Lost/Retry/reconnect/owner isolation mới |
| U03.08 | Parry B2 | Native boundaries mới + package loopback660→990; ring/DSP giữ nguyên |
| U03.09 | Feint/Interrupt C1 | Native boundaries + fixture/native history/audio mới |

Coverage PASS không phải ACCEPTED. User chơi thử cảm giác/hình ảnh và cho phép khép riêng. Không shared monsters/skills mới/balance/progression/prediction/packaged Server/U04; mannequin/art sản phẩm vẫn deferred.
''')
write('D-R1-TEST-MATRIX.md',f'''# D-R1 final matrix — READY_FOR_REVIEW

Source `{source}`. [Manifest](Evidence/D-R1/MANIFEST.json) là index hash/log/PID/world/role và từng gate. D ở f6d0f68 NOT ACCEPTED; không dùng cổng presentation D cũ để thay lượt R1.

| Yêu cầu | Bằng chứng source cuối |
|---|---|
| Environment LOS cho subject/anchor/audio | Native world wall + C2 helper; hai client hidden/reveal capture |
| Toàn bộ telegraph không x-ray | Normal world PDI/depth; exact15-edge geometry test; actual GPU partial-wall screenshots/video, stats/debug off |
| Hidden consume, reveal không replay, expiry tuyệt đối | 20 real checks + audit{audit_count}; same serial/timestamp/revision before Retry; Native dedup/life/late tests |
| Future history không bị retire trước clock | New native clock-eligibility test; fresh visible sounds once trong capture/audio |
| Authority/proxy/Retry/reconnect | Network26 + independent41 mới; server không HUD/audio; initial baseline/life/late native |
| Regression | Full140, Editor/Game, package, BP16, smoke3, combat24, Tab15, fixture15 mới |
| Launcher | Hash/source/module refusal3 + Solo/Network runtime/scoped Stop/placement mới |
| Profile | Actual combat wall-frame measurements client60/server30; cap/profile/smoothing giữ nguyên |

Build/capture lỗi và cảnh không hợp lệ vẫn lưu riêng trong manifest/warnings. D trước có Boot5/settings reopen/terrain/route capture kế thừa; không ghi là lượt R1. READY_FOR_REVIEW chưa ACCEPTED hoặc cho phép merge/khép U03.
''')
write('D-R1-CONTRACTS.md',f'''# U03-D-R1 contracts

Runtime source `{source}`. D at f6d0f68 was NOT ACCEPTED. R1 introduces no gameplay decision or authority/motor/damage change; 35 model/U02/motor/character/animation blobs match that baseline exactly, and remaining C++ edits are presentation or explicitly flagged capture fixtures.

* C2 projection and environment query are shared unchanged with Tab/HP. Canvas subject cues and event audio require the subject information point and label anchor to be on screen and clear from the LocalPlayer camera. Combat bodies are excluded from the environment trace. This does not select a target or change Tab retention.
* The entire confirmed sword box/direction is a normal world primitive with per-pixel depth test, world depth group, zero bias; no Canvas box or debug PDI.15 segments preserve the existing 200×120×180 volume/yaw. The component has no collision/navigation or authority writes; dedicated server creates none.
* Confirmed history identity remains source/target/life/action/serial/encounter/revision. Eligibility uses the existing server clock: future timestamps do not retire serials; eligible hidden events retire silently. Repeated snapshots or revealing an event never rearm sound or its absolute timestamp+1.2 lifetime. Fresh audio allowance stays150ms; initial reconnect baseline is silent, and scope/visibility loss stops active voices.
* Miss/contact/block/parry/cancel rules, animation poses, bindings/schema v2/SaveGame and all A0–C2 gameplay laws stay unchanged. Migration tests use isolated slots; no user settings rewritten for testing.
* New R1 asset inventory: no authored uasset/audio download. World line vertices are generated in U03; the opt-in fixture references the existing Engine Cube. D poses, Attack1–3/Q/E, grip/carry and synthesized PCM/parry expression are inherited unchanged and tested again.
* `-U03R1VisibilityProbe` alone enables the labelled wall/camera diagnostics fixture. Actual Windows input and ordinary authority combat produce the results. Normal Solo/Network launchers do not enable it.
* One existing D clone, immutable old D published/raw/package evidence, private config/Maintenance and original Editor are preserved. Stable launcher preferences retain their directories; new Editor SDK logs are archived separately and prior SDK logs restored at scoped Stop. No source rebuild for report-only changes.

Final gates and limits: [matrix](D-R1-TEST-MATRIX.md), [single canonical report](Docs/U03/REPORT-D.md). Stop at READY_FOR_REVIEW D-R1, never ACCEPTED/merge/U03 closure/U04 automatically.
''')
write('Play-U03-D-CHECKLIST.md','''# U03-D-R1 playtest

Mở **Play-U03-D.cmd** (Solo) hoặc **Play-U03-D-Network.cmd** (hai cửa sổ). A/B là hai trạm encounter riêng, nên quái của A không chuyển sang B. Đổi focus thì chọn Resume. **Stop-U03-D.cmd** dừng đúng session và khôi phục placement Editor; Play trong Editor gốc không mặc định là D-R1.

1. Startup/active/recovery và hướng đòn có dễ đọc không?
2. Hit/block/parry/hụt/break/Feint/Interrupt có phân biệt được bằng hình/âm không?
3. Dodge/guard/CC/X có dễ hiểu; grip kiếm và tư thế có xuyên thân rõ rệt không?
4. HUD/phím/cooldown có dễ đọc? Nhãn/phản hồi đối thủ và HP phải ẩn sau vật cản; phần telegraph bị che không hiện xuyên. HP vừa trúng không tự bật Tab.
5. Won/Lost → Retry → Resume, đổi focus và hai cửa sổ có ổn không? Retry không đánh và không tự Resume.

Escape → **Open regression stations (separate run)** vào trạm fixture có nhãn. **Back to Boot** trở về. Settings lưu riêng Solo/A/B dưới `Artifacts/U03/D/UserSettings`; reconnect giữ preferences, không giữ combat progress.

AI chịu trách nhiệm hash/authority/timing và các cổng kỹ thuật. Người dùng chơi thử cảm giác/hình ảnh và cho phép khép riêng. Hiện chỉ READY_FOR_REVIEW D-R1, chưa ACCEPTED/merge/khép U03/U04; art sản phẩm tiếp tục deferred.
''')
for name in ['D-CONTRACTS.md','D-TEST-MATRIX.md']:
 p=r/name;old=p.read_text(encoding='utf-8-sig');marker='> D-R1 supersedes'
 if not old.startswith(marker):p.write_text('> D-R1 supersedes presentation visibility/Canvas telegraph details and the old final-run status below. D at f6d0f68 was NOT ACCEPTED. This file retains the D baseline; current source/gates are [REPORT-D](Docs/U03/REPORT-D.md) and [R1 matrix](D-R1-TEST-MATRIX.md).\n\n'+old,encoding='utf-8')
print('Updated canonical report, pointers, coverage and checklist; no source/content changes')
