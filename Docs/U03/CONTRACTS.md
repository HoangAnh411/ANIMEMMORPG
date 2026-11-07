# U03 contracts — A0

Approved plan 2026-11-07. Implement A0 only, no U03 runtime binding. One existing module. U02 Attack1 unchanged.

## Fixed definitions

|Action|Active [start,end)|Duration|Raw|Energy/CD|
|---|---|---|---|---|
|Attack1|.16,.22|.40|60|0/0|
|Attack2|.18,.25|.45|70|0/0|
|Attack3|.26,.36|.60|90|0/0|
|Q|.30,.40|.80|100|20/4|
|E|.25,.35|.75|80|25/6|
|Monster|.60,.75|1.50|100|0/0|

Box feet-based depth200/width120/height180cm, center(100,0,90); one hit/target/action. Definition captured immutable by value with version. Intervals/candidates retain old action raw/yaw/identity.

## Model admission/timeline

Monotonic controlled server time, never client-backdated. Batch sorts receive time, validates sequences BEFORE priority sort (X,Dodge,Guard,Feint,Q,E,Attack,Jump), preserves distinct earlier commands. Wrong-life/duplicate/stale reject. Defense/dodge/X/Feint/jump return Unsupported in A0, not fake accepted actions.

Advance and SubmitBatch require ITimelineResolver. Before committing each next structural boundary, NextEvent discovers the earliest unresolved world event through that boundary, including incoming hits during startup and newly created successor actions. ResolveInterval receives only the strictly earlier interval. The clock then commits to the event timestamp; ResolveEvent can call CancelCurrent before endpoint contact, expiry, successor creation or admission. The resolver consumes the event and maintains U02 global timestamp/sourceID/eventID/hurtbox ordering. It must discover every event that can mutate this model before the interval is confirmed; it cannot discover a past event after confirmation. No rewind of confirmed hits. Reentrant Advance and cancellation outside the event callback are rejected. Unopposed helpers explicitly assert there are no world events and are only for isolated model tests. A1 must supply real world collection; the synchronous ordering barrier itself is enforced by the A0 API.

Attack buffer only in normal attacks; slot TTL.15, newest replaces. No buffering during skills/dodge/guard/CC/Feint/airborne/control lock. At natural end consume only expiry>end; successor starts exactly end with queued aim, remainder collected in same update. Third chains first. Grace.15 after1/2; exact deadline expires. New edge exactly action-end fresh. Full combo220raw/1.45s (not actual HP lost). Menu/focus clear pending, drop guard, keep release/AwaitingResume gates; accepted action continues. Release/control transitions precede presses.

Q/E only cancel normal recovery, not startup/active/each other; no skill buffer. Energy100 regen10/s after1s since spend, integrate eligible intervals only. Cost/CD only on success. Dodge/Guard replacement must be valid BEFORE startup cancellation. Pure Interrupt startup only; exact active-start refuses. Death/lost-ground force cutoff. Combo resets on dodge/skill/hardCC/death/lost-ground/guard startup cancel; slow alone does not reset. Current snapshot authority, history64 presentation only.

## Locked dependent-delivery gameplay (not implemented A0)

Dodge300cm/.25s, motor1200cm/s swept capsule, lock through.35, start spacing.60, two charges sequential2s each. Buffer.15 only during dodge/waiting.60 with charge; no held repeat/i-frame. Camera-yaw normalized WASD or backward aim, captured direction; slow does not alter dodge. Blocked consumes charge; floor loss stops movement/falls. U01 step/slope/floor constraints. Saved moves cannot recreate old-life actions/charges.

Guard120deg including60 boundary,70% direct damage reduction,200cm/s no jump/sprint. Posture100 loses25/hit. Hit250 reduced before break. Break.8 then full; hardCC immunity still removes guard/breaks/refills without .8 lock. Outside guard and2s no hit regen25/s with no held-guard backfill. Rejected/interrupted guard needs release/repress. Horizontal source direction at hit; coincident source uses opposite attack direction. Parry[0,.12), spacing.60, one hit/window, no crit/posture/damage/effect; no automatic counter/stun/Interrupt. Block crit once, reduction then round-half-up after all factors. Parry/block consume dedup. Bypass-block and unparryable independent.

HardCC replaces only longer than remaining; cumulative2s then immune2s, reset after continuous free.50. X only during hardCC/CD30, clears hardCC/slow/pending launch/budget, immunity1s to hardCC only, no damage/future-slow immunity. Fixture labels slow/stun/knockdown/launch/grab, no invented launch skill/parameters. Q Feint same Q startup only, no refund, lock.20 attack/guard/dodge/skill/jump, walk/no sprint, successful Feints>=1s. Q never Interrupt. E unblocked/unparried direct hit interrupts startup, no stun; shield alone not effect immunity. Lethal before effects.

Attack/Q/E stop horizontal retain gravity, turn startup to own deadline, body fixed active/recovery, free camera. Held WASD resumes after lock, no combat release gate or stale jump replay. Resolve geometry/obstruction -> life/action/dedup -> hit-time defense -> damage/crit/shield -> death -> surviving effects -> publish.

Monster HP600/raw100 chase300cm/s detect10m/leash15m/reset within.5m spawn; attack within2m plus geometry/LOS feet+90. Same box, body sphere35 at70/head20 at145; humanoid capsule42/96. Server-only idle/chase/action/return/defeated, no rechase before reset, return/death cancel future hit. Only station owner target, no PvP/friendlyfire; multi-source fixture labelled.

Solo one player/monster, network separate stations. Server win monster dead/lose player dead, same-time lethal U02 order no invented draw. Retry owner station only, resets vitals/resources/charges/CD/CC/action/pending/target/position/AI, increments life/encounter revision/rebases collision; preserves watermark/settings/release gate, never auto Resume or arbitrary actor reset.

Tab local information only:20m select/30m retain/occlusion1s, screen distance then3D thenID, offscreen hides UI only, death/newlife clears; no aim changes. Settings existing envelope payloadv2 readsv1, preserve valid bindings, conflict groups default+notice, load no save, LocalPlayer isolated. Attack/Guard/Dodge/X/Q/E/Target LMB/RMB/Shift/X/Q/E/Tab; Escape/camera fixed, R/F/1-4/I/K/M reserved, single key/mouse no wheel/chord.

Presentation blockout provenance, no root-motion gameplay, missing/duplicate notify irrelevant. Parry ring/two-note, block bar, distinct Feint/Interrupt, miss only completed no contact; feedback1.2s, actual key HUD, visible-only opponent HP, no auto target.

## Gates

A0 contracts/model -> A1 combo -> B1 dodge -> B2 defenseCC -> C1 skills -> C2 encounter -> D presentation/settings/integration. Each separate branch from accepted main, committed clone builds/tests, review stop. ACCEPTED grants neither merge nor next delivery. A0 no new playable content/package/launcher. A1-D package/input/video/dedicated Editor+2clients scoped launchers/stop/placement restore. Original Editor/private config untouched. No modules/plugins/GAS/framework. No packaged Server, prediction U05, performance U04, product art/progression/backend/free PvP.

Interval endpoint contract: FActiveInterval carries bEndExclusive. At a current-time endpoint still inside active, contact at that timestamp belongs to the pre-admission barrier; a point at exact active entry is evaluable. Active-end/cancellation cutoff always excluded. Adjacent inclusive sampling endpoints rely on the shared action/target dedup, never double damage. This is consistent with inherited U02 active slices and does not widen gameplay deadlines.

Review correction: interval delivery before a resolver event is always exclusive at its endpoint. ResolveEvent validates and applies cancellation at the committed current time before any point sample there. A valid cutoff excludes that point; invalid cancellation preserves it. Earlier confirmed intervals remain immutable. Death is latched in the model so stale admission context cannot start another action after the resolver has confirmed death. The integrated resolver tests cover successor startup interruption/death at .45 during Advance(1), not merely a separate ledger.
