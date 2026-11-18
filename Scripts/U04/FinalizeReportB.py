"""Author the B handoff from immutable execution records; never grants readiness or acceptance."""
import csv,hashlib,json,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2];isolation=root.parent;runs=isolation/'Runs';docs=root/'Docs/U04'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source='a1e536a79a60a4409e9a6cf64661008f1618e66f'
build=read(runs/'Build-R3-20261118/BUILD-IDENTITY-FULL.json');assert build['sourceSHA']==source
summary=read(runs/'Summary-20261118/RESULTS.json');assert summary['status']=='INCOMPLETE'
audit=read(runs/'Method-Final-Audit-20261118/RECOMPUTED.json');assert audit['completed'] and audit['analyzerSHA256']==digest(root/'Scripts/U04/AnalyzeB.py')
integrity=read(runs/'Final-Integrity-20261118/FILES.json');host=read(runs/'Final-Integrity-20261118/EDITOR-AND-HOST.json');assert integrity['completed'] and host['completed']
automation=read(runs/'Automation-20261118/NAME-RESULTS.json');assert automation['completed'] and len(automation['results'])==140
smoke=read(runs/'Smoke-20261118/results.json');assert len(smoke)==3 and all(r['passed'] for r in smoke)
regressions=[]
for name,file,expected in [('Combat-Capture-20261118','input.json',24),('Defense-Capture-20261118','input.json',15),('Dodge-Regression-Capture-20261118','input.json',38),('Movement-Regression-Capture-20261118','input.json',26),('Network-Capture-20261118','network.json',26)]:
    m=read(runs/name/'Capture'/file);assert m['completed'] and len(m['checks'])==expected and all(x['result']=='PASS' for x in m['checks'])
    regressions.append(dict(run=name,checks=expected,path=str((runs/name/'Capture'/file).resolve())))
rows=summary['trials'];assert len(rows)==38
counts={status:sum(x['status']==status for x in rows) for status in ['PASS','FAIL','INVALID']};assert counts=={'PASS':31,'FAIL':1,'INVALID':6}
tool=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
gates=dict(status='INCOMPLETE',executionCompleted=True,readyForReview=False,sourceSHA=source,toolCommit=tool,
           build=str((runs/'Build-R3-20261118/BUILD-IDENTITY-FULL.json').resolve()),gameSHA256=build['gameSHA256'],moduleSHA256=build['moduleSHA256'],
           mainBaseline='18804bfa32b14471df1ffa4bd7aeaed6cd80074c',counts=counts,matrix=summary['gates'],regressions=regressions,
           automation=dict(executed=140,failed=0,exactNames=True),smoke=3,networkComparisons=41,normalFixtureOff=True,
           finalMethodGroups=9,preCaptureMethodGroups=8,analyzerSHA256=audit['analyzerSHA256'],recomputedOriginalAssertions=38,
           preservationHashChecks=len(integrity['checks']),originalEditorPreserved=True,
           blockers=['Directional dodge preparation/selection repro: fps30-forward-1 retains FAIL; remaining dodge acceptance gates stopped pending review.',
                     '120 FPS combo: only3/5 qualifying trials in7 attempts; four cadence-invalid trials retained.'],
           reviewerAcceptance='NOT_GRANTED; independent reviewer decides follow-up; no merge or U04-C/D')
(isolation/'FINAL-GATES.json').write_text(json.dumps(gates,indent=2),encoding='utf-8')
result={**summary,'sourceSHA':source,'analyzerSHA256':audit['analyzerSHA256'],'handoff':gates}
(docs/'B-RESULTS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
shutil.copyfile(runs/'Summary-20261118/TRIALS.csv',docs/'B-TRIALS.csv')
contract=docs/'B-CONTRACTS.md';s=contract.read_text(encoding='utf-8').replace('Status: IN_PROGRESS.','Status: INCOMPLETE; not READY_FOR_REVIEW. Results in REPORT-B.md.');contract.write_text(s,encoding='utf-8')
matrix='''# U04-B executed matrix

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
'''
(docs/'B-TEST-MATRIX.md').write_text(matrix,encoding='utf-8')
lines=['# U04-B handoff — INCOMPLETE','',
       '**Not READY_FOR_REVIEW; U04.03 is not passed and U04 is not closed.** Two unresolved gates remain: the directional dodge reproduction and insufficient120 FPS combo cadence evidence. Reviewer decides the follow-up. No acceptance, merge, runtime repair or U04-C/D work was performed.','',
       'Baseline main local/remote18804bfa32b14471df1ffa4bd7aeaed6cd80074c. Branch `u04/b-fps-correctness`, isolated clone `Artifacts/U04/B/Source`, runs `Artifacts/U04/B/Runs`. Original main remains at baseline with its exact initial private/untracked status. U04-A closure/source attribution is unchanged.','',
       '## Identity and build','',
       f'Built native source **{source}**, committed before full UBT builds. Later commits change tools/documents only; final native/content/config/plugin/project inputs match that source and no untracked native inputs exist. Game executable SHA256 `{build["gameSHA256"]}`; Editor module `{build["moduleSHA256"]}`. Full build index: `Build-R3-20261118/BUILD-IDENTITY-FULL.json`. Engine5.8.4/CL58902052; actual UBT-selected MSVC14.51.36260, Windows SDK10.0.26100.0. Compiler-newer-than-preferred and engine deprecation warnings remain in logs.','',
       'Generate04:35:58–04:36:05, Editor04:36:05–04:36:29, Game04:36:29–04:36:59, package04:36:59–04:37:47 UTC2026-11-18: all exit0. Exact native logs say `Result: Succeeded`; package says `BUILD SUCCESSFUL`. Three maps cooked: L_Boot, L_CharacterCombatLab, L_NetworkLab. Acceptance evidence uses cold package/Editor processes with -NoLiveCoding. A new plain diagnostic header was fully rebuilt; no reflection layout was patched. Each measured process records executable checksum, creation identity, source/tool/build identity and arguments; native source CLI metadata is not used as binary proof on its own.','',
       '## Measurement and outcome','',
       'Rendered Solo package,1280x720/internal50%, atlas2048, RT pool minimum128 MiB, streaming256 MiB, Lumen indirect/reflections0, virtual shadows0, shadow quality2, background idle0, VSync0. Only the requested cap differs across30→60→120 processes. Actual cvars/viewport are recorded every frame. Dilation1, smoothing false, fixed timestep/frame-rate flags false; the inactive configured FixedFrameRate30 value is retained. No smoothing/input/timestep/dilation change or renderer optimization. At least30 s warmup after readiness; each new process already exceeds the10 s cap-settle requirement.','',
       'Fixture opt-in requires -U04BFPSFixture; ordinary launch does not enable it. The inherited U03Regression URL excludes encounter AI. A flat300 m by30 m floor has top z0 at y20000, no obstacles/slope; the native product pawn starts at x−10000. Combo uses a new stationary600 HP native lab dummy, existing crit-off roll0.5, no shield/defense. Setup/reset occurs before recording; a setup request during recording records INVALID and refuses mutation. Product actions are guarded Windows input; no action or movement is fabricated by a gameplay call.','',
       'Samples are taken after actor ticks, including actual capsule positions and trajectory commits, and buffered until capture end. Authority input receipts, admissions, action starts/completions and hit identity/HP are retained. Native QPC seconds equal Windows QPC/frequency plus16777216; input records keep before/after emission brackets. Frame evidence is rendered game-thread wall cadence, **not scanout**; video30FPS is visual evidence only.','',
       'Each trial FPS = interval count / summed wall intervals; percentile interpolation uses rank(n−1)p. Qualification independently requires mean within5%, at least95% intervals within10% of the target period, no interval greater than two periods, continuous counters, valid focus/configuration/identity. Full bracketing frame intervals are retained for boundary windows; no bad frames are removed. Movement starts after0.5 world seconds continuously stable at actual500/700 cm/s, then uses exactly10 world seconds. Boundary position/wall time = left + alpha(right−left), alpha=(boundaryWorld−leftWorld)/(rightWorld−leftWorld); both original samples and alpha are in assertions. Forward projection, full path length and lateral deviation are published.','',
       '| Gate | 30 FPS | 60 FPS | 120 FPS |','|---|---|---|---|',
       '| Walk |3/3 PASS|3/3 PASS|3/4 PASS;1 INVALID|',
       '| Sprint |3/3 PASS|3/3 PASS|3/4 PASS;1 INVALID|',
       '| Combo |5/5 PASS|5/5 PASS|3/7 PASS;4 INVALID; missing2 valid|',
       '| Directional dodge |first forward attempt FAIL; related gate stopped|not run, blocked|not run, blocked|','',
       'Every movement attempt measured exactly5000/7000 cm by interpolation, with zero lateral deviation; qualifying trials meet cadence independently. Wall duration ranges: walk9.9995033741–10.0006357618 s; sprint9.9993557259–10.0003245212 s. All17 combo attempts have three unique hits on one target life,60/70/90 damage, HP600→380, crit=false, natural authority completions; maximum timeline arithmetic error1.13243e−14 s. Only13 qualify by cadence. First state observation is the next continuous sampled frame; observed lag is retained separately and never relaxes the1 microsecond timeline rule.','',
       'At120 FPS, the four rejected combo attempts have in-band fractions92.5714%,93.7143%,85.7143%,94.8571%, below95%, despite mean119.96–119.98 FPS and correct gameplay. No missing samples/focus/cvar/reset issue was observed in those windows. The observed limitation is interval jitter; its hardware/software cause has not been established and no profiling/optimization was attempted. Exactly7 combo attempts were used. Their gameplay is supplemental, not U04.03 PASS.','',
       'The forward dodge at30 FPS has299.9994551763 cm actual displacement,0.25 s motion and0.35 s release deadline; cadence passes30.076898 FPS. Its locked direction is−X after accepted W/Shift edges in one input-processing frame. The original FAIL is retained. Direction preparation versus product input-state ordering remains unresolved because intent direction was not directly instrumented. [Reproduction and separate follow-up proposal](B-DODGE-REPRO.md). No runtime fix or relabeling was made; remaining directional acceptance cases stop at this gate.','',
       '## Every attempt','',
       'All38 rows follow. FPS and in-band percentage are per-window calculations, not an average of instantaneous FPS. Full P50/P95/P99/max/histograms, wall/world samples, input events, assertions and hashes are in [B-RESULTS](B-RESULTS.json), [CSV](B-TRIALS.csv) and the published manifest.','',
       '| Trial | FPS | in-band % | P99 / max ms | Gameplay result | Label |','|---|---:|---:|---:|---|---|']
order={'walk':0,'sprint':1,'forward':2,'back':3,'left':4,'right':5,'combo':6}
for row in sorted(rows,key=lambda x:(x['targetFPS'],order[x['case']],int(x['trial'].rsplit('-',1)[1]))):
    original=read(Path(row['assertionPath']));g=original['gameplay']
    if row['case']=='combo':detail=f'{g["authorityDuration"]:.15f} s;220 HP'
    else:detail=f'{g.get("forwardCm",g.get("distanceCm")):.6f} cm;err {g["errorCm"]:+.6f}'+(' ;direction−X' if row['case']=='forward' else f';wall {g["wallDuration"]:.6f} s')
    lines.append(f'|{row["trial"]}|{row["measuredFPS"]:.4f}|{row["within10Percent"]*100:.4f}|{row["p99"]*1000:.3f} / {row["max"]*1000:.3f}|{detail}|{row["status"]}|')
lines += ['', '## Regression, methods and preservation','',
          'Fresh cold-clone MCP TestRunner Automation:140/140 Success; exact expected=discovered=executed names, no duplicates/missing/extra, queue empty, actual loaded B module verified. Raw schemas/logs and NAME-RESULTS.json are published; no supported XML export exists. Three packaged NullRHI map load smokes pass; those are load checks, not rendered gameplay. Ordinary normal-encounter package passes4 fixture-off checks using actual command line, crit state, position and inert B commands.','',
          'Fresh final-source A-derived Windows regressions: combat24, defense15, legacy dodge38, movement/focus26, network26 checks, all pass. Dedicated Editor server has0 local players; each client has1 owned pawn and an actually loaded B DLL, with advancing time/frame and physical-input readiness. Client60/server30 profile retained;41 independent saved server/client comparisons pass, plus reconnect retained-history/no-old-feedback verification. Legacy dodge uses40 ms direction preparation and does not replace the blocked stationary-admission B case. Historical D/A names and the inherited A read-only diagnostic flag in these regression tools are provenance labels; all paths/source identities/new evidence are B.','',
          'Before capture8 synthetic method groups pass. Final tool-only audit adds receipt-versus-processing and structural INVALID classification coverage (9 groups total): valid receipt followed by rejection/late processing/no action remains gameplay FAIL; focus/source/config/data-integrity defects stay INVALID with observed gameplay retained. This audit occurred after capture, changes no runtime and recomputes all38 original labels/numeric results unchanged. Both analyzer SHA256 revisions and all method logs/recomputations are retained. Method tests never count as binary gameplay evidence. Five negative identity guards and live wrong-creation Stop preservation pass.','',
          f'Final preservation passes{len(integrity["checks"])} hashes, including every recorded original preflight file, raw/published U03 D/D-R1 and U04-A evidence, both48-file U03 packages and48-file A/B packages, modules and engine. Original Editor PID10880 retains creation UTC2026-11-18T04:17:19.8968150Z and initial window placement; it was never saved/stopped/restarted. All B Editor/game processes are closed, including reconnect. Original main/private changes and ignored historical workspaces remain in place. Initial free disk138574770176 bytes against25 GiB reserve; final snapshot has{host["freeBytes"]} bytes free. No cleanup or engine download.','',
          '## Retained nonpassing setup and handoff','',
          'Build-Initial was interrupted and contains explicit first-include errors. Build-R2 and preliminary Build-Final succeed but precede the final trajectory-end diagnostic correction; only Build-R3 is used for acceptance gates. An early pre-capture process/index used abbreviated source metadata, was stopped and is explicitly INVALID; full40-character identities are now enforced. Original index/process are retained rather than overwritten. All six cadence-invalid attempts and the directional FAIL remain unchanged. Generated cook SecurityToken/blank-line changes were normalized only in the isolated clone by the semantic guard; no original config was changed.','',
          'Publication: `Docs/U04/Evidence/B/Review-20261118/MANIFEST.json`, raw runs under `Artifacts/U04/B/Runs`; package bytes stay in the isolated Build-R3 archive with full file checksums. `VerifyEvidenceB.py` verifies raw/published hashes; `--published-only` works on another checkout. `RecomputeB.py --runs <rawRuns> --out <newFile>` reproduces all original trial decisions with the final analyzer; it never overwrites assertions. The manifest is sealed with INCOMPLETE status, not readiness. Push/remote attestation is recorded separately to avoid a self-referential manifest hash. Reviewer must resolve the directional repro and decide a new120 FPS evidence batch before closure. No ACCEPTED, merge, packaged Server, adverse network, renderer optimization, profiling C or soak D claim.']
(docs/'REPORT-B.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Authored INCOMPLETE handoff,38 retained attempts,31 PASS/6 INVALID/1 FAIL')
