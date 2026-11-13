"""Download/resume snapshot parts and verify the original archive; no extraction."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
URL = 'https://github.com/GavynDracula/GyreNano/releases/download/v0.2.0-prototype.1/'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Destination .tar.gz; an existing mismatched file is never overwritten')
    parser.add_argument('--parts-dir', type=Path, help='Use already-downloaded parts, without network access')
    args = parser.parse_args()
    meta = json.loads((ROOT / 'docs/releases/snapshot-parts.json').read_text())
    if args.output.exists():
        if digest(args.output) != meta['sha256']:
            raise SystemExit('Output already exists with different content; choose another path.')
        print('Already verified:', args.output)
        return
    cache = args.parts_dir or Path(tempfile.gettempdir()) / ('gyrenano-snapshot-' + meta['sha256'][:12])
    cache.mkdir(parents=True, exist_ok=True)
    parts = []
    for row in meta['parts']:
        name = row['name']
        assert Path(name).name == name and name not in {'.', '..'}
        part = cache / name
        good = part.is_file() and part.stat().st_size == row['size_bytes'] and digest(part) == row['sha256']
        if not good:
            if args.parts_dir:
                raise SystemExit('Missing or invalid local part: ' + str(part))
            temporary = cache / (name + '.downloading')
            with urllib.request.urlopen(URL + name, timeout=60) as response, temporary.open('wb') as stream:
                shutil.copyfileobj(response, stream)
            if temporary.stat().st_size != row['size_bytes'] or digest(temporary) != row['sha256']:
                raise SystemExit('Downloaded part failed verification: ' + name)
            temporary.replace(part)
        parts.append(part)
        print('Verified:', name, flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # A unique temporary file avoids clobbering unrelated partial downloads.
    with tempfile.NamedTemporaryFile(dir=args.output.parent, prefix=args.output.name + '.', suffix='.partial', delete=False) as stream:
        temporary = Path(stream.name)
        for part in parts:
            with part.open('rb') as source:
                shutil.copyfileobj(source, stream)
    if temporary.stat().st_size != meta['size_bytes'] or digest(temporary) != meta['sha256']:
        temporary.unlink()
        raise SystemExit('Combined archive failed verification.')
    if args.output.exists():
        temporary.unlink()
        raise SystemExit('Output appeared during download; refusing to overwrite it.')
    temporary.replace(args.output)
    print('Verified archive:', args.output)
    print('Extract into a separate empty workspace, not over the current repository.')

if __name__ == '__main__':
    main()
