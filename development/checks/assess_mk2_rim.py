"""Read-only MK2 perimeter study. Run with development/scripts/run_python.sh.

Measurements are in each switch's local normal, not global Z. No output STL
is produced and no input model is modified. Section plots are measurements,
not a preview or a keycap fit certificate.
"""
from pathlib import Path
import hashlib
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh

DEV = Path(__file__).resolve().parents[1]
ROOT = DEV.parent
sys.path.insert(0, str(DEV / "src"))
from mesh_union import manifold


def boundary_groups(edges):
    adjacency = {}
    for a, b in edges:
        adjacency.setdefault(int(a), set()).add(int(b))
        adjacency.setdefault(int(b), set()).add(int(a))
    while adjacency:
        pending = [next(iter(adjacency))]
        seen = set()
        while pending:
            node = pending.pop()
            if node not in seen:
                seen.add(node)
                pending.extend(adjacency.pop(node, set()) - seen)
        yield list(seen)


def mk2_key_planes(mesh):
    """Find four-corner 13.9 mm aperture loops on upward planar lands."""
    result = []
    for index in np.where((mesh.facets_area > 40) &
                          (mesh.facets_normal[:, 2] > .3))[0]:
        for indices in boundary_groups(mesh.facets_boundary[index]):
            if len(indices) != 4:
                continue
            points = mesh.vertices[indices]
            distances = np.linalg.norm(points[:, None] - points[None, :], axis=2)
            lengths = np.sort(distances, axis=1)
            if not np.allclose(lengths[:, 1:3], 13.9, atol=.04):
                continue
            x = points[np.argsort(distances[0])[1]] - points[0]
            result.append(dict(center=points.mean(0).tolist(),
                               normal=mesh.facets_normal[index].tolist(),
                               x=(x / np.linalg.norm(x)).tolist()))
    return result


def outward_direction(plane, desired):
    n, x = np.array(plane["normal"]), np.array(plane["x"])
    y = np.cross(n, x)
    choices = np.array([x, -x, y, -y])
    return choices[np.argmax(choices @ np.array(desired))]


def profile(solid, plane, desired):
    c, n = np.array(plane["center"]), np.array(plane["normal"])
    direction = outward_direction(plane, desired)
    offsets = np.round(np.arange(7.0, 20.001, .05), 4)
    heights = []
    for offset in offsets:
        q = c + direction * offset
        hits = solid.ray_cast(q + n * 20, q - n * 10)
        heights.append(float((np.array(hits[0].position) - q) @ n)
                       if hits else None)
    samples = {}
    for offset in [8, 9, 10, 11, 12, 13, 14, 15, 16, 18]:
        samples[str(offset)] = heights[np.argmin(abs(offsets - offset))]
    return dict(center_mm=c.tolist(), normal=n.tolist(),
                outward_direction=direction.tolist(), offset_mm=offsets.tolist(),
                height_normal_mm=heights, samples_mm=samples)


def main():
    inputs = {
        "mk2": ROOT.parent / "Charybdis/files/4x6/MK2/charybdis_v4_247_right.stl",
        "left": ROOT / "models/integrated-fr4/left-shell.stl",
        "right": ROOT / "models/integrated-fr4/right-shell.stl",
    }
    hashes = {key: hashlib.sha256(path.read_bytes()).hexdigest()
              for key, path in inputs.items()}
    meshes = {key: trimesh.load(path) for key, path in inputs.items()}
    assert all(m.is_watertight and m.is_winding_consistent for m in meshes.values())
    solids = {key: manifold(mesh) for key, mesh in meshes.items()}
    planes = mk2_key_planes(meshes["mk2"])
    assert len(planes) == 27, "Upstream reference changed; inspect before proceeding"
    local = {side: json.loads((DEV / "references" / f"{side}-switch-planes.json").read_text())
             for side in ["left", "right"]}
    # Physical feature selection by aperture centre, not STL triangle ordering.
    selections = [
        ("MK2 outer high corner", [88.16, 165.70, 38.09], [-1, 0, 0], "right", 9, [-1, 0, 0]),
        ("MK2 opposite high corner", [187.42, 153.66, 22.67], [1, 0, 0], "right", 13, [1, 0, 0]),
        ("MK2 outer low corner", [84.77, 102.66, 30.88], [-1, 0, 0], "left", 14, [1, 0, 0]),
        ("MK2 opposite low corner", [187.42, 90.69, 14.18], [1, 0, 0], "left", 1, [-1, 0, 0]),
    ]
    report = dict(units="mm", input_sha256=hashes,
                  method="First surface hit along switch normal, +20 to -10 mm, every 0.05 mm along an outward local key edge axis. Representative cuts, not whole-perimeter extrema.",
                  comparison="Different layouts, compared in local switch coordinates; not a spatial registration or identical key assignment.",
                  mk2_detected_square_apertures=len(planes), sections=[],
                  input_geometry_modified=False, new_model_generated=False,
                  proposed_nominal_rim_height_mm=4.5,
                  proposal_validated_for_keycap_motion=False)
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.5), sharex=True, sharey=True)
    for axis, selection in zip(axes.ravel(), selections):
        label, target, desired, side, key_index, current_desired = selection
        p = min(planes, key=lambda p: np.linalg.norm(np.array(p["center"]) - target))
        assert np.linalg.norm(np.array(p["center"]) - target) < .1
        reference = profile(solids["mk2"], p, desired)
        current = profile(solids[side], local[side][key_index], current_desired)
        report["sections"].append(dict(reference_label=label, current_side=side,
                                       current_key_index=key_index, mk2=reference, current=current))
        axis.plot(reference["offset_mm"], reference["height_normal_mm"], color="#c56a27", label="MK2 reference", lw=2)
        axis.plot(current["offset_mm"], current["height_normal_mm"], color="#247c91", label=f"GyreNano {side}, key {key_index}", lw=2)
        axis.axhline(0, color="gray", lw=.6)
        axis.axhline(4.5, color="gray", ls="--", lw=.8, label="Proposed nominal 4.5 mm (not geometry)")
        axis.set_title(label)
        axis.set_xlim(7, 20)
        axis.set_ylim(-4, 8)
        axis.grid(alpha=.2)
        axis.legend(fontsize=7, loc="lower left")
        axis.set_xlabel("Outward distance from switch centre [mm]")
        axis.set_ylabel("Rise along switch normal [mm]")
    fig.suptitle("Perimeter cross-sections: original switch lands remain the zero datum", fontsize=13)
    fig.text(.5, .005, "Representative edges on different layouts. No keycap envelope or new shell is shown.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .025, 1, .95))
    output = ROOT / "docs/images/mk2-rim-sections.png"
    fig.savefig(output, dpi=150)
    plt.close(fig)
    for key, path in inputs.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == hashes[key]
    report_path = ROOT / "docs/verification/mk2-rim-study.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(report_path), "plot": str(output), "modified_models": False,
                      "at_12mm": [{"reference": row["reference_label"],
                                    "MK2": row["mk2"]["samples_mm"]["12"],
                                    "GyreNano": row["current"]["samples_mm"]["12"]}
                                   for row in report["sections"]]}, indent=2))


if __name__ == "__main__":
    main()
