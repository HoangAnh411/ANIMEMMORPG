"""Seal real build/MCP output; never manufacture PASS from trigger or zero tests."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--build', required=True)
parser.add_argument('--tests', required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
build, tests = Path(args.build).resolve(), Path(args.tests).resolve()
out = root / 'Docs/U02/Evidence/A'
out.mkdir(parents=True, exist_ok=True)

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(name, data):
    (out / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def git(*arguments):
    return subprocess.check_output(['git', '-C', str(root), *arguments], text=True).strip()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

results = {name: read(build / (name + '.result.json')) for name in ('Generate', 'Editor', 'Game')}
assert all(r['ExitCode'] == 0 for r in results.values()), results
result = read(tests / 'result.json')
process = read(tests / 'process.json')
assert result['executed'] > 0 and result['failed'] == 0
source = result['sourceSHA']
assert source == process['sourceSHA']
assert digest(Path(process['module'])) == process['moduleSHA256'].lower()
expected = set(result['tests'])
mcp = read(tests / 'mcp-results.json')
lines = json.loads(mcp['content'][0]['text'])['returnValue']
parsed = [dict(state=m.group(1), name=m.group(2)) for line in lines
          if (m := re.search(r'Test Completed\. Result=\{([^}]+)\}.*Path=\{([^}]+)\}', line))]
assert len(parsed) == result['executed'] and {t['name'] for t in parsed} == expected
assert all(t['state'] == 'Success' for t in parsed)
assert any(re.search(r'Automation Test Queue Empty\s+' + str(len(parsed)) + r' tests performed', line) for line in lines)

for name in ('Generate', 'Editor', 'Game'):
    command = read(build / (name + '.command.json'))
    assert 'Artifacts' in command['Project'] and 'U02' in command['Project']
    results[name]['command'] = command
write('BUILD-RESULTS.json', results)
write('AUTOMATION-RESULTS.json', dict(**result, perTest=parsed))
shutil.copyfile(tests / 'process.json', out / 'PROCESS.json')
shutil.copyfile(tests / 'mcp-results.json', out / 'MCP-RESULTS.json')
for schema in tests.glob('*.schema.json'):
    shutil.copyfile(schema, out / schema.name)
(out / 'TIMELINE.log').write_text('\n'.join(line for line in lines if 'U02A_' in line) + '\n', encoding='utf-8')

logs = []
for path in sorted((root / 'Artifacts/U02/A').glob('Build-*/*.log')):
    dest = out / (path.parent.name + '-' + path.name + '.gz')
    with gzip.open(dest, 'wb') as target:
        target.write(path.read_bytes())
    logs.append(dict(original=str(path), rawSHA256=digest(path), gzip=dest.name, sha256=digest(dest)))
history = []
for path in sorted((root / 'Artifacts/U02/A').glob('MCPTests-*/Editor.log')):
    dest = out / (path.parent.name + '-Editor.log.gz')
    with gzip.open(dest, 'wb') as target:
        target.write(path.read_bytes())
    logs.append(dict(original=str(path), rawSHA256=digest(path), gzip=dest.name, sha256=digest(dest)))
    if (path.parent / 'result.json').exists():
        previous = read(path.parent / 'result.json')
        history.append(dict(run=path.parent.name, **previous))
write('RUN-HISTORY.json', history)
write('LOGS.json', logs)

config_before = read(root / 'Artifacts/U02/A/local-config-before.json')['Hash']
config_unchanged = digest(root / 'Config/DefaultEngine.ini').upper() == config_before
assert config_unchanged
protected = git('diff', '--name-only', source, 'HEAD', '--', 'Source', 'Content', 'Config', 'Plugins', 'AnimeMMORPG.uproject')
assert not protected, protected
unchanged_u01 = not git('diff', '--name-only', 'e4ab61812b5a1e3d954a1c8f3d2a1b4fb9535560', 'HEAD', '--',
                       'Source/AnimeMMORPG/U01', 'Content', 'Config', 'Plugins', 'AnimeMMORPG.uproject')
assert unchanged_u01
source_paths = ['Source/AnimeMMORPG/U02/U02ActionModel.h', 'Source/AnimeMMORPG/U02/U02ActionModel.cpp',
                'Source/AnimeMMORPG/Tests/U02ActionModelTests.cpp']
game_exe = root / 'Artifacts/U02/A/Source/Binaries/Win64/AnimeMMORPG.exe'
write('MANIFEST.json', dict(
    status='READY_FOR_REVIEW', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    baseSHA='e4ab61812b5a1e3d954a1c8f3d2a1b4fb9535560', sourceSHA=source,
    branch='u02/a-contract-model', buildRun=build.name, testRun=tests.name,
    module=process['module'], moduleSHA256=process['moduleSHA256'],
    editorExe=process['exe'], editorExeSHA256=process['exeSHA256'],
    gameExe=str(game_exe), gameExeSHA256=digest(game_exe),
    sourceGitBlobs={p: git('rev-parse', source + ':' + p) for p in source_paths},
    localConfigByteUnchanged=config_unchanged, existingRuntimeAssetsConfigUnchanged=unchanged_u01,
    sourceEqualsHandoffRuntime=True,
    world='N/A: pure model Automation in Editor process; no gameplay pawn asserted',
    inputVideo='NOT RUN: A has no gameplay input integration',
    package='NOT RUN: A pure model scope; E is Windows integration gate',
    inheritedU01=dict(sourceSHA='5f8a6eabe103a8b31a894c82f32cffb0325474a9', automation=23, maps=3, rerunInA=False),
    failuresRetained=[p.name for p in (root / 'Artifacts/U02/A').glob('Build-*') if (p / 'failure.json').exists() or
                      ((p / 'Editor.result.json').exists() and read(p / 'Editor.result.json')['ExitCode'] != 0)]))
files = sorted(p for p in out.iterdir() if p.is_file() and p.name != 'EVIDENCE-SHA256.json')
write('EVIDENCE-SHA256.json', [dict(file=p.name, bytes=p.stat().st_size, sha256=digest(p)) for p in files])
print(json.dumps(dict(sourceSHA=source, executed=len(parsed), configUnchanged=config_unchanged, output=str(out))))
