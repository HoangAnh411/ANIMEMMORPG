"""Assign the E interaction input in a cold build clone only."""
from pathlib import Path
import unreal
project=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()
if project==Path('D:/Data/AnimeMMORPG/AnimeMMORPG.uproject').resolve():
    raise RuntimeError('Cold isolated clone required')
path='/Game/AnimeMMORPG/U01/Input/IA_U01_Interact'
action=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
if action is None:
    factory=unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class',unreal.InputAction)
    action=unreal.AssetToolsHelpers.get_asset_tools().create_asset('IA_U01_Interact','/Game/AnimeMMORPG/U01/Input',unreal.InputAction,factory)
action.set_editor_property('value_type',unreal.InputActionValueType.BOOLEAN)
bp=unreal.load_asset('/Game/AnimeMMORPG/U01/Blueprints/BP_U01Controller')
unreal.get_default_object(bp.generated_class()).set_editor_property('interact_action',action)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
if bp.get_editor_property('status')!=unreal.BlueprintStatus.BS_UP_TO_DATE:
    raise RuntimeError('Controller Blueprint compile failed')
for obj in (action,bp):
    if not unreal.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=False):
        raise RuntimeError('Asset save failed '+obj.get_path_name())
unreal.log('U01E_AUTHORING SUCCESS interaction action assigned; shared mapping context untouched')
