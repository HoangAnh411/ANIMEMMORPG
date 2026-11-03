import unreal
import json
from pathlib import Path
results=[]
for name in ['L_CharacterCombatLab','L_NetworkLab','L_Boot']:
    dirty=unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()+unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    if dirty: raise RuntimeError('Dirty packages before map switch: '+str([p.get_path_name() for p in dirty]))
    unreal.EditorLevelLibrary.load_level('/Game/AnimeMMORPG/Maps/'+name)
    world=unreal.EditorLevelLibrary.get_editor_world()
    actors=unreal.EditorLevelLibrary.get_all_level_actors()
    for a in actors:
        if isinstance(a,unreal.DirectionalLight):
            a.set_actor_rotation(unreal.Rotator(pitch=-45,yaw=-30,roll=0),False)
        if isinstance(a,unreal.TextRenderActor):
            a.set_actor_rotation(unreal.Rotator(pitch=0,yaw=180,roll=0),False)
    unreal.EditorLevelLibrary.save_current_level()
    row={'map':name,'game_mode':world.get_world_settings().get_editor_property('default_game_mode').get_path_name(),'actors':[]}
    starts=[]
    for a in actors:
        label=a.get_actor_label()
        if label.startswith(('Floor','Ruler_','Spawn_')):
            location=a.get_actor_location(); scale=a.get_actor_scale3d()
            origin,extent=a.get_actor_bounds(False)
            row['actors'].append({'label':label,'location':[location.x,location.y,location.z],'scale':[scale.x,scale.y,scale.z],'bounds_cm':[extent.x*2,extent.y*2,extent.z*2]})
            if isinstance(a,unreal.PlayerStart): starts.append(location)
    if len(starts)==2: row['spawn_distance_cm']=(starts[1]-starts[0]).length()
    results.append(row)
Path('D:/Data/AnimeMMORPG/Artifacts/U00/E/map-measurements.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('U00E_MEASUREMENTS='+json.dumps(results))
