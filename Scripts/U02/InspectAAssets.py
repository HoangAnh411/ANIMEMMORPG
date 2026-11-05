"""Read-only registry/load audit. No asset saves or mutation; run via TestRunner."""
import hashlib
import json
import os
from pathlib import Path
import unreal

root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.wait_for_completion()
rows = []
for data in registry.get_assets_by_path('/Game', recursive=True):
    kind = str(data.asset_class_path.asset_name)
    if kind not in ('AnimSequence', 'AnimMontage', 'Skeleton', 'SkeletalMesh', 'PoseAsset', 'AnimBlueprint', 'BlendSpace'):
        continue
    package = str(data.package_name)
    obj = data.get_asset()
    if obj is None:
        raise RuntimeError('Cannot load ' + package)
    file = root / 'Content' / (package[len('/Game/'):] + '.uasset')
    row = dict(package=package, asset_class=kind, sha256=hashlib.sha256(file.read_bytes()).hexdigest())
    for prop in ('skeleton', 'sequence_length', 'enable_root_motion', 'force_root_lock'):
        try:
            value = obj.get_editor_property(prop)
            row[prop] = value.get_path_name() if isinstance(value, unreal.Object) else str(value)
        except Exception:
            pass
    rows.append(row)
result = dict(pid=os.getpid(), project=str(root), read_only=True, assets=sorted(rows, key=lambda r: r['package']))
out = root / 'Artifacts/U02/A/assets-editor.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2), encoding='utf-8')
unreal.log('U02A_ASSETS_READ_ONLY count=' + str(len(rows)) + ' output=' + str(out))
