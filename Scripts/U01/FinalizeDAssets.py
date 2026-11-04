"""Rebuild only the owned BlendSpace interpolation after programmatic authoring."""
import unreal
result = unreal.U01AnimationEditor.finalize_d_blend_space()
unreal.log('U01D_FINALIZE ' + result)
if not result.startswith('SUCCESS'):
    raise RuntimeError(result)
