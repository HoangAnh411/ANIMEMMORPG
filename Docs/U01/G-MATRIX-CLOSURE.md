# U01 — Đối chiếu ma trận khi khép G

Người dùng xác nhận chơi thử G tại **9c89d08e5e14590166e7933e405e95887afb1b54**, gồm bản sửa focus A/B. Source binary/package không đổi: **5f8a6eabe103a8b31a894c82f32cffb0325474a9**. Các PASS bên dưới phân biệt Automation, tool/input thật, nghiệm thu người dùng và bằng chứng kế thừa; không cộng kiểm tra hậu xử lý vào23Automation tests.

| ID | Kết quả cuối | Bằng chứng / phương thức |
|---|---|---|
| A-BASE | PASS | REPORT-A.md; accepted4216ff8; baseline fullSHA |
| A-ASSET | PASS | ASSETS.md / REPORT-A.md; technical mannequin/clip register |
| A-NET | PASS | REPORT-A.md; feasibility only, superseded by accepted F for network acceptance |
| B-LOOK | PASS | REPORT-B.md/package acceptance2e0e89f; G CameraPolicy/ReleaseGate; G real-input captures and user acceptance9c89d08; Focus follow-up |
| B-BODY | PASS | REPORT-B.md/package acceptance2e0e89f; G CameraPolicy/ReleaseGate; G real-input captures and user acceptance9c89d08; Focus follow-up |
| B-SHOULDER | PASS | REPORT-B.md/package acceptance2e0e89f; G CameraPolicy/ReleaseGate; G real-input captures and user acceptance9c89d08; Focus follow-up |
| B-COLLISION | PASS | REPORT-B.md/package acceptance2e0e89f; G CameraPolicy/ReleaseGate; G real-input captures and user acceptance9c89d08; Focus follow-up |
| B-FOCUS | PASS | REPORT-B.md/package acceptance2e0e89f; G CameraPolicy/ReleaseGate; G real-input captures and user acceptance9c89d08; Focus follow-up |
| B-GATE | PASS | REPORT-B.md/package acceptance2e0e89f; G CameraPolicy/ReleaseGate; G real-input captures and user acceptance9c89d08; Focus follow-up |
| B-GRAVITY | PASS | REPORT-B.md/package acceptance2e0e89f; G CameraPolicy/ReleaseGate; G real-input captures and user acceptance9c89d08; Focus follow-up |
| C-SPEED | PASS | REPORT-C.md/accepted0cba933; G FlatMovement/JumpPhysics/JumpWindows/Terrain/MotorLocks; MOTOR-FPS.json; timed MotionLocks/DefeatedRestore |
| C-DIAGONAL | PASS | REPORT-C.md/accepted0cba933; G FlatMovement/JumpPhysics/JumpWindows/Terrain/MotorLocks; MOTOR-FPS.json; timed MotionLocks/DefeatedRestore |
| C-JUMP | PASS | REPORT-C.md/accepted0cba933; G FlatMovement/JumpPhysics/JumpWindows/Terrain/MotorLocks; MOTOR-FPS.json; timed MotionLocks/DefeatedRestore |
| C-CLOCK | PASS | REPORT-C.md/accepted0cba933; G FlatMovement/JumpPhysics/JumpWindows/Terrain/MotorLocks; MOTOR-FPS.json; timed MotionLocks/DefeatedRestore |
| C-TERRAIN | PASS | REPORT-C.md/accepted0cba933; G FlatMovement/JumpPhysics/JumpWindows/Terrain/MotorLocks; MOTOR-FPS.json; timed MotionLocks/DefeatedRestore |
| C-LOCK | PASS | REPORT-C.md/accepted0cba933; G FlatMovement/JumpPhysics/JumpWindows/Terrain/MotorLocks; MOTOR-FPS.json; timed MotionLocks/DefeatedRestore |
| C-LAB | PASS | REPORT-C.md; Evidence/C-LAB.json; accepted C and G packaged review |
| D-STATES | PASS | REPORT-D.md/accepted1e46f71; G six D tests including LandingTransitions/CarryTrajectory/GripIsolationAndAttachment; MOTOR-FPS.json; G user review. Temporary blockout carry only |
| D-ROOT | PASS | REPORT-D.md/accepted1e46f71; G six D tests including LandingTransitions/CarryTrajectory/GripIsolationAndAttachment; MOTOR-FPS.json; G user review. Temporary blockout carry only |
| D-SWORD | PASS | REPORT-D.md/accepted1e46f71; G six D tests including LandingTransitions/CarryTrajectory/GripIsolationAndAttachment; MOTOR-FPS.json; G user review. Temporary blockout carry only |
| E-REBIND | PASS | REPORT-E.md/acceptedcb46c52/packagec8df4ff; G four E tests; TIMED-CHECKS.json56/56, real-input videos and G user review |
| E-SETTINGS | PASS | REPORT-E.md/acceptedcb46c52/packagec8df4ff; G four E tests; TIMED-CHECKS.json56/56, real-input videos and G user review |
| E-ISOLATION | PASS | REPORT-E.md/acceptedcb46c52/packagec8df4ff; G four E tests; TIMED-CHECKS.json56/56, real-input videos and G user review |
| E-GATE | PASS | REPORT-E.md/acceptedcb46c52/packagec8df4ff; G four E tests; TIMED-CHECKS.json56/56, real-input videos and G user review |
| F-PROCESSES | PASS | REPORT-F.md/accepted2bd9b56; Evidence/F/CHECKS.json92checks; G NETWORK-REGRESSION.json; Focus data; user acceptance9c89d08 |
| F-MOVE | PASS | REPORT-F.md/accepted2bd9b56; Evidence/F/CHECKS.json92checks; G NETWORK-REGRESSION.json; Focus data; user acceptance9c89d08 |
| F-SECURITY | PASS | Accepted F evidence: Evidence/F/CHECKS.json, MANIFEST.json and REPORT-F.md; G SavedMoveReplay/ProxyAnimation. Full F real-process reconnect/attacks/settings cases inherited, not repeated in G; gameplay/assets/config unchanged from accepted F source (CLOSURE-AUDIT.json) |
| F-LIFECYCLE | PASS | Accepted F evidence: Evidence/F/CHECKS.json, MANIFEST.json and REPORT-F.md; G SavedMoveReplay/ProxyAnimation. Full F real-process reconnect/attacks/settings cases inherited, not repeated in G; gameplay/assets/config unchanged from accepted F source (CLOSURE-AUDIT.json) |
| G-SOURCE | PASS | CLOSURE-AUDIT.json; BUILD-RESULTS.json; PACKAGE.csv48files; clone source5f8a6ea; build disk binaries; Editor kept open |
| G-AUTOMATION | PASS | AUTOMATION-RESULTS.json23/23: U00Foundation4, U01 19; fresh cold-clone MCP log. Closure reads existing result, no rerun |
| G-WINDOWS | PASS | SMOKE.json3/3; TIMED-CHECKS.json56/56; ten completed input captures; user package acceptance9c89d08 |
| G-LIFECYCLE | PASS | TIMED-CHECKS.json: five Boot/lab/Boot cycles, Quit/reopen; LONG-PLAY-SUMMARY.json600.233s,263input,3001Game samples,10focus returns; interrupted534s attempt excluded |
| G-FPS | PASS_WITH_RECORDED_LIMIT | FPS-SUMMARY.json/FPS-TRIALS.json and MOTOR-FPS.json;1920x1080/internal100%,30/60FPS achieved,cap120 actual89.5167FPS. Sustained120FPS NOT VERIFIED per original hardware-limit rule; no renderer change |

Không còn tiêu chí kỹ thuật bắt buộc thiếu bằng chứng. G-FPS cho phép ghi mức máy không đạt là chưa kiểm chứng; không biến cap120 thành120FPS. Art anime/model/rig/kiếm/carry chính thức DEFERRED; không nghiệm thu Server đóng gói, mạng xấu/combat/U02 hoặc hiệu năng sản phẩm tổng quát. Các giới hạn chẩn đoán và lịch sử lỗi giữ trong REPORT-G/CLOSURE-AUDIT.json.
