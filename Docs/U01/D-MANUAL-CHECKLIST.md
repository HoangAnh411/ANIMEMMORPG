# U01-D carry — Checklist review package cuối

**READY_FOR_REVIEW**, source package **6ef6ec3125ed455e3963a687df481eb138629df6**. Chạy `Artifacts/U01/D/Play-D.cmd` → CharacterCombatLab. Original Editor chưa xác nhận nạp native D.

**Cách nắm đã được người dùng xác nhận.** Skeleton/socket và PA_U01_RightGrip giữ nguyên hash; lần này chỉ hoàn thiện quỹ đạo vai/cánh tay khi mang kiếm. Build,17/17 tests, motor/apex, attachment, owner-hide và smoke3/3 đã PASS; không cần đo lại bằng stopwatch.

Chỉ còn review các hành vi mới:

1. Idle → W → giữ Ctrl → Space → tiếp tục chạy sau đáp: tay phải giữ kiếm ngoài thân, lưỡi không quét ngang qua ngực/bụng trong đoạn chuyển. Thử cả nhảy/đáp đứng yên.
2. Đổi hướng W/A/S/D lúc đi/sprint và quanh lúc nhảy/đáp; xoay camera nhìn trước/bên. Kiếm không đi xuyên thân hoặc giật/đảo hướng do chuyển pose.
3. Đánh giá pose mang kiếm có chấp nhận được cho blockout một tay: tay phải cố ý giảm mạnh độ vung, chưa phải animation chiến đấu/polish. Nêu đoạn hoặc góc cần sửa nếu tay quá cứng hoặc quỹ đạo chưa hợp lý. Không cần review lại socket/ngón tay riêng trừ khi thấy hồi quy rõ.

[Video chuyển tiếp24s](Evidence/D-Carry/Transitions.mp4) · [Góc trước15s](Evidence/D-Carry/Front.mp4) · [Báo cáo](REPORT-D.md). Capture thực23–24FPS, không tự chứng minh blend100ms mượt. Test quỹ đạo dùng proxy thân/chân, không thay review mesh thực.

Các mục trên **PENDING USER REVIEW**; D chưa nghiệm thu/merge hoặc làm E. Collision kiếm vẫn tắt. Art anime DEFERRED. Hồ sơ/checklist lần trước tại [lịch sử4c8](D-CHECKLIST-4c8-HISTORY.md).
