# U03 — hoàn tất kỹ thuật; chơi thử blockout tích hợp D đã xác nhận

## Trạng thái tổng hợp hiện hành

U03.01–U03.09 hoàn thành trong phạm vi kỹ thuật theo các nghiệm thu A0/A1/B1/B2/C1/C2/D-R1 và ma trận dưới đây. Người dùng đã xác nhận chơi thử blockout tích hợp D ổn ngày **2026-11-16**, được ghi tại `3439fed`. Reviewer AI đối chiếu source/hash/log; người dùng đánh giá cảm giác và hình ảnh blockout qua chơi thử.

Giữ nghiệm thu D-R1 `a7737f9`, source/binary kiểm chứng `0b25523` và mốc khép kỹ thuật D `89358c5`. Không gán `3439fed` hay commit đồng bộ tài liệu cho binary. [Roadmap hiện hành](Docs/ROADMAP.md), [acceptance](Docs/U03/ACCEPTANCE-D-R1.md), [report](Docs/U03/REPORT-D.md), [checklist](Play-U03-D-CHECKLIST.md).

Xác nhận tích hợp D không chứng minh người dùng đã chơi các package B2/C1 cũ; các ghi nhận lịch sử về những bản đó giữ nguyên. Art/animation sản phẩm, hiệu năng U04, mạng xấu U05 và Server đóng gói chưa được nghiệm thu. Các số test/capture bên dưới là kết quả đã có, không phải lượt chạy mới khi đồng bộ hồ sơ.

Hồ sơ U03 **ACCEPTED** theo reviewer tại `b2199687dba33f5348a723506169dd1cfc8628a6`, không có lỗi chặn. Ngày 2026-11-17, người dùng giao khép hồ sơ, fast-forward/push main và tiếp tục U04-A từ main mới đã xác minh. Bước khép chỉ sửa tài liệu, không build/tests/game hoặc tác động Editor; manifest, bằng chứng và mọi failed runs giữ nguyên. Commit hồ sơ không phải nguồn binary.

## Lịch sử bàn giao D-R1 và ma trận bao phủ

Các trạng thái chờ review/chờ chơi thử/không merge sau đây thuộc thời điểm bàn giao hoặc khép kỹ thuật, được trạng thái tổng hợp ở trên thay thế về tình trạng hiện hành.

**ACCEPTED về kỹ thuật D-R1 tại `a7737f9a99bfe8a8637bcf86d09c4f190add7e16`**, source kiểm chứng `0b255233df021f2cc148313e638d918d41a4a11e`. Người dùng cho phép khép hồ sơ D và fast-forward/push main. [Acceptance](Docs/U03/ACCEPTANCE-D-R1.md). Trạng thái READY_FOR_REVIEW/chưa ACCEPTED/không merge dưới đây là lịch sử bàn giao. Lượt khép chỉ sửa tài liệu, không chạy lại build/tests/game hoặc tác động Editor. **Chưa khép toàn U03/U04; playtest đọc đòn/âm/pose/HUD/điều khiển D còn chờ người dùng, art vẫn blockout.**

Source `0b255233df021f2cc148313e638d918d41a4a11e`. Chưa ACCEPTED/merge/khép U03/U04. Full 140 chạy mới; các capture D trước chỉ là bằng chứng kế thừa và đã bị từ chối ở cổng presentation occlusion. [Báo cáo chính](Docs/U03/REPORT-D.md), [manifest mới](Evidence/D-R1/MANIFEST.json).

| ID | Nền giữ nguyên | Bao phủ R1 mới / kế thừa rõ ràng |
|---|---|---|
| U03.01 | Combo A0/A1 | Full140 mới + package combat/fixture; clip1–3 kế thừa |
| U03.02 | Resource/cooldown | Full140 mới + HUD/resources/rebind trong package/mạng |
| U03.03 | Dodge B1 | Full140 mới wall/StepUp/two-pawn/timing + input dodge; terrain video D kế thừa |
| U03.04 | Defense/CC/X B2 | Full140 + fixture/audio/held-input mới; pose assets giữ nguyên |
| U03.05 | Skill/monster/Tab C1/C2 | Full140 + Tab15/combat24/network26 + independent41 mới; route D kế thừa |
| U03.06 | Presentation/settings D | Shared C2 LOS; depth-tested world telegraph; R1 two-client20 + audit17 + future-clock test; BP16/package/smoke mới |
| U03.07 | Authority Retry C2 | Full140 + Won/Lost/Retry/reconnect/owner isolation mới |
| U03.08 | Parry B2 | Native boundaries mới + package loopback660→990; ring/DSP giữ nguyên |
| U03.09 | Feint/Interrupt C1 | Native boundaries + fixture/native history/audio mới |

Coverage PASS không phải ACCEPTED. User chơi thử cảm giác/hình ảnh và cho phép khép riêng. Không shared monsters/skills mới/balance/progression/prediction/packaged Server/U04; mannequin/art sản phẩm vẫn deferred.
