"""Independent regression probes for both photographed defects, on exported STLs."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import json,numpy as np,trimesh
from mesh_union import manifold, load_regression
R=Path(__file__).resolve().parent.parent
old=manifold(load_regression('right-closed-v7.stl'));new=manifold(trimesh.load(R/'exports/right-closed-v11.stl'))
b=json.load(open(R/'references/ball-surface.json'));c=np.array(b['center']);n=np.array(b['normal']);x=np.array([n[2],0,-n[0]]);y=np.cross(n,x)
k=json.load(open(R/'references/right-switch-planes.json'))[7];kc=np.array(k['center']);kn=np.array(k['normal'])
# The camera rays pass through the photographed isolated side window, not the key port.
cam=np.array([-72,-147,128]);d=np.array([0.,120,-100]);d/=np.linalg.norm(d);up=np.cross([1,0,0],d)
records=[]
for px in np.arange(586,603,2):
 for py in np.arange(462,482,2):
  origin=cam+np.array([1,0,0])*(px/1200-.5)*55+up*(.5-py/1000)*55/1.2;end=origin+d*250
  if old.ray_cast(origin,end):continue
  hits=new.ray_cast(origin,end)
  z=[float((np.array(h.position)-kc)@kn) for h in hits[:2]]
  records.append({'pixel':[int(px),int(py)],'hit_key_depths_mm':z,'wall_chord_mm':float(np.linalg.norm(np.array(hits[1].position)-hits[0].position)) if len(hits)>1 else 0})
# It must hit the roof band above the PCB, not a new floor below the PCB.
assert len(records)>=20
assert all(len(a['hit_key_depths_mm'])==2 and a['hit_key_depths_mm'][0]>-3.5 for a in records),records
report={'photographed_window_rays':len(records),'min_window_wall_chord_mm':min(a['wall_chord_mm'] for a in records),'window_ray_records':records}
# Radial probes of the lower rim in the photographed non-key sector.
radial=[]
for depth in [-7.5,-6.5,-5.5]:
 for angle in np.arange(-100,46,2):
  direction=x*np.cos(np.deg2rad(angle))+y*np.sin(np.deg2rad(angle));start=c+n*depth;end=start+direction*30
  row={'depth_mm':depth,'angle_deg':float(angle)}
  for label,solid in [('v7',old),('v8',new)]:
   hits=solid.ray_cast(start,end);row[label+'_entry_radius_mm']=float(np.linalg.norm(np.array(hits[0].position)-start)) if hits else None
  radial.append(row)
assert all(row['v8_entry_radius_mm'] is not None and row['v8_entry_radius_mm']<23.21 for row in radial),[row for row in radial if row['v8_entry_radius_mm'] is None or row['v8_entry_radius_mm']>=23.21]
report['lower_rim_radial_probes']=len(radial);report['v7_recess_probes']=sum(row['v7_entry_radius_mm'] is None or row['v7_entry_radius_mm']>23.3 for row in radial);report['radial_records']=radial
(R/'reports/ball-rim-checks-v11.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if not k.endswith('records')})
