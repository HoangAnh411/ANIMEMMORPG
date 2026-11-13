# U03-C1 — ma trận kiểm chứng

Native/content source `dbe10dab1cd6a9b14c28c732aba66f21d525ac69`. [Manifest](Evidence/C1/MANIFEST.json), [report và failures](REPORT-C1.md). PASS là bằng chứng kỹ thuật đúng tầng, không nghiệm thu cảm giác.

Người dùng đã ACCEPTED về kỹ thuật tại bàn giao `db592ff` và cho phép khép tài liệu/fast-forward main; [hồ sơ nghiệm thu](ACCEPTANCE-C1.md). Giữ nguyên kết quả và bằng chứng, không chạy lại tests. Người dùng chưa chơi thử B2/C1; presentation vẫn blockout, chưa nghiệm thu feel/readability/art và chưa C2.

|Luật|Tầng và bằng chứng cuối|Trạng thái|
|---|---|---|
|Definition/raw/flags/version, active/recovery nửa mở|C1 InterruptEdgesAndCapturedEffects + BlockoutMontageAuthorityPolicy; trước/đúng/sau active-start/end/duration; world raw100/80|PASS|
|Energy100, cost20/25, CD4/6, delay1s/integral10/s/cap; đủ/thiếu/reject/no refund|C1 CooldownRegenAndResourceRejection, FeintEdgesResourcesAndLife; A0/A1 resource/dispatcher; actual input và snapshot ba process|PASS|
|Q/E nối recovery cả ba đòn, từ chối startup/active/lẫn nhau, reset combo/pending/no buffer|C1 RecoveryAndReplacementPermissions; input Recovery1/2/3; inherited combo/buffer rerun|PASS|
|Né/guard chỉ thay startup; validate replacement trước cutoff, zero charges/guard lock|C1 RecoveryAndReplacementPermissions + SequencePriorityAndRejectedReplacement; B2 permission tests; actual Shift/RMB hủy Q/E startup|PASS|
|Q edge Feint trước cast/CD, active-start đóng, held không lặp, min1s, lock.20|C1 FeintEdgesResourcesAndLife + SequencePriorityAndRejectedReplacement; real Q/Q, held Q và T/T sau rebind. Min1s có state-gate boundary test; CD Q4s vẫn ràng buộc cast|PASS|
|Feint walk/no sprint/jump, slow/CC/control policy, không stale jump; giữ WASD đi tiếp|Life/action-qualified real in-window samples; movement-independent E (resume+.0156826s); U01/B2 motor/control/slow/CC; separate Feint motor/saved-move guard|PASS kỹ thuật|
|E Interrupt startup normal/Q/E, exact active-start/active/recovery không pure Interrupt; không stun/refund, Q không Interrupt|C1 InterruptEdgesAndCapturedEffects, WorldSkillInterruptShieldDefenseDeath, actual outgoing/incoming E; hard CC/death giữ cutoff riêng|PASS|
|Block/parry chặn, full shield không miễn, lethal không effect, nhiều target/dedup|C1 WorldSkillInterruptShieldDefenseDeath + WorldEPerTargetDedup; actual E block/parry network và histories ba process|PASS|
|Long/short, collection đảo, successor startup, timestamp group/cutoff không rewind|C1 WorldIncomingEInSuccessorLongShort; Interrupt permutations; A0/A1/B2 causality rerun|PASS|
|Retained wall/slide/StepUp, incoming CC/death và hai pawn né|B1-R1 Game-world tests trong MCP181220; DodgeNetworkRegression18284622/22 trên binary C1|PASS|
|Menu/focus/Resume/rebind/held, reset/life, stale/duplicate/unowned RPC, reconnect|Input18165624/24; Network18240735/35 shared-dispatcher/ServerCombat negative probes/reset; reconnect2/2 có E CD trước disconnect. History chỉ trình bày|PASS|
|Ba process identity/definition/resources/CD/defense/damage/Interrupt/life|Dedicated Editor + ClientA/ClientB35 checks +10 độc lập; resource so tại timestamp authority, không gọi mẫu khác thời điểm là cùng state|PASS|
|Clip provenance, phase/cutoff cues ngoài màu, không notify/root-motion gameplay|C1-ASSET-PROVENANCE, ASSETS.csv; montage Automation + actual animation instance; video/text/world labels|PASS blockout|
|Editor/Game, toàn bộ U00–C1 Automation, package committed clone, smoke ba map|Build181045, MCP181220117 Success/0 Failed, Package181403, Smoke1815583/3; source/binary/package hashes|PASS|
|Launcher hash/profile/session/placement; private config|3 refusal guards, actual client60/server30 cvars, PID/exe/module/source/UserDir scoped stop; Editor restored và config byte hash unchanged|PASS|
|Cảm giác, readability/art/âm sản phẩm và người dùng chơi thử|Người dùng chưa chơi B2/C1; assertions/video không thay xác nhận|CHƯA NGHIỆM THU|

Game-world simultaneous-hit không phải input hai client đồng thời. Bước model1/30–1/120 không là FPS render. Xem từng Test Completed trong TEST-TRACES và hashes trong manifest; không dùng kết quả cũ làm bằng chứng binary mới. Không mở C2 hoặc khép U03.
