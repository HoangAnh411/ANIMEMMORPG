# F60 evidence

Native diagnostics source EDF885A (full SHA in MANIFEST); gameplay and network settings unchanged. Package remains source0f02c77 with48 verified hashes. Every A–D/E run has at least30s warm-up followed by a continuous120s measurement, including two60s foreground blocks for two-client runs. F3 is a continuous300s window. GFrameCounter continuity is checked for every process, including the buffered logging control.

RESULTS and case-results contain mean FPS, median/p95/p99/max wall frame time, foreground/background splits, CPU Game/Render/RHI and GPU raw stat-unit times where available, physical input onset/stop distributions, all focus changes and every frame>100ms. Server NullRHI has no stat-unit viewport: its separate CPU-thread timings are unavailable and GPU timing is N/A. Wall cap time is never substituted for GPU work. CPU/GPU values correspond to the last drawn frame, not scanout.

The gzip CSVs are lossless per-frame exports, not downsampled summaries. Case resources preserve NVIDIA global usage and Windows per-process dedicated/shared GPU memory. Manifest runtime values come from actual collectors, not launch arguments. Raw source files remain in artifacts with hashes in RAW-ARTIFACTS. Historical early server records used shared requested render-dimension fields; server is headless NullRHI and those render dimensions are N/A, as shown by its arguments/runtime identity.

Videos contain only the native900×540 client rectangles, with timing duplicates and original warnings retained. Actual capture rates and hashes are in VIDEOS;30Hz encoding does not certify60FPS smoothness. Native frame measurements establish FPS. Peer cameras were turned by real mouse input to keep the other pawn visible.

Stop latency includes physical braking plus the criterion for fully settled mesh, not just transport. The measured offset decay exactly matches unchanged CMC Exponential stepping (1-dt/0.05 at rest). RESULTS explains the increased60FPS stop tail before selecting60; no smoothing/tick-rate/network change hides it.

HISTORY retains the rejected D run with missing resources and the F3 preflight abort before measurement. WARNINGS retains startup EditorDataStorageUI warnings. EVIDENCE.csv hashes every file here except itself. F is READY_FOR_REVIEW, awaiting user confirmation; no merge or G acceptance.
