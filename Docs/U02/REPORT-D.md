> ACCEPTED: user technical acceptance at d0dd5b0 / verified source82bb890. See [ACCEPTANCE-D.md](ACCEPTANCE-D.md). Review-pending statements below are historical handoff text. No D rebuild/retest for closure.

> Current handoff: corner verification READY_FOR_REVIEW, source82bb890; see [CORNER-REVIEW-D.md](CORNER-REVIEW-D.md) and Evidence/D-Corner. Action66 is geometrically valid; no gameplay algorithm change. Original a0c6224/source3a63edd evidence below remains historical. No D acceptance, merge or E.

# U02-D — READY_FOR_REVIEW

Branch u02/d-collision-hurtbox-sweep from accepted C main 828f83f. C remote verified (Git ref and fresh storage containing 816 SHA-256 checked LFS objects), main fast-forward/push verified. No C rebuild/retest.

D is geometry-only: no HP, damage, shield, crit or death gameplay. Server world pre-actor boundary snapshots all sources/hurtboxes before any actor ticks. Every source advances; all candidates then sort and resolve globally. Before-action mutation drains the same world boundary; actor tick/collider registration order is not a tie-break.

Sphere hurtboxes have explicit stable IDs and subject/life identity. Registry exhaustive collection cannot miss fast targets absent from endpoint overlaps. Relative motion is linear between snapshots; attack axes locked yaw, feet-based center, half extents100/60/90. Piecewise quadratic sphere/box entry/exit clips to active interval; spatial roundoff tolerance1e-7cm never expands gameplay deadlines. Teleport (transform teleport flag), radius change and generation changes break continuity; only current active point may be queried.

Obstruction per hurtbox: origin feet+up90 to nearest sphere point. Visibility event partition includes ray/triangle edge and plane roots plus near-sphere quartic roots; tests include a narrow slit away from the interval midpoint. Retain full contact interval, so blocked first contact cannot discard later visibility. Initial solid containment and closed face touching block. Static box/convex polygon collision and available physics triangle geometry supported; non-polygon/ unavailable physics data are diagnosed and reject potential rays conservatively. Current lab solid shapes must all be supported; no acceptance claim for unvalidated future solid shape assets. Dynamic/nonlinear walls are outside U02 gates.

Original Editor remains open (PID2444). New reflection/layout was built/tested in the isolated D clone; original binary is not patched or restarted. Private config original bytes remain an identical prefix, only public collision-channel additions were staged via a token-free Git blob. No token was printed or staged. No new module/plugin/framework.

## Source và kết quả thực

Source kiểm chứng **`3a63edd886350622d80d7ef5bfba3eb546558b6e`**, nhánh riêng `u02/d-collision-hurtbox-sweep`. Main vẫn C ACCEPTED `828f83f7db118acd1f6fa0cd8fea674b20a2bbcd`. Không merge D hoặc bắt đầu E.

- Full build Editor/Game: `Build-20261106-123424-062-6eae3eb0`, cả hai Result: Succeeded. UE5.8.4 CL58902052; engine/toolchain, commands và raw log hashes tại [build results](Evidence/D/BUILD-RESULTS.json).
- MCP clone `MCPTests-20261106-123542`: **48/48 Success**, queue kết thúc 48 tests performed. U00/U01 và U02 A–C hồi quy; D thêm 8 tests: FeetBoxBoundaryAndRelativeSweep, VisibilityChangesInsideContactInterval, WorldWholeActiveCrossingAndDedup, WorldWallPartialHurtboxAndOrigin, WorldTargetsOrderingAndLifetime, WorldResetAndResolveRevalidation, GlobalBatchAcrossSources, ContainmentRoundedCornersAndStepRates. [Từng test](Evidence/D/AUTOMATION-RESULTS.json), [log MCP](Evidence/D/MCP-RESULTS.json).
- Package `Package-20261106-123643-657-81907530`: UAT BUILD SUCCESSFUL, exit0. Smoke `SmokeB-20261106-124640`: **3/3 map**, gồm Boot Quit, CharacterCombatLab và NetworkLab. [Smoke](Evidence/D/SMOKE.json).
- Input Windows thật `Play-Stations-Retry`: **36/36 assertions**, 1120 native samples, 5 confirmed geometry events. Giữ LMB chỉ một action; hai action tại multi-target cho 2+2 hits, tường kín0, body bị che/head hợp lệ1, góc tường0. Mỗi action/target/life chỉ một result; head ID2 được chọn ở partial wall; timestamp nằm đúng active, không damage. [Assertions](Evidence/D/RUNTIME-ASSERTIONS.json), [query/confirmed trace](Evidence/D/QUERY-TRACE.log), [input timeline](Evidence/D/INPUT.json).
- Launcher [Play-U02-D.cmd](../../Play-U02-D.cmd) đã kiểm 48 package files, source association, PID/executable/hash/world/owner và Stop đúng session. [Launcher evidence](Evidence/D/LAUNCHER.json). [Checklist](../../Play-U02-D-CHECKLIST.md) có lệnh fixture tới bốn trạm; không phải API gameplay sản phẩm.

## Collision và resolver

Hai slot trống đã đối chiếu config thực: ECC_GameTraceChannel1 là U02CombatCandidate (object/query, default Ignore), ECC_GameTraceChannel2 là U02CombatObstruction (trace, default Block). Capsule/mesh/kiếm/hurtbox ignore obstruction; hurtbox QueryOnly và ignore Pawn nên không thay movement. Collector duyệt registry toàn world thay vì endpoint overlap/single blocking sweep. [Config diff đã lọc](Evidence/D/COLLISION-CONFIG.diff).

Mỗi pawn có body sphere radius35, offset từ capsule center−26Z (ID1), head radius20/+49Z (ID2). Dummy body radius35 ở feet+70Z và head radius20 ở feet+145Z. Dummy có server FGuid và life generation, reset tăng generation; không có vital state. Tường xét từng hurtbox, không dùng dummy body làm obstruction cho target khác. [Fixture bố trí](Evidence/D/FIXTURES.json): base(0,−6000,0), bốn lane cách1000cm; target cách150cm, tường kín ở75cm, partial wall cao100cm, corner có hai khối vuông góc. Trạm chỉ thêm vào hai map lab; Boot không đổi, các trạm U01 giữ nguyên.

Scheduler chụp world trước actor tick, advance tất cả nguồn rồi sort một batch theo timestamp/source/event/hurtbox ID trước resolve. BeforeActionMutation drain old interval trước mutation. Death ở D chỉ có fixture ledger invalidation để chứng minh event sau bị loại; HP/death sản phẩm vẫn E. Confirmed delegate cho phép E áp vital synchronously trước event kế; không actor Tick/overlap callback tự trừ HP.

## Hình ảnh, hashes và giới hạn

[Video](Evidence/D/Input-D.mp4) dài19,0 giây so với19,0054 giây wall time; 57 frames capture thực được giữ theo timestamp trong CFR30, không tăng tốc. Capture thưa do đọc native metrics và gửi console fixture; không dùng video này làm bằng chứng render60FPS/biên0,16. AI đã xem khung hình trạm multi-target và partial wall; số hit và hurtbox thực được đối chiếu bằng logs. [Frames/timestamps](Evidence/D/FRAMES.json).

[Manifest](Evidence/D/MANIFEST.json), [48 file package hashes](Evidence/D/PACKAGE.csv), [evidence index](Evidence/D/EVIDENCE-SHA256.json).

- Editor DLL SHA-256: `d26dcc5aaa07b0365e13129f7a49a050f14a19e9fe475e643434391da57a28ef`.
- Packaged Game SHA-256: `31cf71b4a86f3ecd9a7e298ef7d46df960dab225a24023fac3c2bd64eb5f9cc3`.
- Hai map LFS đã tải từ remote vào storage riêng và tính lại SHA-256 khớp; [remote LFS record](Evidence/D/REMOTE-LFS.json).

Giới hạn kỹ thuật cần reviewer lưu ý: mô phỏng tuyến tính giữa hai snapshot server, không rewind/bù trễ hoặc tường động. Hurtbox D dùng sphere; không có arbitrary hurtbox shape. Môi trường hiện hỗ trợ box, convex tam giác và physics triangle data sẵn có; shape không hỗ trợ hoặc thiếu dữ liệu bị diagnostic và chặn bảo thủ, không âm thầm xuyên. Lab/package cuối không có unsupported obstruction trong samples đã review. Registry exhaustive và dựng polygon mỗi world boundary ưu tiên completeness cho lab, chưa tuyên bố hiệu năng production/MMO. Confirmed results là server-local diagnostics D, chưa replicated HP/results/network consensus F. Không mở PvP tự do; pawn target chỉ bật qua native fixture rõ ràng. User không phải nghiệm thu lại cảm giác C.

## Lịch sử lỗi giữ lại

Build đầu lỗi hằng DFlags trùng unity build, đã đổi tên. Các tests đầu phát hiện quaternion không đồng nhất, fixture khe hở không thông theo bề dày tường, builder brush của test world bị nhận nhầm collider. Đã chuẩn hóa trục, sửa fixture hình học, phân biệt builder brush/editor-only, trigger/physics medium và body gameplay thật. Package đầu phát hiện GameplayDebuggerRenderingComponent có bounds nhưng không physics body; đã yêu cầu physics body hợp lệ và thêm render-only fixture hồi quy. Lượt cuối48/48 đạt.

Author script lần đầu gọi Python is_a không có, đã sửa so class trước khi save map. Capture lần đầu geometry bị debugger chặn; lượt tiếp có2hits đúng nhưng verification chạy theo lịch nominal trước actual action finish, đã sửa scheduling theo operation thực, giữ gameplay0,40. Hậu xử lý gặp dòng metrics chưa ghi xong khi Stop; đã chỉ đọc complete log lines. Same-source package/build/tests được tái sử dụng cho các sửa harness. Clone INI được Engine normalize blank lines/token và Git CRLF stat; script chỉ áp sau semantic comparison, không đụng config riêng workspace.

[Failed runs/harness logs](Evidence/D/HISTORY.json), [warnings](Evidence/D/WARNINGS.json); lỗi/ensure/trigger không được tính PASS. Compiler preference/deprecation warnings được giữ nguyên. Chưa dùng Editor gốc làm bằng chứng layout D; full build không có nghĩa Editor gốc đã nạp layout mới.

**READY_FOR_REVIEW** là bàn giao để review kỹ thuật D, không phải nghiệm thu. Chưa damage E, chưa mạng F; không merge hoặc bắt đầu đợt sau.
