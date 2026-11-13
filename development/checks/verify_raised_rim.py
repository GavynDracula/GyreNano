"""Verify exported raised-rim STLs against V14 and original mounting datums."""
from pathlib import Path
import sys
import json
import hashlib
import numpy as np
import trimesh
import manifold3d as mf

DEV = Path(__file__).resolve().parents[1]
ROOT = DEV.parent
sys.path.insert(0, str(DEV / "src"))
from mesh_union import manifold
from raised_rim import local_box, THUMBS, distinct_hits

OUT = DEV / "exports/raised-rim"
VOLUME_TOL = .001


def pose(mesh, solid, p):
    c, n, x = (np.array(p[k]) for k in ["center", "normal", "x"])
    y = np.cross(n, x)
    frame = np.column_stack((x, y, n))
    samples = []
    for edge in [-8.2, -7.5, 7.5, 8.2]:
        for along in [-6, -3, 0, 3, 6]:
            for u, v in [(edge, along), (along, edge)]:
                q = c + x * u + y * v
                hits = [h for h in solid.ray_cast(q + n * .2, q - n * .2)
                        if np.array(h.normal) @ n > .99]
                if hits:
                    samples.append((np.array(hits[0].position) - c) @ frame)
    assert len(samples) >= 36
    samples = np.array(samples)
    slope = np.linalg.lstsq(np.c_[samples[:, :2], np.ones(len(samples))], samples[:, 2], rcond=None)[0]
    measured_n = n - x * slope[0] - y * slope[1]
    measured_n /= np.linalg.norm(measured_n)
    vertices = (mesh.vertices - c) @ frame
    vertices = vertices[(abs(vertices[:, 2]) < .02) & (np.max(abs(vertices[:, :2]), axis=1) < 7.01)]
    assert len(vertices) >= 4
    lo, hi = vertices[:, :2].min(0), vertices[:, :2].max(0)
    mid = (lo + hi) / 2
    return c + frame @ np.r_[mid, slope[2]], measured_n, hi - lo


def original(side):
    path = ROOT.parent / "Charybdis/files/3x5 nano/charybdisnano_v2_v187.stl" if side == "right" else DEV / "references/skeletyl-v4-103.stl"
    mesh = trimesh.load(path)
    v = mesh.vertices.copy()
    mesh.vertices = np.c_[v[:, 0], (70.01831113 if side == "right" else 0) - v[:, 2], v[:, 1] + 8]
    if side == "left":
        mesh.apply_transform(np.diag([-1, 1, 1, 1]))
    return mesh


def sphere_clearance(solid, c, n):
    clipped = solid.trim_by_plane(n, float((c - n * 21) @ n))
    data = clipped.to_mesh64()
    u = np.array([n[2], 0, -n[0]])
    v = np.cross(n, u)
    uv = (data.vert_properties[:, :3] - c) @ np.column_stack((u, v))
    triangles = uv[data.tri_verts]
    a, b, d = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    cross = lambda p, q: p[:, 0] * q[:, 1] - p[:, 1] * q[:, 0]
    area = cross(b - a, d - a)
    s0, s1, s2 = cross(b - a, -a), cross(d - b, -b), cross(a - d, -d)
    inside = (((s0 >= 0) & (s1 >= 0) & (s2 >= 0)) | ((s0 <= 0) & (s1 <= 0) & (s2 <= 0))) & (abs(area) > 1e-12)
    assert not inside.any()
    best = np.inf
    for j in range(3):
        p, q = triangles[:, j], triangles[:, (j + 1) % 3]
        delta = q - p
        t = np.clip(-np.sum(p * delta, axis=1) / np.maximum(np.sum(delta ** 2, axis=1), 1e-30), 0, 1)
        best = min(best, float(np.linalg.norm(p + t[:, None] * delta, axis=1).min()))
    return best


def check_side(side):
    source_path = ROOT / f"models/integrated-fr4/{side}-shell.stl"
    output_path = OUT / f"{side}-shell.stl"
    base_mesh, new_mesh, orig_mesh = trimesh.load(source_path), trimesh.load(output_path), original(side)
    assert new_mesh.is_watertight and new_mesh.is_winding_consistent
    base, new, orig = map(manifold, [base_mesh, new_mesh, orig_mesh])
    added, removed = new - base, base - new
    assert removed.volume() >= -VOLUME_TOL
    assert len(new.decompose()) == 1 and all(s.volume() > 0 for s in new.decompose())
    planes = json.loads((DEV / f"references/{side}-switch-planes.json").read_text())
    results = []
    centers = [[], []]
    for i, p in enumerate(planes):
        c0, n0, size0 = pose(orig_mesh, orig, p)
        c1, n1, size1 = pose(new_mesh, new, p)
        centers[0].append(c0)
        centers[1].append(c1)
        functional = local_box(p, [17, 17, 4.5], -4.3)
        row = dict(key=i, center_shift_from_original_mm=float(np.linalg.norm(c1 - c0)),
                   axis_angle_from_original_deg=float(np.degrees(np.arccos(np.clip(n0 @ n1, -1, 1)))),
                   aperture_size_change_mm=float(abs(size1 - size0).max()),
                   new_material_in_mount_mm3=(added ^ functional).volume(),
                   removed_mount_material_mm3=(removed ^ functional).volume(),
                   new_material_in_socket_proxy_mm3=(added ^ local_box(p, [19.6, 19.6, 7], -11)).volume(),
                   new_material_in_cap_proxy_mm3=(added ^ local_box(p, [19.2, 19.2, 19.8], .2)).volume())
        assert row["center_shift_from_original_mm"] < .001 and row["aperture_size_change_mm"] < .001
        assert row["axis_angle_from_original_deg"] < .001
        assert all(abs(value) < VOLUME_TOL for key, value in row.items() if key.endswith("mm3"))
        results.append(row)
    before, after = map(np.array, centers)
    relative_delta = (after[:, None] - after[None, :]) - (before[:, None] - before[None, :])
    thumbs = THUMBS[side]
    main = [i for i in range(len(planes)) if i not in thumbs]
    thumb_delta = (after[thumbs].mean(0) - after[main].mean(0)) - (before[thumbs].mean(0) - before[main].mean(0))
    overlaps = {}
    for filename in [f"{side}_retainer.stl", f"{side}_thumb_retainer.stl"]:
        part = manifold(trimesh.load(ROOT / "models/integrated-fr4" / filename))
        overlaps[filename] = (added ^ part).volume()
    transforms = json.loads((ROOT / "models/fpc-supports/checks/print-transforms.json").read_text())
    for kind in ["main", "thumb"]:
        name = f"{side}_{kind}_support"
        part = trimesh.load(ROOT / f"models/fpc-supports/{name}_print.stl")
        record = transforms[name]
        # print = R @ assembly + t; undo the stored rigid placement.
        rotation, translation = np.array(record["rotation"]), np.array(record["translation"])
        part.vertices = (part.vertices - translation) @ rotation
        overlaps[name] = (added ^ manifold(part)).volume()
    holder = manifold(trimesh.load(DEV / f"references/{side}-holder-pcb-v6.stl"))
    overlaps["original_holder_board_reference"] = (added ^ holder).volume()
    assert all(abs(v) < VOLUME_TOL for v in overlaps.values()), overlaps
    # Independently probe changed outer roof columns in both exported meshes.
    # Internal exits must remain fixed; normal-direction material thickness is
    # checked separately from vertical thickness, including lowered regions.
    roof = dict(np.load(OUT / f"{side}-fair-roof.npz"))
    selected = np.where((roof["amplitude"] > .01) & (abs(roof["top"]-roof["original"]) > .05))[0][::60]
    thicknesses = []
    thickness_positions = []
    inner_deltas = []
    for index in selected:
        x, y = roof["xy"][index]
        old_hits = distinct_hits(base.ray_cast([x, y, 100], [x, y, -1]))
        new_hits = distinct_hits(new.ray_cast([x, y, 100], [x, y, -1]))
        if len(old_hits) < 2 or len(new_hits) < 2:
            continue  # construction field extends outside the trimmed outline
        inner_deltas.append(abs(old_hits[1].position[2] - new_hits[1].position[2]))
        normal = -np.array(new_hits[1].normal)
        origin = np.array(new_hits[1].position)
        old_origin = np.array(old_hits[1].position)
        old_normal = -np.array(old_hits[1].normal)
        old_ray = base.ray_cast(old_origin + old_normal * .001, old_origin + old_normal * 100)
        new_ray = new.ray_cast(origin + normal * .001, origin + normal * 100)
        assert old_ray and new_ray
        old_thickness = np.linalg.norm(np.array(old_ray[0].position) - old_origin)
        new_thickness = np.linalg.norm(np.array(new_ray[0].position) - origin)
        thicknesses.append([float(old_thickness), float(new_thickness)])
        thickness_positions.append([x, y])
    thicknesses = np.array(thicknesses)
    assert len(thicknesses) > 500
    if side == "left":
        assert max(inner_deltas) < .001, max(inner_deltas)
    required = np.minimum(thicknesses[:, 0], 1.6)
    np.savez_compressed(OUT / f"{side}-wall-probes.npz", xy=thickness_positions, thickness=thicknesses)
    assert np.min(thicknesses[:, 1] - required) > -.001, (thicknesses[np.argmin(thicknesses[:, 1]-required)], thickness_positions[np.argmin(thicknesses[:, 1]-required)])
    print(side, "roof thickness samples", len(thicknesses), "min", thicknesses[:, 1].min(), flush=True)
    row = dict(input_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
               output_sha256=hashlib.sha256(output_path.read_bytes()).hexdigest(),
               watertight=True, winding_consistent=True, components=1,
               removed_volume_mm3=removed.volume(), added_volume_mm3=added.volume(),
               roof_checks=dict(samples=len(thicknesses), max_internal_exit_change_mm=max(inner_deltas),
                                minimum_sampled_normal_thickness_mm=float(thicknesses[:,1].min()),
                                requirement="At least1.6mm along current inner-surface normal, or baseline minimum where already thinner; sampled check, not global certification"),
               max_pairwise_key_vector_change_mm=float(np.linalg.norm(relative_delta, axis=2).max()),
               thumb_to_main_vector_change_mm=float(np.linalg.norm(thumb_delta)),
               max_center_shift_mm=max(p["center_shift_from_original_mm"] for p in results),
               max_axis_change_deg=max(p["axis_angle_from_original_deg"] for p in results),
               max_aperture_change_mm=max(p["aperture_size_change_mm"] for p in results),
               keys=results, added_assembly_overlap_mm3=overlaps,
               exterior_xy_bounds_change_mm=float(abs(new_mesh.bounds[:, :2] - base_mesh.bounds[:, :2]).max()))
    assert row["exterior_xy_bounds_change_mm"] < .001
    if side == "right":
        ball = json.loads((DEV / "references/ball-surface.json").read_text())
        c, n = np.array(ball["center"]), np.array(ball["normal"])
        u = np.array([n[2], 0, -n[0]])
        v = np.cross(n, u)
        shifts = []
        inherited_wall_residuals = []
        seat_shifts = []
        seat_changes = []
        ring_points = [[], []]
        seat_points = [[], []]
        for depth in [-.5, -1, -2, -3]:
            for angle in np.linspace(0, 2 * np.pi, 144, endpoint=False):
                d = u * np.cos(angle) + v * np.sin(angle)
                hits = [s.ray_cast(c + n * depth + d * 20, c + n * depth + d * 25) for s in [orig, base, new]]
                assert all(hits)
                shifts.append(float(np.linalg.norm(np.array(hits[1][0].position) - hits[2][0].position)))
                inherited_wall_residuals.append(float(np.linalg.norm(np.array(hits[0][0].position) - hits[1][0].position)))
                if depth == -3:
                    for i, j in enumerate([0, 2]):
                        ring_points[i].append((np.array(hits[j][0].position) - c) @ np.column_stack((u, v, n)))
        for radius in [23.05, 23.10, 23.14]:
            for angle in np.linspace(0, 2 * np.pi, 144, endpoint=False):
                q = c + radius * (u * np.cos(angle) + v * np.sin(angle))
                old = orig.ray_cast(q + n * .08, q - n * .08)
                if not old or np.array(old[0].normal) @ n < .999:
                    continue
                current = new.ray_cast(q + n * .08, q - n * .08)
                baseline = base.ray_cast(q + n * .08, q - n * .08)
                assert current and np.array(current[0].normal) @ n > .999
                seat_shifts.append(float(np.linalg.norm(np.array(old[0].position) - current[0].position)))
                seat_changes.append(float(np.linalg.norm(np.array(baseline[0].position) - current[0].position)))
                for i, hit in enumerate([old[0], current[0]]):
                    seat_points[i].append((np.array(hit.position) - c) @ np.column_stack((u, v, n)))
        # Mesh cleanup tolerance is1e-5mm; datums remain fixed by construction.
        assert max(shifts) < 1e-4 and max(seat_changes) < 1e-4
        print("ball wall/seat export residual", max(shifts), max(seat_changes), flush=True)
        assert len(seat_shifts) > 100 and max(seat_shifts) < .001
        frames = []
        for ring, seat in zip(ring_points, seat_points):
            xy = np.array(ring)[:, :2]
            fit = np.linalg.lstsq(np.c_[2 * xy, np.ones(len(xy))], (xy * xy).sum(1), rcond=None)[0]
            pts = np.array(seat)
            plane_fit = np.linalg.lstsq(np.c_[pts[:, :2], np.ones(len(pts))], pts[:, 2], rcond=None)[0]
            center = c + np.column_stack((u, v, n)) @ np.r_[fit[:2], plane_fit @ np.r_[fit[:2], 1]]
            normal = n - u * plane_fit[0] - v * plane_fit[1]
            normal /= np.linalg.norm(normal)
            frames.append((center, normal))
        ball_center_delta = float(np.linalg.norm(frames[1][0] - frames[0][0]))
        ball_normal_delta = float(np.degrees(np.arccos(np.clip(frames[1][1] @ frames[0][1], -1, 1))))
        ball_to_key_delta = float(np.linalg.norm((after - frames[1][0]) - (before - frames[0][0]), axis=1).max())
        assert ball_center_delta < .001 and ball_normal_delta < .001 and ball_to_key_delta < .001
        parts = {}
        for name in ["top", "btu", "cover"]:
            part = manifold(trimesh.load(DEV / f"references/trackball-{name}-assembly-v7.stl"))
            parts[name] = (added ^ part).volume()
        capsule = manifold(trimesh.load(DEV / "references/ball35p2-sweep-v10.stl"))
        capsule_overlap = (new ^ capsule).volume()
        minimum_radius = sphere_clearance(new, c, n)
        assert all(abs(v) < VOLUME_TOL for v in parts.values())
        assert abs(capsule_overlap) < VOLUME_TOL and minimum_radius >= 17.6
        row["trackball"] = dict(wall_sample_count=len(shifts), max_wall_shift_vs_V14_mm=max(shifts),
                                inherited_V14_wall_ray_residual_vs_original_mm=max(inherited_wall_residuals),
                                inherited_residual_note="Largest ray residual occurs at depth -2 mm on the already-published V14 mesh. The new rim/collar preserves these hits within the bounded mesh-cleanup tolerance; actual differences are reported separately. Fitted datum below is measured separately.",
                                seat_sample_count=len(seat_shifts), max_seat_shift_vs_original_mm=max(seat_shifts),
                                max_seat_shift_vs_V14_mm=max(seat_changes),
                                fitted_seat_center_shift_vs_original_mm=ball_center_delta,
                                fitted_seat_normal_change_vs_original_deg=ball_normal_delta,
                                max_ball_seat_to_key_vector_change_vs_original_mm=ball_to_key_delta,
                                added_component_overlap_mm3=parts, capsule_35p2_overlap_mm3=capsule_overlap,
                                minimum_axis_distance_mm=minimum_radius, radial_margin_for_34mm_ball_mm=minimum_radius - 17,
                                installed_sphere_center_measured=False)
    print(side, "passed; added", row["added_volume_mm3"], "mm3", flush=True)
    return row


if __name__ == "__main__":
    report = dict(scope="Exported STL versus immutable V14 and original Nano/Skeletyl key and ball datums. Functional mounting conservation, refaired roof, sampled internal-surface/thickness and added-material interference checks.",
                  cap_proxy="19.2 x 19.2 mm square, local normal z=+0.2..+20 mm; no claim of universal keycap or puller/finger fit.",
                  physical_trial_complete=False, sliced=False, volume_tolerance_mm3=VOLUME_TOL,
                  sides={side: check_side(side) for side in ["left", "right"]}, passed=True)
    (OUT / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PASS: all 35 keys, ball datum, sphere channel and support interference checks")
