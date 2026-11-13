"""Verify this release's relocated delivery bytes and packaged archive integrity.

Standard-library only; does not run CAD, alter sources or qualify physical fit.
"""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'docs/releases/delivery-sha256.json').read_text())
for relative, expected in manifest.items():
    path = ROOT / relative
    assert path.is_file(), f'Missing delivery: {relative}'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, relative
    if path.suffix in {'.zip', '.3mf'}:
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None, relative
            assert all(not n.startswith('/') and '..' not in Path(n).parts
                       for n in archive.namelist()), relative
print(f'PASS: {len(manifest)} delivery files match the release SHA-256 manifest.')
