"""Read-only verification for a separately recorded fixture illustration."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from PIL import Image
from C1Run import ROOT, read, sha


def verify_image(path):
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image, path.open('rb') as stream:
        image.load()
        return dict(path=str(path), size=list(image.size), format=image.format,
                    sha256=hashlib.file_digest(stream, 'sha256').hexdigest())


def verify_receipt(receipt_path, image, summary_path, process_path):
    receipt, summary, process = map(read, (receipt_path, summary_path, process_path))
    decoded = verify_image(image)
    for key, expected in [('imageSHA256', decoded['sha256']), ('summarySHA256', sha(summary_path)),
                          ('processSHA256', sha(process_path))]:
        if receipt.get(key) != expected:
            raise ValueError('receipt_mismatch:' + key)
    run = process_path.resolve().parent
    if process['runId'] != run.name or not all(
            path.resolve().is_relative_to(run) for path in (receipt_path, image, summary_path)):
        raise ValueError('receipt_run_path')
    build = read(ROOT.parent/'Runs/Build-03/BUILD-IDENTITY.json')
    if process['binarySHA256'] != build['gameSHA256'] or receipt.get('buildSHA256') != build['gameSHA256']:
        raise ValueError('receipt_build')
    for key in ('runId', 'pid', 'creationTicks'):
        if receipt.get(key) != process[key] or type(receipt[key]) is not type(process[key]):
            raise ValueError('receipt_mismatch:' + key)
    argv = process['arguments']
    if '-U04C1Profile' not in argv or receipt.get('map') != argv[1].split('?', 1)[0]:
        raise ValueError('receipt_map_or_fixture')
    capture = datetime.fromisoformat(receipt['capturedUTC'])
    if capture < datetime.fromisoformat(process['creationUTC']):
        raise ValueError('receipt_capture_before_launch')
    targets = summary.get('targets', [])
    count = summary['hurtboxesPerSubject']
    if summary['subjects'] != 1 or summary['inside'] is not True or count not in (1, 3) or len(targets) != 1:
        raise ValueError('fixture_workload')
    target = targets[0]
    fields = ('subject', 'life', 'stableHurtboxIds')
    if any(receipt.get(key) != target[key] for key in fields) or sorted(target['stableHurtboxIds']) != list(range(1, count+1)):
        raise ValueError('receipt_target_or_hurtboxes')
    return dict(decoded=decoded, runId=run.name, capture=receipt['capturedUTC'],
                target={key: target[key] for key in fields})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('summary', type=Path)
    parser.add_argument('--process', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_receipt(args.receipt, args.image, args.summary, args.process), indent=2))


if __name__ == '__main__':
    main()
