"""Regression for the user's residual window, viewed from the ball side.
Tests the actual exported STL, with V9 as the known failing baseline.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import json,numpy as np,trimesh
from mesh_union import manifold, load_regression
R=Path(__file__).resolve().parent.parent
old=manifold(load_regression('right-closed-v9.stl'))
new=manifold(trimesh.load(R/'exports/right-closed-v11.stl'))
tool=manifold(trimesh.load(R/'references/regression/ball-opening-v9.stl'))
b=json.load(open(R/'references/ball-surface.json'));bc=np.array(b['center']);bn=np.array(b['normal']);bu=np.array([bn[2],0,-bn[0]]);bv=np.cross(bn,bu)
k=json.load(open(R/'references/right-switch-planes.json'))[7];kc=np.array(k['center']);kn=np.array(k['normal']);kx=np.array(k['x']);ky=np.cross(kn,kx)
cam=np.array([-25.,-3,60]);target=np.array([-70,-28,25]);d=target-cam;d/=np.linalg.norm(d);right=np.cross(d,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,d)
records=[];failed=[]
for px in range(580,701,2):
 for py in range(470,591,2):
  origin=cam+right*(px/1200-.5)*48+up*(.5-py/1000)*40;end=origin+d*200
  if old.ray_cast(origin,end):continue
  old_port=tool.ray_cast(origin,end)
  if not old_port:continue
  q=np.array(old_port[-1].position);key=(q-kc)@np.column_stack((kx,ky,kn))
  if not (abs(key[:2]).max()<9.8 and -11<key[2]<-4):continue
  hits=new.ray_cast(origin,end)
  coords=(np.array(hits[0].position)-bc)@np.column_stack((bu,bv,bn)) if hits else np.array([1e6]*3)
  # A ray may graze the 0.02 mm bore overlap or the hood's lower edge
  # before crossing the solid skirt. Measure all complete material intervals
  # in the repair zone, not just that tangent first sliver.
  chords=[]
  for entry,leave in zip(hits[::2],hits[1::2]):
   local=(np.array(entry.position)-bc)@np.column_stack((bu,bv,bn))
   if np.linalg.norm(local[:2])<23.3 and .5<local[2]<8:
    chords.append(float(np.linalg.norm(np.array(leave.position)-entry.position)))
  row={'pixel':[px,py],'hits':len(hits),'first_ball_radius_mm':float(np.linalg.norm(coords[:2])),'first_ball_height_mm':float(coords[2]),'material_chord_mm':max(chords,default=0)}
  records.append(row)
  if len(hits)<2 or row['first_ball_radius_mm']>23.3 or row['material_chord_mm']<.2:failed.append(row)
report={'baseline':'V9','camera_mm':cam.tolist(),'original_window_rays':len(records),'failed_rays':len(failed),'minimum_material_chord_mm':min(x['material_chord_mm'] for x in records),'records':records,'failures':failed}
(R/'reports/inner-window-checks-v11.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['records','failures']},flush=True)
assert len(records)>500 and not failed
