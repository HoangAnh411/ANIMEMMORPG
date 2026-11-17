"""Verify isolated clone; normalize only generated MCP token/blank lines."""
import argparse, subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();r=a.root.resolve()
assert r==Path(__file__).resolve().parents[2]/'Artifacts/U04/A/Source'
base=subprocess.check_output(['git','-C',str(r),'show','HEAD:Config/DefaultEngine.ini'])
f=r/'Config/DefaultEngine.ini'; data=f.read_bytes()
filtered=b''.join(l for l in data.splitlines(keepends=True) if not l.strip().startswith(b'SecurityToken='))
assert [l for l in filtered.splitlines() if l.strip()]==[l for l in base.splitlines() if l.strip()], 'Unexpected semantic config changes'
f.write_bytes(base.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
