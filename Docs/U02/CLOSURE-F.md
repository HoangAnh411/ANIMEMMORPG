# U02 — ma trận khép kỹ thuật A–F

A–E đã ACCEPTED theo ACCEPTANCE-A/B/C/D/E. F **ACCEPTED về kỹ thuật tại d5fb4b0/source8580651**, căn cứ ACCEPTANCE-F. Ma trận bên dưới giữ kết quả đã bàn giao và được reviewer đối chiếu; không phải chạy lại khi khép. Người dùng cho phép push/fast-forward main và lập kế hoạch U03, chưa cho triển khai U03 trước review.

**Khép cuối U02:** focus ACCEPTED tại32061ba theo ACCEPTANCE-FOCUS, gồm cảm giác đổi focus “ok rồi”; không phát hiện lỗi chặn còn mở qua lần rà soát U02.00–U02.06. Chỉ cập nhật hồ sơ/commit/push/xác minh remote/fast-forward main rồi dừng; không còn tính năng U02 cần triển khai, không làm U03 trong lượt này.

| Cổng | Bằng chứng | Kết quả đã nghiệm thu |
|---|---|---|
| Dedicated Editor +2 client,0LocalPlayer server/đúng owner/roles | PROCESS-MANIFEST; Network-input134 assertions; LAUNCHER | Đạt phép kiểm thực |
| Hụt/trúng/tường/head-only/nhiều hurtbox/nhiều target | Network stages Miss/Wall/PartialHead/HitMulti; native source/action/target/life/hurtbox IDs | Ba process cùng confirmed results/HP |
| Damage/crit/shield/death | Crit/ShieldGranted/ShieldHit/ConcurrentLethal;61 Automation gồm full E; đồng thuận deadline/state | Server quyết định; duplicate không roll/trừ thêm |
| Hai nguồn, lethal ordering | Hai concurrent intents đều accepted; cùng timestamp, stable source/event order; hai target chết đúng một lần | Fixture server rõ ràng; không mở PvP |
| Duplicate/stale/wrong ownership/nonfinite/unsupported HP-damage payload | Wire probes theo UTC; server admission counters; reflected RPC schema; F command-life/aim tests | Không có extra damage/action hợp lệ |
| Reset, old life/history | ResetGeneration; native first-full-active reset test; reconnect current-life HP đối chiếu server khi vẫn nhận history cũ | Event cũ không tác động life mới |
| Disconnect trong accepted action/reconnect | Native removal cutoff, no later old-source event; ID mới, initiallife1 rồi fixtureresetlife2/action1; Disconnect-ASSERTIONS | Thực ba process, không dùng command/life ID connection cũ |
| Presentation local/proxy đúng action/phase, gravity/yaw/motor |597 samples;36 supplementary assertions; Network-F/Controls-F videos | Montage cùng IDs; body yaw thực, camera và movement/focus được đo |
| Menu/focus không pause server, Resume không attack | MenuFocusDoesNotPause; controls/owner runtime samples | Input Windows thật, AwaitingResume giữ nguyên |
| Movement/smoothing/settings U01 | Full61 tests; heldW/sprint700/gravity/settings; SMOOTHING mode2/time0,1 trên proxy samples; actual frame profiles30/60/60 | Không sửa smoothing chung |
| Source→binary→run→kết quả | MANIFEST, BUILD/AUTOMATION/PROCESS, RAW-LOGS, EVIDENCE-SHA256; remote SHA kiểm sau push | Failed/INVALID runs giữ riêng; không dùng làm PASS |
| Launcher/Stop/Editor/config | Play-U02-F, Stop-U02-F, LAUNCHER, EDITOR-RESTORED; private config byte guard | Chỉ session-owned PIDs; Editor gốc còn nguyên |
| Hồi quy khựng khi đổi focus | Evidence/Focus;197/197 hashes;71 input +55 supplementary;10 lượt trước/sau,15s/lượt |ACCEPTED32061ba; profile review giảm Lumen/shadow, Editor minimized/Stop đúng |
| Người dùng đánh giá focus | ACCEPTANCE-FOCUS/checklist cạnh launcher | Cảm giác đổi focus đã xác nhận “ok rồi”; không suy thêm nghiệm thu art hay mọi khía cạnh gameplay |

| Đợt | Commit nghiệm thu | Source kiểm chứng | Trạng thái |
|---|---|---|---|
| A |914f7af |f11c944 |ACCEPTED kỹ thuật/model |
| B |95a83ca |94ebcc7 |ACCEPTED action/input/motor |
| C |cdaf102 |9aa7249 |ACCEPTED blockout; xoay/đứng đánh đã được chấp nhận |
| D |d0dd5b0 |82bb890 |ACCEPTED collision/corner; action66 không được gán chắc cho ảnh ban đầu |
| E |903e139 |1f1c359 |ACCEPTED Windows/vital/damage |
| F |d5fb4b0 |8580651 |ACCEPTED dedicated Editor server/hai client trong điều kiện đã đo |
| Focus |32061ba |8580651 runtime; launcher a55839e |ACCEPTED kỹ thuật và cảm giác đổi focus; không đổi luật combat/mạng |

Các file bằng chứng ở Evidence/F. Package Windows và smoke3maps của E là bằng chứng đã ACCEPTED riêng, source1f1c359; không gọi là package F. F chạy Editor binaries trên source mới, chưa Server đóng gói hoặc U05. Anime art/carry sản phẩm, respawn sản phẩm và các tính năng U03 vẫn ngoài phạm vi.
