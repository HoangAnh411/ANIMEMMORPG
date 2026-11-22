"""Offline post-stop mutations of a complete entry_normal workspace. No launch."""
import argparse
import csv
import json
from pathlib import Path
import shutil
from unittest.mock import patch
from C1CounterValidate import validate
from C1Run import read, sha


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();source=a.source.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    before={str(f.relative_to(source)):sha(f) for f in source.rglob('*') if f.is_file()}
    rows=[]
    cases=[('control',None,'PASS'),('windows_path_equivalent',None,'PASS'),
           ('wrong_pid','exit_identity:pid','INVALID'),('one_tick','exit_identity:creationTicks','INVALID'),
           ('wrong_executable','exit_identity:executable','INVALID'),
           ('journal_disagrees','journal_exit_proof:pid','INVALID'),
           ('journal_missing','journal_exit_record_count:0','INVALID'),
           ('journal_duplicate','journal_exit_record_count:2','INVALID'),
           ('proof_missing_ticks','exit_identity:creationTicks','INVALID'),
           ('ticks_float','exit_identity:creationTicks','INVALID'),
           ('executable_relative','exit_identity:executable','INVALID'),
           ('result_only_pid','result_final_exit_proof:pid','INVALID'),
           ('journal_wrong_executable','journal_exit_proof:executable','INVALID'),
           ('journal_missing_proof','journal_exit_proof:missing','INVALID')]
    for name,reason,expected in cases:
        run=out/name/source.name;shutil.copytree(source,run)
        def rebase(value):
            if isinstance(value,str):return value.replace(str(source),str(run))
            if isinstance(value,list):return [rebase(x) for x in value]
            if isinstance(value,dict):return {k:rebase(v) for k,v in value.items()}
            return value
        for f in run.rglob('*.json'):
            # Native exports are byte evidence; rebasing metadata must not reformat them.
            if f.is_relative_to(run/'Raw'):continue
            f.write_text(json.dumps(rebase(read(f)),indent=2),encoding='utf-8')
        journal=[rebase(json.loads(line)) for line in (run/'journal.jsonl').read_text(encoding='utf-8').splitlines()]
        stopped=read(run/'result.json');final=read(run/'final.json')
        # Both verdict files are changed together: equality alone cannot catch this.
        for verdict in (stopped,final):
            proof=verdict['exitEvidence']
            if name=='wrong_pid':proof['pid']+=1
            elif name=='one_tick':proof['creationTicks']+=1
            elif name=='wrong_executable':proof['executable']='D:/Other/AnimeMMORPG.exe'
            elif name=='proof_missing_ticks':proof.pop('creationTicks')
            elif name=='ticks_float':proof['creationTicks']=float(proof['creationTicks'])
            elif name=='executable_relative':proof['executable']='AnimeMMORPG.exe'
            elif name=='windows_path_equivalent':proof['executable']=proof['executable'].upper().replace('\\','/')
        exits=[r for r in journal if r['event']=='original_handle_process_exited']
        assert len(exits)==1
        if name=='result_only_pid':stopped['exitEvidence']['pid']+=1
        if name=='journal_disagrees':exits[0]['evidence']['pid']+=1
        elif name=='journal_wrong_executable':exits[0]['evidence']['executable']='D:/Other/AnimeMMORPG.exe'
        elif name=='journal_missing_proof':exits[0].pop('evidence')
        elif name=='journal_missing':journal=[r for r in journal if r['event']!='original_handle_process_exited']
        elif name=='journal_duplicate':journal.append(json.loads(json.dumps(exits[0])))
        for i,r in enumerate(journal,1):r['seq']=i
        (run/'journal.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in journal),encoding='utf-8')
        for file,value in [('result.json',stopped),('final.json',final)]:
            (run/file).write_text(json.dumps(value,indent=2),encoding='utf-8')
        with patch('subprocess.Popen',side_effect=AssertionError('real launch forbidden')) as launch:
            actual=validate(run,True)
            assert launch.call_count==0
        diagnostic=';'.join(actual.get('invalid',[]))
        passed=actual['status']==expected and (reason is None or reason in diagnostic)
        (run.parent/'validation.json').write_text(json.dumps(actual,indent=2),encoding='utf-8')
        rows.append(dict(case=name,expected=expected,actual=actual['status'],expectedReason=reason or '',actualReason=diagnostic,passed=passed))
    assert before=={str(f.relative_to(source)):sha(f) for f in source.rglob('*') if f.is_file()}
    with (out/'expected-actual.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result=dict(cases=rows,source=str(source),sourceHashes=before,sourceUnchanged=True,realLaunches=0,realInputs=0)
    (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(total=len(rows),passed=sum(r['passed'] for r in rows),failed=[r['case'] for r in rows if not r['passed']])))
    return 0 if all(r['passed'] for r in rows) else 1


if __name__=='__main__':raise SystemExit(main())
