"""Extend the right footprint around the supplied adapter assembly, keeping 2.4 mm walls."""
from pathlib import Path
import json,numpy as np,trimesh,manifold3d as mf
from scipy.spatial import ConvexHull
ROOT=Path(__file__).resolve().parent.parent
old=np.array(json.load(open(ROOT/'references/regression/right-outline-v6.json'))['outer']) if (ROOT/'references/regression/right-outline-v6.json').exists() else np.array(json.load(open(ROOT/'references/right-v3-outline.json'))['outer'])
archive=ROOT/'references/regression/right-outline-v6.json'
if not archive.exists():archive.write_text(json.dumps({'outer':old.tolist()},indent=2))
foot=[]
for part in ['top','btu','cover']:
 v=trimesh.load(ROOT/'references'/f'trackball-{part}-assembly-v7.stl').vertices[:,:2]
 poly=v[ConvexHull(v).vertices];foot.extend(mf.CrossSection([poly]).offset(3.2,circular_segments=96).to_polygons())
pts=np.vstack([old,*foot]);poly=pts[ConvexHull(pts).vertices]
section=mf.CrossSection([poly]).offset(-1.0,circular_segments=96).offset(1.0,circular_segments=96).simplify(.02)
poly=max(section.to_polygons(),key=len);poly=poly[ConvexHull(poly).vertices]
section=mf.CrossSection([poly]);interior=section.offset(-2.4,circular_segments=96)
(ROOT/'references/right-v3-outline.json').write_text(json.dumps({'outer':poly.tolist()},indent=2))
a=interior.extrude(200).translate((0,0,-30));m=a.to_mesh64();trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts,process=False).export(ROOT/'references/right-interior-v3.stl')
report={'wall_thickness_mm':2.4,'part_projection_margin_mm':3.2,'area_added_mm2':section.area()-mf.CrossSection([old]).area(),'old_bounds_mm':[old.min(0).tolist(),old.max(0).tolist()],'new_bounds_mm':[poly.min(0).tolist(),poly.max(0).tolist()]}
(ROOT/'reports/trackball-outline-checks-v7.json').write_text(json.dumps(report,indent=2));print(report)
