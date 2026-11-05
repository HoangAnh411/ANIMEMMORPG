"""One-time migration of first successful C authoring to a separate C graph."""
import unreal
from pathlib import Path
root=Path(unreal.Paths.project_dir()).resolve()
if '/Artifacts/U02/C/Source' not in root.as_posix():raise RuntimeError('C clone only')
target='/Game/AnimeMMORPG/U02/Animation/ABP_U02'
if unreal.EditorAssetLibrary.does_asset_exist(target):raise RuntimeError('Refuses overwrite')
bp=unreal.EditorAssetLibrary.duplicate_asset('/Game/AnimeMMORPG/U01/Animation/ABP_U01',target)
if not bp or not unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False):raise RuntimeError('Duplicate/save failed')
unreal.log('U02C_GRAPH_SEPARATE_SUCCESS '+bp.get_path_name())
