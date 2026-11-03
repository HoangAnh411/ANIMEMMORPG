"""Read-only U01-A asset metadata, invoked through Editor TestRunner console."""
import json
import os
from pathlib import Path
import unreal

ROOT = '/Game/Characters/Mannequins/'
NAMES = [
    'Meshes/SKM_Manny_Simple', 'Meshes/SK_Mannequin',
    'Anims/Unarmed/MM_Idle', 'Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd',
    'Anims/Unarmed/Jog/MF_Unarmed_Jog_Fwd', 'Anims/Unarmed/Jump/MM_Jump',
    'Anims/Unarmed/Jump/MM_Fall_Loop', 'Anims/Unarmed/Jump/MM_Land',
    'Anims/Unarmed/ABP_Unarmed', 'Anims/Unarmed/BS_Idle_Walk_Run',
]
rows = []
for name in NAMES:
    obj = unreal.load_asset(ROOT + name)
    if obj is None:
        raise RuntimeError('Missing asset: ' + name)
    row = dict(path=obj.get_path_name(), asset_class=obj.get_class().get_name())
    for prop in ('skeleton', 'enable_root_motion', 'sequence_length', 'root_motion_mode'):
        try:
            value = obj.get_editor_property(prop)
            row[prop] = value.get_path_name() if isinstance(value, unreal.Object) else str(value)
        except Exception:
            pass  # Properties differ by asset class; missing is not a verified value.
    rows.append(row)
out = Path(unreal.Paths.project_dir()) / 'Artifacts/U01/A/assets-editor.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(dict(pid=os.getpid(), project=unreal.Paths.project_dir(), assets=rows), indent=2), encoding='utf-8')
unreal.log('U01A_ASSETS_READ_ONLY=' + str(out))
