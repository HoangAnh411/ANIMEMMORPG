# U03-D contracts

Status: D.1 audit in progress. This file is a contract, not evidence of passing gates.
Base: `bc3a9955a8c0ecc1cb7f0d43dce13300c9664ac9`; branch `u03/d-integration`.

## Scope and invariants

Complete technical blockout presentation/settings (U03.06) and regress U03.01–09 against `Docs/Description.md` and `Docs/ROADMAP.md`. A0–C2 timing, damage, admission, defense, dodge trajectory, authority, Retry transaction, release gates and per-owner encounters remain authoritative and unchanged. No product anime character/animation, shared monster zone, new skills, balance, progression, prediction, packaged Server or U04 work.

Presentation lives under existing U03 and reuses UU01AnimInstance, U02 confirmed snapshots/history, U03 asset authoring and existing encounter HUD. Inputs are confirmed data, server clock and LocalPlayer. It cannot mutate model/damage/motor. Root motion and notifies cannot determine contact or move capsules. Dedicated servers create no UI/audio.

## Feedback contract

Every event is scoped by encounter ID/revision, subject ID/life, action and event identity. New life/revision/reconnect invalidates old presentation. Important feedback expires at authority event timestamp +1.2 seconds, with a half-open window; repeated snapshots never extend expiry. Late data presents only the remaining window. Repeated/stale data never replays sound. No animation/overlap-derived hit or miss.

Hit, block, parry, miss, guard break, Feint and Interrupt have distinct labels/shapes and blockout sound signals. Preserve parry circle and existing 660 then 990 Hz two-note signal; block has a barrier mark. New signals are authored synthetic PCM, with generation parameters documented, no downloaded assets. Diagnostics remain separately gated.

Miss requires authority-completed action and zero valid contacts. Block/parry are contacts. Cancelled actions never emit an additional miss. Audit authority outcome/history before adding data plumbing; missing telemetry is not permission to change gameplay.

Preserve Attack1–3/Q/E clips, grip/carry/locomotion. Readable preparation, strike and recovery poses/cues; add dodge/guard/break/hard CC/X poses. Monster telegraph uses existing direction and sword box geometry, with non-color cues and unobscured startup.

## HUD, settings and control

HUD shows HP, energy, posture, dodge charges/recharge, Q/E/X cooldown, CC and actual bindings for existing actions. Recent-hit HP is independent of Tab: authority hit timestamp window, matching current identity, on-screen projection and clear environment camera LOS; hide immediately when offscreen/occluded. It never changes target. Tab selection/retention stays C2. Won/Lost/Retry read authority; Retry preserves AwaitingResume/release gate and click cannot attack. Explain A/B as separate owner stations.

Reuse UU01SettingsSubsystem, JSON v2 and SaveGame. Single keyboard/mouse binding only; reject duplicates, wheel, chords, reserved keys. Preserve valid v1/v2 choices and restore conflict closure with a clear message. No load-time rewrite. Missing/corrupt/unsupported data must recover safely. Tests use isolated slots/directories, never user settings. Menu/focus/rebind/Retry/Resume quarantine held inputs. Store user preferences only, no combat progress.

## Initial source audit and asset inventory

| Requirement | Existing source/assets | D work or regression |
|---|---|---|
| Attack clock/identity | U01AnimInstance; U02Presentation; U02PresentationTests | Extend identity regression to encounter revision; inspect all phases |
| Attack1–3/Q/E | Content/AnimeMMORPG/U02/Animation; Content/AnimeMMORPG/U03/Animation; U03AnimationEditor | Preserve and inspect clips/root/grip; author additional blockout poses |
| Parry/Feint/Interrupt | U02CombatComponent snapshot fields and procedural parry tone | Product feedback currently depends on debug drawing; migrate rendering/audio consumption |
| Miss/contact | U02CollisionWorld confirmed resolver results and debug HUD | Audit valid block/parry/cancel outcomes before exposing completed authority feedback |
| Tab visibility | U03LocalInformation; U03TargetModel | Reuse projection/LOS; recent-hit feedback needs independent identity/window |
| Result/Retry | U03Encounter; U01Menu; U03LocalInformation | Regression only for authority and input gates |
| Bind/migrate/store | U01Settings; U01SettingsTests; U01Menu; U01PlayerController | Existing conflict-closure recovery and no load writes; audit storage and held-key coverage; fix obsolete Target unavailable label |
| Monster telegraph | U03Encounter and existing blockout monster | Replace required debug-only cues with packaged presentation |
| Launch/profile | Scripts/U03/*C2*; C2 manifest | Reuse guards; read exact profile before copying; one D clone |

Existing C2 manifest records 131 successful tests for its source, not a D result. Private `Config/DefaultEngine.ini`, `Docs/Maintenance/` and `Scripts/Maintenance/` existed at entry and must not be staged or changed. Preserve accepted artifacts and failed runs. Original Editor must not be saved/restarted/closed; minimize only after D clients ready. New reflection/header layout requires full UBT build and cold clone processes, not original Editor Play.

## Delivery boundary

Commit source before final clone gates. Build/test/package in one D clone; rerun only affected gates after fixes. Retain failed/invalid evidence with source, engine/toolchain, process/world/owner/role and hashes. Final root launchers: Play-U03-D.cmd, Play-U03-D-Network.cmd, Stop-U03-D.cmd and Play-U03-D-CHECKLIST.md. REPORT-D.md, Evidence/D/MANIFEST.json, CLOSURE-D.md separate inherited/new evidence. Reviewer AI verifies technical evidence; user playtests feel and authorizes closure. Stop READY_FOR_REVIEW only after all required gates pass and branch push/remote verification. No ACCEPTED/merge/U03 closure.
