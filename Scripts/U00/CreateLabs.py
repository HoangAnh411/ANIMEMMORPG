"""Create only U00-E lab maps. Run through verified Editor console: py <path>."""
import unreal
import json
from pathlib import Path
ROOT = '/Game/AnimeMMORPG'
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve() == Path('D:/Data/AnimeMMORPG/AnimeMMORPG.uproject').resolve()
def ensure_clean():
    dirty = unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() + unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    if dirty:
        raise RuntimeError('Dirty packages before map change: ' + str([p.get_path_name() for p in dirty]))
def actor(cls, name, xyz):
    obj = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(*xyz))
    obj.set_actor_label(name)
    return obj
cube = unreal.load_asset('/Engine/BasicShapes/Cube')
for name, size in [('L_CharacterCombatLab', 4000), ('L_NetworkLab', 2000), ('L_Boot', 0)]:
    ensure_clean()
    path = ROOT + '/Maps/' + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError('Refuse overwrite existing E map: ' + path)
    if not unreal.EditorLevelLibrary.new_level(path):
        raise RuntimeError('new_level failed')
    world = unreal.EditorLevelLibrary.get_editor_world()
    if size:
        floor = actor(unreal.StaticMeshActor, 'Floor_TopZ0', (0,0,-50))
        floor.static_mesh_component.set_static_mesh(cube)
        floor.set_actor_scale3d(unreal.Vector(size/100,size/100,1))
        floor.static_mesh_component.set_collision_profile_name('BlockAll')
        actor(unreal.DirectionalLight, 'Sun', (0,0,500)).set_actor_rotation(unreal.Rotator(pitch=-45,yaw=-30,roll=0), False)
        actor(unreal.SkyLight, 'SkyLight', (0,0,500))
        points = [('A',-250),('B',250)] if name == 'L_NetworkLab' else [('A',0)]
        for label,x in points:
            actor(unreal.PlayerStart, 'Spawn_'+label, (x,0,110))
            text=actor(unreal.TextRenderActor, 'SpawnLabel_'+label, (x,100,130))
            text.text_render.set_text(label)
        if name == 'L_CharacterCombatLab':
            for meters in [1,10]:
                ruler=actor(unreal.StaticMeshActor, 'Ruler_'+str(meters)+'m', (0,300+meters*30,5))
                ruler.static_mesh_component.set_static_mesh(cube)
                ruler.set_actor_scale3d(unreal.Vector(meters,0.1,0.1))
                text=actor(unreal.TextRenderActor, 'RulerLabel_'+str(meters)+'m', (0,300+meters*30,40))
                text.text_render.set_text(str(meters)+' m = '+str(meters*100)+' cm')
    if not unreal.EditorLevelLibrary.save_current_level():
        raise RuntimeError('Save E map failed')
    print('U00E_CREATED_MAP='+path)
print('U00E_MAP_CREATION_COMPLETE')
