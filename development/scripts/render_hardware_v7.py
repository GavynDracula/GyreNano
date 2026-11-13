"""Run via blender-official execute_blender_code_for_cli on the empty preview seed.
Only renders exported geometry; does not change manufacturing meshes.
"""
import bpy
from mathutils import Vector
from pathlib import Path
import os
ROOT=str(Path(os.environ.get('GYRE_PROJECT_ROOT', Path(__file__).resolve().parents[1] if '__file__' in globals() else Path.cwd())).resolve())
scene=bpy.context.scene
assert not list(scene.objects), 'Use the dedicated empty preview seed'
scene.unit_settings.system='METRIC'
scene.unit_settings.length_unit='MILLIMETERS'
def mat(name,color,rough=.65):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough
 return m
body=mat('Shell',(.22,.43,.51));base=mat('Tray',(.08,.13,.17));floor=mat('Floor',(.67,.7,.72))
for side,dx in [('left',-.15),('right',.15)]:
 for part,material in [('closed',body),('bottom',base)]:
  bpy.ops.wm.stl_import(filepath=f'{ROOT}/exports/{side}-{part}-development.stl',global_scale=.001)
  obj=bpy.context.object;obj.name=side+'_'+part;obj.location.x=dx
  if part=='bottom':obj.location.z=-.0073
  obj.data.materials.append(material)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.0074));bpy.context.object.data.materials.append(floor)
bpy.ops.object.camera_add(location=(0,-.38,.31));cam=bpy.context.object
cam.rotation_euler=(Vector((0,.009,.015))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=.37;cam.data.clip_start=.001;scene.camera=cam
for name,loc,power,size in [('Key',(-.2,-.2,.4),2,.3),('Fill',(.3,-.1,.25),1,.25),('Rim',(0,.3,.3),2,.2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.name=name;light.data.energy=power;light.data.shape='DISK';light.data.size=size
 light.rotation_euler=(Vector((0,0,.015))-light.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Preview world');scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.5,.5,.5,1)
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.3
scene.render.engine='CYCLES';scene.cycles.samples=128;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=ROOT+'/previews/rounded-assembly.png'
# Interior view: remove the trays from rendering, then show the measured carrier.
for side in ['left','right']:
 bpy.data.objects[side+'_bottom'].hide_render=True
bpy.data.objects['Plane'].hide_render=True
for name,loc in [('Inside key',(-.2,-.2,-.3)),('Inside fill',(.2,.25,-.25))]:
 bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.name=name;light.data.energy=3;light.data.size=.25
 light.rotation_euler=(Vector((0,0,.015))-light.location).to_track_quat('-Z','Y').to_euler()
scene.cycles.samples=48
cam.location=Vector((0,-.15,-.32));target=Vector((0,.012,.01))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.36
renders=[]
scene.render.filepath=ROOT+'/previews/inside-mounts-v7.png';bpy.ops.render.render(write_still=True);renders.append(scene.render.filepath)
cam.location=Vector((-.073,-.025,-.055));target=Vector((-.073,.047,.007));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.084
scene.render.filepath=ROOT+'/previews/holder-close-v7.png';bpy.ops.render.render(write_still=True);renders.append(scene.render.filepath)
cam.location=Vector((0,-.15,-.32));target=Vector((0,.012,.01));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.36

pcbmat=mat('Holder PCB reference',(.06,.25,.12))
for side,dx in [('left',-.15),('right',.15)]:
 bpy.ops.wm.stl_import(filepath=ROOT+'/references/'+side+'-holder-pcb-v6.stl',global_scale=.001)
 obj=bpy.context.object;obj.name=side+'_holder_reference';obj.location.x=dx;obj.data.materials.append(pcbmat)
scene.render.filepath=ROOT+'/previews/inside-holder-v7.png';bpy.ops.render.render(write_still=True);renders.append(scene.render.filepath)
for side in ['left','right']:
 bpy.data.objects[side+'_bottom'].hide_render=False
 bpy.data.objects[side+'_holder_reference'].hide_render=True
bpy.data.objects['Plane'].hide_render=False
cam.location=Vector((0,.34,.075));target=Vector((0,.025,.012))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.36
scene.render.filepath=ROOT+'/previews/usb-rear-v7.png';bpy.ops.render.render(write_still=True);renders.append(scene.render.filepath)
result={'renders':renders,'actual_stl_geometry':True,'holder_mesh':'rigidly fitted current upstream PCB; original mounting datums retained'}
