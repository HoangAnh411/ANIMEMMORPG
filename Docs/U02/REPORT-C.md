# U02-C — READY_FOR_REVIEW

Nhánh riêng `u02/c-attack-presentation`, từ main B ACCEPTED `34e5dd73724546deb6e9cbb410a844341fcfad3c`. **Source kiểm chứng `61be83bce9bc4eb1ad15713b2bd4dc291cd37456`**. Không merge C hoặc bắt đầu D. B được nghiệm thu tại95a83ca/source94ebcc7, không chờ xác nhận kỹ thuật lại. Checklist B đã đặt cạnh launcher; original Editor refresh/PIE/Live Coding đã khép trong ACCEPTANCE-B.

## Đã triển khai

Tự author clip kỹ thuật `A_U02_Attack1` trên SK_U01,41mẫu100Hz/0.40s; montage `AM_U02_Attack1` sections Startup0/Active0.16/Recovery0.22. Không clip ngoài hoặc mua/tải asset. Root cố định, root motion disabled/IgnoreRootMotion; không capsule displacement. Bone pose tay dùng chiều dài tay thực và socket đã nghiệm thu, giữ ngón tay grip. Asset hashes tại ASSETS.json.

Graph riêng `ABP_U02` giữ ABP_U01 nguyên byte; combat component gán C graph khi mesh có mặt. Cook explicit thư mục U02. Montage slot sau carry, mask upperarm_r và dưới grip; AttackBlendWeight chỉ1khi trình bày action,0khi idle/finish/cancel để carry/locomotion không bị cached slot đè. Chân/tay trái tiếp tục U01. Không thay damage/collision hoặc quyền motor B.

UU01AnimInstance đọc confirmed combat snapshot + server/world simulation time: late snapshot play/seek current time, stale life/action stop không dừng action mới; matching cancel/reset/finish dừng montage và trả locomotion. Montage/notify không sửa model, không phát hit/damage. Asset hiện không có notify; tests kiểm không notify dependency, không tuyên bố đã phát/đánh giá SFX/VFX. Crit/vital/hurtbox/network agreement chưa thuộc C.

## Kiểm chứng thực

UE5.8.4 CL58902052; MSVC14.51.36260/toolset14.51.36231,SDK10.0.26100.0. Full build Editor/Game clone riêng `Build-20261106-001924-446-56d63463`, cả hai Result:Succeeded/exit0. Không nạp layout C qua Live Coding vào Editor gốc; giữ Editor gốc đang mở ở binary B vừa refresh, không đóng thêm.

Cold MCP `MCPTests-20261106-002059`: **37/37 Success**, queue37tests hoàn tất. U00/U01 23 + A7 + B4 + C3. Tests C: SnapshotClock,MontageAssets,RuntimeIdentityAndReturn. Có late seek, stale cancel, matching cancel/reset/finish, root displacement và serialized montage dependency trên pawn/AnimBP thực. Full carry/landing/grip/motor/replay regression đạt. [Per-test](Evidence/C/AUTOMATION-RESULTS.json), [MCP](Evidence/C/MCP-RESULTS.json), [build](Evidence/C/BUILD-RESULTS.json).

Windows package `Package-20261106-002214-736-125d162e`, UAT exit0/BUILD SUCCESSFUL, cook ba map + U02 assets. Smoke **3/3** tại `SmokeB-20261106-002349` (tái sử dụng script smoke đã có, không lẫn source B). [Smoke](Evidence/C/SMOKE.json), [48package files SHA256](Evidence/C/PACKAGE.csv), [source/binary manifest](Evidence/C/MANIFEST.json).

Input Windows thật `Play-61be83b`, exact PID/exe/hash/owned Game/Standalone/1LocalPlayer/foreground/IME guards;14.5058s,871native samples. **63/63 assertions hậu xử lý**, tách khỏi37Automation:40hành vi B và23trình bày thực (C graph, bảy action có montage/hand movement/return, root-motion mode). [Assertions](Evidence/C/RUNTIME-ASSERTIONS.json), [input/frame timestamps](Evidence/C/INPUT.json), [video](Evidence/C/Input-C.mp4). Bảy accepted, ba rejected; heldW/Ctrl sau recovery, camera/yaw, menu/focus/AwaitingResume/Resume suppression/gravity vẫn đạt.

Video250frames lưu30FPS nhưng capture thực≈17.23FPS; playback nhanh hơn wall time, dùng mảng frame timestamps để liên kết native log. Không chứng minh render60FPS/độ mượt hoặc chất lượng anime. AI đã xem frame chuẩn bị/chém/thu tay và pose thay đổi; user review hình ảnh/cảm giác chưa được giả định PASS. [Các frame](Evidence/C/FRAMES.json).

## Lịch sử lỗi/giới hạn

- First compile auto-pointer/TObjectPtr graph iteration sai, đã sửa. Root arm endpoint bị reachable guard reject71.241cm >55cm, đã đưa về trong tầm, không kéo giãn xương.
- Editor gốc giữ ABP_U01 nên OS chặn copy; không đóng để ép ghi. Đổi thành ABP_U02 riêng, nguyên bộ U01 assets được giữ. Lượt authored ABP_U01 trong clone được archive riêng, không commit vào Content gốc.
- CarryTrajectory fail ở hai lượt: selector carry/grip cũ mơ hồ khi thêm layer attack và cached slot luônweight1. Sửa selector theo bone role, attack mask upperarm riêng, weight0 khi idle; không bỏ A/B pose assertion. Lượt sau37/37 đạt.
- Python không expose graph FunctionGraphs; chỉnh asset bằng helper C++ clone-only. Lượt thêm node trong ranged-for có handled ensure; đã sửa duyệt bản sao và rebuild/test source cuối. Logs lỗi giữ lại. Không dùng ensure/trigger làm PASS.
- GitHub DNS/connectivity lỗi từng lượt; retry trước bàn giao. Compiler preference/UE deprecation warnings còn ở full logs. Không mở AllToolsets, không thêm plugin/module/GAS.
- Native tests xác nhận cancel/reset và root; input video không tự đại diện kiểm mọi death fixture hoặc dedicated two-client late snapshot. Dedicated U02 đồng thuận/action/HP vẫn cổng F. Chưa collision/damage D/E hoặc product art.
- Config riêng nguyên byte so với baseline C; không stage/in token/restore toàn file. Clone token tự sinh chỉ loại đúng dòng đã xác minh, không áp vào workspace config.

Failed builds/tests/author runs giữ trong Artifacts và archive lịch sử, xem HISTORY.json. Source→binary/package→run→result hashes tại manifest và evidence index; commit hồ sơ không thay source của binary.

## Review

Chạy [Play-U02-C.cmd](../../Play-U02-C.cmd), đọc [checklist cạnh launcher](../../Play-U02-C-CHECKLIST.md). Launcher xác minh48file hash, dùng settings/log riêng và khôi phục Editor window theo identity khi Quit. Đánh giá độ đọc được chuẩn bị/chém/thu đòn, kiếm/grip/pose, trở lại movement và cảm giác ngắm/focus. Đây là blockout kỹ thuật; art anime/carry sản phẩm vẫn DEFERRED. **C dừng READY_FOR_REVIEW**, chưa nghiệm thu/merge, chưa D.
