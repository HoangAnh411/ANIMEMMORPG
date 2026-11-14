import unreal
from pathlib import Path
result = unreal.U03AnimationEditor.build_c2_lab()
unreal.log('U03C2_AUTHOR ' + result)
(Path(unreal.Paths.project_dir())/'Saved/U03C2-Authoring.txt').write_text(result,encoding='utf-8')
if not result.startswith('SUCCESS'):
    raise RuntimeError(result)
