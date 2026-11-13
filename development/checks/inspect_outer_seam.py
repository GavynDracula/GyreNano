"""Sample the actual exported outer seam, with frozen pre-repair evidence."""
from pathlib import Path
import sys, hashlib, json
import numpy as np
import trimesh
import manifold3d as mf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DEV = Path(__file__).resolve().parents[1]
ROOT = DEV.parent
sys.path.insert(0, str(DEV / 'src'))
from mesh_union import manifold
from raised_rim import distinct_hits

OUT = DEV / 'exports/raised-rim/outer-seam.json'
PREVIEW = DEV / 'previews/raised-rim/outer-seam.png'

def profile(solid, points):
    result = []
    for point in points:
        hits = distinct_hits(solid.ray_cast([*point, 100], [*point, -1]))
        assert hits, point
        result.append(hits[0].position[2])
    return np.array(result)

def metrics(z):
    changes = np.diff(np.r_[z, z[0]])
    curvature = np.diff(np.r_[changes, changes[0]])
    return {'maximum_adjacent_height_step_mm': float(abs(changes).max()),
            'maximum_second_difference_mm': float(abs(curvature).max()),
            'steps_over_0p5_mm': int((abs(changes) > .5).sum())}

if __name__ == '__main__':
    saved = OUT if OUT.exists() else ROOT / 'models/raised-rim/outer-seam.json'
    evidence = json.loads(saved.read_text()) if saved.exists() else {'sides': {}}
    fig, axes = plt.subplots(2, 1, figsize=(14, 7), constrained_layout=True)
    for side, ax in zip(['left', 'right'], axes):
        source = ROOT / f'models/integrated-fr4/{side}-shell.stl'
        base = manifold(trimesh.load(source))
        polygons = base.slice(.5).to_polygons()
        p = max(polygons, key=lambda p: abs(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - p[:, 1] * np.roll(p[:, 0], -1))))
        p = np.array(mf.CrossSection([p]).simplify(.001).to_polygons()[0])
        edges = np.roll(p, -1, axis=0) - p
        lengths = np.linalg.norm(edges, axis=1)
        cumulative = np.r_[0, np.cumsum(lengths)]
        arc = np.linspace(0, cumulative[-1], int(np.ceil(cumulative[-1] / .1)), endpoint=False)
        indices = np.searchsorted(cumulative, arc, side='right') - 1
        sign = np.sign(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - p[:, 1] * np.roll(p[:, 0], -1)))
        normals = np.c_[-edges[:, 1], edges[:, 0]] / lengths[:, None] * sign
        points = p[indices] + ((arc-cumulative[indices])/lengths[indices])[:, None]*edges[indices] + .03*normals[indices]
        record = evidence['sides'].get(side)
        if record is None:
            before_path = ROOT / f'models/raised-rim/GyreNano{side.title()}Shell.stl'
            before = profile(manifold(trimesh.load(before_path)), points)
            record = {'before_sha256': hashlib.sha256(before_path.read_bytes()).hexdigest(),
                      'before_z_mm': before.tolist()}
        else:
            before = np.array(record['before_z_mm'])
        after_path = DEV / f'exports/raised-rim/{side}-shell.stl'
        solid = manifold(trimesh.load(after_path))
        after = profile(solid, points)
        record.pop('lower_12mm_added_volume_mm3', None)
        record.pop('lower_12mm_removed_volume_mm3', None)
        record.update(after_sha256=hashlib.sha256(after_path.read_bytes()).hexdigest(),
                      arc_mm=arc.tolist(), xy_mm=points.tolist(), after_z_mm=after.tolist(),
                      before=metrics(before), after=metrics(after))
        # Preserve lower ports, bosses and the complete bottom interface.
        prior_path = ROOT / f'models/raised-rim/GyreNano{side.title()}Shell.stl'
        layout = json.loads((DEV / 'parameters/hardware-layout-v7.json').read_text())[side]
        if prior_path.exists() and hashlib.sha256(prior_path.read_bytes()).hexdigest() == record['before_sha256']:
            prior = manifold(trimesh.load(prior_path))
            usb_region = mf.Manifold.cube([20, 25, 12]).translate([layout['usb_center_x']-10, 55, 0])
            record['usb_region_added_mm3'] = float(((solid-prior)^usb_region).volume())
            record['usb_region_removed_mm3'] = float(((prior-solid)^usb_region).volume())
            bottom = mf.Manifold.cube([400, 400, 8]).translate([-200, -200, 0])
            record['bottom8mm_added_mm3'] = float(((solid-prior)^bottom).volume())
            record['bottom8mm_removed_mm3'] = float(((prior-solid)^bottom).volume())
            assert max(record[k] for k in ['usb_region_added_mm3', 'usb_region_removed_mm3',
                                          'bottom8mm_added_mm3', 'bottom8mm_removed_mm3']) < .001
        # Independent repeatable USB/window test against immutable baseline.
        residuals = []
        for x in np.linspace(layout['usb_center_x']-8, layout['usb_center_x']+8, 65):
            for z in np.linspace(.3, 11.7, 39):
                a, b = [x, 85, z], [x, 55, z]
                old_hits, new_hits = distinct_hits(base.ray_cast(a, b)), distinct_hits(solid.ray_cast(a, b))
                assert len(old_hits) == len(new_hits), (side, x, z)
                residuals.extend(np.linalg.norm(np.array(h.position)-g.position) for h, g in zip(old_hits, new_hits))
        record['usb_rays_vs_immutable_baseline'] = {'rays': 65*39, 'max_hit_shift_mm': float(max(residuals))}
        assert max(residuals) < .002  # Existing silhouette cleanup is bounded by0.001mm.
        assert record['after']['steps_over_0p5_mm'] == 0, 'Outer edge still has large abrupt steps'
        evidence['sides'][side] = record
        print(side, record['before'], record['after'], flush=True)
        ax.plot(arc, before, label='Previous shoulder', linewidth=1, alpha=.7)
        ax.plot(arc, after, label='Rebuilt outer seam', linewidth=1)
        ax.set(title=f'{side.title()}: actual mesh, 0.03 mm inside perimeter', xlabel='Perimeter arc (mm)', ylabel='Height (mm)')
        ax.legend()
    evidence['note'] = '0.1 mm perimeter sampling; real exported-mesh heights. Not universal surface-continuity certification.'
    OUT.write_text(json.dumps(evidence, indent=2)+'\n')
    fig.savefig(PREVIEW, dpi=150)
