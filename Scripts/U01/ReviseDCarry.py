"""Own D carry pose authoring: accepted socket and finger pose are read-only."""
import sys
import unreal
result=unreal.U01AnimationEditor.revise_d_carry(sys.argv[1])
unreal.log('U01D_CARRY_AUTHOR '+result)
if not result.startswith('SUCCESS'):raise RuntimeError(result)
if len(sys.argv)>2:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/AnimeMMORPG/Maps/L_CharacterCombatLab')
    result=unreal.U01AnimationEditor.inspect_d_hand(sys.argv[2])
    unreal.log('U01D_CARRY_PREVIEW '+result)
    if not result.startswith('SUCCESS'):raise RuntimeError(result)
