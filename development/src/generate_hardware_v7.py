"""Embed the shared mm coordinate data in the build123d CAD sources."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent.parent
layout=json.load(open(ROOT/'parameters/hardware-layout-v7.json'))
outlines={s:json.load(open(ROOT/'references'/f'{s}-v3-outline.json'))['outer'] for s in ['left','right']}
planes={s:json.load(open(ROOT/'references'/f'{s}-switch-planes.json')) for s in ['left','right']}
header='from build123d import *\nfrom math import hypot,atan2,degrees\nfrom pathlib import Path\nimport os\nROOT='+"str(Path(os.environ.get('GYRE_PROJECT_ROOT', Path(__file__).resolve().parents[1] if '__file__' in globals() else Path.cwd())).resolve())"+'\nDATA='+repr(layout)+'\nOUTLINES='+repr(outlines)+'\n'
helper='''
def nearest_wall(c,poly):
 best=None;distance=1e9
 for p,q in zip(poly,poly[1:]+poly[:1]):
  d=(q[0]-p[0],q[1]-p[1]);t=max(0,min(1,((c[0]-p[0])*d[0]+(c[1]-p[1])*d[1])/(d[0]*d[0]+d[1]*d[1])))
  w=(p[0]+t*d[0],p[1]+t*d[1]);l=hypot(w[0]-c[0],w[1]-c[1])
  if l<distance:best=w;distance=l
 return best,distance
def union_all(parts):
 result=parts[0]
 for p in parts[1:]:result=result+p
 return result
'''
source=header+helper+'''
for side in ['left','right']:
 d=DATA[side];features=[];tools=[];holder_features=[];holder_tools=[]
 for x,y in d['case_mounts']:
  features.append(Pos(x,y,0)*Cylinder(6,8,align=(Align.CENTER,Align.CENTER,Align.MIN)))
  tools.append(Pos(x,y,-.1)*Cylinder(2.75,4.6,align=(Align.CENTER,Align.CENTER,Align.MIN))+Pos(x,y,0)*Cylinder(1.7,6,align=(Align.CENTER,Align.CENTER,Align.MIN)))
 for x,y in d['mounts']:
  q,dist=nearest_wall((x,y),OUTLINES[side]);angle=degrees(atan2(q[1]-y,q[0]-x))
  profile=SlotCenterToCenter(dist,8.6).rotate(Axis.Z,angle).translate(((x+q[0])/2,(y+q[1])/2,4.25))
  support=extrude(profile,amount=4.8)
  drill=Pos(x,y,4.15)*Cylinder(d['holder_insert_diameter']/2,4.1,align=(Align.CENTER,Align.CENTER,Align.MIN))+Pos(x,y,4.15)*Cylinder(1.7,6.2,align=(Align.CENTER,Align.CENTER,Align.MIN))
  holder_features.append(support);holder_tools.append(drill)
 features+=holder_features;tools+=holder_tools
 x=d['usb_center_x'];z=d['usb_center_z'];front=Plane(origin=(x,64.6662553633265,z),x_dir=(1,0,0),z_dir=(0,1,0))
 collar=extrude(front*RectangleRounded(18,12,2),amount=12)
 features.append(collar)
 original=import_step(ROOT+'/../../Charybdis/files/3x5 nano/charybdisnano_v2_v187.step').rotate(Axis.X,90).translate((0,0,8)) if side=='right' else import_step(ROOT+'/references/skeletyl-v4-v99.step').rotate(Axis.X,90).translate((0,0,8)).mirror(Plane.YZ)
 wires=[w for f in original.faces() if f.geom_type==GeomType.PLANE and abs(f.center().Y-64.6662553633265)<.001 for w in f.inner_wires() if 9<w.bounding_box().size.X<11 and 3<w.bounding_box().size.Z<4]
 assert len(wires)==1
 throat=extrude(Face(wires[0]),amount=30,dir=(0,1,0)).translate((0,-5,0))
 relief=extrude(Plane(origin=(x,66.6662553633265,z),x_dir=(1,0,0),z_dir=(0,1,0))*RectangleRounded(14,8.6,1.5),amount=25)
 usb=throat+relief;measure(usb)
 features=union_all(features);bores=union_all(tools)
 assert features.is_valid and bores.is_valid and usb.is_valid
 show(features,side+'_upper_features');measure(features)
 export_stl(features,ROOT+'/references/'+side+'-upper-features-v7.stl',tolerance=.025)
 export_stl(bores,ROOT+'/references/'+side+'-mount-bores-v7.stl',tolerance=.015)
 export_stl(usb,ROOT+'/references/'+side+'-usb-cut-v7.stl',tolerance=.015)
 export_stl(union_all(holder_features)-union_all(holder_tools),ROOT+'/references/'+side+'-holder-support-v7.stl',tolerance=.02)
 # Metal nose and molded plug body use separate insertion envelopes.
 metal=extrude(Plane(origin=(x,60.5,z),x_dir=(1,0,0),z_dir=(0,1,0))*RectangleRounded(8.4,2.6,1.2),amount=6.2)
 plastic=extrude(Plane(origin=(x,66.7,z),x_dir=(1,0,0),z_dir=(0,1,0))*RectangleRounded(12,6,1.3),amount=18)
 export_stl(metal+plastic,ROOT+'/references/'+side+'-usb-plug-envelope-v7.stl',tolerance=.02)
result=features
'''
(ROOT/'src/hardware_v7.py').write_text(source)
bottom=header+'PCB_PLANES='+repr(planes)+'\n'+'''
for side in ['left','right']:
 poly=OUTLINES[side]
 clean=[]
 for i,p in enumerate(poly):
  a=poly[i-1];b=poly[(i+1)%len(poly)]
  if abs((p[0]-a[0])*(b[1]-p[1])-(p[1]-a[1])*(b[0]-p[0]))>1e-7:clean.append(p)
 rim=Wire.make_polygon([(x,y,0) for x,y in clean],close=True);inner=rim.offset_2d(-2.4)
 plate=extrude(Face(rim),amount=2.0,dir=(0,0,-1)).translate((0,0,-5.3))+extrude(Face(rim,[inner]),amount=5.3,dir=(0,0,-1))
 for x,y in DATA[side]['case_mounts']:
  plate=plate+Pos(x,y,-5.3)*Cylinder(6,5.3,align=(Align.CENTER,Align.CENTER,Align.MIN))
 # Clip the circular tabs to the shared exterior, and check the real switch keepouts.
 boundary=extrude(Face(rim),amount=10,dir=(0,0,-1));plate=plate&boundary;measure(plate)
 for p in PCB_PLANES[side]:
  tool=Plane(origin=Vector(p['center'])-Vector(p['normal'])*7.5,x_dir=p['x'],z_dir=p['normal'])*Box(19.6,19.6,7)
  plate=plate-tool
 for x,y in DATA[side]['case_mounts']:
  plate=plate-Pos(x,y,-7.4)*Cylinder(1.7,7.5,align=(Align.CENTER,Align.CENTER,Align.MIN))
  plate=plate-Pos(x,y,-7.31)*Cone(3.2,1.7,1.5,align=(Align.CENTER,Align.CENTER,Align.MIN))
 measure(plate);assert plate.is_valid and len(plate.solids())==1
 show(plate,side+'_bottom_v7')
 export_stl(plate.translate((0,0,7.3)),ROOT+'/exports/'+side+'-bottom-development.stl',tolerance=.02)
result=plate
'''
(ROOT/'src/bottoms_v7.py').write_text(bottom)
print('Wrote CAD sources from hardware-layout-v7.json')
