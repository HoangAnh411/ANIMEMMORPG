# U03-B2 play checklist

Launchers use the verified B2 clone/package and check hashes. Play in the original open Editor is not guaranteed to load B2. Stop restores its captured window placement; no Editor save/restart is performed.

1. Run `Play-U03-B2.cmd`, then Resume. Actual rebound keys appear on HUD. Default: LMB attack, RMB guard, Shift dodge, X escape, Ctrl sprint.
2. In the development console run `U03B2Fixture block`. A labelled wire capsule attacks through the authority/resolver. Hold/release RMB; a fresh correctly timed edge produces a ring and two notes, then holding gives `[ BLOCK ]`.
3. `U03B2Fixture unparryable` tests ordinary blocking. Four normal blocks cause `!! GUARD BREAK !!`; press X while locked. Release RMB before trying again.
4. Try labels `slow`, `stun`, `knockdown`, `launch`, `grab`, `bypass`, `multi`; `off` removes enemies. Launch is explicitly a state-only fixture with no invented impulse. These are test actors, not profession skills or an encounter.
5. Check Controls rebind for Guard/X, hold keys through menu/focus, Resume, release/repress. Guard walks at200cm/s, follows aim and cannot jump/sprint. Ordinary movement resumes after CC.
6. Run `Play-U03-B2-Network.cmd` for dedicated Editor server + two clients (client60/server30). Resume after each focus change. Use `powershell -File Scripts/U03/SetB2Fixture.ps1 -Label block` to create only server-authority enemies; client console cannot create server outcomes. Defense still requires physical input in the focused client.
7. Run `Stop-U03-B2.cmd`. It targets only recorded B2 processes, including reconnects, verifies identity/hash and restores original Editor placement.

Technical review decides ACCEPTED; the user judges feel/readability. No merge, C1/C2 or packaged Server is authorized by this checklist.
