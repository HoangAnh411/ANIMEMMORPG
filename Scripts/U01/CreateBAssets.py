"""Run once in an independently built clone's Editor; never in the user's open Editor."""
import json
from pathlib import Path
import unreal

project = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()
if project == Path('D:/Data/AnimeMMORPG/AnimeMMORPG.uproject').resolve():
    raise RuntimeError('Create native-class assets only in the validated build clone')
root = '/Game/AnimeMMORPG/U01'
tools = unreal.AssetToolsHelpers.get_asset_tools()
created = []

def clean():
    dirty = unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    if dirty:
        raise RuntimeError('Unsaved packages: ' + str([p.get_path_name() for p in dirty]))

def save(obj):
    if not unreal.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False):
        raise RuntimeError('Save failed: ' + obj.get_path_name())

def asset(folder, name, cls):
    path = root + '/' + folder
    if unreal.EditorAssetLibrary.does_asset_exist(path + '/' + name):
        raise RuntimeError('Refuse overwrite: ' + name)
    factory = unreal.DataAssetFactory()
    factory.set_editor_property('data_asset_class', cls)
    obj = tools.create_asset(name, path, cls, factory)
    if obj is None:
        raise RuntimeError('Create failed: ' + name)
    created.append(obj)
    return obj

def blueprint(name, parent, widget=False):
    path = root + '/Blueprints'
    if unreal.EditorAssetLibrary.does_asset_exist(path + '/' + name):
        raise RuntimeError('Refuse overwrite: ' + name)
    factory = unreal.WidgetBlueprintFactory() if widget else unreal.BlueprintFactory()
    factory.set_editor_property('parent_class', parent)
    cls = unreal.WidgetBlueprint if widget else unreal.Blueprint
    bp = tools.create_asset(name, path, cls, factory)
    if bp is None:
        raise RuntimeError('Blueprint create failed: ' + name)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    created.append(bp)
    return bp

clean()
context = asset('Input', 'IMC_U01_B', unreal.InputMappingContext)
actions = {}
for name, key, axis in [('Forward','W',False),('Backward','S',False),('Left','A',False),('Right','D',False),
                        ('MouseX','MouseX',True),('MouseY','MouseY',True),('Jump','SpaceBar',False),
                        ('Shoulder','V',False),('Menu','Escape',False)]:
    action = asset('Input', 'IA_U01_' + name, unreal.InputAction)
    action.set_editor_property('value_type', unreal.InputActionValueType.AXIS1D if axis else unreal.InputActionValueType.BOOLEAN)
    input_key = unreal.Key()
    input_key.set_editor_property('key_name', key)
    context.map_key(action, input_key)
    actions[name] = action

char = blueprint('BP_U01Character', unreal.load_class(None, '/Script/AnimeMMORPG.U01Character'))
cdo = unreal.get_default_object(char.generated_class())
mesh = cdo.get_component_by_class(unreal.SkeletalMeshComponent)
mesh.set_skeletal_mesh_asset(unreal.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple'))
mesh.set_relative_location(unreal.Vector(0,0,-96), False, False)
mesh.set_relative_rotation(unreal.Rotator(yaw=-90), False, False)
# D creates its own AnimBP. B uses source presentation provisionally, never claims animation acceptance.
mesh.set_anim_instance_class(unreal.load_class(None, '/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed_C'))
menu = blueprint('WBP_U01Menu', unreal.load_class(None, '/Script/AnimeMMORPG.U01Menu'), widget=True)
controller = blueprint('BP_U01Controller', unreal.load_class(None, '/Script/AnimeMMORPG.U01PlayerController'))
pc = unreal.get_default_object(controller.generated_class())
pc.set_editor_property('mapping_context', context)
pc.set_editor_property('direction_actions', [actions[k] for k in ('Forward','Backward','Left','Right')])
for prop, key in [('mouse_x_action','MouseX'),('mouse_y_action','MouseY'),('jump_action','Jump'),('shoulder_action','Shoulder'),('menu_action','Menu')]:
    pc.set_editor_property(prop, actions[key])
pc.set_editor_property('menu_class', menu.generated_class())
gm = blueprint('BP_U01LabGameMode', unreal.GameModeBase)
defaults = unreal.get_default_object(gm.generated_class())
defaults.set_editor_property('default_pawn_class', char.generated_class())
defaults.set_editor_property('player_controller_class', controller.generated_class())

for obj in created:
    if isinstance(obj, unreal.Blueprint):
        unreal.BlueprintEditorLibrary.compile_blueprint(obj)
        if obj.get_editor_property('status') != unreal.BlueprintStatus.BS_UP_TO_DATE:
            raise RuntimeError('Blueprint not up to date: ' + obj.get_path_name())
    save(obj)

cube = unreal.load_asset('/Engine/BasicShapes/Cube')
fixture = []
for level in ('L_CharacterCombatLab', 'L_NetworkLab'):
    clean()
    if not unreal.EditorLevelLibrary.load_level('/Game/AnimeMMORPG/Maps/' + level):
        raise RuntimeError('Load map failed')
    world = unreal.EditorLevelLibrary.get_editor_world()
    world.get_world_settings().set_editor_property('default_game_mode', gm.generated_class())
    # B-only camera wall/corner/low overhang fixture, inside the existing U00 floor.
    for label, xyz, scale in [('CameraWall',(600,0,150),(.2,8,3)),
                               ('CameraCorner',(400,400,150),(4,.2,3)),
                               ('CameraOverhang',(-550,200,220),(4,4,.2))]:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*xyz))
        actor.set_actor_label('U01B_' + label)
        actor.static_mesh_component.set_static_mesh(cube)
        actor.static_mesh_component.set_collision_profile_name('BlockAll')
        actor.set_actor_scale3d(unreal.Vector(*scale))
        fixture.append(dict(map=level, label=label, centerCm=xyz, dimensionsCm=[v*100 for v in scale]))
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError('Save map failed')
report = dict(project=str(project), assets=[obj.get_path_name() for obj in created], fixture=fixture,
              note='Boot/template assets unchanged; no U01 motor/animation acceptance in B')
out = project.parent / 'Saved/U01/B-Assets.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
unreal.log('U01B_ASSETS_SUCCESS ' + str(out))
