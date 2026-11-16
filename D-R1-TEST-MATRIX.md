# D-R1 test matrix

| Requirement | Evidence to collect |
|---|---|
| Shared environment LOS for subject and label | Native world wall/camera tests; real hidden/reveal captures |
| Partial sword occlusion | Native exact geometry; world depth proxy; GPU captures with mixed clear/blocked segment positions |
| Hidden event consumed, reveal within window silent | Native history/LOS integration; client metrics, loopback and video |
| Expiry cannot rearm | Native absolute window; real hide/reveal after expiry |
| Independent clients / reconnect | Dedicated clone server, two clients, owner/proxy and reconnect captures |
| No debug dependency | Captures without presentation debug or on-screen messages |
| Regression | Full U00–U03 automation, Editor/Game, package, Boot/combat/network smoke and affected input/Retry/Tab regressions |

Pending rows are not passes. Preserve failed/invalid attempts and record exact final source and hashes separately from inherited D evidence.
