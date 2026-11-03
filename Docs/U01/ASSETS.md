# U01 — Asset kỹ thuật đã chọn

Đọc qua MCP TestRunner `execute_console_command` → `py Scripts/U01/InspectAssets.py` trong Editor PID19808, ngày 2026-11-04 +07. Tool gửi lệnh chưa đủ: kết quả thực đọc ở `Artifacts/U01/A/assets-editor.json`, giữ metadata/hash trong [A-ASSETS.json](Evidence/A-ASSETS.json). 10/10 file có SHA256 khớp register U00, tải được đúng class. Không save/chỉnh asset.

Tất cả đường dẫn dưới `/Game/Characters/Mannequins/`. Mesh chọn `Meshes/SKM_Manny_Simple`, skeleton `Meshes/SK_Mannequin`. Mesh và sáu AnimSequence cùng skeleton thực; không suy từ tên mannequin. Nguồn byte/đường dẫn template cụ thể và SHA256 từng file có trong evidence; register U00 còn nhãn lịch sử UPLOAD_NOT_CONFIRMED, căn cứ và quyền baseline đã được xử lý ở REPORT-B/U00 và nghiệm thu U00, không tự gán giấy phép mới.

| Vai trò U01 | Asset nguồn tương đối | Length giây | enable_root_motion hiện tại |
|---|---|---:|---|
| Idle | Anims/Unarmed/MM_Idle | 7,5667 | False |
| Đi | Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd | 1,5 | True |
| Chạy/sprint | Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd | 1,7667 | True |
| Nhảy lên | Anims/Unarmed/Jump/MM_Jump | 0,8667 | False |
| Rơi | Anims/Unarmed/Jump/MM_Fall_Loop | 3,0 | False |
| Tiếp đất | Anims/Unarmed/Jump/MM_Land | 0,8667 | False |

`Anims/Unarmed/ABP_Unarmed` và `BS_Idle_Walk_Run` đã tải đúng AnimBlueprint/BlendSpace; chỉ tham chiếu cấu trúc, không dùng nguyên xi làm nghiệm thu U01. Đi/jog nguồn bật root motion: **không được gọi bộ nguồn là in-place đã đạt**. Đợt D tạo bản riêng U01, khóa root và cấu hình extraction/AnimBP không áp root translation vào capsule (Ignore Root Motion với extraction phù hợp), kiểm tra cả pose root drift lẫn actor displacement. Đo thực tốc độ/apex và video foot sliding trước nghiệm thu; không chỉ tắt cờ rồi giả định hết dịch chuyển. Clip nguồn được chọn không bảo đảm play-rate/transition đã đạt; giới hạn play rate sẽ ghi theo số đo D.

Nội dung đích `/Game/AnimeMMORPG/U01/Characters`, `Animations`, `Input`, `UI` chỉ tạo khi dùng trong B–E. Nếu thêm socket tay phải, duplicate skeleton/mesh liên quan vào U01 trước chỉnh; giữ template/variant và skeleton chung nguyên vẹn. Kiếm hình khối tự tạo trong D, chỉ attachment, collision/damage tắt. A không tạo kiếm hoặc duplicate asset.

Model/rig/kiếm anime: **DEFERRED theo lựa chọn người dùng**, không được đánh dấu hoàn thành khi mannequin kỹ thuật đạt.
