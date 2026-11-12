# U03-B1 — ma trận kiểm chứng

| Nhóm | Kiểm chứng |
|---|---|
| Model deadline/charges |0,25/0,35/0,60/2/4; hồi tuần tự không reset; không tiêu energy; update dài|
| Buffer |TTL0,15, replacement, exact expiry, hai lượt cạn không buffer; menu/focus/reset clear; hold không lặp|
| Replacement/priority |hủy startup sau kiểm điều kiện; exact active-start từ chối; cùng timestamp né trước đánh sau old-world barrier|
| Motor |300cm±5 trên nền trống; capsule sweep tường/người/góc; nền/step45cm/dốc45°/vực; mất nền thật chuyển Falling; slow không đổi né|
| Lifecycle |death/reset/lost-ground/landing, stale life/duplicate/nonfinite/ownership; saved move không tái tạo action/lượt hoặc jump cũ|
| Regression |U00–A1 phù hợp, collision/dedup/cutoff/whole-active/update dài, camera/gravity/gate/WASD/motor500/700|
| Package/input |Editor/Game cold build, Windows package/cook/smoke3map; physical Shift/WASD/no-direction, held, startup cancel, wall/cliff, menu/focus/Resume; video wall-time|
| Network |dedicated Editor+2clients: authority/admission/charges/position, peer presentation, duplicate/stale/ownership/reconnect; cvar thực và placement ready/Stop|

Kết quả thực, giới hạn và failed runs ghi trong REPORT-B1. Tài liệu này không tự xác nhận PASS hoặc ACCEPTED; A1/A0 nghiệm thu là nền kế thừa, không thay bằng chứng B1.

Bàn giao b2c9676/source6603c30 có90/90 tests và các cổng input/network hợp lệ cho các ca đã kiểm, nhưng **NOT ACCEPTED** vì thiếu consistency tại timestamp giữa bước; [review](REVIEW-B1-b2c9676.md). Giữ nguyên bằng chứng lịch sử.

R1 source3fd6c3d thêm `RetainedWallSlideAndStepPrefixes`, `IncomingMidWallAndStepLethal`, `SimultaneousPawnCCD`:93/93 Success,0 Failed, queue93 hoàn tất, build Editor/Game/package và smoke3/3 mới. Input/video38+17 mới. Trace phải kiểm actual pose tại incoming hit giữa wall/StepUp, lethal cutoff và long/short update; pawn CCD đối đầu/cùng hướng và đảo collection. Network/reconnect R1 ghi kết quả cuối trong [REPORT-B1](REPORT-B1.md). Chưa tự ACCEPTED/merge/B2.


## B1 technical acceptance and closure

The user confirmed **ACCEPTED (technical)** at `4a8b7e82c10b16c31a89bb0a0c25ce06019b6cc4`, verified source `3fd6c3d82e3c85a1eda6be8d35961c863019d4f7`, and authorized documentation closure, branch commit/push and fast-forward/push of main. Earlier READY_FOR_REVIEW/no-merge statements remain historical. See [acceptance](ACCEPTANCE-B1.md).

Scope: U03-B1 dodge and motor integration only. Animation/presentation remain blockout; product visual quality is not accepted. Preserve all original B1/B1-R1 evidence, warnings, failed/invalid runs and the earlier NOT ACCEPTED review. This closure changes documentation only; no source/assets/config changes, no new builds/tests or Editor operations. Stop after merging B1; B2 has not been assigned.
