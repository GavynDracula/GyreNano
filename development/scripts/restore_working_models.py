"""Restore ignored working STL files from published 3MF meshes; keep existing files."""
from pathlib import Path
import shutil
import numpy as np
import trimesh
from export_public_models import MODELS, read_mesh

ROOT = Path(__file__).resolve().parents[1]
for directory in ['exports/trials', 'exports/print', 'reports', 'previews']:
    (ROOT/directory).mkdir(parents=True, exist_ok=True)
for name, destination in MODELS.items():
    target = ROOT/'exports'/destination
    if target.exists():
        print('Keeping', target.relative_to(ROOT))
        continue
    mesh = read_mesh(ROOT.parent/'files'/(name+'.3mf'))
    # ASCII retains double-precision coordinates; binary STL would round them.
    target.write_text(trimesh.exchange.stl.export_stl_ascii(mesh))
    restored = trimesh.load(target)
    assert restored.is_watertight and restored.is_winding_consistent
    # STL reindexes vertices; compare sorted vertex rows, not array order.
    def sorted_points(points):
        return points[np.lexsort(points.T[::-1])]
    assert np.array_equal(sorted_points(mesh.vertices), sorted_points(restored.vertices))
    print('Restored', target.relative_to(ROOT))
versioned = ROOT/'exports/right-closed-v11.stl'
if not versioned.exists():
    shutil.copy2(ROOT/'exports/right-closed-development.stl', versioned)
for side in ['left', 'right']:
    target = ROOT/'exports'/f'{side}-bottom-development.step'
    if not target.exists():
        shutil.copy2(ROOT.parent/'files/3x5'/f'gyre-nano-{side}-bottom-v7.step', target)
