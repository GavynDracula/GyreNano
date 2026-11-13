"""Check the PCB-facing partition, independently of a particular camera.

Sample radial rays toward the actual thumb PCB box, comparing to V10.
Also measure the removal of the photographed front tongue with volume probes.
All dimensions are millimetres in the original enclosure assembly frame.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import json
import numpy as np
import trimesh
import manifold3d as mf
from mesh_union import manifold, load_regression

R = Path(__file__).resolve().parent.parent
old = manifold(load_regression('right-closed-v10.stl'))
new = manifold(trimesh.load(R / 'exports/right-closed-v11.stl'))
b = json.loads((R / 'references/ball-surface.json').read_text())
c = np.array(b['center']); n = np.array(b['normal'])
u = np.array([n[2], 0, -n[0]]); v = np.cross(n, u)
k = json.loads((R / 'references/right-switch-planes.json').read_text())[7]
kc = np.array(k['center']); kn = np.array(k['normal']); kx = np.array(k['x'])
axes = np.column_stack((kx, np.cross(kn, kx), kn))
lo = np.array([-9.8, -9.8, -11]); hi = np.array([9.8, 9.8, -4])
records = []; failures = []
for height in np.arange(.6, 13.21, .2):
    origin = c + n * height
    local = (origin-kc) @ axes
    for angle in np.arange(120., 220.01, .5):
        a = np.deg2rad(angle)
        direction = u*np.cos(a) + v*np.sin(a)
        d = direction @ axes
        t0 = (lo-local)/d; t1 = (hi-local)/d
        near = np.minimum(t0, t1).max(); far = np.maximum(t0, t1).min()
        if near >= far or not 17.8 < near < 27:
            continue
        start = origin + direction * 17.60
        end = origin + direction * (near-.02)
        def chord(solid):
            hits = solid.ray_cast(start, end)
            return sum(np.linalg.norm(np.array(y.position)-x.position)
                       for x,y in zip(hits[::2], hits[1::2]))
        before = chord(old)
        if before < .6:
            continue
        after = chord(new)
        row = dict(angle_deg=float(angle), height_mm=float(height),
                   pcb_radius_mm=float(near), old_chord_mm=float(before),
                   new_chord_mm=float(after))
        records.append(row)
        if after < .3:
            failures.append(row)

# The pictured front protrusion was at approximately theta=225°, n=3.4.
# Probe a finite surrounding sector, not one vertex or a hand-picked ray.
angles = np.deg2rad(np.linspace(220, 245, 101))
poly = np.vstack(([0., 0.], np.column_stack((21.5*np.cos(angles), 21.5*np.sin(angles)))))
probe = mf.CrossSection([poly]).extrude(12).transform(np.column_stack((u,v,n,c+n*.6)))
before = (old ^ probe).volume(); after = (new ^ probe).volume()
report = dict(pcb_partition_rays=len(records), failed_rays=len(failures),
              minimum_material_chord_mm=min(r['new_chord_mm'] for r in records),
              front_tongue_probe=dict(angle_deg=[220,245], radius_mm=21.5,
                                     height_mm=[.6,12.6], v10_volume_mm3=before,
                                     v11_volume_mm3=after),
              records=records, failures=failures)
(R/'reports/partition-checks-v11.json').write_text(json.dumps(report, indent=2))
print({k:v for k,v in report.items() if k not in ['records','failures']}, flush=True)
assert len(records)>100 and not failures
assert before>1 and after<.001
