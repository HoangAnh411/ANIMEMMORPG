# U03-D-R1 presentation occlusion

Base: f6d0f68, NOT ACCEPTED. This revision changes presentation only. C2 camera projection and environment trace (channel 2, excluding combat bodies) are shared with Tab/HP. Subject and label anchor must both be visible before a Canvas cue or sound can appear. History is consumed while hidden; becoming visible cannot replay sound or extend the 1.2 second absolute window.

Sword volume and direction use a production world primitive scene proxy, normal world PDI, world depth group, zero depth bias. The GPU depth tests every fragment, including partially occluded edges. No Canvas telegraph, debug line batcher, gameplay collision, animation authority, timing or damage changes.

Validation: native world occlusion tests, geometry tests, full existing automation, cold Editor/Game builds and Windows package. Opt-in labelled visibility fixture and diagnostics support actual two-client input/video/audio capture with debug overlay disabled. Old D runs/manifests remain historical and unchanged. Final state remains READY_FOR_REVIEW D-R1 pending separate visual play review.
