"""Run once in a cold D build-clone Editor. Native authoring refuses the original project."""
from pathlib import Path
import unreal
result = unreal.U01AnimationEditor.build_d_assets()
unreal.log('U01D_AUTHORING ' + result)
if not result.startswith('SUCCESS'):
    raise RuntimeError(result)
output = Path(unreal.Paths.project_dir()) / 'Saved/U01D-Authoring.txt'
output.write_text(result, encoding='utf-8')
