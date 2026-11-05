"""Observe the actual possessed PIE pawn after original Editor full refresh."""
import json
import os
from pathlib import Path
import unreal

editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world=editor.get_game_world()
if not world:
    raise RuntimeError('No PIE Game world; never use Editor world as fallback')
pc=unreal.GameplayStatics.get_player_controller(world,0)
pawn=pc.get_controlled_pawn() if pc else None
if not pawn:
    raise RuntimeError('No possessed PIE pawn')
component=pawn.get_component_by_class(unreal.U02CombatComponent)
if not component:
    raise RuntimeError('PIE pawn does not contain U02CombatComponent')
out=Path(unreal.Paths.project_dir())/'Artifacts/U02/B/EditorRefresh'
data=dict(pid=os.getpid(),world=world.get_path_name(),controller=pc.get_path_name(),pawn=pawn.get_path_name(),
          component=component.get_path_name(),owner=component.get_owner().get_path_name())
(out/'pie.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
unreal.log('U02_EDITOR_PIE_VERIFIED '+json.dumps(data))
