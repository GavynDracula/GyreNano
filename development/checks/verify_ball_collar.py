"""Audit the exported forward ball collar against frozen pre-rounding samples."""
from pathlib import Path
import sys, hashlib, json
import numpy as np
import trimesh

DEV = Path(__file__).resolve().parents[1]
ROOT = DEV.parent
sys.path.insert(0, str(DEV / 'src'))
from mesh_union import manifold

OUTPUT = DEV / 'exports/raised-rim/ball-collar.json'

def radial_hits(solid, c, n, direction, depth, start, end):
    hits = solid.ray_cast(c+n*depth+direction*start, c+n*depth+direction*end)
    return [(float((np.array(h.position)-c)@direction), float(np.array(h.normal)@direction)) for h in hits]

def main():
    saved = OUTPUT if OUTPUT.exists() else ROOT / 'models/raised-rim/ball-collar.json'
    record = json.loads(saved.read_text()) if saved.exists() else {}
    before_path = ROOT / 'models/raised-rim/GyreNanoRightShell.stl'
    before = None if record else manifold(trimesh.load(before_path))
    if not record:
        record['before_sha256'] = hashlib.sha256(before_path.read_bytes()).hexdigest()
    after_path = DEV / 'exports/raised-rim/right-shell.stl'
    after = manifold(trimesh.load(after_path))
    b = json.loads((DEV / 'references/ball-surface.json').read_text())
    c, n = np.array(b['center']), np.array(b['normal'])
    u = np.array([n[2], 0, -n[0]])
    v = np.cross(n, u)
    rows = []
    for i, deg in enumerate(np.linspace(0, 95, 191)):
        direction = u*np.cos(np.deg2rad(deg))+v*np.sin(np.deg2rad(deg))
        old = record['radial_profile'][i][1] if before is None else next(r for r, dot in radial_hits(before, c, n, direction, -.25, 23.5, 45) if dot>.1)
        new = next(r for r, dot in radial_hits(after, c, n, direction, -.25, 23.5, 45) if dot>.1)
        rows.append([float(deg), old, new])
    # Freeze the complete old hit list so rebuilding does not require an old STL.
    old_wall_samples = record.get('before_wall_samples', [])
    widths = []
    index = 0
    for depth in [-.5, -1, -2, -3, -4, -5, -6, -8, -10, -12]:
        for deg in np.linspace(-20, 120, 281):
            direction = u*np.cos(np.deg2rad(deg))+v*np.sin(np.deg2rad(deg))
            if before is not None:
                old_wall_samples.append([r for r, _ in radial_hits(before, c, n, direction, depth, 17, 48)])
            a = old_wall_samples[index]
            z = [r for r, _ in radial_hits(after, c, n, direction, depth, 17, 48)]
            if len(a)>=2 and len(z)>=2 and 22<a[0]<24 and 22<z[0]<24:
                width, previous = z[1]-z[0], a[1]-a[0]
                assert width >= min(1.6, previous)-.001, (depth, deg, previous, width)
                widths.append([float(depth), float(deg), previous, width])
            index += 1
    rows_array = np.array(rows)
    substantial = [w for w in widths if w[2]>=1.6]
    assert len(substantial)>1000
    assert np.ptp(rows_array[:, 2])<.4 and rows_array[:, 2].max()<27.8
    record.update(after_sha256=hashlib.sha256(after_path.read_bytes()).hexdigest(),
                  units='mm', profile_description='Outward radial exit at ball-local height-0.25mm, angles0..95deg,0.5deg spacing; rounded forward arc, not entire shell silhouette.',
                  radial_profile=rows, before_wall_samples=old_wall_samples,
                  sampled_material_intervals=widths,
                  before_radius_range_mm=[float(rows_array[:, 1].min()), float(rows_array[:, 1].max())],
                  after_radius_range_mm=[float(rows_array[:, 2].min()), float(rows_array[:, 2].max())],
                  baseline_at_least_1p6mm_probe_count=len(substantial),
                  minimum_after_for_these_probes_mm=min(w[3] for w in substantial),
                  inherited_thin_intervals=len(widths)-len(substantial),
                  wall_note='Radial material intervals, including inherited short/tangential intervals. Baseline-aware1.6mm requirement; sampled check, not global minimum wall certification.',
                  passed=True)
    OUTPUT.write_text(json.dumps(record, indent=2)+'\n')
    print('PASS: forward circular arc', record['before_radius_range_mm'], '->', record['after_radius_range_mm'])
    print('Radial wall intervals:',len(widths),'; regular intervals minimum:',record['minimum_after_for_these_probes_mm'])

if __name__ == '__main__':
    main()
