> Checklist lịch sử tại941bc3d; xem D-MANUAL-CHECKLIST.md cho bản sửa hiện tại.

# U01-D — Checklist review package

**READY_FOR_REVIEW; chưa có xác nhận nghiệm thu D của người dùng.** Source package `715238443e33e1a2760ea3d89f4d1698f092e511`. Chạy `Artifacts/U01/D/Play-D.cmd`, vào CharacterCombatLab. Original Editor không phải bản dùng để nghiệm thu này. Xem [REPORT-D](REPORT-D.md), [video27s](Evidence/D-PLAY.mp4).

| Mục | Bằng chứng đã chạy | Trạng thái |
|---|---|---|
| Idle/move/sprint/jump-up/fall/land, không kẹt | 3 tests D; input Windows/capturePID22692, samples đủ0–4 | PASS tự động/tool |
| Rời mép không jump-up giả, land rồi về idle | Game fixture + thao tác menu chọn Ledge và W thật | PASS tự động/tool |
| Animation không cộng tốc độ/apex | BP/mesh/AnimBP thật: đi50m/sprint70m mỗi10s, apex~1,20m | PASS tự động |
| Pose thực chạy nhiều frame khi ổn định | Test chu kỳ tay/chân, sample interpolation cold-load; video locomotion mới | PASS tự động/tool |
| Kiếm bám tay, collision không ảnh hưởng motor | Socket riêng, sai lệch vị trí0cm; video move/jump/land; collision/overlap/physics/nav tắt | PASS tự động/tool |
| Không sửa shared skeleton/template, không anime art | Hash11 asset riêng và Git diff nguồn | PASS phạm vi; anime DEFERRED |
| Foot sliding/cảm giác chuyển động có chấp nhận được | Video10Hz có18frame lặp/270; AI xem ảnh mẫu, chưa thay đánh giá của người review | PENDING REVIEW |
| Xác nhận chơi thử package D tổng thể | Chưa có xác nhận người dùng cho D | PENDING USER |

Review gộp, không cần stopwatch để thay số đo tự động:

1. Resume, đứng yên rồi W; giữ Ctrl khi di chuyển, nhả; quan sát chân khi chạy thẳng ổn định. Có thể Escape → Fixture reset runway → Resume để quay lại đường80m.
2. Nhấn Space ngắn/dài, nhảy lúc đứng/chạy; nhìn tư thế lên/rơi/land rồi idle hoặc tiếp tục chạy, không đứng cứng/kẹt fall. Escape → Next terrain station tới Ledge → Resume, đi khỏi mép để xem fall trực tiếp.
3. Xoay camera khi đứng/di chuyển để xem kiếm theo tay phải trong các pose. Kiếm khối và clip unarmed chỉ kiểm attachment; chưa có tư thế nắm kiếm/art anime sản phẩm. Chọn V/đứng gần vật cản để xem cơ chế owner-hide của mesh/kiếm nếu cần review thêm.
4. Nếu có trượt chân rõ kéo dài, pose bất thường hoặc kiếm rời tay, ghi vị trí/trạng thái hoặc đoạn video cần sửa. Chưa đánh dấu toàn checklist PASS chỉ từ kết quả tests.

Không dùng checklist này nghiệm thu rebind/settings E, mạng F, full lifecycle/FPS/10phút G hoặc art anime. Main chưa merge D.
