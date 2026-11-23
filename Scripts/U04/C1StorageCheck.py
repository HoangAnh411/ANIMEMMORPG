"""Measure lossless Insights CSV archives without writing to historical runs."""
import argparse
import gzip
import hashlib
import json
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from C1Run import ROOT, read, sha, write


def roundtrip(source, dest, expected):
    start = time.perf_counter()
    digest = hashlib.sha256()
    count = 0
    with source.open('rb') as stream, dest.open('xb') as output:
        with gzip.GzipFile(filename='', fileobj=output, mode='wb', compresslevel=1, mtime=0) as zipstream:
            for data in iter(lambda: stream.read(4 << 20), b''):
                digest.update(data)
                count += len(data)
                zipstream.write(data)
    compressed = time.perf_counter() - start
    assert (count, digest.hexdigest()) == (expected['bytes'], expected['sha256']), source
    start = time.perf_counter()
    reopened = hashlib.sha256()
    recovered = 0
    with gzip.open(dest, 'rb') as stream:
        for data in iter(lambda: stream.read(4 << 20), b''):
            reopened.update(data)
            recovered += len(data)
    elapsed = time.perf_counter() - start
    assert (recovered, reopened.hexdigest()) == (count, expected['sha256']), dest
    return dict(source=str(source), archive=str(dest), rawBytes=count, gzipBytes=dest.stat().st_size,
                rawSHA256=expected['sha256'], gzipSHA256=sha(dest),
                compressionSeconds=compressed, decompressionSeconds=elapsed,
                recoveredBytes=recovered, recoveredSHA256=reopened.hexdigest())


def main(out):
    out.mkdir()
    ledger_path = ROOT.parent/'CC-B-Foreground-Control-20261123-091739/method-ledger.json'
    ledger = read(ledger_path)
    rows = [r for r in ledger if r['mode'] in ('timing','memory')]
    for row in rows:
        export = Path(row.get('exportPath',ledger_path.parent/row['id']/'Exports')).resolve()
        run = Path(row['raw']).resolve()
        trace = run/'capture.utrace'
        receipt = read(export/'exit.json')
        assert receipt['exitCode']==0
        digest=sha(trace)
        assert digest==row['trace']['sha256']==read(export/'process.json')['traceSHA256']
        dest=out/row['id'];dest.mkdir()
        shutil.copyfile(export/'Insights.log',dest/'Insights.log')
        def archive(item):
            print(row['id'],item['path'],'start',flush=True)
            v=roundtrip(export/item['path'],dest/(item['path']+'.gz'),item)
            print(row['id'],item['path'],v['gzipBytes'],flush=True)
            return v
        with ThreadPoolExecutor(max_workers=2) as workers:
            files=list(workers.map(archive,receipt['exports']))
        write(dest/'storage.json',dict(mode=row['mode'],traceBytes=trace.stat().st_size,traceSHA256=digest,
             originalRetainedBytes=row['retainedBytes'],exportPath=str(export),files=files))
    write(out/'roundtrip-complete.json',dict(runs=[r['id'] for r in rows],gzipLevel=1,bufferBytes=4<<20))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('out',type=Path)
    args=parser.parse_args()
    main(args.out.resolve())
