"""Resample exported shoulders against the recorded pre-smoothing section data.

The immutable before profiles/hash were captured from the rejected integrated
shoulder STL. This preserves comparison evidence without a second 330MB mesh
copy. Sections include original functional surfaces and silhouette crossings;
they are diagnostics, not whole-shell smoothness certification.
"""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DEV = Path(__file__).resolve().parents[1]
ROOT = DEV.parent
sys.path.insert(0, str(DEV / 'src'))
from mesh_union import manifold

if __name__ == '__main__':
    evidence = json.loads((ROOT / 'models/raised-rim/transition-sections.json').read_text())
    solids, hashes = {}, {}
    for side in ['left', 'right']:
        path = DEV / f'exports/raised-rim/{side}-shell.stl'
        solids[side] = manifold(trimesh.load(path))
        hashes[side] = hashlib.sha256(path.read_bytes()).hexdigest()
    fig, axes = plt.subplots(2, 3, figsize=(15, 7), constrained_layout=True)
    for section, ax in zip(evidence['sections'], axes.flat):
        side = section['side']
        start, end = np.array(section['start_xy_mm']), np.array(section['end_xy_mm'])
        t = np.array(section['distances_mm'])
        xy = start + (end - start) * t[:, None] / t[-1]
        after = []
        for x, y in xy:
            hits = solids[side].ray_cast([x, y, 100], [x, y, -1])
            after.append(float(hits[0].position[2]) if hits else None)
        section['after_z_mm'] = after
        section['after_sha256'] = hashes[side]
        section['metrics'] = []
        for values, color, label in [(section['before_z_mm'], '#d5833b', 'Before'),
                                     (after, '#147878', 'Revised')]:
            z = np.array(values, dtype=float)
            slopes = np.diff(z) / np.diff(t)
            jumps = abs(np.diff(np.arctan(slopes))) * 180 / np.pi
            section['metrics'].append(dict(maximum_adjacent_slope_change_deg=float(np.nanmax(jumps)),
                                           p95_adjacent_slope_change_deg=float(np.nanpercentile(jumps, 95))))
            ax.plot(t, z, color=color, label=label, lw=1.4)
        ax.set(title=side.title() + ': ' + section['section'],
               xlabel='Distance along section (mm)', ylabel='Surface height (mm)')
        ax.grid(alpha=.25)
        ax.legend()
    (DEV / 'exports/raised-rim/transition-sections.json').write_text(json.dumps(evidence, indent=2) + '\n')
    fig.savefig(DEV / 'previews/raised-rim/transition-sections.png', dpi=150)
    print('Six current exported-mesh profiles recorded against fixed before samples')
