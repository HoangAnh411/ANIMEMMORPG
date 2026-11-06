"""Remove only clone-generated token and INI blank-line normalization after semantic comparison."""
from pathlib import Path
import argparse,subprocess
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);r=p.parse_args().root.resolve()
assert r==Path('D:/Data/AnimeMMORPG/Artifacts/U02/F/Source').resolve()
base=subprocess.check_output(['git','-C',str(r),'show','HEAD:Config/DefaultEngine.ini'])
config=r/'Config/DefaultEngine.ini';data=config.read_bytes();filtered=b''.join(l for l in data.splitlines(keepends=True) if not l.strip().startswith(b'SecurityToken='))
assert [l for l in filtered.splitlines() if l.strip()]==[l for l in base.splitlines() if l.strip()],'Unexpected semantic clone config change'
config.write_bytes(base.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
