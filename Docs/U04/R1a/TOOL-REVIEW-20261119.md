# R1a — sửa analyzer admission và correlation, chờ review lại

**TOOL_ONLY_REVIEW_PENDING. B vẫn INCOMPLETE; R1a chưa ACCEPTED toàn bộ. Không rebuild native, chạy thêm gameplay/Automation UE, R1b hoặc merge.**

Baseline handoff là `e9a8264a0f94863001e13af319f7fcf0c379e314`; native vẫn `8cbcb6a6d6dfc4e29bff8731a6aaab187f887cb4`. Bản input đã review không đổi. Không tác động Editor hoặc thư mục `Artifacts/Reviewer-R1a-20261119`.

`AnalyzeR1.py` candidate **u04r1-entry-3** đã bỏ hoàn toàn vận tốc frame trước `dodgeStart` khỏi cổng đứng yên. Dữ liệu bắt buộc là `AuthorityAdmission.velocityBeforeBatch`, parse XYZ hữu hạn và kiểm `hypot(X,Y) <= 0.01 cm/s`. Không fallback về sample trước, vận tốc nhận receipt, cấu hình hay zero mặc định. Thiếu/malformed dữ liệu hoặc admission đang chuyển động trả INVALID.

## Chuỗi bằng chứng bắt buộc

`dodge_chain` dùng chung bởi đường `dodge()` production analyzer và synthetic tests:

1. Đúng một Dodge intent và receipt, command trùng; đúng một admission cho command đó. Native frame `pawnPath`/controller nối path của intent/edge với pawn GUID và life; receipt/admission/trajectory phải cùng GUID/life, lifeId nhất quán.
2. Thứ tự native `diagnosticSerial` phải tăng. Cạnh Dodge phải là cạnh mới, hợp lệ, cùng frame và ngay trước intent trong luồng physical edges. Mỗi hướng đóng góp cần có cạnh down hợp lệ trước Dodge, chưa up, và snapshot observed/release-gate vẫn hợp lệ. Không đọc engine-held/OS-held để suy thứ tự; không mượn cạnh đến sau Dodge.
3. Trục được khôi phục từ binding snapshot hiện hành và các cạnh đã chứng minh. Hướng yêu cầu phải đã được chuẩn bị; snapshot gửi được đối chiếu với hướng này, receipt phải giữ nguyên snapshot/yaw.
4. Admission nối trajectory bằng pawn/life, command, live `modelDodgeStart`/`at`, trajectory start và sequence kế tiếp. Mọi intermediate commit giữ cùng identity; phải có đúng một terminal commit tại motion-end deadline. Không chọn terminal đầu tiên nếu có dữ liệu mơ hồ.

`Received.command` là command thực nhận. `Received.commandId` là published snapshot cũ, có thể vẫn bằng0; analyzer không nhầm nó với command mới. `trajectory.combat.commandId` là last-processed-command snapshot, nên chỉ được dùng như cross-check sau khi đã bắt buộc **single-command trial**; có thêm receipt command khác thì INVALID. Không suy trajectory ID từ equality giữa command sequence và dodge sequence.

Thiếu/sai/mơ hồ correlation, direction preparation hoặc admission speed là **INVALID**. Khi input/precondition đã chứng minh nhưng sent snapshot, transport hoặc model direction sai, kết quả là **FAIL**, không đổi thành lỗi harness. Các luật distance, trajectory0.25s, release0.35s, deadline epsilon và cadence không được nới. Origin vẫn là vị trí authority nhận receipt; clock vẫn collector entry.

Raw hiện có chỉ ghi aggregate release gate theo binding cho modifier aliases. Khi không chứng minh được gate của alias vật lý riêng, analyzer trả INVALID thay vì giả định. Frozen fixture/harness WASD + physical LeftShift có đủ dữ liệu; rebind phím đơn H đã có synthetic positive test. Không thêm diagnostic/native mới để giải trường hợp thiếu dữ liệu này.

## Kiểm chứng tool-only

**19 nhóm synthetic đạt**, gồm các nhóm cũ và:

- Frame trước đứng yên nhưng `velocityBeforeBatch=0.010001 cm/s` → INVALID; biên horizontal0.01 đạt; thiếu/null/NaN/vector sai định dạng → INVALID.
- Thiếu intent/receipt/admission/trajectory, thiếu/sai command, sai pawn/life nhất quán nội bộ nhưng khác chuỗi, sai trajectory sequence/start hoặc admission trùng → INVALID.
- W đến sau Dodge, W đã up, hướng bị quarantine, intent bị motor lock → INVALID; không dùng held-state snapshot tự khai làm bằng chứng thay cạnh.
- Input hợp lệ nhưng snapshot gửi, receipt hoặc authority model sai → FAIL. Bốn hướng và rebind H hợp lệ đạt synthetic.

Đã chạy lại `RecomputeR1a.py` từ gzip raw đã công bố, không ghi đè bất kỳ output cũ nào:

| Kiểm lịch sử | Trước | Tính lại |
|---|---:|---:|
| Repro đúng input/model, scope R1a |24|24|
| Idle đạt cadence |9|9|
| Whole-trace repro cadence PASS |2|2|
| Whole-trace repro cadence INVALID |22|22|

Hai CSV giống **từng byte** bản gốc. Recompute còn đối chiếu core JSON với assertions đã lưu. **0 lượt lịch sử đổi nhãn.** Manifest cũ vẫn SHA-256 `dd45d73d734d6855923264681316e2110bc7f006abd342347fcdc3d6fcd75e9b`, **450** liên kết raw/published được rehash đạt. B/diagnostic trước R1a không được tính lại hay sửa.

Audit bổ sung `dodge_chain` trên 24 raw cũ, với yêu cầu hướng tiến/standing, cho **6 CHAIN_PASS +18 INVALID**: sáu W→Shift đứng yên có đủ chuỗi; hai loại fallback thiếu hướng tiến và prior-frame control có vận tốc bị loại. Đây là audit eligibility riêng, `acceptance=false`, không thay PASS repro của 24 ca theo contract R1a và không cấp PASS cadence/nghiệm thu cho bất kỳ lượt nào.

## Hồ sơ bổ sung và tái lập

[Manifest bổ sung](Evidence/ToolReview-20261119/MANIFEST.json) giữ synthetic log, patch tool, bảng/JSON tính lại và additional chain audit. [Manifest R1a cũ](Evidence/Review-20261119/MANIFEST.json) giữ nguyên. Output host riêng tại `Artifacts/U04/B-R1a/ToolReview-v3-Final-20261119`; các output thử tool trước đó cũng được giữ.

Chạy `python Scripts/U04/ReviewDodgeAnalyzerR1.py --out <thư-mục-mới>` để rehash 450 liên kết, chạy synthetic và tính lại. Lệnh chỉ khởi chạy Python, không UE/game/input/capture. Manifest R1b đề xuất đã trỏ candidate entry-3 nhưng vẫn **PROPOSED_NOT_AUTHORIZED**. Dừng để reviewer đánh giá lại analyzer và phương pháp; không tự ACCEPTED hoặc bắt đầu batch.
