import unreal,json
from pathlib import Path
project=Path(unreal.Paths.project_dir()).resolve()
assert project==Path('D:/Data/AnimeMMORPG/Artifacts/U02/D/Source').resolve()
cls=unreal.load_class(None,'/Script/AnimeMMORPG.U02CollisionLab');assert cls
rows=[]
for name in ['L_CharacterCombatLab','L_NetworkLab']:
 path='/Game/AnimeMMORPG/Maps/'+name
 unreal.EditorLevelLibrary.load_level(path)
 existing=[a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.is_a(cls)]
 assert not existing,'Refuses duplicate station authoring'
 actor=unreal.EditorLevelLibrary.spawn_actor_from_class(cls,unreal.Vector(0,-6000,0));assert actor
 actor.set_actor_label('U02D_CollisionStations');actor.set_editor_property('tags',[unreal.Name('U02D_Fixture')])
 assert unreal.EditorLevelLibrary.save_current_level()
 rows.append(dict(map=path,fixtureClass=cls.get_path_name(),stationBase=[0,-6000,0],offsetY=-1000,stations=['MultiTarget','FullWall','VisibleHead','Corner']))
(project/'Saved/U02D-Stations.json').write_text(json.dumps(rows,indent=2))
unreal.log('U02D_AUTHOR_SUCCESS')
