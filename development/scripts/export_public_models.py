"""Publish geometry-only 3MF meshes without rounding coordinates to binary STL.

Run with scripts/run_python.sh. No printer profiles or G-code are embedded.
Every coordinate and triangle index must survive the XML round trip exactly.
"""
from pathlib import Path
from io import StringIO
import hashlib
import json
import shutil
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
MODELS = {
    '3x5/gyre-nano-right-v11': 'right-closed-development.stl',
    '3x5/gyre-nano-left-v7': 'left-closed-development.stl',
    '3x5/gyre-nano-right-bottom-v7': 'right-bottom-development.stl',
    '3x5/gyre-nano-left-bottom-v7': 'left-bottom-development.stl',
    'trials/right-ball-thumb-fit': 'trials/right-ball-thumb-fit.stl',
    'trials/right-holder-usb-fit': 'trials/right-holder-usb-fit.stl',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_mesh(path):
    with zipfile.ZipFile(path) as archive:
        model = ET.fromstring(archive.read('3D/3dmodel.model'))
    vertices = np.array([[float(e.attrib[k]) for k in ('x', 'y', 'z')]
                         for e in model.iter(f'{{{NS}}}vertex')])
    faces = np.array([[int(e.attrib[k]) for k in ('v1', 'v2', 'v3')]
                      for e in model.iter(f'{{{NS}}}triangle')])
    return trimesh.Trimesh(vertices, faces, process=False)

def export(name, source):
    mesh = trimesh.load(source)
    assert mesh.is_watertight and mesh.is_winding_consistent
    assert len(mesh.split(only_watertight=False)) == 1
    target = ROOT.parent / 'files' / (name + '.3mf')
    target.parent.mkdir(parents=True, exist_ok=True)
    xml = StringIO()
    xml.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" xmlns="{NS}">\n')
    xml.write(f'<metadata name="Title">{Path(name).name}</metadata>\n')
    xml.write('<metadata name="Description">Gyre Nano development mesh; geometry only; no printer settings. Derived from BastardKB Charybdis / Skeletyl, CC BY-NC-SA 4.0.</metadata>\n')
    xml.write('<resources><object id="1" type="model"><mesh><vertices>\n')
    for x, y, z in mesh.vertices:
        xml.write(f'<vertex x="{x:.17g}" y="{y:.17g}" z="{z:.17g}"/>\n')
    xml.write('</vertices><triangles>\n')
    for a, b, c in mesh.faces:
        xml.write(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>\n')
    xml.write('</triangles></mesh></object></resources><build><item objectid="1"/></build></model>\n')
    entries = {
        '[Content_Types].xml': '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>',
        '_rels/.rels': '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/3dmodel.model"/></Relationships>',
        '3D/3dmodel.model': xml.getvalue(),
    }
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for filename, contents in entries.items():
            info = zipfile.ZipInfo(filename, (2026, 11, 10, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, contents.encode('utf-8'))
    restored = read_mesh(target)
    assert np.array_equal(mesh.vertices, restored.vertices)
    assert np.array_equal(mesh.faces, restored.faces)
    assert restored.is_watertight and restored.is_winding_consistent
    assert target.stat().st_size < 100 * 1024**2
    row = dict(file=str(target.relative_to(ROOT.parent)), sha256=sha(target),
               source_stl_sha256=sha(source), bytes=target.stat().st_size,
               vertices=len(mesh.vertices), triangles=len(mesh.faces),
               bounds_mm=mesh.bounds.tolist(), watertight=True,
               single_component=True, coordinate_roundtrip_exact=True,
               triangle_indices_roundtrip_exact=True)
    print(name, row['bytes'], 'bytes; exact mesh round trip', flush=True)
    return row

if __name__ == '__main__':
    rows = [export(name, ROOT/'exports'/source) for name, source in MODELS.items()]
    for side in ['left', 'right']:
        shutil.copy2(ROOT/'exports'/f'{side}-bottom-development.step',
                     ROOT.parent/'files/3x5'/f'gyre-nano-{side}-bottom-v7.step')
    (ROOT.parent/'files/manifest.json').write_text(json.dumps({
        'units': 'millimeter', 'scope': 'Geometry-only development snapshot. No printer configuration.',
        'models': rows}, indent=2) + '\n')
