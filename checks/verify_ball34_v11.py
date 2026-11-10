"""Continuous insertion clearance, independently measured on exported triangles.
The exact build123d capsule sweeps a 35.2 mm sphere along the original axis.
An analytic radial triangle check additionally avoids inscribed-STL optimism.
The datum is the original flange seat. The tested center travels n=-3..80 mm,
a conservative range, not an inferred/assumed physical bearing contact height.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import json,numpy as np,trimesh
from mesh_union import manifold
R=Path(__file__).resolve().parent.parent
b=json.load(open(R/'references/ball-surface.json'));c=np.array(b['center']);n=np.array(b['normal']);x=np.array([n[2],0,-n[0]]);y=np.cross(n,x)
upper=trimesh.load(R/'exports/right-closed-v11.stl');solid=manifold(upper)
probe=manifold(trimesh.load(R/'references/ball35p2-sweep-v10.stl'))
probe_overlap=(solid^probe).volume()
# All swept spheres are inside n>=-20.6; clip below -21 mm conservatively.
clipped=solid.trim_by_plane(n,float((c-n*21)@n));mm=clipped.to_mesh64();mesh=trimesh.Trimesh(mm.vert_properties[:,:3],mm.tri_verts,process=False)
uv=(mesh.vertices-c)@np.column_stack((x,y));tri=uv[mesh.faces]
best=1e9;closest=None
cross=lambda a,b:a[:,0]*b[:,1]-a[:,1]*b[:,0]
a,b0,cc=tri[:,0],tri[:,1],tri[:,2]
area=cross(b0-a,cc-a);s0=cross(b0-a,-a);s1=cross(cc-b0,-b0);s2=cross(a-cc,-cc)
inside=((s0>=0)&(s1>=0)&(s2>=0)|((s0<=0)&(s1<=0)&(s2<=0)))&(abs(area)>1e-12)
assert not inside.any(), 'A face projects across the insertion axis'
for j in range(3):
 p=tri[:,j];q=tri[:,(j+1)%3];d=q-p;t=np.clip(-np.einsum('ij,ij->i',p,d)/np.maximum(np.einsum('ij,ij->i',d,d),1e-30),0,1);dist=np.linalg.norm(p+t[:,None]*d,axis=1);i=int(dist.argmin())
 if dist[i]<best:
  best=float(dist[i]);closest=(mesh.triangles[i,j]+t[i]*(mesh.triangles[i,(j+1)%3]-mesh.triangles[i,j])).tolist()
report={'ball_diameter_mm':34,'probe_diameter_mm':35.2,'axis_origin_mm':c.tolist(),'axis_direction':n.tolist(),'sphere_center_path_axial_mm':[-3,80],'minimum_shell_axis_distance_mm':best,'minimum_radial_margin_for_34mm_ball_mm':best-17,'closest_case_point_mm':closest,'continuous_capsule_upper_interference_mm3':probe_overlap,'scope':'Upper enclosure and thumb region for insertion along original inclined ball axis. Original adapter bearing contact and adapter installation motions are separate.','method':'Continuous capsule boolean plus analytic minimum over projected triangle interiors/edges, not discrete ball poses.'}
(R/'reports/ball34-clearance-v11.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
assert probe_overlap<.001 and best>=17.60
