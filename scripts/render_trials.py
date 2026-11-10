"""Render the validated STL trials in a separate scene; never alter manufacturing geometry."""
import bpy
from mathutils import Vector
from pathlib import Path
import os
R=Path(str(Path(os.environ.get('GYRE_PROJECT_ROOT', Path(__file__).resolve().parents[1] if '__file__' in globals() else Path.cwd())).resolve()))
# The loaded preview has already been inspected. Use a new scene and leave it intact.
scene=bpy.data.scenes.new('FDM trials');bpy.context.window.scene=scene
assert not list(scene.objects)
scene.unit_settings.system='METRIC';scene.unit_settings.length_unit='MILLIMETERS'
def material(name,rgb):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=.65
 return m
body=material('Trial blue',(.23,.44,.52));cut=material('Crop face orange',(.8,.4,.12));floor=material('Neutral floor',(.68,.7,.72))
for name,offset in [('right-ball-thumb-fit',(-.09,-.025,0)),('right-holder-usb-fit',(.025,-.025,0))]:
 bpy.ops.wm.stl_import(filepath=str(R/'exports/trials'/(name+'.stl')),global_scale=.001)
 obj=bpy.context.object;obj.name=name;obj.location=offset;obj.data.materials.append(body);obj.data.materials.append(cut)
 bounds=[max(v.co[k] for v in obj.data.vertices) for k in range(3)]
 for face in obj.data.polygons:
  coords=[obj.data.vertices[i].co for i in face.vertices]
  on_cut=any(all(abs(co[k]-plane)<1e-7 for co in coords) for k in [0,1] for plane in [0,bounds[k]])
  if name=='right-holder-usb-fit' and all(abs(co.z-.013)<1e-7 for co in coords):on_cut=True
  if on_cut:face.material_index=1
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.0002));bpy.context.object.data.materials.append(floor)
bpy.ops.object.camera_add(location=(.02,-.22,.18));cam=bpy.context.object
cam.rotation_euler=(Vector((-.01,0,.018))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.22;cam.data.clip_start=.001;scene.camera=cam
for location,power,size in [((-.1,-.15,.3),2,.2),((.2,0,.2),1,.2),((0,.2,.25),2,.2)]:
 bpy.ops.object.light_add(type='AREA',location=location);light=bpy.context.object;light.data.energy=power;light.data.size=size
 light.rotation_euler=(Vector((0,0,.02))-light.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Trial world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(R/'previews/fdm-trials.png')
bpy.ops.render.render(write_still=True)
result={'render':scene.render.filepath,'orange':'artificial crop faces, not added material','manufacturing_geometry_modified':False}
