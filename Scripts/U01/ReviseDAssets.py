"""Apply observed hand calibration on own assets and capture the resulting preview."""
import sys
import unreal
result=unreal.U01AnimationEditor.revise_d_assets(sys.argv[1])
unreal.log('U01D_REVISION_ASSETS '+result)
if not result.startswith('SUCCESS'):raise RuntimeError(result)
if len(sys.argv)>2:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/AnimeMMORPG/Maps/L_CharacterCombatLab')
    result=unreal.U01AnimationEditor.inspect_d_hand(sys.argv[2])
    unreal.log('U01D_REVISION_INSPECT '+result)
    if not result.startswith('SUCCESS'):raise RuntimeError(result)
