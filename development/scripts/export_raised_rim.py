"""Publish checked candidate shells as exact-coordinate, geometry-only 3MF."""
from pathlib import Path
import hashlib
import json
import shutil

from export_public_models import export

DEV = Path(__file__).resolve().parents[1]
ROOT = DEV.parent
SOURCE = DEV / "exports/raised-rim"
TARGET = ROOT / "models/raised-rim"

if __name__ == "__main__":
    verification = json.loads((SOURCE / "verification.json").read_text())
    assert verification["passed"]
    records = []
    for side in ["left", "right"]:
        path = SOURCE / f"{side}-shell.stl"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == verification["sides"][side]["output_sha256"]
        records.append(export(f"raised-rim/GyreNano{side.title()}Shell", path))
        # Keep local viewing STLs synchronized with the exact packaged mesh.
        viewing_stl = TARGET / f"GyreNano{side.title()}Shell.stl"
        shutil.copy2(path, viewing_stl)
        assert hashlib.sha256(viewing_stl.read_bytes()).hexdigest() == verification["sides"][side]["output_sha256"]
    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / "manifest.json").write_text(json.dumps({
        "status": "Candidate upper shells; physical fit pending",
        "units": "millimeter", "geometry_only": True, "sliced": False,
        "coordinates": "Original assembly datums, no translation/rotation/scaling",
        "models": records,
    }, indent=2) + "\n")
    for name in ["verification.json", "build.json"]:
        shutil.copy2(SOURCE / name, TARGET / name)
    for source_name, name in [("candidate.png", "preview.png"), ("baseline.png", "before.png"), ("top.png", "top.png"), ("left-transition-detail.png", "left-transition-detail.png"), ("right-transition-detail.png", "right-transition-detail.png"), ("right-outer-seam.png", "right-outer-seam.png"), ("right-ball-collar.png", "right-ball-collar.png")]:
        shutil.copy2(DEV / "previews/raised-rim" / source_name, TARGET / name)
    sections = SOURCE / "transition-sections.json"
    if sections.exists():
        evidence = json.loads(sections.read_text())
        assert all(section["after_sha256"] == verification["sides"][section["side"]]["output_sha256"]
                   for section in evidence["sections"]), "Regenerate section evidence for the current meshes"
        shutil.copy2(sections, TARGET / sections.name)
        shutil.copy2(DEV / "previews/raised-rim/transition-sections.png", TARGET / "transition-sections.png")

    seam = SOURCE / "outer-seam.json"
    evidence = json.loads(seam.read_text())
    assert all(evidence["sides"][side]["after_sha256"] == verification["sides"][side]["output_sha256"] for side in ["left", "right"])
    shutil.copy2(seam, TARGET / seam.name)
    shutil.copy2(DEV / "previews/raised-rim/outer-seam.png", TARGET / "outer-seam.png")

    collar = SOURCE / "ball-collar.json"
    evidence = json.loads(collar.read_text())
    assert evidence["passed"] and evidence["after_sha256"] == verification["sides"]["right"]["output_sha256"]
    shutil.copy2(collar, TARGET / collar.name)
