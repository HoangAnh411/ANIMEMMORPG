# Counter definitions

Counters are uint64 owned by each collision-world instance. Only Active windows increment; begin zeros all fields, end disables before export. One closed measurement per process. No totals aggregate across worlds/runs. Trace counters are sampled after actor tick from these values. Summary uses end minus reset-at-begin; Queries has independent end-minus-begin.

|Field|Unit / exact increment|
|---|---|
|collectIntervals|one CollectHitCandidates entry (before source validity return)|
|hurtboxVisits|one entry into Hurts loop per collected interval, including source/self and rejected registrations|
|geometryTests|one actual SphereAttackContact invocation after eligibility/continuity tests|
|occlusionCalls|one Unobstructed entry, including HUD visibility calls; not necessarily one per target/contact|
|candidates|one Out.Add after geometry, visibility and timestamp acceptance, before dedup|
|confirmedHits|one Confirmed.Add after successful applied product damage/parry result|
|duplicateSuppression|candidate already present in ledger resolved hit identities, observed at ResolveHit entry or rejected CanResolveHit in CollectCurrent; repeated suppression observations count separately|
|actions|one product ActionStarted trace event in the active window|
|queriesPostContactDelta|existing Queries after SphereAttackContact reports contact; never total visits/queries|

Target subject count and IDs/HP are exported from fixture actors; registration gauges must additionally be validated against actual world registrations before matrix acceptance. Visits should equal collected intervals times actual registered hurtbox count when registration set stays constant; includes attacker hurtboxes. Geometry is eligible intervals per target hurtbox, not N alone. Occlusion includes FirstVisible callback multiplicity and HUD; derive measured counts from source and actual intervals, never equate to N. Duplicate suppression observation adds read-only HasResolvedHit membership probes; overhead pairs include these lightweight observations.

CPU scopes: WorldUpdate (DrainAt inclusive including rejected/reentrant calls), CollectCandidates, Geometry (SphereAttackContact), Occlusion (Unobstructed), ResolveDedup (ResolveHit), ApplyDamage (ApplyResolved only). Dedup filtering outside ResolveHit is currently not covered by ResolveDedup; this must be completed or declared a method gate deficiency before matrix.
