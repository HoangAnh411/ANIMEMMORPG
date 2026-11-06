import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--label',required=True);a=p.parse_args();d=a.session/a.label;m=json.loads((d/'analysis.json').read_text());inp=json.loads((d/'input.json').read_text());windows=json.loads((d/'windows.json').read_text());rows=[]
for q in m['trials']:
 r=dict(index=q['index'],direction=q['direction'],activationMs=q['activationFrameMs'],ownerMs=q['keyToOwnedTransformMs'],serverMs=q['keyToServerTransformMs'],peerMs=q['keyToPeerTransformMs'])
 for band in ['0:0.5','0.5:2','2:5','5:15']:
  b=q['bins'][band];r[band]=dict(p95=b['wallMs']['p95'],max=b['wallMs']['max'],gpuP95=b['gpuMs']['p95'] if b['gpuMs'] else None,renderP95=b['renderMs']['p95'] if b['renderMs'] else None,roles=b['allRoles'])
 rows.append(r)
res=dict(completed=m['completed'],trials=rows,editorsAlwaysIconic=bool(windows) and all(e['iconic'] for w in windows for e in w['editors']),windowSamples=len(windows),inputRestored=inp['completed'],noMultiSecondDegradation=all(q['bins']['2:5']['wallMs']['p95']<25 and q['bins']['5:15']['wallMs']['p95']<25 for q in m['trials']),profiles=m['profiles']);(d/'SUMMARY.json').write_text(json.dumps(res,indent=2));print(json.dumps(dict(label=a.label,complete=res['completed'],n=len(rows),editorIconic=res['editorsAlwaysIconic'],lateP95=[round(r['5:15']['p95'],2) for r in rows],maxes=[round(max(r[b]['max'] for b in ['0:0.5','0.5:2','2:5','5:15']),2) for r in rows],ownerMs=[r['ownerMs'] for r in rows])))
