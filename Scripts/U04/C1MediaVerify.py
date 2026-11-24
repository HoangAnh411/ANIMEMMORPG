"""Read-only verification for a separately recorded fixture illustration."""
import argparse
import hashlib
from pathlib import Path

from PIL import Image
from C1Run import read


def verify_image(path):
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image, path.open('rb') as stream:
        image.load()
        return dict(path=str(path), size=list(image.size), format=image.format,
                    sha256=hashlib.file_digest(stream, 'sha256').hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('summary', type=Path)
    parser.add_argument('--build', required=True)
    args = parser.parse_args()
    summary = read(args.summary)
    required = ('subjects','hurtboxesPerSubject','inside')
    if not all(key in summary for key in required) or summary['hurtboxesPerSubject'] not in (1, 3):
        parser.error('fixture workload evidence missing')
    import json
    print(json.dumps(dict(build=args.build, decoded=verify_image(args.image),
                          workload={key:summary[key] for key in required},
                          summary=str(args.summary), scope='Image decode and native workload only'), indent=2))


if __name__ == '__main__':
    main()
