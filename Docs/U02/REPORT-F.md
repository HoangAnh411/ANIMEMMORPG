# U02-F ? READY_FOR_REVIEW

E ?? ACCEPTED t?i903e139/source1f1c359 theo review ng??i d?ng. Closure `e6e1e2f5cf30b713ebe560acab98b63751076493` ?? push v? fast-forward main tr??c F; kh?ng ch?y l?i E ch? ?? kh?p h? s?. F ? nh?nh `u02/f-dedicated-two-clients`, ch?a merge, ch?a b?t ??u U03.

Source ki?m ch?ng **`85806519f98ef9078c5832e6193bb3bc8d924b54`**. Commit b?n giao sau source n?y ch? s?a scripts/h? s?, kh?ng ??i Source/Content/Config/Plugins. [MANIFEST](Evidence/F/MANIFEST.json), [PROCESS-MANIFEST](Evidence/F/PROCESS-MANIFEST.json) v? [EVIDENCE-SHA256](Evidence/F/EVIDENCE-SHA256.json) li?n k?t source?binary?process/session?IDs?k?t qu?. ??y l? dedicated **Editor** server v? hai client Editor `-game`, kh?ng ph?i Server ??ng g?i. Package Windows c?a E gi? source ri?ng1f1c359, kh?ng g?n SHA F cho binary E.

## Tri?n khai

Dummy ch? spawn server, replicated pawn ID/life/vital; static lab geometry d?ng c?ng c?u h?nh/t?n ?n ??nh v? net-addressable tr?n c?c process. Root ph?i Static tr??c khi ??ng k? collider. Kh?ng ??i thu?t to?n sweep, che khu?t t?ng hurtbox, damage/shield/death ho?c timing0,16/0,22/0,40. Kh?ng s?a replication/smoothing chung U01.

M?t actor replicated lu?n relevant trong NetworkLab gi? t?i ?a64 confirmed results c? serial, source/life/action/target/life/hurtbox/timestamp/damage/HP/crit/death. Server l? n?i duy nh?t resolve/tr? HP; client nh?n history ?? tr?nh b?y/log, kh?ng ?p l?i damage. Snapshot vital gi? HP/shield/death hi?n t?i, k? c? reconnect nh?n l?i history c?. HUD kh?ng d?ng result life c? ?? ghi ?? tr?ng th?i m?i. History64 l? c?a s? tr?nh b?y/diagnostics, kh?ng h?a giao m?i event trong m?ng x?u U05.

Attack RPC ch? c? command sequence, local diagnostic time, yaw v? expected pawn/life; kh?ng c? client-supplied damage/HP/action ID. Server ki?m ownership b?ng actor channel, life, command watermark, finite aim v? quy?n action. Startup aim RPC c?ng r?ng bu?c pawn/life/action; aim c? kh?ng retarget action m?i. Client timestamp kh?ng backdate start/hit. Accepted/rejected counters v? l? do cu?i ???c replicate; log server l?u t?ng quy?t ??nh ??y ??.

Fixtures file/console ch? opt-in `-U02FProbe`, non-Shipping, server NetworkLab. Concurrent fixture t?m ??t control Playing ?? nh?n hai intent c?ng boundary r?i ph?c h?i control lock; ??y l? fixture ordering r? r?ng, kh?ng m? ???ng input gameplay b? AwaitingResume. C?c ca ??nh A/B th?ng th??ng d?ng LMB Windows th?t. Gameplay lab ch? ??nh dummy; native pawn-versus-pawn ordering tests k? th?a E v?n l? fixture ri?ng.

## Ki?m ch?ng tr?n source cu?i

- Full Editor/Game build trong clone: `Build-20261106-180455-913-bde29c16`, Generate/Editor/Game ExitCode0, log Result: Succeeded. Header/reflection m?i d?ng cold clone; kh?ng restart ho?c tuy?n b? Editor g?c n?p layout m?i.
- MCP `MCPTests-20261106-180707`, port18030: **61/61 Success**, queue61 tests performed. Ch?y l?i to?n b? U00/U01/U02 A?F. [AUTOMATION-RESULTS](Evidence/F/AUTOMATION-RESULTS.json) v? MCP-RESULTS ghi t?ng test.
- Ba tests F: CommandLifeAndDuplicateAdmission (duplicate/stale/wrong subject/nonfinite v? old-life/action aim); AuthoritativeResultHistoryAndReplicationSchema (bounded history, kh?ng ?p HP khi publish, wire schema); NetworkLabStaticFloorAttachment (attachment/world transform/n?m dummy v? reset trong NetworkLab).
- Session `Session-20261106-180839`: serverPID9988, A13236, B4316; reconnect A8300. **134/134 input assertions**: ownership/pawn roles ri?ng, server0LocalPlayer, ??ng thu?n hit/miss/wall/head-only/multiple hurtboxes/targets,60/90, shield, death, reset, duplicate/stale command, nonfinite aim, menu/focus v? concurrent lethal. Hai ngu?n concurrent ??u accepted; ch? ngu?n resolve tr??c g?y lethal l?n m?i target. [Network input](Evidence/F/Network-input.json).
- **36/36 h?u x? l? b? sung** tr?n logs ??c l?p; controls597 samples, held WASD sau recovery, combat lock/replay authority, sprint700cm/s, gravity/menu, Resume kh?ng attack, focus/fresh-W, settings kh?ng ??i, actual body yaw lock/camera t? do, montage local/proxy c?ng action, root-motion ignore, server advances, one RNG roll/valid hit, reject ??ng probe, old history kh?ng ghi ?? HP hi?n t?i khi reconnect. [RUNTIME-ASSERTIONS](Evidence/F/RUNTIME-ASSERTIONS.json).
- Disconnect b?ng Alt-F4 khi server ?? nh?n action v? ch?a h?t0,40. Native removal event c? cutoff; kh?ng result c?a source c? t? cutoff tr? ?i. Reconnect ID m?i, life1/action0 ban ??u; fixture reset th?nhlife2 r?i input th?t t?o action1, c? ba process c?ng HP/results. L?nh/ID connection c? kh?ng ???c t?i s? d?ng. [Disconnect proof](Evidence/F/Disconnect-ASSERTIONS.json). Damage h?p l? tr??c removal v?n ???c gi?, kh?ng y?u c?u x?a ng??c l?ch s?.
- Profile actual cvars client60/server30, DX12/SM6,900x540, internal50%, Lumen atlas2048, RT128MiB, texture256MiB. Trong controls: server298 frames median33,388ms/p9534,071ms; m?i client597 frames median16,667ms/p9516,667ms. ??y l? profile c?ng m?y4GB VRAM k? th?a U01, kh?ng ph?i ?? h?a s?n ph?m1080p. Proxy smoothMode2/time0,1 ???c ?o597 samples/client trong SMOOTHING.json. Kh?ng s?a smoothing ?? ch?a hitch.
- [Network video](Evidence/F/Network-Network-F.mp4) v? [Controls video](Evidence/F/Controls-Controls-F.mp4): CFR30 theo wall timestamp, gi? ?nh c? qua gap, kh?ng t?ng t?c/n?i suy. B? sung7/4 last-frame holds cho ph?n bookkeeping cu?i0,23/0,12s; gi? b?n Unpadded v? metadata ch?nh s?ch. Kh?ng d?ng c?c freeze/gap ?? kh?ng ??nh art m??t. VIDEO-CLOCKS t?ch run-start UTC (c? prepare) v? video-origin g?n ??ng t? nonce fixture ??u; stage UTC/IDs gi? ri?ng.
- Stop ch? d?ng PID/executable/project/userDir/hash c?a session, g?m reconnect; original EditorPID18756 c?n s?ng v? window show-state kh?p tr??c minimize. EDITOR-RESTORED.json ghi x?c minh th?t. Config ri?ng gi? nguy?n byte, kh?ng stage token.

## L?ch s? l?i v? gi?i h?n b?ng ch?ng

Gi? failed builds/runs, raw logs/video/metadata v? warnings trong Evidence/F, RUN-HISTORY v? RAW-LOGS. Build ??u l?i test symbol Flags trong unity v? ph?m vi ForwardErrorMessages; s?a test. Runtime ??u ph?t hi?n Static collider kh?ng attach ???c root Movable, l?m r?i v? reject Airborne; s?a root mobility, th?m regression fixture/world-transform. Runtime ti?p d?ng v? reset helper E ch? cho CharacterLab; m? ??ng hai lab server-only, th?m regression reset NetworkLab. Kh?ng ??i lu?t hit/damage.

Hai l??t Automation trung gian b? lo?i:180458 v? HEAD clone ??i gi?a build v? test,180624 v? MCP port handover. Ghi INVALID, kh?ng d?ng PASS. Final180707 cold-load sau full build ho?n t?t, module hash ??i chi?u l?i. Test fixture ban ??u rename world thay v? package n?n kh?ng v?o map guard; s?a c?ch d?ng fixture, gi? run ??.

Reconnect helper t?ng b?c array ConvertFrom-Json sai tr?n PowerShell5 v? guard t? ch?i; s?a enumeration, gi? FAILED-RECONNECT. Assertion t?ng ??i life1 sau ch?nh lab resetlife2; ??i chi?u l?i initial/post-reset states, kh?ng h? lu?t. Controls harness t?ng k?t th?c s?m do focus m?t th?i gian; gi? Controls-Failed-Schedule v? thu l?i ??. Assertion sprint c? d?ng >700 trong khi lu?t t?c ??700 (native float ?o699,99); s?a k? v?ng ??ng config700 v? ki?m t?c ?? th?c. M?t ph?p ki?m l?ch s? t?ng gi? ??nh target600 khi reconnect, trong khi source c? ?? g?y hit h?p l? tr??c removal; nay ??i chi?u ??ng snapshot server c?ng l??t s?ng. C?c b?n assertions sai v?n ???c gi?.

Stop guard t?ng t? ch?i v? ???ng d?n '/' kh?c '\'; chu?n h?a GetFullPath tr??c so s?nh, v?n gi? PID/executable/hash/project/userDir guard. Kh?ng b? foreground/IME/AwaitingResume. Reconnect frame output trong run n?y d?ng ???ng d?n file A c? t? argument template; ph?n t?ch l?c **PID v? UTC** r? r?ng. Helper m?i c?p ???ng d?n Frames ri?ng; kh?ng tr?n hai PID l?m FPS evidence.

Warnings engine/toolchain/optional MCP/fixture v? performance console lookup gi? nguy?n, kh?ng b?o zero warnings. Kh?ng d?ng Editor-world actor, trigger-success, zero tests ho?c replicated-property declaration thay k?t qu? ba process.

## B?n giao

Ch?y [Play-U02-F.cmd](../../Play-U02-F.cmd), d?ng b?ng [Stop-U02-F.cmd](../../Stop-U02-F.cmd); [checklist ng?n](../../Play-U02-F-CHECKLIST.md). Launcher ki?m source/module/engine, gi? profile ?? nghi?m thu U01, ??a hai pawn t?i fixture v? y?u c?u Resume sau ??i focus. Ch? nh? ng??i d?ng ??nh gi? ?? ??c HUD/phase/ki?m/pose v? movement/focus hai c?a s?.

DLL Editor SHA-256 `b324e86adfd91b21fa9460f370e132c464f06068ee63867f91d1bb4409b3894d`; Engine executable `a423ab94410aa4f4cc34d99a2af75240c5d0e376a33d903a3e819fecf1177143`; Game build executable `5a07966e0bde0d1d97e2f267f326746948e60e82add49ed5286fa88f4f02e725`. Game build executable n?y kh?ng ???c g?i l? package F. Launcher smoke th?c: session183024, server19480/A19764/B9420; source/module/engine guards ??t,0LocalPlayer server v? ??ng owner m?i client,5 dummy life2/HP600,crit fixture off ??ng thu?n. LAUNCHER.json v? Launcher.png l?u native states/?nh; StopLatestF ?? d?ng ??ng session v? gi? Editor g?c.

U02 A?E ?? ACCEPTED theo h? s? t?ng ??t; F d?ng READY_FOR_REVIEW. Ch?a user acceptance m?ng, Server ??ng g?i, U05, anime art s?n ph?m, respawn s?n ph?m ho?c U03.
