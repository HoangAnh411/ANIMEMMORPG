"""Read/compile validation only in the D clone. Does not save any asset."""
import unreal,json
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve();assert root==Path('D:/Data/AnimeMMORPG/Artifacts/U03/D/Source').resolve()
rows=[];missing=[]
registry=unreal.AssetRegistryHelpers.get_asset_registry()
for path in unreal.EditorAssetLibrary.list_assets('/Game/AnimeMMORPG',recursive=True,include_folder=False):
 obj=unreal.load_asset(path)
 if not obj:missing.append(path);continue
 if isinstance(obj,unreal.Blueprint):
  unreal.BlueprintEditorLibrary.compile_blueprint(obj)
  status=str(obj.get_editor_property('status'));rows.append(dict(asset=path,status=status));assert obj.get_editor_property('status')!=unreal.BlueprintStatus.BS_ERROR,(path,status)
 package=path.split('.')[0]
 for dep in registry.get_dependencies(package,unreal.AssetRegistryDependencyOptions()):
  name=str(dep)
  if name.startswith('/Game/') and not unreal.EditorAssetLibrary.does_asset_exist(name):missing.append(dict(asset=path,missing=name))
result=dict(completed=not missing,blueprints=rows,missing=missing,sourceScope='D cold clone; no save')
(root/'Saved/D-AssetAudit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');assert result['completed'],missing
unreal.log('U03D_ASSET_AUDIT PASS '+str(len(rows)))
