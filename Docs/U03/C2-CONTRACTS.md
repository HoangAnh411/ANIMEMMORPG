# U03-C2 contracts

Base main: `8d1d2c37bc6259a58dd110a63f4fc1d3963b058f`. Branch: `u03/c2-encounter`. Written before runtime integration. This is an implementation contract, not evidence of completion or acceptance.

## Identity and authority

One server encounter per logged-in controller, containing an immutable encounter ID, monotonically increasing revision, owner, player and monster subjects, and spawn transforms. GameMode creates/destroys ownership on login/logout. Reconnect receives new identity; arena reconnect policy does not apply. Running/Won/Lost are authority state. Resolver's existing timestamp/source/event/hurtbox ordering decides simultaneous lethal; first terminal result wins, no draw. Death synchronously invalidates future source damage.

Only the player–monster pair belonging to the same Running encounter may damage each other. Validate relationship during collection and resolution. No fixture-wide character targeting flag in C2 gameplay. Old regression stations remain separately accessible and never run their enemy fixture alongside the default encounter.

Retry accepts no client actor target. Owning PlayerController sends encounter ID/revision/monotonic sequence; validate ownership, terminal state, identity, revision and sequence before mutation. At one server barrier: close old events, invalidate both old lives, increment revision/lives, reset both subjects, rebase collision, publish Running last. No model advance/admission/damage may interleave the resets. Clear HP/shields, energy, charges, cooldowns, posture, CC/slow/immunity, action/combo/pending, feedback, movement and AI. Preserve command watermarks, user settings, release gates and AwaitingResume. Retry never resumes input; clicking its UI must not attack.

## Monster and scheduler

Dedicated character reuses U01 motor and U02/U03 combat/vital/hurtboxes. Server Idle/Chase/Action/Return/Defeated state; clients present replicated state only. Use Monster definition, not Attack1 or player combo. HP600/raw100, startup .60, active [.60,.75), recovery .75, total1.50s. Capsule radius42/half-height96cm; body radius35 at feet+70, head radius20 at feet+145. Same feet-based depth200/width120/height180 sword box centered at forward100/up90 and shared obstruction/dedup/defense/damage resolver.

Chase/Return speed300cm/s. Detect/retain at distance <=1000cm with environment LOS between feet+90 points; begin attack at <=200cm plus LOS. Distance only admits an action, never guarantees contact. Lose target on death, distance >1000 or blocked LOS; distance >1500 from spawn also enters Return. Track target yaw through startup; active/recovery lock yaw. Action stops horizontal movement and retains gravity. Normal monster hit is blockable/parryable with no automatic stun/Interrupt.

Pure Interrupt cancels Monster startup only, including t=start and strictly before start+.60. Exact active entry refuses; active/recovery refuse. Monster cannot Feint/dodge/guard. E's surviving unblocked/unparried direct hit may Interrupt; Q cannot. No added stun/recovery penalty; subsequent AI action requires fresh admission.

Aim, LOS/range/leash loss, Return, Interrupt and death participate in authority timestamp ordering before endpoint contact. Confirmed earlier hits remain immutable; cutoff excludes contact at/after cutoff with no deadline epsilon. Return cancels unpublished action, cannot rechase, navigates obstacles at300, never teleports. Only within <=50cm of spawn: reset combat/fullHP/new life/rebase exactly once, then become Idle. Dead monsters remain Defeated until Retry. No timeout healing while stuck.

## Local information targeting

Target binding is local to each LocalPlayer. One physical edge toggles off if selected, otherwise selects live opponents <=2000cm whose feet+90 aim point projects inside that LocalPlayer viewport and has clear environment camera LOS. Order: squared screen-center distance, squared character 3D distance, stable subject ID. Hold never repeats. Retain <=3000cm. Hide marker/HP immediately when occluded; clear after continuous >=1s occlusion; visibility resets timer. Offscreen hides presentation without clearing. Death/new life/new encounter clears without replacement. No RPC, camera rotation, aim assist, facing/hitbox/damage authority changes.

## Presentation, reset and delivery

C2 mode in CharacterCombatLab/NetworkLab; solo one encounter, network separate labelled owner stations with navigable return paths. Startup/active/recovery have readable poses and non-color cues; warning matches actual sword geometry. Animation/notify/root motion never determine damage/movement. UI reads server result and offers Retry, visible-only target marker/HP, actual bindings.

Snapshot and history distinguish subject life and encounter revision. Stale events, packets, callbacks and markers cannot affect a new life/revision. Keep existing smoothing/review profile, clients60/server30. One C2 clone; preserve B2/C1 packages and evidence, failed/invalid runs and final C2 environment. No original Editor save/restart, no private config staging. Reflection/header changes require full UBT/cold processes; original Editor Play is not guaranteed C2.

No quest/loot/XP/boss/new profession/dungeon/PvP/product resurrection/prediction/lag compensation/packaged Server or D. Final handoff requires source/binary-associated logs/hashes/video, launchers/checklist/report, commit/push and remote verification; stop READY_FOR_REVIEW, never ACCEPTED/merge/U03 closure. User feel/readability/chase/Retry evaluation remains a separate pending gate; B2/C1 are still not user-playtested.
