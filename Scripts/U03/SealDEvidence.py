"""Seal the initial D.2 build/Automation checkpoint; does not assert D.3 readiness."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import subprocess

root = Path(__file__).resolve().parents[2]
runs = root / "Artifacts/U03/D/Runs"
dest = root / "Evidence/D"
dest.mkdir(parents=True, exist_ok=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()


files = []
for run in sorted(runs.iterdir()):
    if not run.is_dir():
        continue
    for path in sorted(run.rglob("*")):
        if not path.is_file() or path.suffix not in {".log", ".json"}:
            continue
        raw = path.read_bytes()
        # Preserve raw evidence in Artifacts, publish validated UTF-8 with token redaction.
        encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        text = raw.decode(encoding, errors="strict")
        text = re.sub(r"(?im)(SecurityToken\s*[=:]\s*)[^\s,\"}]+", r"\1[REDACTED]", text)
        encoded = text.encode("utf-8")
        target = dest / "Runs" / path.relative_to(runs)
        target = target.with_suffix(target.suffix + ".gz")
        target.parent.mkdir(parents=True, exist_ok=True)
        packed = gzip.compress(encoded, mtime=0)
        assert gzip.decompress(packed) == encoded
        target.write_bytes(packed)
        files.append(dict(raw=str(path.relative_to(root)), rawSHA256=sha(raw),
                          published=str(target.relative_to(root)), publishedSHA256=sha(packed),
                          decodedSHA256=sha(encoded), rawEncoding=encoding, rawBytes=len(raw), publishedBytes=len(packed)))

clone = root / "Artifacts/U03/D/Source"
source = subprocess.check_output(["git", "-C", str(clone), "rev-parse", "HEAD"], text=True).strip()
binaries = []
for path in [clone / "Binaries/Win64/UnrealEditor-AnimeMMORPG.dll",
             clone / "Binaries/Win64/AnimeMMORPG.exe",
             Path("D:/Software/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe")]:
    if path.exists():
        binaries.append(dict(path=str(path), sha256=sha(path.read_bytes())))
result_path = runs / "MCPTests-20261115-132156/result.json"
tests = json.loads(result_path.read_text(encoding="utf-8-sig")) if result_path.exists() else None
manifest = dict(status="IN_PROGRESS", scope="Initial D.2 HUD checkpoint; not D.3 or playable handoff",
                base="bc3a9955a8c0ecc1cb7f0d43dce13300c9664ac9", branch="u03/d-integration",
                binarySource=source, clone=str(clone.relative_to(root)),
                engine=json.loads(Path("D:/Software/UE_5.8/Engine/Build/Build.version").read_text(encoding="utf-8-sig")),
                binaries=binaries, files=files, automation=tests,
                inherited=dict(manifest="Docs/U03/Evidence/C2/MANIFEST.json", tests=131,
                               scope="Accepted C2 baseline only; not a D run"),
                failedRuns=["Build-20261115-131806"],
                pending=["full presentation and audio", "authority-completed miss feed", "blockout poses",
                         "packaged telegraph", "physical input/video/loopback audio", "final timing/world regression",
                         "Windows package and Blueprint/map smoke", "five Boot loops and settings reopen",
                         "dedicated Editor with two clients", "runtime profile", "playable guarded D launchers"],
                originalConfigSHA256=sha((root / "Config/DefaultEngine.ini").read_bytes()))
(dest / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(dict(status=manifest["status"], binarySource=source, files=len(files),
                      executed=tests["executed"] if tests else None)))
