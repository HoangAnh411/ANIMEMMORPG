# CC-A — tooling và replay offline, chờ review

U04-C1 **INCOMPLETE**. Đợt này chỉ viết tooling và chạy backend giả: không chạy package, Editor, build, Unreal tests, input Windows hoặc checker process Windows thật. Counter runtime vẫn **0/12**, timing **0/36**, memory **0/12**, overhead **0/3**. Readiness runtime tại 7ea50a7 đã được người dùng ACCEPTED; không chạy lại probe riêng. Không mở CC-B, profiling, C2, khép hoặc merge C1.

## Thay đổi

- `Scripts/U04/C1CounterRun.py`: entry riêng, chỉ Build-03 có SHA Game đã pin, ID chưa dùng, N=1/10/40, H=1/3, in/out. Không có lựa chọn trace, duration, action count, batch hoặc retry. Native inputs phải khớp 13b4f34. Dùng nguyên `C1Run.arguments` và `run_owned_launch`, inventory bảo vệ trước/sau, stop bằng handle Popen gốc và verdict đã nghiệm thu.
- `C1Counter.py`: kế thừa setup, metrics mới, IME và guard từ readiness. Sau setup của process hiện tại: prepare, chờ 2 giây, metrics mới cùng pawn/life; begin 5; guard; một LMB xuống, giữ 35 ms, nhả; chờ native tự đóng capture. Không gửi `end`, quit, shortcut cleanup hoặc lấy lại focus. Resume có marker riêng; gameplay LMB có `purpose=counter-action`. Mỗi cạnh kiểm foreground/identity sát SendInput; khi lỗi giữ thông tin phím còn down rồi để outer lifecycle stop child, không phát key-up toàn cục.
- `C1CounterValidate.py`: đối chiếu schema native thực xuất, không suy raw damage từ HP tự khớp. Ghép action GUID/life/sequence, actor/controller/authority, target GUID/life/hurtbox, thời gian action, damage 60, HP và counter. Kiểm frame không rỗng, liên tiếp, focus, monotonic counter, hai biên và profile B/smoothing=false. Queries vẫn là **post-contact**. Đối chiếu thêm delta `combat.damageResults` / `geometryQueries` từ metrics mới hai phía, không dùng giá trị lũy kế làm delta. Khi mở lại hồ sơ, validator còn buộc result/final cùng verdict và exit proof hợp lệ; ca stop mất metadata không được PASS lại. Chỉ probe nội bộ gọi kiểm capture trước stop; verdict cuối vẫn qua lifecycle đã nghiệm thu.
- `C1Validate.py`: chuyển CLI cũ sang validator này; chỉ nhận chế độ single-action, đường validation 60-action cũ trả INVALID. Không phục hồi input Method-Timing-01.
- `C1CounterChecks.py`: fixtures native-shaped tổng hợp và replay entry→probe→validator→stop→result/final/CLI. Không coi fixture giả là bằng chứng native đúng.

Các file readiness/lifecycle đã nghiệm thu (`C1Run`, `C1Readiness`, `C1Win32`, `C1Identity`, các suite 86/18/7) giữ nguyên byte so với 7ea50a7. Native giữ nguyên 13b4f34; GATES và các hồ sơ cũ giữ nguyên.

## Kết quả offline

Suite CC cuối: **53/53** expected/actual khớp. Có 12 cấu hình dữ liệu tổng hợp; không phải 12 ô runtime. Các ca âm gồm damage 50 nhưng HP tự khớp, đúng số hit sai action/source life/target life, hurtbox lạ, H=3 nhân damage, ngoài vùng vẫn hit, frame rỗng/gap/mất focus, dữ liệu trước cửa sổ, action ngoài biên, PID/world/run ID khác, thiếu life, smoothing sai, registration/counter sai, thiếu summary, output cũ/ID dùng lại, metrics cũ, mất focus lúc gõ prepare và giữa LMB down/up, mất metadata chỉ lúc stop. Có ca giữ cumulative cũ 17 DamageResults / 29 Queries nhưng chỉ đối chiếu delta mới.

Replay `entry_normal`: result/final PASS, CLI 0; `entry_wrong_damage`: FAIL/FAIL, CLI 1. `entry_focus_between_lmb`: INVALID, held=LMB, chỉ có cạnh xuống, **0 input sau guard_failed**; không nhả sang cửa sổ khác. `entry_stop_oserror`: INVALID/INVALID, CLI 1, vẫn processExited=true và wait=signaled, marker false và lỗi metadata được giữ. Đây là exit proof **giả**; regression 7 ca vẫn dùng adapter stop thật với kernel giả như suite đã nghiệm thu.

Hồi quy: **86/86 + 18/18 + 7/7** đạt trong thư mục mới. Không sửa expected, không thay suite cũ. Raw mọi lượt phát triển Offline-01…06 và hồi quy giữ ở `Artifacts/U04/C1/Counter-Correctness-A/`; bản nén kèm manifest đưa vào Evidence. Offline-01/02 có 43 ca, Offline-03 có 51 ca, Offline-04/05/06 có 53 ca; đều giữ nguyên. Bản cuối là Offline-06 và kiểm thêm verdict khi mở lại hồ sơ sau stop. Workspace giả của Offline-02 trở đi được giữ để mở lại validator; đường dẫn artifact trong process/capture trỏ tới workspace giả đó. Khi giải nén ở nơi khác, chạy lại checker với output mới để tạo lại đường dẫn sở hữu process giả; không sửa receipt để giả thành run thật.

[Expected/actual CC](EXPECTED-ACTUAL.csv), [kết quả hồi quy](REGRESSIONS.json), [diff tooling](TOOLING.patch), [manifest](Evidence/MANIFEST.json), [verification](VERIFICATION.json).

## Giới hạn phải review

[Danh mục counter và mức bằng chứng](COUNTERS-AND-RESET.md) phân biệt PASS của các assertion có export với việc nghiệm thu counter toàn bộ. `evidenceLimits` luôn đi cùng verdict; không được bỏ khi tổng hợp ledger.

Build-03 không xuất snapshot HP ban đầu từng target, identity của mọi registration tại hai biên, ledger từng lần occlusion/suppression, giá trị DamageBegin/QueriesBegin hay marker Closed/reopen. HP ban đầu dựa trên source prepare cố định; baseline cumulative được kiểm thêm qua metrics. PID/creation được nối qua original/query handle, argv/output riêng và journal; summary chỉ có PID/world, không tự chứa FILETIME. Frames được gắn qua output mới rỗng, hash và thời gian/world cùng summary/metrics, không tự chứa PID/run ID.

Vì vậy **chứng minh động reopen và hai world đồng thời vẫn INCOMPLETE**; nguồn từng lần occlusion/suppression và identity registration chỉ có mức source/aggregate. Không tự thêm native fields, không thêm launch để lấp các khoảng này. Reviewer cần quyết định mức bằng chứng trước khi giao CC-B. Chưa có kết luận counter native đúng hoặc workload runtime PASS.

## Tái lập và điểm dừng

Chỉ chạy offline, output mới:

```powershell
python -B Scripts/U04/C1CounterChecks.py --out <new-offline-directory>
python -B Scripts/U04/C1Offline.py --out <new-86-directory>
python -B Scripts/U04/C1IdentityChecks.py --out <new-18-directory>
python -B Scripts/U04/C1StopVerdictChecks.py --out <new-7-directory>
```

`CC-B-LEDGER.json` chỉ là 12 ô NOT_RUN theo thứ tự được yêu cầu. Không có batch launcher. Mọi lần launch thật cần giao CC-B riêng sau khi CC-A được chấp nhận; ô đầu phải được đối chiếu raw trước khi tiếp tục và dừng ở FAIL/INVALID đầu tiên. Không lấy FPS diagnostic làm baseline. Bàn giao tooling để review và dừng tại đây.
