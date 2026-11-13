# U03-B2 - test matrix

**ACCEPTED (technical) at `fa5c74cb`**, verified native source `515f8190a35afbc8663669419c6ce502967e3df3`; see [ACCEPTANCE-B2](ACCEPTANCE-B2.md). The user has not playtested B2; presentation remains blockout and feel/product visuals are not accepted. Results below are existing handoff evidence, not reruns during documentation closure. Actual results and failed/invalid runs are in [REPORT-B2](REPORT-B2.md). No count was used as a coverage target.

| Rule/layer | Evidence | Result |
|---|---|---|
| Parry [start,start+.12), spacing.60, hold/release/cooldown, one eligible hit | `ParryHalfOpenEdges`; `WorldLateInputAndStableSimultaneousHits`; physical/video parry then block | PASS |
| Inclusive +/-60 degrees, rear, coincident source; unparryable independent of bypass/grab | `AngleAndIndependentHitFlags`; `WorldGuardAnglesAndHitTimeAim`; `WorldFlagsInterruptAndLethalEffects` | PASS |
| Posture25 to0 still blocks; break.8/refill; immune break without lock;2s/25-per-second eligible integration, no guard backfill | `PostureBreakAndEligibleRegen`; real four-block break/X | PASS |
| Strongest slow/expiry; shorter/equal/longer hard CC;2s cumulative lock, .50 free reset,2s immunity | `EscapeSlowAndCooldown`; `ControlReplacementBudgetAndFreeReset`; timeline/world fixtures | PASS |
| X airborne, invalid no spend,1s immunity/30s cooldown, clears slow/launch/budget, future slow allowed, no energy cost | `TimelineGuardReplacementAndAirborneX`; `EscapeSlowAndCooldown`; physical grab/break/X and network | PASS |
| Crit once, final rounding, shield before HP, dedup on block/parry; block suppresses attached effects; lethal before effects | `WorldParryBlockDedupCritShield`; `WorldFlagsInterruptAndLethalEffects`; inherited `DamageFormulaRoundingAndCrit` and U02 vital/collision tests | PASS |
| Late guard/release/aim cannot rewrite prior hit; old guard/life identity rejected; startup replacement validates before cancel/reset combo | `WorldLateInputAndStableSimultaneousHits`; `WorldAimCausalityOwnershipLifeAndMotor`; `TimelineGuardReplacementAndAirborneX`; actual LMB/RMB cancellation | PASS |
| Long/short updates and reversed collection; hard CC/death cut the retained wall/StepUp prefix; two dodging pawns | `HardCCMidWallAndStepTrajectory`; `SlowPreservesRetainedDodge`; inherited B1-R1 mid-hit/lethal/pawn CCD tests, rerun | PASS |
| U00 through B1, combo, ground/landing, menu/focus/Resume/held keys, life/reset/saved moves, movement after expiry | all107 Automation Success,0 Failed in MCPTests-121631;22 physical checks including held W after natural stun expiry | PASS |
| Physical rebind and motor | `PhysicalRebindLetterReconciliation`; Guard C / X Z through actual UI and restoring defaults; actual200cm/s/no sprint/jump | PASS |
| Dedicated Editor + two clients, authority identity/outcomes/HP/posture/CC/X, duplicate/stale/unowned/reset | NetworkCapture-1225:21/21 live checks plus6/6 independent saved-sample deadline/result comparisons | PASS |
| Dodge network regression and reconnect | DodgeNetworkRegression-1235:22/22; Session-122206:2/2 live reconnect checks after old physical X cooldown | PASS |
| Build/package/maps | committed-clone Generate/Editor/Game exit0, UAT exit0, three-map smoke3/3 | PASS |
| Presentation/launchers |22-check final input video, actual ordered two-note loopback, parry ring; source/module/engine/package hashes; ready/minimize/Stop/restore, including reconnect | PASS (blockout; user visual judgment pending) |

The14 B2 Automation tests are listed in the manifest's complete107-test result. The93 inherited tests were rerun against this source; historical B1 videos are not used as proof of B2 binaries. Input videos encode30FPS wall time; model partitioning is not rendered FPS. Sequential client inputs do not prove simultaneous contacts; real Game-world fixtures provide that proof.

Retain all failed/invalid/superseded runs: initial compiler/hash failures, multi-source setup, slow fixture blocker, late physical parry edge, real letter-rebind bug, AI fixture HUD/aim correction, UTF-8 tail/probe-counter harness issues and Stop wrapper correction. See report, manifest and raw/published logs. No packaged Server, lag compensation/prediction/U05, U04 benchmark, product PvP or product art acceptance is claimed.
