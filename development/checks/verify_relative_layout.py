"""Measure key-to-key and ball-seat-to-key geometry against the upstream meshes.
The ball datum is the adapter seat, not an inferred physical sphere centre.
"""
from pathlib import Path
import sys,runpy,json
import numpy as np
import trimesh
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from mesh_union import manifold
# Reuse independently measured switch bearing planes and apertures; also re-run
# all existing per-key preservation checks on the actual exported files.
pose=runpy.run_path(str(R/'checks/verify_keys.py'))['pose']
def original(side):
 path=R.parent.parent/'Charybdis/files/3x5 nano/charybdisnano_v2_v187.stl' if side=='right' else R/'references/skeletyl-v4-103.stl'
 mesh=trimesh.load(path);v=mesh.vertices.copy();mesh.vertices=np.c_[v[:,0],(70.01831113 if side=='right' else 0)-v[:,2],v[:,1]+8]
 if side=='left':mesh.apply_transform(np.diag([-1,1,1,1]))
 return mesh
report={'scope':'Relative mounting geometry within each half. New outer skin, tray height above desk and user-adjustable placement between halves are not claimed identical. The physical sphere centre is determined by the installed adapter/bearings, not measured here.','baselines':{'right':'Charybdis charybdisnano_v2_v187.stl','left':'Skeletyl V4 case_v4_103.stl, mirrored'},'sides':{}}
models={};centres={}
for side,thumb in [('left',[0,16,17]),('right',[5,7])]:
 old=original(side);new=trimesh.load(R/'exports'/f'{side}-closed-development.stl');a,b=manifold(old),manifold(new);models[side]=(a,b)
 planes=json.loads((R/'references'/f'{side}-switch-planes.json').read_text());values=[]
 for mesh,solid in [(old,a),(new,b)]:
  points=[]
  for p in planes:
   normal,h,xy,size=pose(mesh,p,solid);n=np.array(p['normal']);x=np.array(p['x']);y=np.cross(n,x)
   points.append(np.array(p['center'])+x*xy[0]+y*xy[1]+n*h)
  values.append(np.array(points))
 before,after=values;centres[side]=values;main=[i for i in range(len(planes)) if i not in thumb]
 pair0=before[:,None,:]-before[None,:,:];pair1=after[:,None,:]-after[None,:,:]
 vector0=before[thumb].mean(0)-before[main].mean(0);vector1=after[thumb].mean(0)-after[main].mean(0)
 row={'main_indices':main,'thumb_indices':thumb,'max_absolute_key_center_shift_mm':float(np.linalg.norm(after-before,axis=1).max()),'max_pairwise_vector_change_mm':float(np.linalg.norm(pair1-pair0,axis=2).max()),'max_pairwise_distance_change_mm':float(np.abs(np.linalg.norm(pair1,axis=2)-np.linalg.norm(pair0,axis=2)).max()),'thumb_centroid_relative_to_main_before_mm':vector0.tolist(),'thumb_centroid_relative_to_main_after_mm':vector1.tolist(),'thumb_to_main_change_mm':float(np.linalg.norm(vector1-vector0))}
 report['sides'][side]=row
 assert row['max_absolute_key_center_shift_mm']<.001 and row['max_pairwise_vector_change_mm']<.001
ball=json.loads((R/'references/ball-surface.json').read_text());c=np.array(ball['center']);n=np.array(ball['normal']);u=np.array([n[2],0,-n[0]]);v=np.cross(n,u);A=np.c_[u,v,n]
a,b=models['right'];ring=[[],[]];seat=[[],[]];changes=[]
for depth in [-.5,-1,-2,-3]:
 for theta in np.linspace(0,2*np.pi,144,endpoint=False):
  d=u*np.cos(theta)+v*np.sin(theta);start=c+n*depth+d*20;end=c+n*depth+d*25
  hits=[s.ray_cast(start,end) for s in [a,b]]
  assert all(hits)
  points=[np.array(h[0].position) for h in hits];changes.append(float(np.linalg.norm(points[1]-points[0])))
  if depth==-3:
   for i,p in enumerate(points):ring[i].append((p-c)@A)
# Probe the retained flange bearing strip (r=23..23.15 mm). Beyond
# r=23.15 the new skin deliberately blends into the outside of the seat;
# those exterior points are not the mounting datum being compared.
for radius in [23.05,23.10,23.14]:
 for theta in np.linspace(0,2*np.pi,144,endpoint=False):
  d=u*np.cos(theta)+v*np.sin(theta);point=c+d*radius
  old=a.ray_cast(point+n*.08,point-n*.08)
  if not old or np.array(old[0].normal)@n<.999:continue
  new=b.ray_cast(point+n*.08,point-n*.08)
  assert new and np.array(new[0].normal)@n>.999
  assert np.linalg.norm(np.array(new[0].position)-old[0].position)<.001
  for i,hits in enumerate([old,new]):seat[i].append((np.array(hits[0].position)-c)@A)
assert len(seat[0])>100
frames=[]
for points,samples in zip(ring,seat):
 xy=np.array(points)[:,:2];fit=np.linalg.lstsq(np.c_[2*xy,np.ones(len(xy))],(xy*xy).sum(1),rcond=None)[0];cx,cy=fit[:2]
 pts=np.array(samples);plane=np.linalg.lstsq(np.c_[pts[:,:2],np.ones(len(pts))],pts[:,2],rcond=None)[0]
 center=c+A@np.array([cx,cy,plane@np.array([cx,cy,1])]);normal=n-u*plane[0]-v*plane[1];normal/=np.linalg.norm(normal)
 frames.append((center,normal))
center0,normal0=frames[0];center1,normal1=frames[1];before,after=centres['right']
seat_shift=float(np.linalg.norm(center1-center0));angle=float(np.degrees(np.arccos(np.clip(normal0@normal1,-1,1))))
relative_delta=np.linalg.norm((after-center1)-(before-center0),axis=1)
report['trackball']={'wall_samples':len(changes),'seat_samples':len(seat[0]),'max_original_wall_sample_displacement_mm':max(changes),'fitted_seat_center_shift_mm':seat_shift,'fitted_seat_normal_change_deg':angle,'max_ball_seat_to_any_key_vector_change_mm':float(relative_delta.max()),'fitted_center_before_mm':center0.tolist(),'fitted_center_after_mm':center1.tolist(),'nominal_seat_datum_mm':c.tolist(),'nominal_axis':n.tolist(),'physical_sphere_center_verified':False}
assert max(changes)<.001 and seat_shift<.001 and angle<.001 and relative_delta.max()<.001
report['passed']=True
(R/'reports/relative-layout-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
