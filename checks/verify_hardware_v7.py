"""Actual STL checks for original holder datums, wall tabs and USB plug clearance."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import json,numpy as np,trimesh,manifold3d as mf
from mesh_union import manifold
ROOT=Path(__file__).resolve().parent.parent
layout=json.load(open(ROOT/'parameters/hardware-layout-v7.json'));report={}
for side,d in layout.items():
 upper_mesh=trimesh.load(ROOT/'exports'/f'{side}-closed-development.stl');upper=manifold(upper_mesh)
 lower=manifold(trimesh.load(ROOT/'exports'/f'{side}-bottom-development.stl')).translate((0,0,-7.3))
 board=manifold(trimesh.load(ROOT/'references'/f'{side}-holder-pcb-v6.stl'))
 plug=manifold(trimesh.load(ROOT/'references'/f'{side}-usb-plug-envelope-v6.stl'))
 mcu=mf.Manifold.cube((18.6,34.6,9)).translate((d['usb_center_x']-9.3,d['mcu_center_xy'][1]-17.3,4.25))
 source=ROOT.parent/'Charybdis/files/3x5 nano/charybdisnano_v2_v187.stl' if side=='right' else ROOT/'references/skeletyl-v4-103.stl'
 original=trimesh.load(source);v=original.vertices.copy();original.vertices=np.column_stack((v[:,0],(70.01831113 if side=='right' else 0)-v[:,2],v[:,1]+8))
 if side=='left':original.apply_transform(np.diag([-1,1,1,1]))
 baseline=manifold(original)
 mounts=[]
 for x,y in d['mounts']:
  z=[]
  for a in np.linspace(0,2*np.pi,16,endpoint=False):
   q=np.array([x+4*np.cos(a),y+4*np.sin(a),4.1]);end=q+[0,0,.4]
   hits=upper.ray_cast(q,end)
   if hits:z.append(float(hits[0].position[2]))
  sleeve=(mf.Manifold.cylinder(3.8,4.15,circular_segments=96)-mf.Manifold.cylinder(3.8,2.85,circular_segments=96)).translate((x,y,4.3))
  mounts.append({'missing_clean_support_ring_mm3':(sleeve-upper).volume(),'center_xy':[x,y],'bearing_hits':len(z),'max_datum_error_mm':max(abs(v-4.25) for v in z) if z else None})
 wall_tabs=[]
 for x,y in d['case_mounts']:
  # Complete ring around insert must survive the PCB cuts, including at the split.
  annulus=(mf.Manifold.cylinder(4,4.25,circular_segments=64)-mf.Manifold.cylinder(4,2.9,circular_segments=64)).translate((x,y,.1))
  missing=(annulus-upper).volume()
  wall_tabs.append({'center_xy':[x,y],'insert_support_ring_missing_mm3':missing})
 report[side]={'holder_pcb_upper_intersection_mm3':(upper^board).volume(),'holder_pcb_lower_intersection_mm3':(lower^board).volume(),'mcu_envelope_existing_source_overlap_mm3':(baseline^mcu).volume(),'mcu_envelope_added_interference_mm3':((upper-baseline)^mcu).volume(),'usb_plug_upper_intersection_mm3':(upper^plug).volume(),'usb_plug_lower_intersection_mm3':(lower^plug).volume(),'holder_mounts':mounts,'wall_tabs':wall_tabs}
 print(side,report[side],flush=True)
(ROOT/'reports/hardware-checks-v7.json').write_text(json.dumps(report,indent=2))
for s,r in report.items():
 assert all(abs(v)<.001 for k,v in r.items() if k.endswith('_mm3') and 'existing_source' not in k),(s,'hardware interference')
 assert all(x['bearing_hits']==16 and x['max_datum_error_mm']<.001 and x['missing_clean_support_ring_mm3']<.001 for x in r['holder_mounts']),(s,'holder support datum')
 assert all(x['insert_support_ring_missing_mm3']<.001 for x in r['wall_tabs']),(s,'screw support ring')
