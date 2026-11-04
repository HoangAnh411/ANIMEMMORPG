"""Rendered clone-only hand diagnosis; does not save maps or edit assets."""
import sys
from pathlib import Path
import unreal

project=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()
if 'Artifacts' not in project.parts or project==Path('D:/Data/AnimeMMORPG/AnimeMMORPG.uproject'):
    raise RuntimeError('Requires build clone')
output=Path(sys.argv[1]).resolve()
if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/AnimeMMORPG/Maps/L_CharacterCombatLab'):
    raise RuntimeError('Cannot load preview map')
result=unreal.U01AnimationEditor.inspect_d_hand(str(output))
unreal.log('U01D_HAND_INSPECT '+result)
if not result.startswith('SUCCESS'):raise RuntimeError(result)
