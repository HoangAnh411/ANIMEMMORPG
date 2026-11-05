# U01-F evidence

Source/build/package: `df897f6088da4cca423085e9fe8e9c2869c98420`. MANIFEST identifies artifacts, executable/module digests and limits. CHECKS contains 92 native runtime/input postprocessing checks; these are distinct from the 23 Automation tests in AUTOMATION.

Each case JSON holds real OS-input timestamps, process identity, measured capture Hz and aligned native Game-world samples for all processes. Video export removes only the desktop gap between two native 900×540 client rectangles; frame order, duplicate timing frames and in-game warnings remain. Raw/export SHA256 are recorded in each case JSON. No interpolation, speed change or hidden game warning. Capture is approximately 19.88–27.65 unique captures/s, not certification of rendered FPS or 0.10-second animation smoothness.

NormalA proves walking/jumping; its Ctrl edge did not become sprint. A sprint is independently observed by server/owner/peer in AttacksSettingsA before malicious probes. NormalB and ReconnectBOnRunway show both speeds. SpeedA proves actual malformed client prediction and authority correction, beyond a rejected RPC claim. PROCESSES/SETTINGS and server events preserve disconnect/reconnect and local settings identity. PYTHON-REGRESSION preserves unmitigated startup errors as well as the scoped runtime flag; it does not claim engine/plugin repair.

Full raw logs/videos/builds remain under the artifact directories listed in MANIFEST; only focused evidence is checked in. EVIDENCE.csv hashes every file here except itself. F remains READY_FOR_REVIEW pending user acceptance.
