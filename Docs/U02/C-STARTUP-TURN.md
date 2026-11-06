# C startup turn revision ? ACCEPTED_LOCAL - REMOTE_PENDING

User requested revision after 39bb09c (tested source 61be83b). C remains unaccepted.

Attack aim stays server-owned. Startup following aim does not mean body equals aim in every startup frame. At acceptance preserve current body yaw. Sample shortest-arc smoothstep from segment start/body to aim by the original action active-start deadline (0.16 s). Exactly 180 degrees always takes positive yaw. Retarget during startup samples the current trajectory, starts a new segment there, and keeps the original deadline. Complete body yaw before delivering any active interval, including an update spanning all active. Active/recovery ignore new aim for body orientation. Camera stays free. No changes to timings, gravity, locks, release gates or authority.

Replicated action data includes segment start/body and target. Clients sample presentation from server simulation time; they cannot select hit yaw. No generic U01 smoothing changes. Rapid aim changes just before active may require rapid catching up; this revision removes the initial instantaneous turn and does not promise slow motion under all camera input.

Animation revision must include preparation in upper body/shoulders and feet, keep accepted grip/socket and root fixed, and return cleanly to locomotion. Existing C footage is historical and its original 30 FPS encoding played faster than wall time. Correct timestamp resampling and before/after matching views are required for review.

Required evidence: new clone Editor/Game builds, trajectory/adapter plus related regression tests, new Windows package and three-map smoke, guarded input captures with actual body/mesh/aim/action-time diagnostics, real-time videos, hashes and updated launcher/checklist. No technical PASS or user feel acceptance is inferred from the old C artifacts.


Accepted by user at cdaf102, verified source 9aa7249: technical blockout and turn/standing attack feel. Acceptance survives network failures; remote verification is still required before main fast-forward and D. See ACCEPTANCE-C.md.
