# C1 — verdict khi stop mất metadata, chờ review

U04-C1 giữ **INCOMPLETE**:0/36 timing,0/12 memory,0/3 overhead. Lượt này chỉ sửa tooling và chạy offline. Không chạy child Windows thật, readiness Build-03, game/Editor, build, Unreal tests hoặc input. Không mở ma trận, khép hoặc merge C1.

## Diff từc9e5a6c

[Diff tooling](TOOLING.patch), unified=0; nếu áp dùng git apply --unidiff-zero.

- Backend.stop_launched ghi identityVerifiedAtStop=True chỉ sau khi capture_owned đọc lại và đối chiếu thành công PID/executable/FILETIME trên handle gốc. Nhánh OSError giữ markerFalse, lỗi metadata và cleanup qua handle gốc như trước.
- run_owned_launch giữ processExited=True và exitEvidence khi stop đã trả proof wait signaled. Nếu marker thiếu hoặc không phải chính booleanTrue, đặt status=INVALID và stopIdentityError trước khi ghi result.json. main ghi cùng verdict vào final.json và trả1. Không sửa exit proof hoặc che identityCaptureError.
- Chỉ cập nhật hai fixture stop bình thường trong suite cũ để chúng công bố markerTrue. Không sửa expected hay bỏ ca. File source/native và GATES không đổi; mọi suite/evidence đã bàn giao giữ nguyên.

## Replay entry-to-exit

Suite mới dùng C1Run.main và Backend.stop_launched/capture_owned thật, với kernel/process/time/verify/probe giả. Backend constructor Win32 không được gọi; subprocess.Popen thật bị chặn. Launch và verify thành công, probe trảPASS, rồi mới kích hoạt OSError trong lần đọc FILETIME lúc stop. Có đúng3 lượt đọc metadata trong replay: capture ban đầu, verify, stop.

|Ca|Expected result.json / final.json|CLI|Child đã thoát|
|---|---|---|---|
|normal|PASS / PASS; markerTrue|0|True|
|stop_oserror|INVALID / INVALID; markerFalse, giữ lỗi metadata|1|True|
|missing_flag|INVALID / INVALID; marker thiếu|1|True|
|null_flag|INVALID / INVALID; marker null|1|True|
|numeric_flag|INVALID / INVALID; marker1 không phải booleanTrue|1|True|
|string_flag|INVALID / INVALID; marker chuỗiTrue|1|True|
|false_flag|INVALID / INVALID; markerFalse|1|True|

7/7 ca đạt. Replay assert result và final có exitEvidence bằng nhau, wait=signaled, handleSource=original_Popen; stop_oserror vẫn giữ FILETIME đã pin và identityCaptureError. Terminate/wait/close đều nhắm handle giả gốc456, không OpenProcess tìm target theo PID. Giữ bản copy process/journal/result/final của mỗi ca để review.

[Expected/actual](Evidence/Stop-Verdict-Offline-01/cases.csv.gz), [transcript](Evidence/Stop-Verdict-Offline-01/transcript.txt.gz), [results và proof](Evidence/Stop-Verdict-Offline-01/results.json.gz).

Hồi quy offline:18/18 ca identity bổ sung và86/86 ca cũ đạt trong thư mục mới. Các expected cũ không đổi. Đây không phải Automation Unreal hoặc kiểm Windows thật. Không chạy lại các suite đã bàn giao.

## Hồ sơ và điểm dừng

[Manifest](Evidence/MANIFEST.json), [verification](VERIFICATION.json). Gzip roundtrip và SHA-256 được kiểm; source snapshot ghi tooling đã kiểm. Native inputs giữ nguyên13b4f34f07bd1cb8e7402984d9479fd5eb9fe2e7; GATES và hồ sơ trước không đổi.

Tái lập chỉ offline với output mới: python Scripts/U04/C1StopVerdictChecks.py --out <new-dir>. Không tự chạy checker Windows hoặc probe Build-03. Bàn giao diff và expected/actual để reviewer quyết định; chưa có quyền chạy readiness thật hoặc bước profiling tiếp theo.
