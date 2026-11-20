# U04-B handoff — INCOMPLETE

**Current status: U04-B technically ACCEPTED at `251335895394c5ddb260d875a05d26462fbd1d70`. The user authorized documentation closure and merge/push on2026-11-20. [Acceptance B](ACCEPTANCE-B.md), [combined report](R1b/Continuation/REPORT.md). The INCOMPLETE batch below is historical; all FAIL/INVALID verdicts and evidence remain unchanged. Native/binary remains8cbcb6a6, analyzer entry-4. No build/gameplay/Automation rerun for closure; C/D remain unstarted.**

**Not READY_FOR_REVIEW; U04.03 is not passed and U04 is not closed.** Two unresolved gates remain: the directional dodge reproduction and insufficient120 FPS combo cadence evidence. Reviewer decides the follow-up. No acceptance, merge, runtime repair or U04-C/D work was performed.

Baseline main local/remote18804bfa32b14471df1ffa4bd7aeaed6cd80074c. Branch `u04/b-fps-correctness`, isolated clone `Artifacts/U04/B/Source`, runs `Artifacts/U04/B/Runs`. Original main remains at baseline with its exact initial private/untracked status. U04-A closure/source attribution is unchanged.

## Identity and build

Built native source **a1e536a79a60a4409e9a6cf64661008f1618e66f**, committed before full UBT builds. Later commits change tools/documents only; final native/content/config/plugin/project inputs match that source and no untracked native inputs exist. Game executable SHA256 `09df0ccf3987e706cdf4c559b465a2376ee2ed78d55f255c89882793c5cd22cb`; Editor module `31d5757beaf723d5f52e0ba8a9e63d5c2a02e1e327898735144dd4c17d760184`. Full build index: `Build-R3-20261118/BUILD-IDENTITY-FULL.json`. Engine5.8.4/CL58902052; actual UBT-selected MSVC14.51.36260, Windows SDK10.0.26100.0. Compiler-newer-than-preferred and engine deprecation warnings remain in logs.

Generate04:35:58–04:36:05, Editor04:36:05–04:36:29, Game04:36:29–04:36:59, package04:36:59–04:37:47 UTC2026-11-18: all exit0. Exact native logs say `Result: Succeeded`; package says `BUILD SUCCESSFUL`. Three maps cooked: L_Boot, L_CharacterCombatLab, L_NetworkLab. Acceptance evidence uses cold package/Editor processes with -NoLiveCoding. A new plain diagnostic header was fully rebuilt; no reflection layout was patched. Each measured process records executable checksum, creation identity, source/tool/build identity and arguments; native source CLI metadata is not used as binary proof on its own.

## Measurement and outcome

Rendered Solo package,1280x720/internal50%, atlas2048, RT pool minimum128 MiB, streaming256 MiB, Lumen indirect/reflections0, virtual shadows0, shadow quality2, background idle0, VSync0. Only the requested cap differs across30→60→120 processes. Actual cvars/viewport are recorded every frame. Dilation1, smoothing false, fixed timestep/frame-rate flags false; the inactive configured FixedFrameRate30 value is retained. No smoothing/input/timestep/dilation change or renderer optimization. At least30 s warmup after readiness; each new process already exceeds the10 s cap-settle requirement.

Fixture opt-in requires -U04BFPSFixture; ordinary launch does not enable it. The inherited U03Regression URL excludes encounter AI. A flat300 m by30 m floor has top z0 at y20000, no obstacles/slope; the native product pawn starts at x−10000. Combo uses a new stationary600 HP native lab dummy, existing crit-off roll0.5, no shield/defense. Setup/reset occurs before recording; a setup request during recording records INVALID and refuses mutation. Product actions are guarded Windows input; no action or movement is fabricated by a gameplay call.

Samples are taken after actor ticks, including actual capsule positions and trajectory commits, and buffered until capture end. Authority input receipts, admissions, action starts/completions and hit identity/HP are retained. Native QPC seconds equal Windows QPC/frequency plus16777216; input records keep before/after emission brackets. Frame evidence is rendered game-thread wall cadence, **not scanout**; video30FPS is visual evidence only.

Each trial FPS = interval count / summed wall intervals; percentile interpolation uses rank(n−1)p. Qualification independently requires mean within5%, at least95% intervals within10% of the target period, no interval greater than two periods, continuous counters, valid focus/configuration/identity. Full bracketing frame intervals are retained for boundary windows; no bad frames are removed. Movement starts after0.5 world seconds continuously stable at actual500/700 cm/s, then uses exactly10 world seconds. Boundary position/wall time = left + alpha(right−left), alpha=(boundaryWorld−leftWorld)/(rightWorld−leftWorld); both original samples and alpha are in assertions. Forward projection, full path length and lateral deviation are published.

| Gate | 30 FPS | 60 FPS | 120 FPS |
|---|---|---|---|
| Walk |3/3 PASS|3/3 PASS|3/4 PASS;1 INVALID|
| Sprint |3/3 PASS|3/3 PASS|3/4 PASS;1 INVALID|
| Combo |5/5 PASS|5/5 PASS|3/7 PASS;4 INVALID; missing2 valid|
| Directional dodge |first forward attempt FAIL; related gate stopped|not run, blocked|not run, blocked|

Every movement attempt measured exactly5000/7000 cm by interpolation, with zero lateral deviation; qualifying trials meet cadence independently. Wall duration ranges: walk9.9995033741–10.0006357618 s; sprint9.9993557259–10.0003245212 s. All17 combo attempts have three unique hits on one target life,60/70/90 damage, HP600→380, crit=false, natural authority completions; maximum timeline arithmetic error1.13243e−14 s. Only13 qualify by cadence. First state observation is the next continuous sampled frame; observed lag is retained separately and never relaxes the1 microsecond timeline rule.

At120 FPS, the four rejected combo attempts have in-band fractions92.5714%,93.7143%,85.7143%,94.8571%, below95%, despite mean119.96–119.98 FPS and correct gameplay. No missing samples/focus/cvar/reset issue was observed in those windows. The observed limitation is interval jitter; its hardware/software cause has not been established and no profiling/optimization was attempted. Exactly7 combo attempts were used. Their gameplay is supplemental, not U04.03 PASS.

The forward dodge at30 FPS has299.9994551763 cm actual displacement,0.25 s motion and0.35 s release deadline; cadence passes30.076898 FPS. Its locked direction is−X after accepted W/Shift edges in one input-processing frame. The original FAIL is retained. Direction preparation versus product input-state ordering remains unresolved because intent direction was not directly instrumented. [Reproduction and separate follow-up proposal](B-DODGE-REPRO.md). No runtime fix or relabeling was made; remaining directional acceptance cases stop at this gate.

## Every attempt

All38 rows follow. FPS and in-band percentage are per-window calculations, not an average of instantaneous FPS. Full P50/P95/P99/max/histograms, wall/world samples, input events, assertions and hashes are in [B-RESULTS](B-RESULTS.json), [CSV](B-TRIALS.csv) and the published manifest.

| Trial | FPS | in-band % | P99 / max ms | Gameplay result | Label |
|---|---:|---:|---:|---|---|
|fps30-walk-1|29.9159|99.3333|36.292 / 39.515|5000.000000 cm;err +0.000000;wall 9.999503 s|PASS|
|fps30-walk-2|29.9982|100.0000|34.331 / 34.698|5000.000000 cm;err +0.000000;wall 10.000517 s|PASS|
|fps30-walk-3|29.9991|100.0000|34.190 / 36.613|5000.000000 cm;err +0.000000;wall 10.000172 s|PASS|
|fps30-sprint-1|29.9997|100.0000|34.492 / 34.898|7000.000000 cm;err +0.000000;wall 10.000061 s|PASS|
|fps30-sprint-2|30.0002|100.0000|34.256 / 34.627|7000.000000 cm;err +0.000000;wall 9.999876 s|PASS|
|fps30-sprint-3|30.0013|100.0000|34.215 / 34.731|7000.000000 cm;err +0.000000;wall 9.999536 s|PASS|
|fps30-forward-1|30.0769|100.0000|34.042 / 34.045|299.999455 cm;err -0.000545 ;direction−X|FAIL|
|fps30-combo-1|29.9887|100.0000|34.777 / 35.029|1.450000000000003 s;220 HP|PASS|
|fps30-combo-2|29.9939|100.0000|34.325 / 34.590|1.450000000000003 s;220 HP|PASS|
|fps30-combo-3|29.9994|100.0000|34.137 / 34.230|1.450000000000003 s;220 HP|PASS|
|fps30-combo-4|29.9853|100.0000|34.457 / 34.522|1.450000000000003 s;220 HP|PASS|
|fps30-combo-5|29.9890|100.0000|34.387 / 34.548|1.450000000000003 s;220 HP|PASS|
|fps60-walk-1|59.9991|99.8333|17.596 / 18.388|5000.000000 cm;err +0.000000;wall 9.999936 s|PASS|
|fps60-walk-2|59.9982|100.0000|17.417 / 18.045|5000.000000 cm;err +0.000000;wall 10.000211 s|PASS|
|fps60-walk-3|59.9987|100.0000|17.561 / 18.117|5000.000000 cm;err +0.000000;wall 10.000193 s|PASS|
|fps60-sprint-1|59.9978|100.0000|17.524 / 18.180|7000.000000 cm;err +0.000000;wall 10.000175 s|PASS|
|fps60-sprint-2|60.0004|100.0000|17.565 / 17.710|7000.000000 cm;err +0.000000;wall 9.999867 s|PASS|
|fps60-sprint-3|59.9978|100.0000|17.469 / 17.823|7000.000000 cm;err +0.000000;wall 10.000325 s|PASS|
|fps60-combo-1|59.9778|100.0000|17.634 / 17.669|1.449999999999989 s;220 HP|PASS|
|fps60-combo-2|59.9747|100.0000|17.528 / 17.536|1.449999999999989 s;220 HP|PASS|
|fps60-combo-3|59.9762|100.0000|17.504 / 17.583|1.449999999999989 s;220 HP|PASS|
|fps60-combo-4|60.0066|100.0000|17.313 / 17.342|1.449999999999989 s;220 HP|PASS|
|fps60-combo-5|60.0012|100.0000|18.050 / 18.247|1.449999999999989 s;220 HP|PASS|
|fps120-walk-1|119.9939|95.6667|9.421 / 10.166|5000.000000 cm;err +0.000000;wall 9.999972 s|PASS|
|fps120-walk-2|119.9514|93.7500|9.579 / 13.023|5000.000000 cm;err +0.000000;wall 10.000636 s|INVALID|
|fps120-walk-3|119.9966|95.8333|9.329 / 10.053|5000.000000 cm;err +0.000000;wall 9.999826 s|PASS|
|fps120-walk-4|119.9907|96.8333|9.320 / 10.291|5000.000000 cm;err +0.000000;wall 10.000220 s|PASS|
|fps120-sprint-1|119.9913|96.8333|9.377 / 9.954|7000.000000 cm;err +0.000000;wall 10.000079 s|PASS|
|fps120-sprint-2|120.0038|96.2500|9.363 / 10.043|7000.000000 cm;err +0.000000;wall 9.999356 s|PASS|
|fps120-sprint-3|119.9919|94.5000|9.511 / 10.221|7000.000000 cm;err +0.000000;wall 10.000132 s|INVALID|
|fps120-sprint-4|119.9957|95.0000|9.441 / 9.863|7000.000000 cm;err +0.000000;wall 9.999927 s|PASS|
|fps120-combo-1|119.9634|97.1429|9.171 / 9.467|1.449999999999989 s;220 HP|PASS|
|fps120-combo-2|119.9612|92.5714|9.612 / 9.653|1.449999999999989 s;220 HP|INVALID|
|fps120-combo-3|119.9754|93.7143|9.313 / 9.639|1.449999999999989 s;220 HP|INVALID|
|fps120-combo-4|119.9792|95.4286|9.432 / 9.932|1.449999999999989 s;220 HP|PASS|
|fps120-combo-5|119.9679|85.7143|9.447 / 9.800|1.449999999999989 s;220 HP|INVALID|
|fps120-combo-6|119.9701|94.8571|9.506 / 9.590|1.449999999999989 s;220 HP|INVALID|
|fps120-combo-7|119.8337|95.4286|9.283 / 9.722|1.449999999999989 s;220 HP|PASS|

## Regression, methods and preservation

Fresh cold-clone MCP TestRunner Automation:140/140 Success; exact expected=discovered=executed names, no duplicates/missing/extra, queue empty, actual loaded B module verified. Raw schemas/logs and NAME-RESULTS.json are published; no supported XML export exists. Three packaged NullRHI map load smokes pass; those are load checks, not rendered gameplay. Ordinary normal-encounter package passes4 fixture-off checks using actual command line, crit state, position and inert B commands.

Fresh final-source A-derived Windows regressions: combat24, defense15, legacy dodge38, movement/focus26, network26 checks, all pass. Dedicated Editor server has0 local players; each client has1 owned pawn and an actually loaded B DLL, with advancing time/frame and physical-input readiness. Client60/server30 profile retained;41 independent saved server/client comparisons pass, plus reconnect retained-history/no-old-feedback verification. Legacy dodge uses40 ms direction preparation and does not replace the blocked stationary-admission B case. Historical D/A names and the inherited A read-only diagnostic flag in these regression tools are provenance labels; all paths/source identities/new evidence are B.

Before capture8 synthetic method groups pass. Final tool-only audit adds receipt-versus-processing and structural INVALID classification coverage (9 groups total): valid receipt followed by rejection/late processing/no action remains gameplay FAIL; focus/source/config/data-integrity defects stay INVALID with observed gameplay retained. This audit occurred after capture, changes no runtime and recomputes all38 original labels/numeric results unchanged. Both analyzer SHA256 revisions and all method logs/recomputations are retained. Method tests never count as binary gameplay evidence. Five negative identity guards and live wrong-creation Stop preservation pass.

Final preservation passes4392 hashes, including every recorded original preflight file, raw/published U03 D/D-R1 and U04-A evidence, both48-file U03 packages and48-file A/B packages, modules and engine. Original Editor PID10880 retains creation UTC2026-11-18T04:17:19.8968150Z and initial window placement; it was never saved/stopped/restarted. All B Editor/game processes are closed, including reconnect. Original main/private changes and ignored historical workspaces remain in place. Initial free disk138574770176 bytes against25 GiB reserve; final snapshot has121412898816 bytes free. No cleanup or engine download.

## Retained nonpassing setup and handoff

Build-Initial was interrupted and contains explicit first-include errors. Build-R2 and preliminary Build-Final succeed but precede the final trajectory-end diagnostic correction; only Build-R3 is used for acceptance gates. An early pre-capture process/index used abbreviated source metadata, was stopped and is explicitly INVALID; full40-character identities are now enforced. Original index/process are retained rather than overwritten. All six cadence-invalid attempts and the directional FAIL remain unchanged. Generated cook SecurityToken/blank-line changes were normalized only in the isolated clone by the semantic guard; no original config was changed.

Publication: `Docs/U04/Evidence/B/Review-20261118/MANIFEST.json`, raw runs under `Artifacts/U04/B/Runs`; package bytes stay in the isolated Build-R3 archive with full file checksums. `VerifyEvidenceB.py` verifies raw/published hashes; `--published-only` works on another checkout. `RecomputeB.py --runs <rawRuns> --out <newFile>` reproduces all original trial decisions with the final analyzer; it never overwrites assertions. The manifest is sealed with INCOMPLETE status, not readiness. Push/remote attestation is recorded separately to avoid a self-referential manifest hash. Reviewer must resolve the directional repro and decide a new120 FPS evidence batch before closure. No ACCEPTED, merge, packaged Server, adverse network, renderer optimization, profiling C or soak D claim.
