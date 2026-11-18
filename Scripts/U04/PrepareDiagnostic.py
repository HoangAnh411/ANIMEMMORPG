import argparse,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--isolation',required=True,type=Path);a=p.parse_args()
r=(a.isolation/'Source').resolve();assert r==Path(__file__).resolve().parents[2]
base=subprocess.check_output(['git','-C',str(r),'show','HEAD:Config/DefaultEngine.ini'])
f=r/'Config/DefaultEngine.ini';before=f.read_bytes()
filtered=[x for x in before.splitlines() if x.strip() and not x.strip().startswith(b'SecurityToken=')]
assert filtered==[x for x in base.splitlines() if x.strip()], 'Unexpected semantic config change'
f.write_bytes(base.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
print('Diagnostic clone semantic config guard passed')
