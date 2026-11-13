# U03-C1 — Q/E, Feint and Interrupt

Assigned from main f826371b9409c39453e5bd2ed8f8414749f1d34b, branch u03/c1-skills. Earlier statements excluding C1 are historical. One runtime module and the existing authority timeline, retained dodge trajectory and damage resolver remain authoritative. No C2, GAS, prediction, lag compensation, product art or packaged Server.

|Action|Raw|Startup|Active|Duration|Energy|Cooldown|
|---|---|---|---|---|---|---|
|Q Hư Trảm|100|.30|[.30,.40)|.80|20|4|
|E Phá Thế|80|.25|[.25,.35)|.75|25|6|

Both use the existing feet-based sword box and one hit per target/action, with blockable/parryable/Interrupt rules captured with action definition/version. Q never interrupts. E interrupts only surviving targets' normal/Q/E startup after an unblocked/unparried direct contact and damage/shield; shield absorption alone does not suppress it. Exact active-start is excluded. Interrupt adds no stun or lock, and does not share hard-CC immunity. Death precedes effects.

Admission validates life/sequence before priority. Drain old intervals and the entire event group before mutation. Release/control precedes press; equal-time priority is valid X, dodge, guard, Feint, Q, E, attack, jump. Different receive times preserve order. Q/E are edges without buffer, grounded/action-permitted only, requiring voluntary guard release. They replace only normal recovery, resetting combo and pending attacks. Check permission, energy and cooldown before replacement; rejected commands preserve resources/action. Spend and start cooldown on acceptance; no cancellation refunds. Energy caps at100, integrates10/s only after one second since the last spend; Feint is not a spend.

Authority classifies a new Q edge during current Q startup as Feint before new-cast cooldown. Successful Feints are at least1s apart and cancel the unfired action. Lock attack/guard/parry/dodge/skills/jump and sprint for.20s; permit walking under existing slow/control/CC. Invalid Feint preserves the action and creates no buffer. Exact active-start closes Feint. Dodge/guard may replace valid skill startup only; active/recovery cannot be replaced. Validate charges/guard permission before cutoff.

Skills stop horizontal movement, retain gravity and turn to aim through their own startup deadline; active/recovery fix body with free camera. Held WASD resumes at recovery end. Feint releases skill horizontal lock with its separate action/sprint lock, discarding jump presses during it. No menu release gate is used as combat lock. New life resets Feint state; snapshots/history remain life-bound presentation and never restore old gameplay.

Presentation is blockout with provenance, phase labels and distinct textual Feint/Interrupt feedback. Animation, notifies and root motion never authorize motor/damage. HUD shows real bindings, energy and Q/E deadlines. Labelled fixtures use actual action/collision/resolver and do not replace Q/E player input.

Delivery requires Editor/Game builds, all U00–C1 Automation, committed-clone Windows package and three-map smoke, physical input/video and dedicated Editor plus two clients with matching identities/resources/results. Retain failed/invalid runs, logs and hashes. Preserve private config bytes and original Editor without save/restart. Original Editor Play is not guaranteed C1. User has not playtested B2/C1; no feel acceptance. Push and verify remote, then READY_FOR_REVIEW only when required gates are evidenced; no acceptance/merge/C2.
