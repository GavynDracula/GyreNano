"""Read exported STLs; check closure and assembly / conservative PCB collisions."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import numpy as np
import trimesh
import manifold3d as mf
from mesh_union import manifold
ROOT=Path(__file__).resolve().parent.parent
report={}
for side in ['left','right']:
 upper=trimesh.load(ROOT/'exports'/f'{side}-closed-development.stl')
 lower=trimesh.load(ROOT/'exports'/f'{side}-bottom-development.stl');lower.apply_translation((0,0,-7.3))
 a,b=manifold(upper),manifold(lower)
 collisions=[]
 for p in json.load(open(ROOT/'references'/f'{side}-switch-planes.json')):
  z=np.array(p['normal']);x=np.array(p['x']);y=np.cross(z,x)
  tool=mf.Manifold.cube((19.6,19.6,7),center=True).transform(np.column_stack((x,y,z,np.array(p['center'])-z*7.5)))
  collisions.append((b^tool).volume())
 report[side]={'upper_watertight':upper.is_watertight,'lower_watertight':lower.is_watertight,'upper_winding_consistent':upper.is_winding_consistent,'lower_winding_consistent':lower.is_winding_consistent,'upper_lower_intersection_mm3':(a^b).volume(),'pcb_lower_max_intersection_mm3':max(collisions),'assembly_bounds_mm':np.vstack((np.minimum(upper.bounds[0],lower.bounds[0]),np.maximum(upper.bounds[1],lower.bounds[1]))).tolist()}
 assert upper.is_watertight and lower.is_watertight and upper.is_winding_consistent and lower.is_winding_consistent
 assert (a^b).volume()<.001 and max(collisions)<.001
(ROOT/'reports/assembly-checks.json').write_text(json.dumps(report,indent=2));print(report)
