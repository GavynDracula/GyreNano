"""Pose supplied original parts at the original adapter flange seat; check final STLs."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import json,numpy as np,trimesh,manifold3d as mf
from mesh_union import manifold
ROOT=Path(__file__).resolve().parent.parent
ball=json.load(open(ROOT/'references/ball-surface.json'));c=np.array(ball['center']);n=np.array(ball['normal']);x=np.array([n[2],0,-n[0]]);z=np.cross(x,n)
# Source top flange bottom is Y=-3. Its circular center is X=-.042995,Z=.016768.
# Align that underside to original shell seat n=0; retain common source part coordinates.
origin=c+3*n+.042995*x-.016768*z
T=np.eye(4);T[:3,:]=np.column_stack((x,n,z,origin))
upper=manifold(trimesh.load(ROOT/'exports/right-closed-v11.stl'))
lower=manifold(trimesh.load(ROOT/'exports/right-bottom-development.stl')).translate((0,0,-7.3))
m=trimesh.load(ROOT.parent/'Charybdis/files/3x5 nano/charybdisnano_v2_v187.stl');v=m.vertices.copy();m.vertices=np.column_stack((v[:,0],70.01831113-v[:,2],v[:,1]+8));original=manifold(m)
paths={'top':'3x5 nano/adapter_v2_top_v75.stl','btu':'mods/btu/adapter_btu_bottom_v32.stl','cover':'sensor_cover_v51.stl'}
report={'transform_source_to_assembly':T.tolist(),'datum':'Top adapter Y=-3 flange underside seated at original shell rim; common native coordinates retained for BTU and cover.','parts':{}}
models={}
interior=manifold(trimesh.load(ROOT/'references/right-interior-v3.stl'))
for name,path in paths.items():
 m=trimesh.load(ROOT.parent/'Charybdis/files'/path);m.apply_transform(T);m.export(ROOT/'references'/f'trackball-{name}-assembly-v7.stl');a=manifold(m);models[name]=a
 report['parts'][name]={'source':path,'bounds_mm':m.bounds.tolist(),'original_shell_overlap_mm3':(a^original).volume(),'upper_overlap_mm3':(a^upper).volume(),'added_upper_overlap_mm3':(a^(upper-original)).volume(),'lower_overlap_mm3':(a^lower).volume(),'outside_inner_footprint_mm3':(a-interior).volume()}
# Check top adapter's insertion normal without attributing original snap contact to new geometry.
report['top_insertion_added_overlap_mm3']=[((models['top'].translate(n*d))^(upper-original)).volume() for d in np.arange(0,36,2)]
report['part_pair_overlap_mm3']={a+'_'+b:(models[a]^models[b]).volume() for a,b in [('top','btu'),('top','cover'),('btu','cover')]}
core=manifold(trimesh.load(ROOT/'references/ball-mount-core.stl'))
report['original_mount_core_removed_mm3']=((original-upper)^core).volume()
report['horizontal_clearance_probe_mm']=.5
report['parts_outside_inner_after_clearance_probe_mm3']={name:max((a.translate((.5*np.cos(t),.5*np.sin(t),0))-interior).volume() for t in np.linspace(0,2*np.pi,16,endpoint=False)) for name,a in models.items()}
assert report['original_mount_core_removed_mm3']<.001
assert max(report['parts_outside_inner_after_clearance_probe_mm3'].values())<.001
(ROOT/'reports/trackball-assembly-checks-v11.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
assert all(abs(p['added_upper_overlap_mm3'])<.001 and abs(p['lower_overlap_mm3'])<.001 and abs(p['outside_inner_footprint_mm3'])<.001 for p in report['parts'].values())
report['straight_normal_insertion_validated']=False
report['validation_scope']='Static installed geometry only. The original shell also intersects a straight normal insertion; do not infer an insertion path from added-material overlap.'
(ROOT/'reports/trackball-assembly-checks-v11.json').write_text(json.dumps(report,indent=2))
