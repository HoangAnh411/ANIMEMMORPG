"""Build-clone-only U01-C input/lab update. No template/Boot edits."""
import json
import math
from pathlib import Path
import unreal

project = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()
if project == Path('D:/Data/AnimeMMORPG/AnimeMMORPG.uproject').resolve() or 'Artifacts' not in project.parts:
    raise RuntimeError('Requires isolated C build clone')
root = '/Game/AnimeMMORPG/U01'
tools = unreal.AssetToolsHelpers.get_asset_tools()

def save(obj):
    if not unreal.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False):
        raise RuntimeError('Save failed: ' + obj.get_path_name())

sprint_path = root + '/Input/IA_U01_Sprint'
if unreal.EditorAssetLibrary.does_asset_exist(sprint_path):
    raise RuntimeError('Refuse overwriting C asset')
factory = unreal.DataAssetFactory()
factory.set_editor_property('data_asset_class', unreal.InputAction)
sprint = tools.create_asset('IA_U01_Sprint', root + '/Input', unreal.InputAction, factory)
sprint.set_editor_property('value_type', unreal.InputActionValueType.BOOLEAN)
context = unreal.load_asset(root + '/Input/IMC_U01_B')
for key_name in ('LeftControl','RightControl'):
    key = unreal.Key()
    key.set_editor_property('key_name', key_name)
    context.map_key(sprint, key)
controller = unreal.load_asset(root + '/Blueprints/BP_U01Controller')
unreal.get_default_object(controller.generated_class()).set_editor_property('sprint_action', sprint)
unreal.BlueprintEditorLibrary.compile_blueprint(controller)
character = unreal.load_asset(root + '/Blueprints/BP_U01Character')
character_defaults = unreal.get_default_object(character.generated_class())
character_defaults.set_editor_property('jump_max_count',1)
character_defaults.set_editor_property('jump_max_hold_time',0)
movement_defaults = character_defaults.get_component_by_class(unreal.CharacterMovementComponent)
movement_defaults.set_walkable_floor_angle(45)
movement_defaults.set_editor_property('max_step_height',45)
unreal.BlueprintEditorLibrary.compile_blueprint(character)
for obj in (sprint,context,controller,character):
    save(obj)

dirty = unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
if dirty:
    raise RuntimeError('Dirty packages before map change')
if not unreal.EditorLevelLibrary.load_level('/Game/AnimeMMORPG/Maps/L_CharacterCombatLab'):
    raise RuntimeError('Load lab failed')
existing = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
if any(str(actor.get_actor_label()).startswith('U01C_') for actor in existing):
    raise RuntimeError('Refuse duplicate C lab')
cube = unreal.load_asset('/Engine/BasicShapes/Cube')
records = []

def box(name, center, dimensions, pitch=0):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*center))
    actor.set_actor_label('U01C_' + name)
    actor.static_mesh_component.set_static_mesh(cube)
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
    actor.set_actor_scale3d(unreal.Vector(*[v/100 for v in dimensions]))
    actor.set_actor_rotation(unreal.Rotator(pitch=pitch), False)
    bounds_center, extent = actor.get_actor_bounds(False)
    normal = actor.get_actor_up_vector()
    records.append(dict(label=actor.get_actor_label(), centerCm=list(center), localDimensionsCm=list(dimensions),
        measuredBoundsCenterCm=[bounds_center.x,bounds_center.y,bounds_center.z], measuredBoundsExtentCm=[extent.x,extent.y,extent.z],
        measuredNormal=[normal.x,normal.y,normal.z], measuredAngleDegrees=math.degrees(math.acos(max(-1,min(1,normal.z))))))
    return actor

def label(name, text, xyz):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*xyz))
    actor.set_actor_label('U01C_Label_' + name)
    actor.text_render.set_text(text)
    actor.text_render.set_world_size(35)
    actor.set_actor_rotation(unreal.Rotator(yaw=180), False)

def station(name, xyz):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(*xyz))
    actor.set_actor_label('U01C_Reset_' + name)
    actor.set_editor_property('tags', [unreal.Name('U01C_Reset_' + name)])
    label(name, 'TEST FIXTURE: ' + name, (xyz[0],xyz[1]+200,100))

# The measured interval is 80m. Extra 5m at each end is acceleration/braking space.
box('Runway', (4000,-4000,-50), (9000,600,100))
station('Runway', (-400,-4000,110))
for meters in range(0,81,10):
    box('RunwayMark' + str(meters), (meters*100,-4000,1), (5,600,2))
    label('Meter' + str(meters), str(meters)+' m', (meters*100,-4350,70))

for index, angle in enumerate((30,44,45,46,60)):
    y = 2500 + index*1000
    radians = math.radians(angle)
    length, thickness = 800,20
    box('Approach'+str(angle), (-400,y,-50), (800,500,100))
    box('Slope'+str(angle), (length/2*math.cos(radians)+thickness/2*math.sin(radians),y,
        length/2*math.sin(radians)-thickness/2*math.cos(radians)), (length,400,thickness), angle)
    station('Slope'+str(angle), (-300,y,110))
    label('Angle'+str(angle), str(angle)+' deg | 45 deg walkable limit', (-300,y-250,100))

for index, height in enumerate((20,40,60)):
    y = 8000+index*500
    box('StepFloor'+str(height), (200,y,-50), (2000,400,100))
    box('Step'+str(height), (200,y,height/2), (400,400,height))
    station('Step'+str(height), (-300,y,110))
    label('Step'+str(height), str(height)+' cm step | motor step 45 cm', (-300,y-250,100))

for index, height in enumerate((180,260)):
    y=10000+index*500
    box('CeilingFloor'+str(height), (500,y,-50), (1800,400,100))
    box('Ceiling'+str(height), (500,y,height+10), (1000,400,20))
    station('Ceiling'+str(height), (-300,y,110))
    label('Ceiling'+str(height), 'Roof underside '+str(height)+' cm', (-300,y-250,100))

box('LedgePlatform', (0,12000,250), (800,400,100))
box('LedgeLanding', (1100,12000,-50), (1400,1000,100))
station('Ledge', (0,12000,410))
label('Ledge', '300 cm drop | coyote/buffer fixture', (0,12300,400))
box('CorridorFloor', (500,13500,-50), (1400,600,100))
box('CorridorWallA', (500,13430,150), (1000,20,300))
box('CorridorWallB', (500,13570,150), (1000,20,300))
box('CorridorCorner', (1000,13670,150), (20,200,300))
station('Corridor120', (0,13500,110))
label('Corridor120', 'Clear corridor 120 cm', (0,13800,100))

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError('Save lab failed')
if controller.get_editor_property('status') != unreal.BlueprintStatus.BS_UP_TO_DATE:
    raise RuntimeError('Controller Blueprint compile failed')
out=project.parent/'Saved/U01/C-Lab.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(dict(project=str(project), fixtures=records, sourceInput=sprint.get_path_name(),
    stationCount=13, measuredRunwayCm=8000, sprintKeys=['LeftControl','RightControl']),indent=2),encoding='utf-8')
unreal.log('U01C_ASSETS_SUCCESS ' + str(out))
