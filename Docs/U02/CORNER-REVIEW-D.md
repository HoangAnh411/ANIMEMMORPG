# U02-D — xác minh góc tường (bổ sung review)

Giữ lịch sử handoff `a0c6224`, source `3a63edd`. D chưa nghiệm thu; không merge hoặc bắt đầu damage E. Không đổi luật hộp đánh, nearest point, che khuất từng hurtbox, dedup hoặc quỹ đạo mesh kiếm.

## Action gốc và phép đối chiếu độc lập

Đọc log `Review-20261106-125757`: action66 của source `9CCBE9A14402196C6C5B79AE5C0AB506:2`, target `6FEADC494323CF272968718B5926A5DC:1`, confirmed hurtbox body ID1 tại gameplay time `160.22657531758537`. Query cùng action ghi cả body/head visible. Đây là tình huống tái dựng có tọa độ rõ, **không khẳng định chính xác là action trong ảnh của người dùng**.

- Feet `(162.889, -9181.335, 2.150)` cm, yaw `90.720003351569176°`.
- Origin `(162.889, -9181.335, 92.150)`; body center `(150, -9000, 70)`, radius35.
- Nearest point body `(152.4632662973, -9034.6556283672, 74.2331715793)` cm.
- Tường1: min `(65,-9140,0)`, max `(85,-8980,220)`.
- Tường2 ngang: min `(65,-9140,0)`, max `(155,-9120,220)`.

Oracle độc lập dùng segment/AABB slab clipping với spatial bounds đóng, không gọi hàm visible hoặc triangle code của gameplay. Đoạn origin→nearest **không giao cả hai tường**. Tại mặt Y=-9140 đoạn ở X≈159.950975, mặt Y=-9120 ở X≈158.529407: đều nằm ngoài mép X=155 của tường ngang. Head cũng thông. Hộp query giao hurtbox nên body hit là hợp lệ theo luật đã chốt, dù hộp chồng lên tường.

Chuyển feet attacker sang X=120, giữ Y/Z: đoạn đi qua X≈126.838448 và X≈130.147241 ở hai mặt ngang, nằm trong tường. Body/head đều phải bị chặn. Tests đối chiếu oracle với polygon obstruction; tiếp xúc đúng mặt/cạnh được tính block. Kích thước hộp, hurtbox và tolerance giữ nguyên.

**Kết luận hình học: không phát hiện lỗi quyết định hit ở action66. Không sửa thuật toán gameplay.** Phần thay đổi native chỉ phục vụ fixture và diagnostics.

## Debug một action

`U02DebugAction 0` trong lab chọn action tiếp theo của local authority pawn. Có thể chọn sequence cụ thể bằng `U02DebugAction N` trước khi query của action đó chạy; không rewind/replay action lịch sử. Identity lưu đủ pawn/life/action, không chỉ sequence. Dữ liệu query giữ lại sau khi đòn kết thúc. Khi chọn action khác, bản ghi cũ được xóa; không vẽ thêm debug tạm 0,5s của các action khác khi chế độ chọn đang bật.

Hình cyan là hộp feet-based; sphere màu theo kết quả, magenta là origin feet+90; vàng là nearest point. Xanh lá `CONFIRMED`, vàng `VALID` (hình học hợp lệ nhưng không thêm hit do cùng target/action), đỏ `BLOCKED` và dấu wall-block, xám `OUTSIDE`. HUD hiển thị full source/life/action và số hits của riêng action, tách bộ đếm cộng dồn. Target prefix/hurtbox ID trên hình được ánh xạ tới target full ID trong SELECTED.log/CASE-ACTIONS.json. Nét diagnostics ở lớp foreground để đọc được đường nằm sau bề mặt; không có nghĩa đường đó xuyên tường hợp lệ. Điểm và tên component tường chặn được ghi log.

`U02CornerCase open` đặt fixture theo tọa độ action66 và tự chọn action kế. `blocked` đặt X120; `outside` đặt X400 trên sàn để target ngoài query. Chỉ hoạt động trong CharacterCombatLab, authority, ngoài action. Đây là lab fixture, không phải gameplay teleport/reset. `U01FixtureReset CombatD3` cùng `U02DebugAction 0` dùng kiểm body che/head hợp lệ.

## Kiểm chứng

Các tests mới: CornerReviewAction66IndependentGeometry và CornerReviewWorldOrderAndStepMatrix. Bao phủ oracle độc lập, face/edge contact đóng, hai thứ tự collider × 30/60/120 Hz/bước0,5s × mở/bị chặn; mỗi target vẫn chỉ một body confirmation dù cả hai hurtbox hợp lệ. Các tests D cũ tiếp tục kiểm partial wall, cả body/head bị chặn, relative motion và dedup.

Lượt fixture đầu thất bại ở bước0,5s do teleport setup chưa có cặp snapshot liên tục trước attack; đã cho fixture thiết lập snapshot sau teleport, không bỏ guard continuity. Lượt runtime đầu ba case mở/chặn/head đạt, case OUTSIDE đặt ngoài sàn nên attack bị reject airborne; đã sửa vị trí fixture trên sàn. Lượt đầu ảnh đường bị mặt tường che; chuyển depth vẽ diagnostics, không sửa obstruction. Tất cả failed runs được giữ.

Kết quả và hashes của binary/debug cuối được ghi trong `Evidence/D-Corner`. Hình/video là bằng chứng trình bày đã chọn action; deadline/geometry dựa trên native trace và tests. Hình kiếm chưa có cơ chế va/bật/ngắt theo quỹ đạo với môi trường; không triển khai damage E.

## Bàn giao bổ sung — READY_FOR_REVIEW

Source kiểm chứng mới **`82bb890e108490692a5ff16cecc930c4807fb69d`**. Full Editor/Game build `Build-20261106-131741-019-792fb12e` thành công. MCP `MCPTests-20261106-131917` có **50/50 Success**, kết thúc queue50. Package `Package-20261106-132004-482-1b6ee417` UAT exit0/BUILD SUCCESSFUL; smoke `SmokeB-20261106-132307` **3/3**. Không dùng lượt build/test cũ làm kết quả của source mới. Sau đó chỉ sửa capture/seal/docs, không thay native/content/config.

Input riêng `Corner/Play-Verified`: **23/23 assertions**, bốn action độc lập. Source pawn tái dựng `9D3A76DC4933EE36E1236FAAB5FFA393`: life3/action1 mở góc có1 hit body; life4/action1 cả hai blocked có0; life5/action1 partial có1 head; life6/action1 OUTSIDE có0. Không dùng sequence1 mà bỏ qua life ID để trộn kết quả. [Ánh xạ IDs](Evidence/D-Corner/CASE-ACTIONS.json), [selected/confirmed trace](Evidence/D-Corner/SELECTED.log), [runtime assertions](Evidence/D-Corner/RUNTIME-ASSERTIONS.json).

| Case | Kết luận và ảnh riêng |
|---|---|
| Action66Open | [Body CONFIRMED, head VALID, action hits1](Evidence/D-Corner/Action66Open.png) |
| AllBlocked | [Body/head BLOCKED, tường/điểm chặn, action hits0](Evidence/D-Corner/AllBlocked.png) |
| PartialHead | [Body BLOCKED, head CONFIRMED, action hits1](Evidence/D-Corner/PartialHead.png) |
| Outside | [Hurtbox OUTSIDE, action hits0](Evidence/D-Corner/Outside.png) |

[Sơ đồ độc lập nhìn từ trên](Evidence/D-Corner/Independent-TopView.svg), [oracle số liệu](Evidence/D-Corner/INDEPENDENT.json), [trích action66 gốc](Evidence/D-Corner/ORIGINAL-ACTION66.log). Raw log review được nén giữ kèm hash trong lịch sử để truy vết nguồn tọa độ.

[Video](Evidence/D-Corner/Input-D.mp4): 43,2667 giây, khoảng acquisition43,2360 giây;35 frame capture thực, giữ frame theo timestamp trong CFR30. Không tăng tốc, không nội suy chuyển động giả; video thưa nên không dùng để đánh giá độ mượt hoặc suy thời điểm hit chính xác. Thời gian xử lý encoder sau frame cuối được ghi riêng. Lượt trước bị assertion video chặn vì lẫn thời gian encoder vào capture horizon; đã sửa harness, giữ failed metadata/log. Screenshot có acquisition window (mốc trên ghi sau screenshot và wait), không giả định timestamp pixel chính xác; hình được liên kết bằng action ID hiển thị và native trace. Không chạy smoke đồng thời với phiên capture được bàn giao cuối.

Editor DLL SHA-256 `2f3d6d2754120636e4520601767bc0167ab6065d1e577e312326ebc9c96b51d4`; packaged Game SHA-256 `5381af2f6de5f0a7bdfd51705090f0325399bc0e006b950beac207889a5bb60e`. [Manifest](Evidence/D-Corner/MANIFEST.json), [48 package hashes](Evidence/D-Corner/PACKAGE.csv), [evidence hashes](Evidence/D-Corner/EVIDENCE-SHA256.json). Launcher hiện trỏ package này, đã kiểm actual source/Game world/owner và Stop theo session identity. Config riêng giữ nguyên prefix baseline; không stage/in token. Editor gốc PID2444 không bị đóng/restart, không tuyên bố đã nạp layout debug mới.

Giữ D **READY_FOR_REVIEW**; reviewer quyết định nghiệm thu. Không merge D hoặc bắt đầu E. Không cần người dùng kiểm lại cảm giác chơi vì không đổi luật/motor/animation; bằng chứng debug và sơ đồ đã đủ để review đường kiểm, nhưng không khẳng định action trong ảnh ban đầu chính là action66.
