"""Read-only inventory before the one authorized original-Editor binary refresh."""
import json
import os
from pathlib import Path
import unreal

root=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
editing=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
dirty=list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages())+list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages())
world=editing.get_editor_world()
data=dict(pid=os.getpid(),project=str(root),map=world.get_path_name() if world else None,
          dirty=[p.get_path_name() for p in dirty],
          combat_class_present=hasattr(unreal,'U02CombatComponent'))
out=root/'Artifacts/U02/B/EditorRefresh';out.mkdir(parents=True,exist_ok=True)
(out/'before.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
unreal.log('U02_EDITOR_REFRESH_AUDIT '+json.dumps(data))
