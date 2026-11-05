"""Author C only in full-build clone; refuses overwrite through native authoring."""
import unreal
from pathlib import Path
result=unreal.U02AnimationEditor.build_c_assets()
unreal.log('U02C_AUTHOR '+result)
path=Path(unreal.Paths.project_dir())/'Saved/U02C-Authoring.txt'
path.write_text(result,encoding='utf-8')
if not result.startswith('SUCCESS'):raise RuntimeError(result)
