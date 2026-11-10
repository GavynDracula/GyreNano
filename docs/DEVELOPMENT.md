# Development snapshot

Printing requires only the files in `files/`. Rebuilding and running checks use
the sources and upstream references below. This is an archived development
pipeline, not a single-command parametric keyboard generator.

## Environment

Use a Python environment with `numpy`, `scipy`, `trimesh`, `manifold3d`, `rtree`,
`matplotlib` and `Pillow`. The measured snapshot used Python 3.13 and versions
listed in [the environment record](verification/environment.json).
CAD hardware generation additionally requires build123d; rendering uses Blender;
reference slicing uses the Bambu Studio macOS application.

`scripts/run_python.sh` uses `GYRE_PYTHON` if set, then `.venv/bin/python`, then an
existing local CAD-support environment, then `python3`. It does not install tools.
For a project-local environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install numpy scipy trimesh manifold3d rtree matplotlib Pillow
bash scripts/run_python.sh scripts/restore_working_models.py
```

Restoration creates ignored working STL files from the published 3MF models and
keeps existing files. Coordinates are preserved; ASCII serialization and therefore
file hashes may differ from the original STL. It also restores bottom STEP files.

## Upstream inputs and checks

Place a checkout of [Charybdis](https://github.com/Bastardkb/Charybdis/tree/47af70b9cd9b8d1d3a055ea88ab95c724bd3c02a)
at `../Charybdis`, using commit `47af70b9cd9b8d1d3a055ea88ab95c724bd3c02a`.
The scripts refer to this sibling path. The required Skeletyl mesh is included in
`references/`; its source and hash are documented in [attribution](ATTRIBUTION.md).

After restoring working models:

```sh
bash scripts/run_python.sh checks/verify_relative_layout.py
bash scripts/run_python.sh checks/verify_trackball_v11.py
bash scripts/run_python.sh checks/verify_ball34_v11.py
```

The broader local `scripts/check_all.py` suite also uses historical V7–V10
regression meshes in `references/regression/*.stl.gz`. They remain in the local
archive and are excluded from Git; that full historical suite is not available
from a fresh clone alone. Current measurement evidence is in `docs/verification/`.

## Modeling and export

- Right upper: run `src/fair_envelope_v9.py right`, then `src/mesh_v11.py`.
- Left upper: run `src/fair_envelope_v7.py left`, then `src/mesh_v7.py`.
- Hardware/bottom sources: `src/generate_hardware_v7.py` embeds the current
  parameters into `src/hardware_v7.py` and `src/bottoms_v7.py`; these are build123d
  programs. Inspect and validate the CAD objects before exporting changed parts.
- Dense `references/*-rounded-envelope.stl` files are regenerated locally.
- Publish unchanged working meshes with `scripts/export_public_models.py`.
  It verifies coordinate and triangle-index equality after a 3MF XML round trip.
- `scripts/slice_fdm_review.py --public-3mf` checks all six public models with
  the supplied reference profiles. G-code and application state stay temporary.

Run each Python command through `bash scripts/run_python.sh`. For CAD/Blender
backends that execute source text without `__file__`, set `GYRE_PROJECT_ROOT` to
the checkout's absolute directory or run with that directory as the working
directory. Rendering scripts have scene prerequisites; inspect the active scene
before running them. Renders do not validate manufacturing fit.

Some maintenance scripts, including `package_delivery.py`, need the local archive
and logs. They are retained for ongoing work, not needed to print this snapshot.

## Coordinates

All engineering dimensions are millimetres. Original right mesh `(x,y,z)` becomes
`(x, 70.01831113-z, y+8)`; left becomes `(x,-z,y+8)` and is then mirrored in X.
This is a rigid coordinate conversion, not a change to relative key positions.

Upper-case meshes use the assembly datum. Bottom meshes use their own bed datum:
translate them by **Z = −7.3 mm** to assemble. Bottom STEP files already use assembly
coordinates. `assembly.scad` reads the restored working STL files; the separation
between halves in its preview is arbitrary and does not specify typing posture.

## Git scope

`files/` and `pics/` are the public deliverables. `.gitignore` excludes working
exports, previews, local logs, historical archives, personal progress notes,
nested upstream checkouts and generated dense envelopes. Nothing in those local
directories is deleted by this repository preparation.
