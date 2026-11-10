"""Connected lower air space beneath holder shelves, excluding intended bolt bores."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import json,trimesh,manifold3d as mf
from mesh_union import manifold
ROOT=Path(__file__).resolve().parent.parent
report={}
for side in ['left','right']:
 upper=manifold(trimesh.load(ROOT/'exports'/f'{side}-closed-development.stl'))
 lower=manifold(trimesh.load(ROOT/'exports'/f'{side}-bottom-development.stl')).translate((0,0,-7.3))
 interior=manifold(trimesh.load(ROOT/'references'/f'{side}-interior-v3.stl'))
 clip=mf.Manifold.cube((400,400,13)).translate((-200,-200,-5))
 air=(interior^clip)-upper-lower
 parts=sorted([p for p in air.decompose() if p.volume()>.001],key=lambda p:-p.volume())
 report[side]={'region_z_mm':[-5,8],'air_components':[{'volume_mm3':p.volume(),'bounds':p.bounding_box()} for p in parts]}
 assert sum(p.volume()>1000 for p in parts)==1,'Extra lower chamber disconnected from main cavity'
 print(side,'main connected air volume',parts[0].volume(),'small components clipped at the inspection boundary',[p.volume() for p in parts[1:]])
(ROOT/'reports/lower-cavity-connectivity-v7.json').write_text(json.dumps(report,indent=2))
