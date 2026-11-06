# Kế hoạch U03 — Combat Kiếm Vũ đầy đủ

**DRAFT_FOR_REVIEW — chỉ kế hoạch, chưa cho triển khai.** Nền main76b627d khép U02 kỹ thuật (33ad1f0 sửa báo cáo/ghi nghiệm thu,76b627d đồng bộ hợp đồng/ma trận), F nghiệm thu d5fb4b0/source8580651. [Khảo sát source](SURVEY.md) ghi các điểm nối thực. Ưu tiên luật: Description → ROADMAP → hợp đồng và bằng chứng U00–U02. Không suy từ technical acceptance thành xác nhận cảm giác hai cửa sổ, art sản phẩm hoặc U05.

## Phạm vi và luật cố định

Giữ module/pawn/motor/camera/settings/maps và server authority hiện có. Không GAS/plugin/framework mới, backend/progression, tám skill đầy đủ, boss/raid, PvP tự do, hồi sinh sản phẩm, Server đóng gói hoặc prediction/bù trễ U05. Art vẫn blockout kỹ thuật có quyền sử dụng rõ; không mua/tải clip chưa rõ quyền. Giữ các trạm hồi quy U01/U02.

| Hành động | Thông số từ Description |
|---|---|
| Attack1/2/3 | Raw60/70/90; tổng.40/.45/.60; active[.16,.22)/[.18,.25)/[.26,.36); cùng hộp feet200×120×180cm, một hit/target/action |
| Combo | Tổng220/1,45s khi nối ngay; một buffer.15s, cạnh mới thay cũ; sau hit1/2 thêm.15s để nối; giữ LMB không tự lặp/Feint |
| Quyền action | Dừng ngang, giữ gravity; startup theo aim, active/recovery khóa yaw; startup attack hủy bằng dodge/guard; Q/E được hủy recovery attack; mất nền hủy phần chưa phát/reset combo/không hoàn tài nguyên |
| Năng lượng | Max100, hồi10/s sau1s không tiêu; attack/dodge/guard/X không tiêu; reject không bắt đầu cost/cooldown |
| Dodge |3m/.25s; khóa attack/jump/guard/interact tới.35; khoảng bắt đầu tối thiểu.60; hai lượt hồi tuần tự2s/lượt, dùng tiếp không reset; buffer.15 chỉ khi đang dodge/chờ.60, không hết lượt/CC/attack active-recovery; không i-frame/xuyên người/tường/vượt vực |
| Guard/parry | Guard120°, giảm70%, bước2m/s, không jump/sprint; posture100, mất25/hit, break.8s rồi đầy; ngoài guard và không nhận hit2s thì hồi25/s. Parry[0,.12), mới press/release, cách mở.60; chỉ hit đầu, không mất posture, không counter/stun/Interrupt tự động |
| CC/X | Hard CC chỉ thay khi remaining mới dài hơn; khóa liên tục tối đa2s rồi miễn2s; reset tích lũy sau.50s tự do liên tục. Slow mạnh nhất. X chỉ khi hard CC, cooldown30s, giải CC/reset tích lũy/miễn hard CC1s, không miễn damage |
| Q | Raw100; startup.30, active[.30,.40), tổng.80;20 năng lượng/CD4s; Q lần nữa trong startup Feint; không Interrupt; chỉ startup bị Interrupt |
| E | Raw80; startup.25, active[.25,.35), tổng.75;25 năng lượng/CD6s; direct hit ngắt startup hợp lệ, block/parry chặn Interrupt; không Feint/stun tự thêm |
| Feint Q | Không hoàn cost/CD; khóa attack/guard/dodge/skill/jump.20, cho đi thường không sprint; cách thành công trước1s. Q/E không có buffer, startup có thể dodge/guard hủy; không hủy lẫn nhau |
| Quái tham chiếu | HP600/raw100; startup.60/active.15/recovery.75, tầm2m, chỉ startup bị Interrupt; chase3m/s, detect10m có LOS, leash15m từ spawn; mất target: chết/ngoài10m/LOS feet+.90 bị che; vềspawn không tái chase, trong.5m hồi HP/reset |
| Tab | Chọn sống/thấy trong20m gần tâm camera; hòa gần nhân vật rồi ID; vị trí3D; giữ≤30m, che liên tục1s bỏ; ngoài màn hình chỉ ẩn UI; chết/life mới bỏ ngay; không tự xoay/hướng đòn/chuyển target |

Ưu tiên lệnh cùng thời điểm của một chủ thể: **X hợp lệ → dodge → bắt đầu guard → Feint → Q → E → attack → jump**; khác thời điểm giữ thứ tự nhận. Reset combo bởi dodge/skill/CC/death, startup-guard và mất nền. Menu/focus xóa pending/bỏ guard nhưng không hủy action đã nhận/cooldown/gravity/địch; Resume không tái kích hoạt nút đang giữ. Quy tắc tường từng hurtbox của U02 giữ nguyên; không thêm kiếm va tường.

## Quyết định phải review trước khi viết phần phụ thuộc

Các dòng sau là **đề xuất hợp đồng, chưa phải luật đã duyệt**. Không âm thầm điền thông số còn thiếu.

| ID | Điểm chưa đủ rõ | Đề xuất để review / phần bị chặn |
|---|---|---|
| R1 | TTL/grace đúng.15 và những state nhận attack buffer | Đề xuất khoảng nửa mở, đúng deadline hết; edge mới đúng action-end có thể nối ngay. Kiểm riêng end−.15/end+.15. Chốt bảng accept/queue/reject khi đang attack/skill/dodge/guard/CC/Feint, không tự suy mọi state đều nhận buffer. Phần combo trước A, state tương lai trước B/C |
| R2 | Event cùng timestamp: admission/defense/hit | Batch server có cutoff; resolve phần quá khứ trước mutation, không nhận lệnh vào timestamp đã đóng. Đề xuất queue intent tới boundary world kế tiếp, ghi riêng receive/accept; không backdate. Priority chỉ giữa commands cùng chủ thể; cross-subject dùng timestamp/ID/event ổn định, không mặc định mọi guard thắng hit. Phải chốt bằng trace micro-scenarios trước adapter A/B |
| R3 | Buffer có rồi một update vượt action-end/active đòn sau | Chuyển ở deadline được lịch simulation xác nhận; chỉ dùng intent/aim history hợp lệ lúc đó, clip sweep từng action; không lấy aim ở Now cho active quá khứ. Nếu không đủ history, dừng thiết kế để review, không bỏ hit hoặc nới timing |
| R4 | Chi tiết hướng guard/dodge và biên | Guard cập nhật yaw aim theo timeline server, kiểm ±60° tại hit; đề xuất biên góc tính hợp lệ. Dodge camera-relative hướng input nhận lúc accept, không input thì lùi theo yaw aim. Cần duyệt vector tham chiếu khi thân/camera lệch180°, origin/direction hit dùng cho guard |
| R5 | Dodge sát vực, dốc/góc và interruption | Chốt ground probe/step/slope dùng nền U01, điểm dừng an toàn và chính sách phần chuyển động đã đi khi CC/death/mất nền; không snap đủ3m hoặc hoàn lượt. Không tự thêm grace vực/miễn damage |
| R6 | Defense/contact/RNG/CC đồng thời | Đề xuất contact hợp lệ consume dedup đúng một lần kể cả parry/block; parry không roll crit, block roll một lần. Đỡ hit cuối25→0 vẫn giảm70% rồi break; hard-CC immune vẫn break posture nhưng không khóa. Chốt thứ tự defense→damage/shield→death→Interrupt/CC và xử lý chính event gây lethal trước B |
| R7 | Thông số CC thử và hình học quái | Description chưa định nghĩa width/height hurt/query quái hoặc nguồn gây slow/stun để test toàn bộCC. Chỉ fixture CC có nhãn, không tự thêm skill gameplay; reviewer duyệt kích thước quái/telegraph phù hợp tầm2m trước C |
| R8 | Thắng/thua/retry và save | Đề xuất sân thử người chơi–một quái, thắng khi quái chết/thua khi player chết; cùng batch cả hai chết báo kết quả riêng đã chốt thứ tự, không suy luật đấu trường. Retry authority reset cả hai/cost-CD-charge-posture-CC/AI/target/history epoch, tăng life. Chỉ settings được lưu, không persist combat/reward; cần duyệt trước C/D |

Không cần người dùng chốt lại số60/70/90 hoặc cửa sổ đã ghi trong Description. R1–R8 phải được đánh dấu quyết định trong hợp đồng A hoặc checkpoint trước B/C tương ứng; còn mở thì chỉ dừng phần phụ thuộc. Không lấy việc kế hoạch được nhận là quyền tự quyết mọi dòng mở.

## Thiết kế dự kiến và ranh giới tích hợp

- Giữ model thuần/clock/RNG kiểm soát và một resolver authority/world. Registry định nghĩa C++ giới hạn Attack1–3/Q/E/quái; Blueprint chỉ asset/UI, không override luật instance.
- Definition ID/version immutable gắn **action ID**, không đọc raw damage/timing của action hiện tại khi resolve candidate cũ. Vital hiện hard-code60 phải được nối đúng payload authority, không cho client gửi damage. Snapshot thêm action kind/phase/deadlines, combo/pending, energy/CD/charge/guard/posture/CC/outcome cần trình bày.
- Timer/resource/defense history cần đủ để trả lời timestamp hit; expiry tại endpoint không được làm mất shield/parry/CC trạng thái trước đó. Death/Interrupt invalidate hit chưa phát theo cutoff; effect đã phát theo luật riêng, không rewind clock model.
- Dispatcher thống nhất accepted/rejected/queued/replaced/expired; command/session/life chống replay. Attack/aim bind current action; pending cũng có identity/life và expiry. Không dùng thứ tự Tick/TSet/overlap/pointer để phân xử.
- Guard là movement mode/policy200, dodge là chuyển động collision-limited trong motor được saved-move bảo vệ; không dịch capsule bằng montage/root motion. Combat lock không ghi release gate WASD; hard lock/menu vẫn có rearm đúng luật.
- Tách tối thiểu truy cập identity/feet/aim/vital/action source hiện cast player/dummy để có quái ACharacter tốc độ300 server-only. Không dùng ProbeSpeed fixture, không thay pawn/motor player hoặc tạo hệ ability cho nghề tương lai.
- Rebind mở rộng save schema versioned: attack/guard/dodge/X/Q/E/Tab nhận phím đơn/nút chuột, không wheel/chord; camera/Escape cố định; R/F/1–4/I/K/M giữ reserved. Migration chỉ fallback binding xung đột, báo rõ, không autosave khi load. Combat runtime không lưu thành progression.

## Đợt A — Combo, dispatcher, năng lượng/cooldown (U03.01/.02)

Từ main U02 đã khép, nhánh `u03/a-combo-resource` sau khi kế hoạch được duyệt. Checkpoint A.0 chốt CONTRACTS/TEST-MATRIX/ASSETS/R1–R3 và model thuần trước runtime; không triển khai dodge/guard/Q/E gameplay sớm. A.1 tích hợp ba attack, buffer, scheduler, snapshots và blockout tối thiểu riêng từng đòn để input thật đọc được; energy/CD dùng API fixture cho tới C, không gán skill chưa có.

Kiểm: phase từng đòn và±mốc; TTL/thay pending/new edge/held không loop; combo220/1,45s khi nối ngay; hết grace trở lại1; ba vòng raw660, dummy600 chết hit9 (HP damage cap600, không gọi660 là HP mất); skip nhiều boundary không sinh đòn ngoài một slot; cancel thật startup, reject active/recovery sai quyền; menu/focus/reset/life/old commands; WASD recovery/camera/yaw; snapshot/definition cũ không dùng damage đòn mới. Dedicated Editor+hai client hồi quy action mới, Windows smoke nội dung A. Cổng: mọi R1–R3 đã chốt, clock/identity/authority/pending không nhập nhằng, source/binary/input bằng chứng khớp. Commit/push/báo cáo rồi dừng review A.

## Đợt B — Dodge, guard/parry, posture, CC/X (U03.03/.04/.08)

Chỉ từ A đã nghiệm thu/merge theo lệnh; nhánh `u03/b-defense`. Chốt R4–R6, tích hợp Shift/RMB/X, charges hồi tuần tự, historical defense, posture/CC, quyền hủy và replication. Fixture cung cấp CC/attack tags, không tự tạo skill bắt/boss.

Kiểm: dodge3m/.25, lock.35, reopen.60, recharge2s tuần tự, buffer.15 hợp lệ; tường/người/góc/dốc/vực/teleport, không i-frame; guard speed200/no jump/sprint; góc120 và deadline; parry0/.119/.120, cooldown.599/.600, release+press/hold một lần; multi-hit/sources chỉ một parry, attack không parry được vẫn block; hit25→0, break.8, posture regen sau2s; CC replace/2s cap/2s immune/.50 reset, X30/1s và damage vẫn nhận; slow mạnh nhất. Test hit lịch sử trong frame dài với guard/parry/expiry/death/Interrupt cutoff, đảo collection order. Windows input + server/two-client defense/movement/presentation, hồi quy U00–A. Dừng review B.

## Đợt C — Q/E, quái tham chiếu, Tab và vòng sân thử (U03.05/.09)

Từ B đã nghiệm thu; nhánh `u03/c-skills-enemy`. Chốt R7/R8. Q/E dùng cùng scheduler/collision/vital; state machine AI tối thiểu detect/chase/windup/active/recovery/return/defeated. Tab chỉ thông tin, không aim assist.

Kiểm: Q/E đúng damage/timing/cost/CD; energy không đủ reject không tiêu/CD; recovery-cancel attack hợp lệ, không hủy lẫn nhau; Q Feint trước/đúng active, khóa.20/sprint/jump, reopen1s, không refund; E chỉ direct/unblocked/unparried hit mới Interrupt đúng startup, không stun; energy regen sau1s theo timestamp. Quái LOS10/leash15/return.5, tốc độ300,1,50s cycle và active collision, return hủy hit/resetHP/quyền nhận thưởng fixture, không tái chase sớm; không damage sau death. Tab20/30, screen/camera LOS, tie distance/ID, occlusion1s/reset khi thấy lại, dead/new-life bỏ ngay. Retry cả hai và event/session cũ; Windows+hai client nhận cùng skill/AI/HP/outcome, không AI client tự quyết. Dừng review C.

## Đợt D — Tích hợp trình bày, controls/save và sân thử (U03.06/.07)

Từ C đã nghiệm thu; nhánh `u03/d-integration`. Hoàn thiện blockout attack1–3/Q/E/dodge/guard/parry/CC, grip/carry/locomotion; tín hiệu ngoài màu, âm parry hai nốt và nhãn riêng hit/block/parry/miss/break/Feint/Interrupt; HUD phím thật/resource/cooldown, HP target chỉ khi nhìn thấy, feedback1,2s. Không để art thay luật hoặc root motion dịch motor. Phần trước D đã có presentation tối thiểu để nghiệm thu runtime từng đợt, không dồn toàn bộ kiểm animation tới cuối.

Rebind/save/load migration, conflict/reserved/chuột/chord/IME, giữ phím qua menu/Resume, file hỏng/old version/không autosave khi load. Package mới cook đủ ba map/assets, smoke3/3, Boot–Quit/reopen input thật; full Automation tên/số thực, input/video đúng wall time; dedicated server0LocalPlayer/hai client đúng owner, late snapshot/reset/disconnect/duplicate/stale/outcome đồng thuận. Giữ profile60/60/30 đã đo, không gọi internal50% là1080p sản phẩm; hiệu năng đầy đủ thuộc U04. Bàn giao .cmd/Stop/checklist ngắn, source/hash/log/video/manifest/ma trận closure. Dừng READY_FOR_REVIEW U03, không tự merge hoặc bắt đầu U04.

## Bằng chứng và quy trình cho mọi đợt

Trước mỗi đợt kiểm repo/branch/remote/config riêng thực, từ main đã nghiệm thu → nhánh riêng → triển khai/kiểm chứng → commit/push/xác minh remote → báo cáo/dừng. Không tự merge hoặc bắt đầu đợt sau. Giữ Editor gốc và nội dung chưa lưu; header/reflection full build clone, Live Coding chỉ khi phù hợp và phải có log hoàn tất. Không tải source engine/tạo Server target trong phạm vi này.

Tests model không thay input Windows thật; native world fixture không thay ba process; bước1/30–1/120 không phải FPS render đã đo. Test liên quan mỗi đợt, full regression ở tích hợp D; snapshot/asset/source đổi thì bằng chứng cũ là lịch sử. Không chốt số tests trước. Log run/UTC/PID/executable/world/netmode/owner/roles/source/binary/package SHA-256, command/action/hit/life/definition, receive/accept/gameplay times và lý do reject. Giữ failed runs/warnings, không dùng trigger-success hoặc zero tests làm PASS.

Mỗi đợt có smoke packaged nội dung mới và hồi quy server/hai client như ROADMAP yêu cầu. D full package/smoke/integration; không build/package lại chỉ vì sửa báo cáo. Capture foreground/PID/hash/IME guards giữ nguyên; video ghi clock origin và frame timestamps từ lúc bắt đầu, không lẫn run-start có prepare hoặc tăng tốc. Stop chỉ session-owned process và khôi phục Editor theo identity. Checklist người dùng chỉ cảm giác/độ đọc/pose/movement/focus khi bản chơi được, AI tự hoàn tất phép kiểm kỹ thuật trước.

## Điều kiện bắt đầu

Review kế hoạch này, đặc biệt R1–R3 và lịch event ở hit/defense; sau đó người dùng giao riêng U03-A. R4–R8 có thể chốt ở checkpoint phụ thuộc đã nêu nhưng không để AI tự đoán khi code. **Hiện chưa có source, asset, gameplay, build hoặc test U03 nào được triển khai.**
