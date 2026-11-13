"""Vertical ray audit for unintended roof openings; current envelope vertex sampling (V7: 0.3 mm grid).
Exclude only the projected switch ports and the ball opening. This is a sampled
geometric check, not a claim of waterproofness or sub-grid defect detection.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from matplotlib.path import Path as PolygonPath
import numpy as np,json,trimesh
import manifold3d as mf
from mesh_union import manifold
ROOT=Path(__file__).resolve().parent.parent
report={}
for side in ['left','right']:
 shell=manifold(trimesh.load(ROOT/'exports'/f'{side}-closed-development.stl'))
 surface=trimesh.load(ROOT/'references'/f'{side}-rounded-envelope.stl')
 points=surface.vertices[surface.vertices[:,2]>2]
 outline=np.array(json.loads((ROOT/'references'/f'{side}-v3-outline.json').read_text())['outer'])
 boundary_mask=PolygonPath(outline).contains_points(points[:,:2],radius=-.15)
 boundary_excluded=int((~boundary_mask).sum());points=points[boundary_mask]
 ports=[]
 for p in json.load(open(ROOT/'references'/f'{side}-switch-planes.json')):
  n=np.array(p['normal']);x=np.array(p['x']);y=np.cross(n,x)
  ports.append(mf.Manifold.cube((14.3,14.3,8),center=True).transform(np.column_stack((x,y,n,np.array(p['center'])-n*2))))
 if side=='right':
  ports.append(manifold(trimesh.load(ROOT/'references/ball-opening-v11.stl'))^manifold(trimesh.load(ROOT/'references/right-interior-v3.stl')))
 tested=0;skipped=0;holes=[]
 # Boundary points are excluded: test points with material in the reference envelope.
 for x,y,z in points:
  origin=(float(x),float(y),90);end=(float(x),float(y),0.01)
  if any(port.ray_cast((float(x),float(y),200),(float(x),float(y),-100)) for port in ports):skipped+=1;continue
  tested+=1
  if not shell.ray_cast(origin,end):holes.append([float(x),float(y),float(z)])
 report[side]={'boundary_excluded':boundary_excluded,'checked_points':tested,'intentional_port_samples':skipped,'unexpected_open_samples':holes}
 print(side,tested,'unexpected openings',len(holes),flush=True)
(ROOT/'reports/roof-checks.json').write_text(json.dumps(report,indent=2))

assert all(not r["unexpected_open_samples"] for r in report.values()), "Unexpected roof opening samples"
