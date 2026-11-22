# Counter, reset và giới hạn bằng chứng Build-03

Source pin: 13b4f34f07bd1cb8e7402984d9479fd5eb9fe2e7. `U04C1Profile.cpp` export summary và frames tại end; các điểm tăng dưới đây trong `U02CollisionWorld.cpp` chỉ tăng khi C1Profile.Active. Đơn vị là số lần trong cửa sổ, không phải tổng qua nhiều process. Registration là gauge tại hai biên.

|Trường|Đơn vị và điểm tăng/source|Đối chứng và điều kiện|
|---|---|---|
|registeredSubjects / registeredHurtboxes|Số life identity duy nhất / component còn hợp lệ trong Hurts; Profile:31–35|Hai biên bằng nhau; fixture N+1 subject, N×H+2 hurtbox. Hai component attacker Body/Head stable1/2: U01Character:198–201. Targets export N GUID riêng, mỗi target H ID. Không có danh sách identity registration hai biên: source/aggregate, chưa chứng minh từng thành phần động.|
|collectIntervals|Mỗi entry CollectHitCandidates, trước lookup Source; CollisionWorld:267|Không áp số interval cố định hoặc bằng N. >0 với một action. Source lookup thất bại có thể tăng interval mà không duyệt hurtbox; các công thức bên dưới có điều kiện fixture ổn định.|
|hurtboxVisits|Mỗi entry vòng Hurts trước mọi filter; :271|Trong fixture đã settle, source sống và topology giữ nguyên: interval × (N×H+2). Attacker vẫn bị duyệt nhưng bị bỏ ở self filter trước geometry. Nếu dữ liệu đầy đủ mà không khớp: FAIL công thức fixture, giữ raw để review giả định.|
|geometryTests|Ngay trước SphereAttackContact sau eligibility/continuity filter; :303–304|Trong fixture đứng yên, đúng source/life, đã settle 2 giây và không death: interval × N×H. Không mặc định bằng N×H cho toàn action. |
|queriesPostContactDelta|Queries chỉ ++ sau Range.bHit; :305|begin giữ QueriesBegin; summary xuất chênh lệch. Trong vùng fixture box mở: bằng geometry; ngoài vùng: 0. Metrics prepared/after cung cấp geometryQueries cumulative để đối chiếu delta độc lập với summary. Không gọi đây là tổng query/visit.|
|candidates|Mỗi Out.Add sau contact, FirstVisible và kiểm timestamp; :328–329|confirmed ≤ candidates ≤ QueriesDelta ≤ geometry ≤ visits. Không đặt candidates=N vì recollect/barrier và H làm thay đổi số quan sát.|
|confirmedHits|Sau DamageResults.Add và Confirmed.Add; :378–382|Bằng số damageEvents thực, trong vùng N, ngoài vùng 0. Mỗi identity action/source life/target life chỉ một damage60 và đúng HP đích. Metrics damageResults delta đối chiếu slice sản phẩm.|
|duplicateSuppression|ResolveHit entry nếu HasResolvedHit (:346), hoặc CollectCurrent RemoveAll từ chối CanResolveHit và HasResolvedHit (:454)|Đếm **quan sát** identity đã resolve, không phải số identity hoặc H−1. Kiểm số nguyên ≥0, monotonic, khớp CSV cuối. Không có ledger quan sát độc lập để tái dựng chính xác tổng; giữ giới hạn aggregate. Không gọi H=3 PASS chỉ vì suppression tăng.|
|occlusionCalls|Mỗi Unobstructed entry (:249), trước xử lý visibility|FirstVisible (:307; CollisionGeometry:110–145) có thể gọi callback nhiều lần; mỗi candidate thành công cần ≥1 call. HUD (:729–740) cũng gọi từng hurtbox của HUDTarget; `Visible |=` không short-circuit. Chỉ kiểm occlusion≥candidates, monotonic và khớp frame cuối. Ngoài vùng không ép 0; không suy count bằng N hoặc Queries. Không xuất origin ledger.|
|actions|Event kind ActionStarted trong capture active; Profile:179–183|Đúng một event Attack1 (definition0/version1/raw60), đúng PID/world/run/source/pawn/controller/localRole3, GUID/life/sequence mới. Action wall nằm trong start/end; gameplay start nằm sau prepared, trong frame capture; damage.at nằm trong activeStart/activeEnd của action đó.|

Damage linkage dùng `U02CombatComponent.cpp:362–379,410–419` và Profile:143–150: action pawnId/life/action → damage source/sourceLife/action → target subject/life/stableHurtboxIds. Event sai action/life với dữ liệu đầy đủ là FAIL. Thiếu trường làm đứt liên kết là INVALID, không PASS từ tổng counter. In: đúng một damage60/target, beforeHP1.000.000→afterHP999.940; out: không event, HP1.000.000. Mọi target sống, shield0, crit/death false, absorbed0. HP1.000.000 ban đầu do prepare source (:38) xác lập, không phải snapshot target trước input.

## Reset và cô lập

|Điểm|Đối chiếu source|Mức chứng minh đợt này / runtime dự kiến|
|---|---|---|
|Reset ở begin|Profile:113–118: inactive, !Closed, Subjects có giá trị; reserve, DamageBegin=DamageResults.Num, QueriesBegin=Queries, registrationBegin; C1Profile=FCounters{} rồi Enabled/Active=true và Start|Source đọc; replay tổng hợp dùng cumulative cũ17/29 và delta mới. Chưa có runtime counter. Không giả mạo rằng đã reset native thực nghiệm.|
|Slice DamageResults / Queries|Profile:115,127,143: export từ DamageBegin đến Num, Queries−QueriesBegin; không xóa vector/cumulative|Source + metrics prepared/after đối chứng. Không có marker index native xuất trực tiếp. Prepared nằm trước begin, không có action giữa; nếu ngoại lai gây event thì validator từ chối action/delta.|
|Active|Profile:73–80 chỉ sample active; Event:181 chỉ ghi/increment active; CollisionWorld điểm tăng có guard|Replay từ chối old frame/action trước biên. Chưa kiểm native thực nghiệm.|
|Closed|Profile:85,113,124; prepare/begin đòi !Closed; end đặt Active=false, Closed=true|Source only. **Dynamic reopen INCOMPLETE**: không có marker/lệnh phản hồi đủ quan sát; không gửi begin lần hai hoặc thêm process thử.|
|Capture theo UWorld|Profile:60 TMap UWorld*, BeginWorld:166–175 tạo capture/delegate, EndWorld:177 remove delegate/map; subsystem counter theo world|Source only; offline wrong-world INVALID. **Hai world đồng thời INCOMPLETE**, chưa có experiment/export đủ để tuyên bố cách ly động.|
|Giữa process/run|Entry từ chối ID/path đã tồn tại trước Backend; mỗi process output mới Raw rỗng trước prepare/begin; argv absolute output/log/userDir, original/query FILETIME và journal; capture hashes|Replay stale ID/output/log, PID/world sai đều INVALID; không launch thật. CC-B phải mỗi ô process/thư mục riêng, xác minh stop trước ô kế. Chứng minh thực nghiệm giữa process vẫn NOT_RUN.|

## Quy tắc verdict

- **PASS**: mọi assertion có export và các điều kiện fixture đã nêu khớp; luôn kèm evidenceLimits. Chưa đồng nghĩa counter correctness được reviewer nghiệm thu.
- **FAIL**: bằng chứng đủ và đúng identity/profile/cửa sổ nhưng gameplay/counter trái kỳ vọng (damage, HP, số hit, registration hoặc công thức fixture).
- **INVALID**: thiếu/mixed/malformed evidence, frame rỗng/gap/focus mất, sai PID/world/run/profile, action ngoài capture, freshness/hash sai, guard thất bại hoặc stop không có marker boolean true. INVALID ưu tiên khi cả hai loại lỗi xuất hiện.
- Stop chỉ được PASS khi outer lifecycle nhận identityVerifiedAtStop **is True**; metadata OSError vẫn dừng đúng original handle và giữ processExited/wait, nhưng verdict INVALID. Không có keyboard cleanup sau lỗi.

Counter aggregate/frame matching chỉ chứng minh sự nhất quán các export, không thay thế event/HP. Không suy một hàm là bottleneck từ call count; CC-A không có timing/GPU/memory baseline.
