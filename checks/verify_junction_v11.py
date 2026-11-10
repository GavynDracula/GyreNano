"""Regression for the exposed socket floor seen through the V8 side window.
Uses final exported geometry. Positive results require new exterior material,
not merely blocking the window with a floor beneath the PCB.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import json,numpy as np,trimesh
from mesh_union import manifold, load_regression
R=Path(__file__).resolve().parent.parent
old=manifold(load_regression('right-closed-v8.stl'))
new=manifold(trimesh.load(R/'exports/right-closed-v11.stl'))
k=json.load(open(R/'references/right-switch-planes.json'))[7];kc=np.array(k['center']);kn=np.array(k['normal'])
cam=np.array([-72,-147,44.]);d=np.array([0.,120,-20]);d/=np.linalg.norm(d);up=np.cross([1,0,0],d)
records=[];fail=[]
for px in range(632,691,2):
 for py in range(510,577,2):
  origin=cam+np.array([1,0,0])*(px/1200-.5)*44+up*(.5-py/1000)*44/1.2;end=origin+d*250
  oh=old.ray_cast(origin,end)
  # Only rays demonstrably entering the old side window and hitting the
  # socket's deep floor, not the legitimate key opening or the ball aperture.
  if not oh:continue
  op=np.array(oh[0].position);depth=float((op-kc)@kn)
  if not (-11.02<depth<-10.98 and np.array(oh[0].normal)@kn>.999):continue
  nh=new.ray_cast(origin,end);q=np.array(nh[0].position) if nh else op
  new_depth=float((q-kc)@kn);advance=float((op-q)@d)
  row={'pixel':[px,py],'old_hit_mm':op.tolist(),'new_hit_mm':q.tolist(),'new_key_depth_mm':new_depth,'new_exterior_ahead_mm':advance}
  records.append(row)
  if not nh or advance<2 or new_depth<-9:fail.append(row)
report={'rays':len(records),'failed_rays':len(fail),'minimum_exterior_advance_mm':min(r['new_exterior_ahead_mm'] for r in records),'minimum_new_key_depth_mm':min(r['new_key_depth_mm'] for r in records),'records':records,'failures':fail}
(R/'reports/outer-window-checks-v11.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['records','failures']},flush=True)
assert len(records)>100 and not fail
