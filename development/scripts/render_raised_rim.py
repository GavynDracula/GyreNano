"""Run in a dedicated empty Blender scene through the Blender CAD backend.

For execute_blender_code_for_cli, compile this file with its real __file__.
No manufacturing geometry is changed, and no slicer is called.
"""
from pathlib import Path
import bpy
from mathutils import Vector

DEV = Path(__file__).resolve().parents[1]
ROOT = DEV.parent
OUT = DEV / "previews/raised-rim"
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
assert not list(scene.objects), "Use a dedicated empty preview seed"
scene.unit_settings.system = "METRIC"
scene.unit_settings.length_unit = "MILLIMETERS"
groups = {"baseline": [], "candidate": []}
for group in groups:
    folder = ROOT / "models/integrated-fr4" if group == "baseline" else DEV / "exports/raised-rim"
    for side, shift in [("left", -.115), ("right", .115)]:
        bpy.ops.wm.stl_import(filepath=str(folder / f"{side}-shell.stl"), global_scale=.001)
        obj = bpy.context.object
        obj.name = f"{group}_{side}"
        obj.location.x = shift
        obj.color = (.28, .44, .48, 1)
        for face in obj.data.polygons:
            face.use_smooth = False
        obj.data.set_sharp_from_angle(angle=.6)
        groups[group].append(obj)

bpy.ops.object.camera_add(location=(.22, -.28, .26))
camera = bpy.context.object
camera.rotation_euler = (Vector((0, .005, .018)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = .29
camera.data.clip_start = .001
scene.camera = camera
scene.render.engine = "BLENDER_WORKBENCH"
shading = scene.display.shading
shading.light = "STUDIO"
shading.studiolight_rotate_z = .5
shading.color_type = "OBJECT"
shading.show_shadows = False
shading.show_cavity = False
shading.cavity_type = "BOTH"
shading.curvature_ridge_factor = 1.1
shading.curvature_valley_factor = .8
shading.background_type = "WORLD"
scene.world.color = (.8, .8, .8)
scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

for visible in ["baseline", "candidate"]:
    for group, objects in groups.items():
        for obj in objects:
            obj.hide_render = group != visible
    scene.render.filepath = str(OUT / f"{visible}.png")
    bpy.ops.render.render(write_still=True)

camera.location = (0, .005, .4)
camera.rotation_euler = (Vector((0, .005, 0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
scene.render.filepath = str(OUT / "top.png")
bpy.ops.render.render(write_still=True)
# Dedicated detail views use the same checked meshes and lighting.
for side, camera_position, target in [
    ("left", (.17, -.18, .21), (-.025, -.008, .025)),
    ("right", (-.12, -.20, .20), (.025, -.01, .027)),
]:
    for obj in groups["candidate"]:
        obj.hide_render = obj.name != f"candidate_{side}"
    camera.location = camera_position
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = .12
    scene.render.filepath = str(OUT / f"{side}-transition-detail.png")
    bpy.ops.render.render(write_still=True)
# Close view of the repaired outside seam beside the ball cup.
for obj in groups["candidate"]:
    obj.hide_render = obj.name != "candidate_right"
camera.location = (.06, -.23, .11)
camera.rotation_euler = (Vector((.06, -.045, .026)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.ortho_scale = .105
scene.render.filepath = str(OUT / "right-outer-seam.png")
bpy.ops.render.render(write_still=True)
# Face-on collar view uses the actual ball-seat normal, without geometry edits.
import json
ball = json.loads((DEV / "references/ball-surface.json").read_text())
ball_center = Vector(ball["center"]) * .001 + Vector((.115, 0, 0))
camera.location = ball_center + Vector(ball["normal"]) * .2
camera.rotation_euler = (ball_center - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.ortho_scale = .09
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.filepath = str(OUT / "right-ball-collar.png")
bpy.ops.render.render(write_still=True)
result = {"renders": [str(OUT / name) for name in ["baseline.png", "candidate.png", "top.png",
          "left-transition-detail.png", "right-transition-detail.png", "right-outer-seam.png", "right-ball-collar.png"]],
          "source_models_modified": False, "sliced": False}
