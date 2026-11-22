# CC-A-R1 — ràng buộc exit proof, chờ review

U04-C1 **INCOMPLETE**: counter runtime 0/12, timing 0/36, memory 0/12, overhead 0/3. Chỉ chạy offline, không chạy package, Editor, build, Unreal tests hoặc input Windows. Không mở CC-B, profiling, khép hoặc merge C1.

## Diff hẹp từ 0d929c4

- `C1CounterValidate.py`: sau stop, bắt buộc proof có PID và creationTicks kiểu int, bằng chính xác process.json đã được nối với launch proof. Không tolerance, không chuyển FILETIME sang float hoặc so với CIM. Executable dùng `C1Identity.path_key` (Windows normcase/normpath, đường dẫn absolute); relative/missing path trả INVALID. Mỗi lỗi ghi rõ trường `exit_identity:pid`, `:creationTicks`, `:executable`.
- Journal của chính run phải có đúng một `original_handle_process_exited`, có evidence object. Proof phải có cùng tập trường và giá trị/kiểu với record journal, riêng executable so bằng quy tắc đường dẫn Windows. Thiếu/trùng record, thiếu evidence/trường hoặc lệch giá trị đều INVALID với diagnostic riêng. Đây là đối chiếu journal thật của workspace giả đầy đủ, không chỉ so hai verdict với nhau.
- Giữ kiểm tra processExited=true, marker **is True**, handleSource=original_Popen, wait=signaled và verdict nhất quán. Khi result/final khác proof, diagnostic chỉ rõ trường `result_final_exit_proof:<field>`.
- `C1CounterChecks.py`: chỉ bổ sung creationTicks/executable vào stop proof của backend **giả**, cho khớp schema adapter thật. Không sửa expected 53 ca.
- `C1CounterExitChecks.py`: replay hậu kiểm mới, sao chép toàn bộ workspace entry_normal từ lượt hồi quy mới, rebase metadata/path tới bản sao, giữ nguyên byte Raw và log. Mỗi ca có result/final/process/capture/journal/summary/CSV đầy đủ. Không gọi launcher/Win32; Popen bị chặn. Kiểm hash source trước/sau để chứng minh workspace nguồn không bị sửa.

[Diff tooling](TOOLING.patch) dùng unified=0; nếu áp dụng dùng `git apply --unidiff-zero`. Native inputs, Build-03, readiness, lifecycle stop và toàn bộ hồ sơ CC-A cũ giữ nguyên. Các suite 86/18/7 không đổi và không chạy lại vì không sửa đường điều khiển của chúng; hồi quy CC-A 53 ca được chạy lại trên tooling cuối.

## Expected/actual

**14/14** ca hậu kiểm đạt, gồm:

|Ca|Expected / actual|Diagnostic|
|---|---|---|
|control|PASS / PASS|Không lỗi|
|windows_path_equivalent|PASS / PASS|Khác hoa/thường và slash vẫn cùng Windows path|
|wrong_pid|INVALID / INVALID|exit_identity:pid|
|one_tick|INVALID / INVALID|exit_identity:creationTicks|
|wrong_executable|INVALID / INVALID|exit_identity:executable|
|journal_disagrees|INVALID / INVALID|journal_exit_proof:pid|
|journal_missing / duplicate|INVALID / INVALID|journal_exit_record_count:0 / 2|
|proof_missing_ticks / ticks_float|INVALID / INVALID|exit_identity:creationTicks|
|executable_relative|INVALID / INVALID|exit_identity:executable|
|result_only_pid|INVALID / INVALID|result_final_exit_proof:pid|
|journal_wrong_executable|INVALID / INVALID|journal_exit_proof:executable|
|journal_missing_proof|INVALID / INVALID|journal_exit_proof:missing|

Các ca wrong_pid và one_tick sửa **đồng thời exitEvidence trong cả result.json và final.json**; status hai file vẫn PASS để tái hiện lỗi. Chỉ validator hậu kiểm trả INVALID vì process identity không khớp. Ca journal_disagrees chỉ sửa evidence journal, giữ hai proof verdict nguyên vẹn. Không ca âm nào được coi là đạt chỉ vì trả INVALID do lỗi không liên quan: checker buộc diagnostic chứa đúng reason kỳ vọng.

Hồi quy CC-A: **53/53** ở Regression-CC-A-02, CLI 0; mọi expected cũ giữ nguyên, gồm stop_oserror và zero input sau guard lỗi. Regression-CC-A-01 cũng 53/53; source entry_normal của lượt này dùng làm baseline cho mutations, không phải package thật.

Exit-Link-01 có 0/14 ca đạt do lỗi fixture sao chép: reformat summary.json làm lệch hash raw trước khi tới exit checks. Lượt này giữ nguyên. Exit-Link-02 sửa copier để giữ byte Raw; 14/14 đạt đúng reason. Không sửa validator để bỏ hash check và không sửa artifact cũ.

[Expected/actual mới](EXPECTED-ACTUAL.csv), [hồi quy CC-A](REGRESSION-CC-A.csv), [manifest raw/archive](Evidence/MANIFEST.json), [verification](VERIFICATION.json). Raw ở `Artifacts/U04/C1/Counter-Correctness-A-R1/`, gồm cả lượt lỗi. Bản nén chứa workspace và kết quả; hash từng file và zip roundtrip đã kiểm. Các executable trong workspace giả chỉ là text fixture không thể dùng làm game.

## Tái lập và dừng

```powershell
python -B Scripts/U04/C1CounterChecks.py --out <new-regression-directory>
python -B Scripts/U04/C1CounterExitChecks.py --source <new-regression-directory>/entry_normal/Workspace/C1/Runs/normal --out <new-mutations-directory>
```

Nguồn phải là workspace fake hoàn chỉnh mới tạo, có stop proof đúng schema, không sửa hồ sơ cũ để làm ca đối chứng. Checker mutation chỉ đọc nguồn và ghi bản sao mới. Khi giải nén ở đường dẫn khác, tái tạo bằng các lệnh offline trên để có đường dẫn metadata đúng.

Bàn giao CC-A-R1 để reviewer xét trước lần launch đầu tiên. Chưa có bằng chứng counter runtime, chưa có quyền chạy CC-B hoặc profiling.
