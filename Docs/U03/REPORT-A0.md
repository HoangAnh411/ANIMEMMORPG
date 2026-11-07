# U03-A0 ? READY_FOR_REVIEW

Ch? b?n giao A0. Ch?a ACCEPTED, ch?a merge main, ch?a b?t ??u A1. Ng??i d?ng duy?t k? ho?ch v? giao ri?ng A0 ng?y 2026-11-07.

## Ngu?n v? ph?m vi

- N?n main v? remote x?c minh tr?c ti?p: `f8434d23e4f27a649dde4ea21f47dd296c0fc9ba`. Nh?nh `u03/a0-contract-model`.
- **Source build/test cu?i: `9ef8e38c2f47f7b082fef32fb9d9a9a7cb8761cf`**, ?? push v? ??i chi?u `git ls-remote`. Commit h? s? ti?p sau kh?ng ??i Source/Content/Config/Plugins/project; kh?ng g?n SHA h? s? cho binary.
- Source ch? th?m `U03/U03ActionModel.h/.cpp` v? `Tests/U03ActionModelTests.cpp`. [Contract](CONTRACTS.md), [matrix](TEST-MATRIX.md), ROADMAP chia A0/A1/B1/B2/C1/C2/D, gi? ID/lu?t gameplay.
- Kh?ng ??i runtime U01/U02, input, animation, assets, maps, module/plugin/project ho?c config ?? commit. Kh?ng tri?n khai A1. Diff: `git diff f8434d2..9ef8e38c2f47f7b082fef32fb9d9a9a7cb8761cf -- Source Docs/U03 Docs/ROADMAP.md Scripts/U03`.
- Working tree g?c ban ??u ch? `Config/DefaultEngine.ini` modified, kh?ng staged. Hash ??i chi?u tr??c/sau x?c nh?n nguy?n byte; kh?ng in/stage token, kh?ng restore config g?c. [Manifest](Evidence/A0/MANIFEST.json) ghi boolean b?t bi?n v? hash source/binary/log.
- Editor g?c PID12280, start 2026-11-07 10:34:06 local, gi? m?; kh?ng save/restart/Live Coding hay d?ng binary g?c l?m b?ng ch?ng m?i. Header/model m?i d?ng full UBT trong clone; Editor g?c ch?a ???c x?c nh?n ?? n?p native m?i. Khi c?n refresh Editor g?c ph?i full build/restart t?i m?c ???c giao.

## Model v? c?c trace c?n review

`FActionDefinition` fixed/versioned; `FActionInstance` ch?p const value, identity v? cutoff. `FTimelineModel` gi? buffer/grace/admission/timeline; `FResourceModel` t?ch ph?n energy v? CD. Kh?ng UObject, RPC, actor tick ho?c clock h? ?i?u h?nh. Q/E ch? l? command model, ch?a bind gameplay. X/dodge/guard/Feint/jump ch?a c? implementation ? A0 tr? Unsupported r? r?ng; priority sorting v?n ki?m tr??c c?c command ?? h? tr?.

Sequence ???c x?t theo receive/sequence tr??c priority ?? kh?ng lo?i nh?m command sequence th?p nh?ng h?p l?. Payload xung ??t c?ng sequence/timestamp b? t? ch?i to?n b?, kh?ng cho collection ch?n h?nh ??ng. Batch ??o th? t? v?n ra c?ng action/k?t qu?.

Timeline c? c?c ?o?n active c?a action c? v? successor b?t ??u ??ng action-end trong c?ng update d?i, gi? raw/aim ri?ng. TTL ??ng end kh?ng consume; c?nh m?i ??ng end x?t m?i; slot m?i thay c?; Attack3 n?i Attack1. Ba definition c?ng220 raw/1.45s. ??y l? raw/model, kh?ng ph?i HP runtime m?t220.

Endpoint hi?n t?i c?n active ???c sample tr??c admission; active-end/cutoff lu?n lo?i tr?, kh?ng epsilon. C?c sample ??u/cu?i k? nhau ph?i qua ledger dedup. H?y b?ng dodge/guard ch? khi replacement h?p l? v? c?n startup; ??ng active-start t? ch?i. Interrupt startup lo?i active t??ng lai. Death/Interrupt ledger c?t event tr??c event ti?p theo.

[Timeline th?c](Evidence/A0/TIMELINE.log) v? [log Editor cu?i](Evidence/A0/MCPTests-20261107-111345/Editor.log.gz) ghi tr?c ti?p interval/raw/action/yaw, source/target/hurtbox v? resolve accepted. C? trace buffer `.30 -> .40`, active successor `[.58,.65)`, expiry `.25+.15 == .40` kh?ng consume; hai lethal `.18` ch? source1 th?ng theo ID v? source2 retaliation b? lo?i. Barrier fixture l?y interval t?i `.18` c?n endpoint h?p l?, ?p raw60 c?nHP40 tr??c guard press.

**Ranh gi?i quan tr?ng:** SubmitBatch tr? interval tr??c admission nh?ng kh?ng t? ch?y world collision/vital callback. Adapter A1 ph?i drain **v? resolve** ch?ng tr??c mutation/admission; B2 th?m defense history theo hit-time. Guard/barrier test l? fixture model v?i ledger U02 th?t, guard runtime v?n Unsupported; kh?ng ch?ng minh runtime parry/guard m?i. Kh?ng d?ng fixture HP l?m b?ng ch?ng ph?ng th? s?n ph?m.

## Build v? Automation m?i

Clone: `D:/Data/AnimeMMORPG/Artifacts/U03/A0/Source`, source ?? commit, s?ch tr??c kh?i ??ng tests. Kh?ng copy binaries t? Editor g?c. UE5.8.4 CL58902052; MSVC14.51.36260/toolset14.51.36231; SDK10.0.26100.0; ISPC1.24.0, bundled DotNet10.0.

Build cu?i `Build-20261107-111220-338-9ff4c8e9`: Generate0, Editor0, Game0; log c? `Result: Succeeded`. [Commands/exits/logs](Evidence/A0/Build-20261107-111220-338-9ff4c8e9/SOURCE.json); c?c file command/result JSON v? log.gz c?nh ??. L?nh th?c d?ng `Scripts/U00.ps1 -Task Build -ProjectPath D:/Data/AnimeMMORPG/Artifacts/U03/A0/Source/AnimeMMORPG.uproject -EngineRoot D:/Software/UE_5.8 -OutputRoot D:/Data/AnimeMMORPG/Artifacts/U03/A0/Runs`; UBT target Editor/Game Win64 Development, WaitMutex/NoHotReloadFromIDE.

Automation cu?i `MCPTests-20261107-111345`, PID17880, NullRHI clone, MCP ri?ng port18030. `VerifyA0Tests.ps1` ??c schema TestRunner/LogsToolset **t?i clone**, trigger filter `AnimeMMORPG`, ??c t?ng Test Completed v? queue66 ho?n t?t tr??c QUIT_EDITOR ch? clone. **66 executed /66 Success /0 Failed:5 A0 m?i +61 h?i quy U00?U02 m?i ch?y.** [T?ng test](Evidence/A0/MCPTests-20261107-111345/result.json), [raw MCP](Evidence/A0/MCPTests-20261107-111345/mcp-results.json), [process/hash/command](Evidence/A0/MCPTests-20261107-111345/process.json).

| Test m?i `AnimeMMORPG.U03.A0.` | K?t qu? |
|---|---|
| AdmissionOrdering | Success |
| DefinitionIdentity | Success |
| ResolveBarrierAndLethal | Success |
| ResourceAndCutoff | Success |
| TimelineAndBuffer | Success |

Model steps30/60/120Hz v? update2s; kh?ng ghi th?nh FPS runtime ?? ?o. Pure model world/net/pawn/owner/role N/A. C?c Game-world fixtures U00?U02 m?i ch?y trong c?ng process l? h?i quy Automation, kh?ng ph?i input Windows/network process m?i.

Editor module SHA256 `9291705bf4bb7e05d431b1c156a281d637d93671efd66c98c978da9d3336b02c`. Game exe SHA256 `7baa6917877b1c8dcbcdfdbeeb4c436f4a2aef5a4b748e1f1944c8eca90c5148`. Manifest c? source Git blobs v? raw/published log SHA256. Package N/A v? A0 kh?ng c? gameplay m?i; kh?ng t?o launcher/package gi?.

## L??t l?i, warning, gi?i h?n v? ?i?m d?ng

Build ??u `Build-20261107-110112-629-8c6e9a4f`, source1d65b53, Editor exit6: `U03ActionModelTests.cpp(87,44): error C2668: 'Life': ambiguous call to overloaded function`; th?m C4459 do global helper Flags trong unity build che t?n Flags c?a engine/U02. ?? ??i helper U03A0Life/U03A0Intent/U03A0Flags, gi? log th?t b?i. C?c build sau th?nh c?ng, hai l??t Automation trung gian182d7f2/1f8e897 ??u66/66, kh?ng c?ng d?n th?nh s? test cu?i.

Superseded build logs/source IDs gi? ??; kh?ng gi? l?i m?i binary trung gian n?n kh?ng c? binary hash ??y ?? cho build b5848ad ?? b? thay th?. Kh?ng d?ng build trung gian ?? l?m b?ng ch?ng b?n giao. Final binary/process/hash v? raw logs ni?m phong ??y ??. [Warnings/error nguy?n v?n](Evidence/A0/WARNINGS.json) gi? c? failed runs; logs ch?a redaction ? Artifacts, b?n publish c? s? redactions/hash trong manifest, kh?ng publish credential.

Warning c?n: compiler m?i h?n preferred; engine/U01 API deprecated, U01AnimationTests double->float; MCP/EULA v? c?nh b?o kh?i ??ng plugin trong log. Kh?ng b?t AllToolsets ?? che c?nh b?o. Kh?ng c? Automation fail tr?n source cu?i; l?i build do test helper ?? s?a. Reviewer quy?t ??nh c? l?i ch?n k? thu?t c?n l?i hay kh?ng.

U00/U01/U02 AF/focus ACCEPTED l? **nghi?m thu k? th?a**; kh?ng x?c minh l?i197 evidence hashes hay t? m? l?i review focus. 61 Automation h?i quy ? tr?n l? b?ng ch?ng m?i ri?ng l??t n?y, kh?ng thay input/video/package/network k? th?a. A0 kh?ng ch?y Play/input/video/package/cook/dedicated+hai client ho?c benchmark; c?c c?ng gameplay theo t?ng ??t v?n c?n nguy?n.

R?i ro ?? A1/B2 ki?m ti?p: adapter enforce barrier v? event queue cho action sinh trong interval, aim/defense history, immutable payload qua runtime resolver, release/control input batch v? snapshot/life. Model PASS kh?ng kh?p c?c r?i ro runtime ??.

**READY_FOR_REVIEW U03-A0. D?ng t?i ??y; ch?a ACCEPTED, kh?ng merge main, kh?ng b?t ??u A1.**
