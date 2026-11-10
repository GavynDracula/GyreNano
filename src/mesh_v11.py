"""V11 global-sheet composition: one continuous enclosure; transplant only functional original mounts.
Uses the established mesh fallback after upstream B-rep boolean failures.
"""
from pathlib import Path
import json
import numpy as np
import trimesh
import manifold3d as mf
from mesh_union import manifold
ROOT=Path(__file__).resolve().parent.parent
def box(size,center,x,n):
 return mf.Manifold.cube(size,center=True).transform(np.column_stack((x,np.cross(n,x),n,center)))
def export_checked(solid,side):
 candidate=ROOT/'previews'/f'{side}-v11-candidate.stl';repairs=[]
 for attempt in range(5):
  m=solid.to_mesh64();mesh=trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts,process=False)
  candidate.write_text(trimesh.exchange.stl.export_stl_ascii(mesh))
  reread=trimesh.load(candidate)
  if reread.is_watertight and reread.is_winding_consistent:break
  counts=np.bincount(reread.edges_unique_inverse);bad=reread.edges_unique[counts>2]
  print("export repair",attempt,len(bad),flush=True)
  assert 0<len(bad)<100
  for ids in bad:
   p,q=reread.vertices[ids];n=q-p;length=np.linalg.norm(n)
   if length<1e-8:tool=mf.Manifold.sphere(.003,circular_segments=12).translate(p)
   else:
    n/=length;x=np.cross(n,[1,0,0] if abs(n[0])<.9 else [0,1,0]);x/=np.linalg.norm(x)
    tool=mf.Manifold.cylinder(length+.006,.003,circular_segments=12).transform(np.column_stack((x,np.cross(n,x),n,p-n*.003)))
   solid=solid-tool;repairs.append([p.tolist(),q.tolist()])
 else:raise RuntimeError('Mesh export repair did not converge')
 candidate.replace(ROOT/'exports'/f'{side}-closed-v11.stl')
 return solid,mesh,repairs
def build(side):
 source=ROOT.parent/'Charybdis/files/3x5 nano/charybdisnano_v2_v187.stl' if side=='right' else ROOT/'references/skeletyl-v4-103.stl'
 orig=trimesh.load(source);v=orig.vertices.copy();orig.vertices=np.column_stack((v[:,0],(70.01831113 if side=='right' else 0)-v[:,2],v[:,1]+8))
 if side=='left':orig.apply_transform(np.diag([-1,1,1,1]))
 a=manifold(orig)
 outer=manifold(trimesh.load(ROOT/'references'/f'{side}-rounded-envelope.stl'))
 interior=manifold(trimesh.load(ROOT/'references'/f'{side}-interior-v3.stl'))
 cavity=outer.translate((0,0,-3))^interior
 b=outer-cavity
 if side=='right':
  # B-rep offset/extrusion failed validity; use the same sampled planar wire
  # through the established Manifold/Clipper fallback, and revalidate the STL.
  ball=json.load(open(ROOT/'references/ball-surface.json'))
  cn=np.array(ball['center']);nz=np.array(ball['normal']);ux=np.array([nz[2],0,-nz[0]]);uy=np.cross(nz,ux)
  # One continuous backing volume joins the original inclined seat to the
  # upper skin. The adapter tool defines its inside; no competing offset rings.
  footprint=mf.CrossSection([np.array(ball['outline'])[:,:2]]).offset(3,circular_segments=64)
  backing=footprint.extrude(100)^box((300,300,120),cn+nz*51.6,ux,nz)
  local=(np.array(ball['outline'])-cn)@np.column_stack((ux,uy))
  if np.sum(local[:,0]*np.roll(local[:,1],-1)-local[:,1]*np.roll(local[:,0],-1))<0:local=local[::-1]
  inclined=(mf.CrossSection([local]).offset(3,circular_segments=64)-mf.CrossSection.circle(22.95,circular_segments=256)).extrude(8.5).transform(np.column_stack((ux,uy,nz,cn-nz*8.4)))
  b=b+((backing+inclined)^outer)
 # Wall-integrated screw tabs, original holder datums and reinforced USB port.
 features=manifold(trimesh.load(ROOT/'references'/f'{side}-upper-features-v7.stl'))
 bores=manifold(trimesh.load(ROOT/'references'/f'{side}-mount-bores-v7.stl'))
 usb=manifold(trimesh.load(ROOT/'references'/f'{side}-usb-cut-v7.stl'))
 hardware=json.load(open(ROOT/'parameters/hardware-layout-v7.json'))[side]
 mcu=mf.Manifold.cube((18.6,34.6,9)).translate((hardware['usb_center_x']-9.3,hardware['mcu_center_xy'][1]-17.3,4.25))
 b=(b+(features^outer))-mcu
 mounts=[bores,usb]
 for cutter in mounts:b=b-cutter
 retained=[];locks=[];pcb=[];planes=json.loads((ROOT/'references'/f'{side}-switch-planes.json').read_text())
 # Holder mounts are clean CAD sleeves sharing the original centers and Z datum.
 # Their outer profile is rebuilt rather than splicing fragments of the old mesh.
 holder=manifold(trimesh.load(ROOT/'references'/f'{side}-holder-support-v7.stl'))
 # Bond the four-normal-mm original key frames into the vertical-thickness
 # sheet. Without this band the underside can open sideways on steep keys.
 for key_index,p in enumerate(planes):
  if not ((side=='right' and key_index==7) or (side=='left' and key_index==16)):continue
  c=np.array(p['center']);n=np.array(p['normal']);x=np.array(p['x']);y=np.cross(n,x)
  outside=mf.CrossSection.square((18,18),center=True).offset(2.6,circular_segments=48)
  inside=mf.CrossSection.square((13.8,13.8),center=True).offset(1.5,circular_segments=64)
  depth=4.0
  collar=(outside-inside).extrude(depth).transform(np.column_stack((x,y,n,c-n*(depth+.05))))
  b=b+(collar^outer)
 for key_index,p in enumerate(planes):
  c=np.array(p['center']);n=np.array(p['normal']);x=np.array(p['x'])
  capture=box((18.6,18.6,4.5),c-n*2.05,x,n) # top -4.3 .. +0.2
  lock=mf.CrossSection.square((13.8,13.8),center=True).offset(1.5,circular_segments=64).extrude(4.5).transform(np.column_stack((x,np.cross(n,x),n,c-n*4.3))) # finite original plate region -4.3 .. +0.2
  # Preserve the functional frame exactly, but trim old peripheral ribs to
  # the new envelope: those ribs otherwise protrude as thin free-standing fins.
  if (side=='right' and key_index==7) or (side=='left' and key_index==16):
   # A small overlap avoids coincident cut/restore faces at the guard boundary.
   landing=mf.CrossSection.square((13.8,13.8),center=True).offset(1.6,circular_segments=64).extrude(4.7).transform(np.column_stack((x,np.cross(n,x),n,c-n*4.4)))
   retained.append(a^landing)
  else:retained.append(a^capture)
  b=b-lock
  opening=box((13.9,13.9,4.5),c-n*2.05,x,n)
  b=b-opening
  keepout=box((19.6,19.6,7),c-n*7.5,x,n);pcb.append(keepout)
  b=b-keepout
  locks.append(mf.CrossSection.square((13.8,13.8),center=True).offset(1.5,circular_segments=64).extrude(4.2).transform(np.column_stack((x,np.cross(n,x),n,c-n*4))))
 if side=='right':
  ball_core=manifold(trimesh.load(ROOT/'references/ball-mount-core.stl'))
  # Fuse the original rim into the continuous skin. Subtracting its outer
  # prism left horizontal slots where the original ring tapers underneath.
  # Preserve the inclined flange interface through n=2.4 mm. Above it,
  # form a normal-axis hood with angular fairing toward the thumb.
  # Independent exported-mesh checks verify ball insertion and static fit.
  transition=2.4
  lower_bore=mf.Manifold.cylinder(35+transition+.01,23.15,circular_segments=256).transform(np.column_stack((ux,uy,nz,cn-nz*35)))
  # Independent spherical insertion clearance: never narrow the local
  # cross-section below 17.6 mm about the original ball axis.
  angles=np.linspace(0,2*np.pi,256,endpoint=False)
  # Above the flange a continuous hood separates the PCB cavity from the
  # ball opening. It occupies only the thumb-facing sector.
  # Concentrate the closure near the PCB corner. The V10 broad 140..220
  # degree plateau created free tongues at both ends of the thumb-side rim.
  hood_center_deg=175.;hood_half_plateau_deg=15.;hood_fairing_deg=40.
  delta=np.abs(np.arctan2(np.sin(angles-np.deg2rad(hood_center_deg)),np.cos(angles-np.deg2rad(hood_center_deg))))
  t=np.clip((delta-np.deg2rad(hood_half_plateau_deg))/np.deg2rad(hood_fairing_deg),0,1);angular=1-t*t*t*(10+t*(-15+6*t))
  radii=23.17-(23.17-17.65)*angular
  poly=np.column_stack((radii*np.cos(angles),radii*np.sin(angles)))
  mouth=mf.CrossSection([poly]).extrude(120).transform(np.column_stack((ux,uy,nz,cn+nz*(transition-.01))))
  ball_pass=mf.Manifold.cylinder(160,17.65,circular_segments=256).transform(np.column_stack((ux,uy,nz,cn-nz*40)))
  mouth=mouth+ball_pass
  adapter_clear=lower_bore+mouth
  m=adapter_clear.to_mesh64();trimesh.Trimesh(m.vert_properties[:,:3],m.tri_verts,process=False).export(ROOT/'references/ball-opening-v11.stl')
  b=b-(adapter_clear^interior)
  # Short inner skirt, inside the adapter's conical free aperture. Its
  # underside stays above the original support seat; it closes the low
  # sightline below the hood without occupying the PCB corner or flange.
  skirt_bottom=.6;skirt_top=2.55
  skirt=mf.Manifold.cylinder(skirt_top-skirt_bottom,17.9+.6*skirt_bottom,17.9+.6*skirt_top,circular_segments=256).transform(np.column_stack((ux,uy,nz,cn+nz*skirt_bottom)))
  sector_angles=np.linspace(np.deg2rad(140),np.deg2rad(220),65)
  sector_poly=np.vstack(([0,0],np.column_stack((50*np.cos(sector_angles),50*np.sin(sector_angles)))))
  sector=mf.CrossSection([sector_poly]).extrude(20).transform(np.column_stack((ux,uy,nz,cn-nz*5)))
  # Share the hood contour down to the skirt: an independent round bore
  # would leave the skirt ends as unsupported fins after trimming the hood.
  skirt_profile=np.column_stack(((radii+.02)*np.cos(angles),(radii+.02)*np.sin(angles)))
  skirt_inner=mf.CrossSection([skirt_profile]).extrude(160).transform(np.column_stack((ux,uy,nz,cn-nz*40)))
  skirt=(skirt-skirt_inner)^sector
  for keepout in pcb:skirt=skirt-keepout
  b=b+skirt
  retained.append(a^ball_core)
 holder=holder-mcu
 for keepout in pcb:holder=holder-(keepout-a)
 combined=b+(holder^outer)
 for piece in retained:combined=combined+piece
 for bore in mounts:combined=combined-bore
 parts=combined.decompose();positive=[p for p in parts if p.volume()>0]
 print(side,'parts',[(p.volume(),p.genus(),p.bounding_box(),(p^a).volume()) for p in parts],flush=True)
 main=max(positive,key=lambda p:p.volume())
 discarded=[]
 for part in positive:
  if part is main:continue
  original_overlap=(part^a).volume()
  assert part.volume()<.1 and abs(original_overlap)<1e-6,'Detached structural part'
  discarded.append({'volume_mm3':part.volume(),'bounds_mm':part.bounding_box(),'original_overlap_mm3':original_overlap})
 combined=max(positive,key=lambda p:p.volume())
 combined,mesh,repairs=export_checked(combined,side)
 preservation=[]
 for zone in locks:preservation.append({'added_mm3':((combined-a)^zone).volume(),'removed_mm3':((a-combined)^zone).volume()})
 return {'sealed_void_volumes_mm3':[-p.volume() for p in parts if p.volume()<0],'discarded_new_skin_slivers':discarded,'volume_mm3':combined.volume(),'components':len(combined.decompose()),'genus':combined.genus(),'watertight':True,'old_frame_volume_removed_mm3':(a-combined).volume(),'key_preservation':preservation,'pcb_added_interference_mm3':[((combined-a)^p).volume() for p in pcb],'reliefs':repairs,'bounds_mm':mesh.bounds.tolist()}
if __name__=='__main__':
 report={side:build(side) for side in ['right']}
 (ROOT/'reports/v11-geometry-checks.json').write_text(json.dumps(report,indent=2))

if __name__ == "__main__":
 import shutil
 shutil.copy2(ROOT/"exports/right-closed-v11.stl", ROOT/"exports/right-closed-development.stl")
