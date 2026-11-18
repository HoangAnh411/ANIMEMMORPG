# U04-B executed matrix

Status: **INCOMPLETE; not READY_FOR_REVIEW**. Source a1e536a79a60a4409e9a6cf64661008f1618e66f. All38 attempts retained:31 PASS,6 INVALID,1 FAIL. [Every trial](B-TRIALS.csv), [assertions/index](B-RESULTS.json), [report](REPORT-B.md).

| Case | Required per FPS | 30 FPS | 60 FPS | 120 FPS |
|---|---:|---|---|---|
| Walk5000 +/-50 cm /10 world s | 3 | 3 PASS /3 attempts | 3 PASS /3 | 3 PASS /4;1 cadence INVALID |
| Sprint7000 +/-50 cm /10 world s | 3 | 3 PASS /3 | 3 PASS /3 | 3 PASS /4;1 cadence INVALID |
| Forward dodge300 +/-5 cm | 3 | first attempt FAIL direction; gate stopped | not run: related gate stopped | not run: related gate stopped |
| Back/left/right dodge, each | 3 each | not run: related gate stopped | not run: related gate stopped | not run: related gate stopped |
| Combo123 /220 damage /1.45 s | 5 | 5 PASS /5 | 5 PASS /5 | 3 PASS /7;4 cadence INVALID; insufficient evidence |

No cap/quality/timestep workaround or additional attempt beyond the budget. Dodge related gates stop at the unresolved direction reproduction; no runtime fix was made. The legacy40 ms preparation dodge regression is supplemental and does not fill the B stationary-admission matrix.

Full Automation140/140, exact expected/discovered/executed names; three-map packaged load smoke3/3; normal fixture-off4 checks; combat24, defense15, legacy dodge38, movement/focus26, dedicated Editor+two clients26 checks;41 independent network comparisons and reconnect history/feedback check. All pass on the final binary. Network remains client60/server30.

Before capture:8 synthetic method groups pass. Final receipt/structural-invalidity audit:9 groups pass, all38 original decisions/numeric results recompute unchanged. Method tests are not binary gameplay evidence. Preservation4392 hashes and original Editor creation/window state pass.
