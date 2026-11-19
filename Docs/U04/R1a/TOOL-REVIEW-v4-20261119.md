# R1a — phân loại rejection và completion, chờ review lại

**TOOL_ONLY_REVIEW_PENDING. R1a chưa ACCEPTED toàn bộ; B vẫn INCOMPLETE. Không rebuild native, chạy UE/gameplay, R1b hoặc merge.**

Baseline `2b93a0f8f4f70fa69c248d8b7acacea1e2e23bdb`; native vẫn `8cbcb6a6d6dfc4e29bff8731a6aaab187f887cb4`. Candidate analyzer mới: **u04r1-entry-4**. Bản input và luật runtime không đổi.

## Lỗi và sửa thứ tự gate

Bản entry-3 yêu cầu terminal trajectory trước khi xét admission result. Vì vậy Stale/rejection không có trajectory bị ghi INVALID dù input/precondition đã chứng minh. Entry-4 chia luồng:

1. Chứng minh edge → intent → receipt → admission, pawn/life/command, snapshot/yaw, vận tốc ngang `velocityBeforeBatch <=0.01 cm/s`; kiểm chất lượng native samples và serial đến admission. Thiếu/malformed/mơ hồ dữ liệu cần thiết vẫn INVALID.
2. Sau khi gate này đạt, authority không Accepted → **FAIL ngay tại admission**. Không đòi trajectory, endpoint, model của action mới hoặc capture kéo dài tới release deadline. Queued/Replaced cũng không phải immediate Accepted của single-Dodge fixture đã chuẩn bị. Snapshot/transport/model sai khi đã đủ bằng chứng cũng trả FAIL tại đây, không bị thiếu terminal che lại.
3. Chỉ admission Accepted mới đi tiếp sang trajectory. Terminal duy nhất có đủ identity/timestamp thì đo theo luật cũ. Terminal trùng hoặc correlation sai vẫn INVALID.

Failure tại admission giữ `failureEstablishedAt`, input/correlation và giới hạn native evidence đã kiểm; không tạo distance/duration/terminal giả. Cadence đi kèm là diagnostic của evidence window, không thể biến FAIL thành một lượt nghiệm thu PASS. Không thay clock collector-entry, cổng FPS, runtime deadline hoặc epsilon.

## Accepted nhưng không có terminal

Không tự đồng nhất “không tìm thấy event” với lỗi gameplay. Để kết luận không hoàn tất, phải có capture begin/end đóng, native sample/counter/clock/config/focus hợp lệ, serial không mất qua đoạn cần quan sát, và coverage tới `admission.at+0.35s` **cộng native sample kế tiếp**. Đây là allowance quan sát một frame, không sửa deadline0.35s.

Tại sample xác nhận, snapshot phải thuộc đúng pawn/life/command:

- Sequence không hề tiến từ receipt: **FAIL**, Accepted nhưng không có trajectory được quan sát trong capture đầy đủ.
- Đúng sequence/start nhưng còn `locked=true` quá deadline và frame allowance: **FAIL**, action chưa hoàn tất.
- Capture ngắn, mất frame/event, thiếu/malformed lock state, sequence/start mơ hồ: **INVALID**.
- State đã unlocked nhưng thiếu terminal: **INVALID do thiếu bằng chứng terminal**, không suy endpoint/duration từ vị trí muộn và không tự gán lỗi gameplay chưa được chứng minh.

Rejection không cần các bằng chứng completion này: kết quả authority đã đủ để xác nhận FAIL sau khi gate tới admission đạt. Thiếu dữ liệu/correlation tới admission vẫn INVALID dù admission result được ghi Stale.

## Synthetic và proof

**24 nhóm synthetic đạt**, gồm19 nhóm trước và các nhóm rejection không trajectory, rejection với dữ liệu thiếu/mơ hồ, Accepted không hoàn tất, thiếu completion telemetry và model sai không trajectory. Rejection integer/number nguyên1–9 được kiểm; unknown/malformed result không được suy thành rejection hợp lệ. Các tests mới kiểm:

- Stale + không trajectory + capture kết thúc ngay sau admission → FAIL.
- Accepted còn lock hoặc không tiến sequence trong capture đủ → FAIL.
- Capture ngắn, terminal event bị mất, frame thiếu, state thiếu, terminal mơ hồ hoặc unlocked không terminal → INVALID.
- Model sai dù không trajectory → FAIL khi precondition/correlation tới admission hợp lệ.

`CLASSIFICATION-PROBES.json` công bố8 bộ raw **synthetic**, expected và actual verdict, giúp reviewer tái hiện trực tiếp. Không coi synthetic là gameplay evidence.

Đã rehash **450 liên kết R1a cũ +11 liên kết tool supplement entry-3**, rồi tính lại từ gzip raw. **24/9/2/22 giữ nguyên; hai CSV giống từng byte; 0 nhãn lịch sử đổi.** Manifest cũ vẫn `dd45d73d734d6855923264681316e2110bc7f006abd342347fcdc3d6fcd75e9b`; supplement entry-3 vẫn `4ba3b8bb279badc7dee301d2ed1ea95aed3cf1208d35c536d92c8862bae814d7`. Audit chain bổ sung vẫn6 CHAIN_PASS/18 INVALID với scope riêng, không cấp nghiệm thu R1b.

## Hồ sơ

[Manifest entry-4](Evidence/ToolReview-v4-20261119/MANIFEST.json) giữ log24 nhóm,8 classification probes, patch, JSON/CSV tính lại và hash. Output host riêng: `Artifacts/U04/B-R1a/ToolReview-v4-Final-20261119`; output thử tool trước đó giữ nguyên. Không tác động `Artifacts/Reviewer-R1a-20261119`, Editor hoặc các artifact lịch sử.

Tái lập: `python Scripts/U04/ReviewDodgeAnalyzerR1.py --out <thư-mục-mới>`. Script chỉ chạy Python tests/hash/recompute, không UE/game/input/capture. Manifest R1b đề xuất trỏ entry-4 và vẫn **PROPOSED_NOT_AUTHORIZED**. Dừng để reviewer đánh giá lại; không tự ACCEPTED hoặc chạy batch.
