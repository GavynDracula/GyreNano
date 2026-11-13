"""Prepare compact STL delivery and exact cut-out trials. No global scaling or smoothing."""
from pathlib import Path
import sys,json
import numpy as np
import trimesh
import manifold3d as mf
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from mesh_union import manifold
out=R/'exports/trials';out.mkdir(exist_ok=True)
printing=R/'exports/print';printing.mkdir(exist_ok=True)
report={'units':'mm','assumed_nozzle_mm':.4,'assumed_layer_mm':.2,'parts':{},'trials':{}}
models={}
for side in ['left','right']:
 for part in ['closed','bottom']:
  name=f'{side}-{part}-development.stl';p=R/'exports'/name
  m=trimesh.load(p);old_bytes=p.stat().st_size
  assert m.is_watertight and m.is_winding_consistent and len(m.split())==1
  # Preserve the exact, already-validated ASCII mesh. Float32 binary STL
  # rounds near-coincident boolean seam vertices and can break manifoldness.
  # Compression belongs in a ZIP, not a lossy coordinate conversion.
  import os
  target=printing/name
  if target.exists():target.unlink()
  os.link(p,target)
  models[(side,part)]=m
  normals=m.face_normals;area=m.area_faces;centers=m.triangles_center
  underside=(normals[:,2]<-np.sqrt(.5))&(centers[:,2]>.25)
  report['parts'][name]={'bounds_mm':m.bounds.tolist(),'size_mm':m.extents.tolist(),'volume_mm3':float(m.volume),'triangles':len(m.faces),'watertight':True,'components':1,'source_bytes':old_bytes,'delivery_bytes':p.stat().st_size,'coordinate_change_mm':0,'encoding':'Original STL, unchanged; ZIP-compressed delivery','downward_area_over_45deg_above_bed_mm2':float(area[underside].sum()),'overhang_metric_scope':'Orientation screening only; bridging and support access require slicer inspection.'}
# Engineering masters and the V11 versioned file remain unchanged.
# These are exact sections of the production mesh. Keep Z orientation, translate only.
a=manifold(models[('right','closed')])
for name,lo,hi,purpose in [
 ('right-ball-thumb-fit',[-97,-60,0],[-20,0,55],'34 mm ball, specified adapter and adjacent thumb switch/PCB; same build direction as the full shell'),
 ('right-holder-usb-fit',[-103,24,0],[-49,71,13],'Original holder screw spacing, support datum, USB cable nose and insert fit; upper case clipped at Z=13')]:
 lo=np.array(lo,dtype=float);hi=np.array(hi,dtype=float)
 clip=mf.Manifold.cube(hi-lo).translate(lo);cut=a^clip
 parts=cut.decompose();positive=[p for p in parts if p.volume()>0]
 discarded=[]
 if len(positive)>1 and name=='right-holder-usb-fit':
  main=max(positive,key=lambda item:item.volume())
  supports=manifold(trimesh.load(R/'references/right-holder-support-v7.stl'))
  assert ((cut-main)^supports).volume()<.0001
  for item in positive:
   if item is main:continue
   bounds=item.bounding_box()
   assert item.volume()<20 and bounds[2]>12,(item.volume(),bounds)
   discarded.append({'volume_mm3':item.volume(),'bounds_mm':list(bounds),'reason':'Disconnected upper key-roof remnant outside holder support; created by crop plane.'})
  cut=main
 else:assert len(positive)==1,(name,[p.volume() for p in positive])
 # Remove near-coincident Boolean tessellation without changing the design.
 # Manifold's simplification guarantee is < tolerance displacement; independently
 # require added/removed material below 0.0001 mm3 in original assembly coordinates.
 shift=-np.array(cut.bounding_box()[:3])
 normalized=cut.translate(shift).simplify(1e-7)
 restored=normalized.translate(-shift)
 added=(restored-cut).volume();removed=(cut-restored).volume()
 assert abs(added)<.0001 and abs(removed)<.0001
 mesh_data=normalized.to_mesh64();m=trimesh.Trimesh(mesh_data.vert_properties[:,:3],mesh_data.tri_verts,process=False)
 path=out/(name+'.stl');candidate=out/(name+'.candidate.stl')
 candidate.write_text(trimesh.exchange.stl.export_stl_ascii(m))
 reread=trimesh.load(candidate)
 assert reread.is_watertight and reread.is_winding_consistent and len(reread.split())==1
 candidate.replace(path)
 report['trials'][name]={'clip_min_assembly_mm':lo.tolist(),'clip_max_assembly_mm':hi.tolist(),'translation_to_print_mm':shift.tolist(),'size_mm':m.extents.tolist(),'volume_mm3':float(m.volume),'watertight':True,'discarded_crop_remnants':discarded,'normalization_tolerance_mm':1e-7,'normalization_added_mm3':added,'normalization_removed_mm3':removed,'purpose':purpose,'limits':'Cut boundaries change stiffness and support demand. Trial is not a replacement enclosure or proof of whole-case printability.'}
# Independently inspect the thin inner skirt from the original ball axis.
b=json.loads((R/'references/ball-surface.json').read_text());c=np.array(b['center']);n=np.array(b['normal']);u=np.array([n[2],0,-n[0]]);v=np.cross(n,u)
a=manifold(trimesh.load(R/'exports/right-closed-v11.stl'));rows=[]
for height in [.61,.8,1.0,1.2,1.6,2.0,2.35]:
 angle=np.deg2rad(175);direction=u*np.cos(angle)+v*np.sin(angle)
 origin=c+n*height+direction*17.5;end=c+n*height+direction*23.0
 hits=a.ray_cast(origin,end)
 lengths=[float(np.linalg.norm(np.array(y.position)-x.position)) for x,y in zip(hits[::2],hits[1::2])]
 rows.append({'ball_axial_height_mm':height,'radial_material_chords_mm':lengths})
report['skirt_radial_sections']=rows
report['status']='FDM preparation and geometry screening; not a validated printer profile or production approval.'
(R/'reports/fdm-preparation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'parts':report['parts'],'trials':report['trials'],'skirt':rows},indent=2),flush=True)
