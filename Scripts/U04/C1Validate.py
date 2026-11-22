"""Compatibility CLI: only the reviewed single-action counter validator is supported."""
import argparse
import json
from pathlib import Path
from C1CounterValidate import validate
from C1Run import write

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--single-action',action='store_true')
    a=p.parse_args();v=validate(a.run,a.single_action);write(a.run/'validation.json',v)
    print(json.dumps(v,indent=2));raise SystemExit(0 if v['status']=='PASS' else 1)
