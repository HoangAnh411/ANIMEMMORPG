import unreal
from pathlib import Path
result = unreal.U03AnimationEditor.build_d_assets()
unreal.log('U03D_AUTHOR ' + result)
(Path(unreal.Paths.project_dir())/'Saved/U03D-Authoring.txt').write_text(result,encoding='utf-8')
if not result.startswith('SUCCESS'):
    raise RuntimeError(result)
