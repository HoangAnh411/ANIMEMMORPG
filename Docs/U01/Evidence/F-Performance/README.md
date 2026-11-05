# F performance revision

See MANIFEST for source/build/package and per-process review profile. RESULTS contains all twelve intermediate runs plus four final runs and the independent server timer A/B/A. CSVs are every-frame native Game-world observations aligned to real physical-input timestamps. Identities are attached from native U01F_NET Game-world records; Editor world is excluded.

Frame intervals use host UTC (millisecond precision), not the clamped game DeltaSeconds. Packet observation is limited by client frame rate. Mesh samples are game-thread presentation, not GPU scanout; onset in the same frame does not mean zero CMC smoothing. All stopped-actor packet-change intervals remain recorded; moving cadence excludes only gaps whose endpoints do not lie in the same actual W-held interval.

Baseline and Repeat videos retain both 900×540 client rectangles, frame order, duplicate timing frames and in-game warnings. Only the desktop gap between clients is removed. VIDEOS includes raw/export hashes and measured capture rates; 30Hz encoding is not claimed as actual game FPS. Capture metadata preserves all events and foreground/PID guards. Raw footage/logs stay in Artifacts/U01/F.

The same-machine 4GiB profile changes cache/pool sizes and internal resolution, minimizes the original Editor without closing it, and honors the dedicated process's existing timer-resolution request. DX12/SM6/Lumen and network update/smoothing remain unchanged. The original graphics workload remains a documented limitation. F still awaits user review; no F merge or G acceptance.

EVIDENCE.csv hashes every file here except itself. The continuous GPU.csv drops only the incomplete last row interrupted when stopping the sampler; raw CSV is retained in artifacts.
