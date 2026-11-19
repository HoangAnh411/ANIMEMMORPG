"""Tool-only review proof. Reads frozen R1a evidence; never starts UE/game/input.

Creates a NEW output directory; neither legacy evidence nor reviewer outputs
are writable targets. Additional chain audit is not an acceptance verdict.
"""
import argparse,collections,gzip,hashlib,json,re,subprocess,sys
from pathlib import Path
from AnalyzeR1 import VERSION,dodge_chain

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    root=Path(__file__).resolve().parents[2];a.out.mkdir(parents=True,exist_ok=False)
    legacy=root/'Docs/U04/R1a/Evidence/Review-20261119';manifest=legacy/'MANIFEST.json'
    expected='dd45d73d734d6855923264681316e2110bc7f006abd342347fcdc3d6fcd75e9b'
    assert sha(manifest)==expected,'legacy manifest changed'
    native_paths=['Source','Content','Config','Plugins','AnimeMMORPG.uproject']
    assert not subprocess.check_output(['git','-C',str(root),'diff','e9a8264a0f94863001e13af319f7fcf0c379e314','--']+native_paths)
    def run(name,args):
        with (a.out/name).open('wb') as output:r=subprocess.run([sys.executable,'-X','utf8']+args,cwd=root,stdout=output,stderr=subprocess.STDOUT)
        assert r.returncode==0,(name,r.returncode)
    run('SYNTHETIC.log',['Scripts/U04/TestAnalyzeR1.py'])
    test_log=(a.out/'SYNTHETIC.log').read_text(encoding='utf-8')
    count=int(re.search(r'Ran (\d+) tests',test_log)[1])
    run('LEGACY-SEAL.log',['Scripts/U04/VerifyEvidenceB.py',str(manifest)])
    run('RECOMPUTE.log',['Scripts/U04/RecomputeR1a.py','--published',str(legacy),'--out',str(a.out/'Recomputed')])
    comparisons=[]
    for doc,generated in [('REPRO-MATRIX.csv','REPRO-RESULTS.csv'),('COLLECTOR-MATRIX.csv','IDLE-RESULTS.csv')]:
        original=root/'Docs/U04/R1a'/doc;new=a.out/'Recomputed'/generated
        assert original.read_bytes()==new.read_bytes(),doc
        comparisons.append(dict(historical=original.relative_to(root).as_posix(),recomputed=generated,sha256=sha(new),byteIdentical=True))
    results=[]
    for fps in (30,60,120):
        for case in ('w-shift','shift-w','w-up-shift','previous'):
            for attempt in (1,2):
                trial=f'fps{fps}-{case}-{attempt}'
                f=legacy/f'Runs/Repro-fps{fps}-20261119/Raw/{trial}.jsonl.gz'
                data=gzip.decompress(f.read_bytes());raw=[json.loads(s) for s in data.decode('utf-8-sig').splitlines()]
                rows=[r for r in raw if r['kind']=='frame']
                record=dict(trial=trial,requestedDirection='forward',scope='ADDITIONAL_CHAIN_AUDIT_ONLY',acceptance=False,rawSHA256=hashlib.sha256(data).hexdigest())
                try:
                    chain=dodge_chain(raw,rows,'forward')
                    record.update(status='CHAIN_PASS' if not chain['reasons'] else 'FAIL',reasons=chain['reasons'],command=chain['command'],pawnId=chain['pawnId'],life=chain['life'],trajectorySequence=chain['trajectorySequence'],admissionVelocity=chain['admissionVelocity'])
                except (ValueError,KeyError,TypeError) as e:record.update(status='INVALID',reason=str(e))
                results.append(record)
    counts=dict(collections.Counter(r['status'] for r in results));assert counts=={'CHAIN_PASS':6,'INVALID':18},counts
    (a.out/'ADDITIONAL-CHAIN-AUDIT.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    recomputed=json.loads((a.out/'Recomputed/SUMMARY.json').read_text(encoding='utf-8'))
    assert (recomputed['reproGameplayPassed'],recomputed['idleMethodPassed'],recomputed['reproCadencePassed'],recomputed['reproCadenceInvalid'])==(24,9,2,22)
    (a.out/'TOOL-DIFF.patch').write_bytes(subprocess.check_output(['git','-C',str(root),'diff','e9a8264a0f94863001e13af319f7fcf0c379e314','--','Scripts/U04']))
    summary=dict(completed=True,phase='R1A_TOOL_ONLY_REVIEW_PENDING',BStatus='INCOMPLETE',R1bStarted=False,acceptance=False,
                 baseline='e9a8264a0f94863001e13af319f7fcf0c379e314',nativeSource='8cbcb6a6d6dfc4e29bff8731a6aaab187f887cb4',nativeInputsUnchanged=True,
                 legacyManifestSHA256=expected,legacyEvidenceAssociations=450,syntheticGroups=count,csvComparisons=comparisons,
                 historicalReproGameplay=24,historicalIdleCadence=9,historicalReproCadencePassed=2,historicalReproCadenceInvalid=22,historicalReclassified=0,
                 additionalChainAudit=counts,newGameplayRuns=0,newNativeBuilds=0,analyzerVersion=VERSION,
                 tools=[dict(path=str(p.relative_to(root)),sha256=sha(p)) for p in [Path(__file__),root/'Scripts/U04/AnalyzeR1.py',root/'Scripts/U04/TestAnalyzeR1.py',root/'Scripts/U04/RecomputeR1a.py',root/'Scripts/U04/AnalyzeR1a.py']])
    assert sha(manifest)==expected
    (a.out/'SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('PASS tool-only proof:',count,'synthetic groups;450 legacy associations;24/9/2/22 historical counts and CSV bytes unchanged; additional chain audit6/18; no UE run/build')

if __name__=='__main__':main()
