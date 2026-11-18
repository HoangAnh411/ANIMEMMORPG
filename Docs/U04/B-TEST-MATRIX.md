# U04-B matrix

All gates are pending; this file is a requirement inventory, not an execution result.

| Gate | Per FPS 30 / 60 / 120 | Maximum attempts |
|---|---|---|
| Walk | 3 valid, 5000 +/-50 cm /10 world seconds | 5 per FPS |
| Sprint | 3 valid, 7000 +/-50 cm /10 world seconds | 5 per FPS |
| Forward dodge | 3 valid, 300 +/-5 cm | 5 per FPS |
| Backward dodge | 3 valid, 300 +/-5 cm | 5 per FPS |
| Left dodge | 3 valid, 300 +/-5 cm | 5 per FPS |
| Right dodge | 3 valid, 300 +/-5 cm | 5 per FPS |
| Combo123 | 5 valid, 60/70/90, total220, timeline1.45 s | 7 per FPS |

Each selected gameplay window must independently satisfy the cadence, continuity, focus, identity and configuration contract. Preserve nonqualifying gameplay as supplemental evidence.

Method tests: cap120/actual60, missing counter, duplicate timestamp, long frame, FPS/percentiles, boundary interpolation, duplicate hit, wrong life/action, crit, unexplained HP delta, cvar/reset/focus/source changes.

Final regression: exact-name full Automation; all three maps; fixture-off normal launch; focused combat/dodge/focus; dedicated Editor + two clients with inherited A profile. All pending.
