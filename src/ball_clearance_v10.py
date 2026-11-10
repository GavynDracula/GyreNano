"""Exact CAD check objects, millimetres; execute with build123d backend.

The demo sphere is a pose on the checked path, not an inferred bearing centre.
Validate sphere34_v10 and probe_sweep_v10 before exporting check references.
"""
from build123d import Axis, Align, Cylinder, Sphere, Vector

seat = Vector(-49.7884582778934, -32.0372274373079, 32.66025394843741)
axis = Vector(-0.5, 0, 0.8660254037844388)
sphere34_v10 = Sphere(17).translate(seat + axis * 3)
probe_local = Cylinder(17.6, 83, align=(Align.CENTER, Align.CENTER, Align.MIN))
probe_local += Sphere(17.6)
probe_local += Sphere(17.6).translate((0, 0, 83))
probe_sweep_v10 = probe_local.rotate(Axis.Y, -30).translate(seat - axis * 3)
