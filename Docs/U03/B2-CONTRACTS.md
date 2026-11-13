# U03-B2 — defense, control and escape

Assigned from main `88244cf67ddc679fec2ceaccb0d9f68c40ce653a`, branch `u03/b2-defense-cc`. Historical statements that B2 was unassigned no longer apply. This delivery does not authorize acceptance, merge or C1.

One runtime module, dispatcher/rebind/release gate, cooperative world barrier, retained B1-R1 swept trajectory and U02 hit/dedup/vital path. No Q/E/Feint gameplay, AI, encounter/Retry/Tab, framework, GAS, prediction, lag compensation or packaged Server.

## Authority and time

All deadlines use monotonic server seconds and half-open intervals. Drain old intervals and the full stable timestamp/source/action/hurtbox event group before aim, release, press, escape or action mutation. Current life-bound model state decides defense while all models are at the hit barrier; presentation history never decides a past hit. Sequence validation precedes command priority; release/control transitions precede presses. Client sends intents with pawn/life/sequence only, never damage or defense outcomes.

Order: geometry/obstruction → life/action/dedup → defense → crit/damage/shield → death → surviving target effects → publish. Parry and block consume dedup. Parry consumes no crit roll. Block rolls once, applies factor .30 before final round-half-up, then shield before HP. Block/parry suppress attached adverse effects; shield alone does not. Death cuts future action and dodge trajectory at its event timestamp.

## Guard and posture

RMB uses the existing rebind path. Guard follows aim yaw and moves at 200 cm/s in camera-relative directions; no jump/sprint. Admission requires grounded, playing, no hard CC or dodge lock and either idle or normal-attack startup. Validate before replacement; accepted startup replacement resets combo. Active/recovery rejection preserves the old action. A rejected/interrupted held guard cannot rearm without release. Menu/focus, lost ground, death and hard CC drop guard and clear relevant pending intents.

Horizontal angle includes ±60°. Source direction is evaluated at hit time; coincident feet use the negative attack direction. Bypass, grab and existing DoT cannot block. Unparryable is independent of bypass. A valid press opens [start,start+.12) if start≥previous-open+.60; holding or pressing during cooldown never buffers a new window. First eligible hit closes it immediately; no counter/stun/Interrupt.

Posture 100, normal block costs25; the 25→0 hit still receives damage reduction. Break lasts .8s, participates in the hard CC budget and accepts X; leaving break refills posture. During hard CC immunity break drops guard/refills without lock. Outside guard after2s without a valid hit, integrate25/s only over eligible intervals; never backfill held time.

## Control and X

Slow uses the strongest active fraction, retaining weaker unexpired applications; dodge speed/distance stay unchanged. Stun/knockdown/launch/grab/break share replacement: only a duration strictly greater than remaining replaces, never adds. Accumulate locked time only, at2s exit and gain2s hard CC immunity. Reset budget after.50s continuously free. X requires current hard CC and ready-at, works airborne, clears current hard CC/slow/pending launch/budget and grants1s hard CC immunity. Cooldown30s only on success; no damage, energy cost, damage immunity or immunity to future slow. Launch fixtures carry a labelled state only; no invented impulse or profession skill.

## Delivery gates

Full Editor/Game build, fresh complete Automation, Windows package and three-map smoke from committed source in a clone; physical defensive input/video and dedicated Editor server plus two clients, including reset/reconnect/replay/ownership checks. Evidence distinguishes model, world, physical input and network processes; retains failed/invalid runs. Original Editor remains open without save/restart. Private config bytes and secrets are preserved. Launchers verify source/binary/package hashes, client60/server30, ready/minimize/restore behavior. Original Editor Play is not guaranteed to run B2. Stop at READY_FOR_REVIEW only after all required work and remote SHA verification.
