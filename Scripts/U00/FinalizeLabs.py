import unreal
import json
from pathlib import Path
ROOT='/Game/AnimeMMORPG'
assets=unreal.EditorAssetLibrary.list_assets(ROOT,recursive=True,include_folder=False)
for path in assets:
    obj=unreal.load_asset(path)
    if isinstance(obj, unreal.Blueprint):
        unreal.BlueprintEditorLibrary.compile_blueprint(obj)
        print('U00E_BP_STATUS='+obj.get_path_name()+':'+str(obj.get_editor_property('status')))
        if obj.get_editor_property('status') != unreal.BlueprintStatus.BS_UP_TO_DATE:
            raise RuntimeError('Blueprint not up to date: '+path)
        unreal.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=True)
def create_gm(name,parent,controller,boot=False):
    path=ROOT+'/Blueprints/'+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError('Refuse overwrite GM')
    factory=unreal.BlueprintFactory()
    factory.set_editor_property('parent_class',parent)
    bp=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,ROOT+'/Blueprints',unreal.Blueprint,factory)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cdo=unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property('player_controller_class',unreal.load_class(None,ROOT+'/Blueprints/'+controller+'.'+controller+'_C'))
    if boot:
        cdo.set_editor_property('default_pawn_class',None)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
create_gm('BP_BootGameMode',unreal.GameModeBase,'BP_BootController',True)
parent=unreal.load_class(None,'/Game/ThirdPerson/Blueprints/BP_ThirdPersonGameMode.BP_ThirdPersonGameMode_C')
create_gm('BP_CharacterLabGameMode',parent,'BP_LabController')
create_gm('BP_NetworkLabGameMode',parent,'BP_NetworkController')
for level,gm in [('L_CharacterCombatLab','BP_CharacterLabGameMode'),('L_NetworkLab','BP_NetworkLabGameMode'),('L_Boot','BP_BootGameMode')]:
    dirty=unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()+unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    if dirty: raise RuntimeError('Dirty before map change: '+str([p.get_path_name() for p in dirty]))
    unreal.EditorLevelLibrary.load_level(ROOT+'/Maps/'+level)
    world=unreal.EditorLevelLibrary.get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode',unreal.load_class(None,ROOT+'/Blueprints/'+gm+'.'+gm+'_C'))
    unreal.EditorLevelLibrary.save_current_level()
    print('U00E_MAP_GM='+level+':'+gm)
print('U00E_FINALIZE_COMPLETE')
