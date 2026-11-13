"""Independent comparison of written STLs to upstream meshes, within each switch land."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import numpy as np
import trimesh
from mesh_union import manifold
import manifold3d as mf
ROOT=Path(__file__).resolve().parent.parent
rows=[]
def pose(mesh,p,solid):
 n=np.array(p['normal']);x=np.array(p['x']);y=np.cross(n,x);center=np.array(p['center'])
 # Compare the SAME physical locations, avoiding tessellation-dependent face selection.
 sample=[]
 for edge in [-8.2,-7.5,7.5,8.2]:
  for along in [-6,-3,0,3,6]:
   for u,vv in [(edge,along),(along,edge)]:
    q=center+x*u+y*vv
    hits=solid.ray_cast(q+n*.2,q-n*.2)
    hits=[h for h in hits if np.array(h.normal)@n>.99]
    if hits:sample.append((np.array(hits[0].position)-center)@np.column_stack((x,y,n)))
 sample=np.array(sample);assert len(sample)>=36
 design=np.column_stack((sample[:,:2],np.ones(len(sample))))
 slope=np.linalg.lstsq(design,sample[:,2],rcond=None)[0]
 normal=n-x*slope[0]-y*slope[1];normal/=np.linalg.norm(normal)
 plane_offset=slope[2]
 v=(mesh.vertices-center)@np.column_stack((x,y,n))
 v=v[(np.abs(v[:,2])<.02)&(np.max(np.abs(v[:,:2]),axis=1)<7.01)]
 assert len(v)>=4
 lo=v[:,:2].min(0);hi=v[:,:2].max(0)
 return normal,plane_offset,(lo+hi)/2,hi-lo
for side in ['left','right']:
 path=ROOT.parent.parent/'Charybdis/files/3x5 nano/charybdisnano_v2_v187.stl' if side=='right' else ROOT/'references/skeletyl-v4-103.stl'
 original=trimesh.load(path);v=original.vertices.copy()
 original.vertices=np.column_stack((v[:,0],(70.01831113 if side=='right' else 0)-v[:,2],v[:,1]+8))
 if side=='left':original.apply_transform(np.diag([-1,1,1,1]))
 final=trimesh.load(ROOT/'exports'/f'{side}-closed-development.stl')
 assert final.is_watertight and final.is_winding_consistent
 a,b=manifold(original),manifold(final)
 for i,p in enumerate(json.load(open(ROOT/'references'/f'{side}-switch-planes.json'))):
  n=np.array(p['normal']);x=np.array(p['x']);y=np.cross(n,x)
  zone=mf.CrossSection.square((13.8,13.8),center=True).offset(1.5,circular_segments=64).extrude(4.2).transform(np.column_stack((x,y,n,np.array(p['center'])-n*4)))
  added=((b-a)^zone).volume();removed=((a-b)^zone).volume()
  n0,h0,c0,size0=pose(original,p,a);n1,h1,c1,size1=pose(final,p,b)
  angle=float(np.degrees(np.arccos(np.clip(n0@n1,-1,1))))
  row=dict(side=side,key=i,reference_center_mm=p['center'],center_xy_delta_mm=float(np.linalg.norm(c1-c0)),bearing_plane_delta_mm=float(abs(h1-h0)),axis_delta_deg=angle,aperture_size_delta_mm=float(np.max(np.abs(size1-size0))),added_mm3=added,removed_mm3=removed)
  pcb=mf.Manifold.cube((19.6,19.6,7),center=True).transform(np.column_stack((x,y,n,np.array(p['center'])-n*7.5)))
  row['pcb_added_interference_mm3']=((b-a)^pcb).volume()
  assert row['pcb_added_interference_mm3']<.001,row
  rows.append(row)
  assert added<.001 and removed<.001,row
  assert row['center_xy_delta_mm']<.01 and row['bearing_plane_delta_mm']<.01 and angle<.01 and row['aperture_size_delta_mm']<.01,row
report={'datum':'original STEP rotated X+90, translated Z+8; left mirrored X; all local dimensions mm','scope':'Written final STL versus official baseline mesh within rounded 16.8 mm functional switch lands, corner radius 1.5 mm (outside frame air is filled in V5) from -4 to +0.2 mm; relative keyboard geometry, not world height above desk','key_count':len(rows),'max_center_xy_delta_mm':max(r['center_xy_delta_mm'] for r in rows),'max_bearing_plane_delta_mm':max(r['bearing_plane_delta_mm'] for r in rows),'max_axis_delta_deg':max(r['axis_delta_deg'] for r in rows),'max_aperture_size_delta_mm':max(r['aperture_size_delta_mm'] for r in rows),'keys':rows}
(ROOT/'reports/key-geometry-verification.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='keys'})
