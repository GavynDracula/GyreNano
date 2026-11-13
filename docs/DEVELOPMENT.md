# Development and reproduction

The repository has four public entry directories:

| Directory | Purpose |
| --- | --- |
| `files/` | Printable geometry and supporting checks |
| `pcb/` | Current editable PCB projects and sample packages |
| `docs/` | Documentation, images and release evidence |
| `development/` | Enclosure sources, parameters, reference geometry and tools |

## Current delivery verification

From the repository root, using standard Python only:

```sh
python3 development/scripts/verify_delivery.py
```

This checks delivery hashes and ZIP/3MF integrity, not physical fit or manufacturing approval.

## Enclosure development environment

Use Python with `numpy`, `scipy`, `trimesh`, `manifold3d`, `rtree`, `matplotlib` and `Pillow`. Baseline versions are in [verification/environment.json](verification/environment.json). Exact CAD work additionally needs build123d; rendering needs Blender. Use the relevant CAD backend for model changes.

`development/scripts/run_python.sh` selects `GYRE_PYTHON`, then `development/.venv/bin/python`, then the existing local CAD-support environment, then `python3`. It installs nothing. The wrapper changes its working directory to `development/` and sets `GYRE_PROJECT_ROOT` there. Script arguments are relative to `development/`:

```sh
python3 -m venv development/.venv
development/.venv/bin/python -m pip install numpy scipy trimesh manifold3d rtree matplotlib Pillow
bash development/scripts/run_python.sh scripts/restore_working_models.py
bash development/scripts/run_python.sh checks/verify_relative_layout.py
```

Restoration reads six published baseline 3MF files from `files/`, creates ignored working STLs in `development/exports/`, preserves existing files and restores bottom STEP files. Coordinates remain unchanged, but ASCII STL serialization may differ from historical hashes.

Place the [Charybdis checkout](https://github.com/Bastardkb/Charybdis/tree/47af70b9cd9b8d1d3a055ea88ab95c724bd3c02a) at `../Charybdis` relative to this repository, pinned to commit `47af70b9cd9b8d1d3a055ea88ab95c724bd3c02a`. Skeletyl geometry is under `development/references/`; see [attribution](ATTRIBUTION.md).

Further checks use the same wrapper:

```sh
bash development/scripts/run_python.sh checks/verify_trackball_v11.py
bash development/scripts/run_python.sh checks/verify_ball34_v11.py
```

`development/scripts/check_all.py` also needs V7–V10 meshes in `development/references/regression/*.stl.gz`. Those large fixtures remain local and in the snapshot, not in a normal clone. Delivery-hash verification does not rerun the whole historical suite.

## Enclosure modeling

The following paths are relative to `development/`:

- Right upper baseline: `src/fair_envelope_v9.py right`, then `src/mesh_v11.py`.
- Left upper baseline: `src/fair_envelope_v7.py left`, then `src/mesh_v7.py`.
- Hardware/bottoms: `src/generate_hardware_v7.py` prepares the `src/hardware_v7.py` and `src/bottoms_v7.py` build123d programs.
- `scripts/export_public_models.py` publishes baseline 3MF files to the repository's `files/` directory and verifies coordinate/triangle equality. It overwrites those files; use only after a reviewed model change.
- For backends executing source without `__file__`, set `GYRE_PROJECT_ROOT` to the absolute **development directory**, or use that as their working directory. Inspect the model before export.

Working exports, reports, previews and regenerated dense envelopes stay under `development/` and are ignored. Renders do not validate manufacturing fit. The archive-dependent `package_delivery.py` was removed from active tools and is retained only in the historical snapshot.

The historical slicing script remains available but was **not run for this release**. Users slice the supplied geometry themselves; no printer profile or G-code is part of the current delivery.

## Coordinates

All engineering dimensions are millimetres. Original right mesh `(x,y,z)` becomes `(x, 70.01831113-z, y+8)`; left becomes `(x,-z,y+8)` and is then mirrored in X. This rigid conversion does not change relative key positions.

Upper meshes use the assembly datum. Baseline bottom meshes use a bed datum: translate **Z = −7.3 mm** for assembly. Bottom STEP files already use assembly coordinates. `development/assembly.scad` reads restored meshes; its separation between hands is arbitrary.

## PCB sources and historical engineering snapshot

Current KiCad/EDA sources are under `pcb/keyfield-fr4`, `pcb/keyfield-fpc`, `pcb/holders` and `pcb/sensor`, with local/embedded libraries. Holder/sensor EDA projects contain corrected mask openings; their KiCad projects are older reference artwork.

Cross-version PCB scripts and locked inputs are in the optional [engineering snapshot](https://github.com/GavynDracula/GyreNano/releases/download/v0.2.0-prototype.1/GyreNano-EngineeringSnapshot-20261113.tar.gz). Its checksum is in [cleanup.json](releases/cleanup.json). Local copy: `.local/GyreNano-EngineeringSnapshot-20261113.tar.gz`, excluded from Git.

Extract into an **empty separate workspace**, never over this checkout. It preserves the pre-cleanup layout, with `SNAPSHOT-SHA256.json`, scripts, native projects, reports, references and working exports. It intentionally predates the top-level reorganization. Some generated scripts embed the old absolute path: regenerate their preparation stage or adjust that path in the restored copy. Python/CAD environments and the sibling Charybdis checkout remain external. This is provenance, not a one-command portable rebuild claim.

The old large backup ZIP, extracted duplicates, loose chronological PCB directories and runtime debris were removed. The local progress journal is `.local/PROGRESS.md`. [Release notes](releases/v0.2.0-prototype.1.md) and migration manifests describe both cleanup steps.
