# U02-D - IN_PROGRESS

Branch u02/d-collision-hurtbox-sweep from accepted C main 828f83f. C remote verified (Git ref and fresh storage containing 816 SHA-256 checked LFS objects), main fast-forward/push verified. No C rebuild/retest.

D is geometry-only: no HP, damage, shield, crit or death gameplay. Server world pre-actor boundary snapshots all sources/hurtboxes before any actor ticks. Every source advances; all candidates then sort and resolve globally. Before-action mutation drains the same world boundary; actor tick/collider registration order is not a tie-break.

Sphere hurtboxes have explicit stable IDs and subject/life identity. Registry exhaustive collection cannot miss fast targets absent from endpoint overlaps. Relative motion is linear between snapshots; attack axes locked yaw, feet-based center, half extents100/60/90. Piecewise quadratic sphere/box entry/exit clips to active interval; spatial roundoff tolerance1e-7cm never expands gameplay deadlines. Teleport (transform teleport flag), radius change and generation changes break continuity; only current active point may be queried.

Obstruction per hurtbox: origin feet+up90 to nearest sphere point. Visibility event partition includes ray/triangle edge and plane roots plus near-sphere quartic roots; tests include a narrow slit away from the interval midpoint. Retain full contact interval, so blocked first contact cannot discard later visibility. Initial solid containment and closed face touching block. Static box/convex polygon collision and available physics triangle geometry supported; non-polygon/ unavailable physics data are diagnosed and reject potential rays conservatively. Current lab solid shapes must all be supported; no acceptance claim for unvalidated future solid shape assets. Dynamic/nonlinear walls are outside U02 gates.

Original Editor remains open. New reflection/layout requires full isolated D clone build; original binary is not patched or restarted. Private config bytes preserved, only public collision-channel additions staged via filtered Git blob. Verification is IN_PROGRESS; no results claimed yet.
