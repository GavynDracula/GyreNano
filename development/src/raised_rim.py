"""Raise the complete shoulder of immutable V14 shells using the mesh fallback.

All coordinates are assembly millimetres. Nonfunctional shoulder roofs are refaired;
switch lands, ball mount, hardware and bottom interface are protected. Outputs
are candidates, never automatic replacements of the public V14 baseline.
"""
from pathlib import Path
import json
import hashlib
import sys

import numpy as np
import trimesh
import manifold3d as mf
from scipy.interpolate import RectBivariateSpline, RBFInterpolator
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d
from matplotlib.path import Path as PolygonPath

from mesh_union import manifold

DEV = Path(__file__).resolve().parents[1]
ROOT = DEV.parent
OUT = DEV / "exports/raised-rim"
PARAMS = {
    "main_rise_normal_mm": 4.5,
    "thumb_rise_normal_mm": 1.8,
    "keycap_guard_width_mm": 19.2,
    "keycap_guard_normal_range_mm": [0.2, 20.0],
    "inner_round_transition_mm": 2.8,
    "outer_top_radius_mm": 1.5,
    "attachment_overlap_mm": 0.65,
    "triangle_edge_target_mm": 0.22,
    "ball_fade_mm": 5.0,
    "ball_preserve_offset_mm": 12.5,
    "outer_outline_inset_mm": 0.0,
    "fair_surface_smoothing": 12.0,
    "fair_surface_gradient_sample_mm": 4.0,
    "minimum_roof_normal_thickness_mm": 2.0,
    "outline_cleanup_tolerance_mm": 0.001,
    "coplanar_cleanup_tolerance_mm": 0.00001,
    "seam_band_width_mm": 1.5,
    "seam_clean_band_mm": 0.55,
    "seam_arc_sample_mm": 0.15,
    "seam_arc_smoothing_mm": 0.65,
    "seam_mesh_edge_mm": 0.18,
    "ball_collar_target_radius_mm": 27.5,
    "ball_collar_fixed_radius_mm": 23.5,
    "ball_collar_refine_mm": 0.65,
}
THUMBS = {"left": [0, 16, 17], "right": [5, 7]}


def smoothstep(t):
    t = np.clip(t, 0, 1)
    return t * t * t * (10 + t * (-15 + 6 * t))


def smooth_positive(value, width):
    """C2 rounded max(value, 0), exact outside [-width, width].

    Integral of the quintic smoothstep. Its derivative is continuous, is
    bounded by [0, 1], and its second derivative vanishes at either join.
    Unlike a hard clamp this introduces no crease where lift starts/stops.
    """
    t = np.clip((value + width) / (2 * width), 0, 1)
    rounded = 2 * width * (t ** 6 - 3 * t ** 5 + 2.5 * t ** 4)
    return np.where(value >= width, value, rounded)


def edge_distance(points, polygon):
    distance = np.full(len(points), np.inf)
    for a, b in zip(polygon, np.roll(polygon, -1, axis=0)):
        d = b - a
        t = np.clip((points - a) @ d / max(d @ d, 1e-20), 0, 1)
        distance = np.minimum(distance, np.linalg.norm(points - a - t[:, None] * d, axis=1))
    return distance


def exterior_distance(points, polygon):
    distance = edge_distance(points, polygon)
    distance[PolygonPath(polygon).contains_points(points)] = 0
    return distance


def key_hull(planes, height):
    points = []
    for p in planes:
        c, n, x = (np.array(p[k]) for k in ["center", "normal", "x"])
        y = np.cross(n, x)
        for u in [-9.6, 9.6]:
            for v in [-9.6, 9.6]:
                for h in [0, height]:
                    points.append((c + x * u + y * v + n * h)[:2])
    return mf.CrossSection.hull_points(np.array(points)).offset(.35, circular_segments=96)


def distinct_hits(hits):
    """An edge/vertex hit can occur once per adjacent triangle."""
    unique = []
    for hit in hits:
        if not unique or np.linalg.norm(np.array(hit.position) - unique[-1].position) > 1e-6:
            unique.append(hit)
    return unique


def local_box(plane, size, lower):
    c, n, x = (np.array(plane[k]) for k in ["center", "normal", "x"])
    return mf.Manifold.cube(size, center=True).transform(
        np.column_stack((x, np.cross(n, x), n, c + n * (lower + size[2] / 2))))


def make_shoulder(side, base, planes, outer, main_hull, thumb_hull, field):
    """Lift the complete shoulder to the sidewall; there is no outer fall-off.

    A single height field spans the exterior of both key wells. The only
    height step is at the key-well boundary. A circular top-edge profile joins
    the elevated shoulder to the existing vertical outside wall.
    """
    main_poly = np.array(main_hull.to_polygons()[0])
    thumb_poly = np.array(thumb_hull.to_polygons()[0])
    outer_poly = np.array(outer.to_polygons()[0])
    # Extend roof operations beyond the silhouette, then trim once at the
    # end. Coincident Boolean sidewalls otherwise create microscopic fins.
    region = outer.offset(.5, circular_segments=128) - (main_hull + thumb_hull)
    ball_poly = None
    if side == "right":
        ball = json.loads((DEV / "references/ball-surface.json").read_text())
        exclusion = mf.CrossSection([np.array(ball["outline"])[:, :2]]).offset(PARAMS["ball_preserve_offset_mm"], circular_segments=128)
        ball_poly = np.array(exclusion.to_polygons()[0])
        region -= exclusion
    flat = region.extrude(1).refine_to_length(PARAMS["triangle_edge_target_mm"])
    stats = {}
    centers = np.array([p["center"] for p in planes])
    normals = np.array([p["normal"] for p in planes])
    rise = np.array([PARAMS["thumb_rise_normal_mm"] if i in THUMBS[side] else PARAMS["main_rise_normal_mm"] for i in range(len(planes))])
    # One global thin-plate fit includes height and local slope samples.
    # No per-region height ceilings or positive-only lift masks: those
    # retained old humps and created multiple visible transition contours.
    step = PARAMS["fair_surface_gradient_sample_mm"]
    delta_samples = np.array([[0, 0], [step, 0], [-step, 0], [0, step], [0, -step]])
    fit_xy = (centers[:, None, :2] + delta_samples).reshape(-1, 2)
    fit_z = (centers[:, None, 2] + rise[:, None] / normals[:, None, 2]
             - np.sum(delta_samples[None, :, :] * normals[:, None, :2], axis=2) / normals[:, None, 2]).ravel()
    if side == "right":
        # Continue the same outer shoulder as the left half across the absent
        # high thumb key. This is only a surface guide, never an added key.
        virtual = json.loads((DEV / "references/left-switch-planes.json").read_text())[16]
        vc, vn = np.array(virtual["center"]), np.array(virtual["normal"])
        vc[0] *= -1
        vn[0] *= -1
        fit_xy = np.vstack((fit_xy, vc[:2] + delta_samples))
        fit_z = np.r_[fit_z, vc[2] + PARAMS["thumb_rise_normal_mm"] / vn[2]
                      - (delta_samples * vn[:2]).sum(1) / vn[2]]
    fair_surface = RBFInterpolator(fit_xy, fit_z, kernel="thin_plate_spline",
                                   smoothing=PARAMS["fair_surface_smoothing"])
    cache = {}

    def warp(vertices):
        xy, inverse = np.unique(vertices[:, :2], axis=0, return_inverse=True)
        original_roof = field.ev(xy[:, 1], xy[:, 0])
        d_outer = edge_distance(xy, outer_poly)
        d_outer[~PolygonPath(outer_poly).contains_points(xy)] = 0
        base_height = []
        roof_minimum = []
        boundary_fallbacks = 0
        for k, point in enumerate(xy):
            if d_outer[k] < .001:
                # Read the real boundary roof from just inside its wall, then
                # extrapolate its triangle plane to the silhouette. Historical
                # analytic fields differ from the final ball-side shell by mm.
                starts = outer_poly
                edges = np.roll(outer_poly, -1, axis=0) - outer_poly
                t = np.clip(np.sum((point-starts)*edges, axis=1) / np.sum(edges*edges, axis=1), 0, 1)
                projected = starts + t[:,None]*edges
                edge_index = np.argmin(np.linalg.norm(projected-point, axis=1))
                edge = edges[edge_index]
                inward = np.array([-edge[1], edge[0]]) / np.linalg.norm(edge)
                area = np.sum(outer_poly[:,0]*np.roll(outer_poly[:,1],-1)-outer_poly[:,1]*np.roll(outer_poly[:,0],-1))
                inward *= np.sign(area)
                for inset in [.03, .08, .2, .5]:
                    q = projected[edge_index] + inward*inset
                    boundary_hits = distinct_hits(base.ray_cast([q[0], q[1], 100], [q[0], q[1], -1]))
                    if boundary_hits and boundary_hits[0].normal[2] > .1:
                        break
                assert boundary_hits and boundary_hits[0].normal[2] > .1, (side, point)
                hit = boundary_hits[0]
                normal = np.array(hit.normal)
                height = hit.position[2] - np.dot(point-q, normal[:2])/normal[2]
                base_height.append(height)
                roof_minimum.append(2.0)
                boundary_fallbacks += 1
                continue
            hits = distinct_hits(base.ray_cast([point[0], point[1], 100], [point[0], point[1], -1]))
            if hits:
                base_height.append(hits[0].position[2])
                assert len(hits) >= 2
                inner_z = hits[1].position[2]
                nz = max(abs(hits[1].normal[2]), .15)
                roof_minimum.append(min(base_height[-1], inner_z + PARAMS["minimum_roof_normal_thickness_mm"] / nz))
            else:
                # Exactly on the vertical outside silhouette, a vertical ray
                # can be tangent and return no hits. This fallback is confined
                # to that outline, not internal openings or unsupported spans.
                assert d_outer[k] < .0001, (side, point, d_outer[k])
                base_height.append(original_roof[k])
                roof_minimum.append(2.0)
                boundary_fallbacks += 1
        base_height = np.array(base_height)
        target = fair_surface(xy)
        if ball_poly is not None:
            # Fixed ball collar is a local boundary condition. Do not let its
            # steep tilted rim drive global extrapolation on the far wall.
            ball_weight = 1 - smoothstep(exterior_distance(xy, ball_poly) / 12.0)
            target = target * (1 - ball_weight) + base_height * ball_weight
        amplitude = smoothstep(exterior_distance(xy, main_poly) / PARAMS["inner_round_transition_mm"])
        amplitude *= smoothstep(exterior_distance(xy, thumb_poly) / PARAMS["inner_round_transition_mm"])
        if ball_poly is not None:
            amplitude *= smoothstep(exterior_distance(xy, ball_poly) / PARAMS["ball_fade_mm"])
        top = base_height + amplitude * (target - base_height)
        radius = PARAMS["outer_top_radius_mm"] * amplitude
        offset = np.maximum(radius - d_outer, 0)
        fillet_drop = radius - np.sqrt(np.maximum(radius ** 2 - offset ** 2, 0))
        top -= fillet_drop
        # A manufacturing thickness constraint, not a styling contour. Keep
        # any already-thin original area intact. Record its activation.
        minimum = np.array(roof_minimum)
        constrained = top < minimum
        if side == "left":
            top = minimum + smooth_positive(top - minimum, .25)
        # On the right the old cavity terminates abruptly at perimeter ribs.
        # Clamping the outside roof to that ceiling recreates stepped styling.
        # Rebuild its nonfunctional inner roof beneath the fair surface instead;
        # final assembly and normal-thickness checks govern this new ceiling.
        np.savez_compressed(OUT / f"{side}-fair-roof.npz", xy=xy, top=top,
                            original=base_height, minimum=minimum, target=target,
                            amplitude=amplitude, constrained=constrained)
        cache.update(top=top[inverse], xy=xy, inverse=inverse)
        # At the outer silhouette the analytic historical roof can differ
        # from the final shell. Extend attachment down inside the existing
        # perimeter wall, rather than leaving closed sliver voids below it.
        wall_overlap = (6.0 if side == "right" else 0.0) * (1 - smoothstep(d_outer / .75))
        floor = np.minimum(base_height, top) - PARAMS["attachment_overlap_mm"] - wall_overlap
        if side == "right":
            floor = np.minimum(floor, top - 3.2)
        z = floor[inverse] + vertices[:, 2] * (top - floor)[inverse]
        stats.update(vertices=len(vertices), unique_xy=len(xy),
                     max_vertical_addition_mm=float(np.max(top - base_height)),
                     max_roof_vs_source_mm=float(np.max(abs(original_roof - base_height))),
                     silhouette_ray_fallbacks=boundary_fallbacks,
                     exterior_drop_to_old_roof=False,
                     maximum_lowering_mm=float(np.max(base_height-top)),
                     thickness_limit_candidates=int(constrained.sum()),
                     thickness_constraint_vertices=int(constrained.sum()) if side == "left" else 0,
                     interior_roof_rebuilt=side == "right",
                     construction_extrema_include_outside_trimmed_silhouette=True,
                     surface_method="single global thin-plate height-and-slope fit")
        return np.column_stack((vertices[:, :2], z))

    shoulder = flat.warp_batch(warp)
    assert shoulder.status() == mf.Error.NoError
    print(side, "integrated shoulder", stats, flush=True)
    cutter = flat.warp_batch(lambda vertices: np.column_stack((vertices[:, :2],
                      cache["top"] + vertices[:, 2] * (100 - cache["top"]))))
    assert cutter.status() == mf.Error.NoError
    return shoulder, cutter, stats


def repair_outer_seam(side, base, outline):
    """Rebuild only the outer 1.5 mm band with a continuous arc-height guide.

 The original roof/sidewall intersection has grid-aligned stair faces. A
 periodic filtered guide replaces that boundary, blended back into the roof.
 Mounting/clearance cutters remain exact; this is geometry, not shading.
 """
    p = np.array(outline.to_polygons()[0])
    edges = np.roll(p, -1, axis=0) - p
    lengths = np.linalg.norm(edges, axis=1)
    cum = np.r_[0, np.cumsum(lengths)]
    L = cum[-1]
    direction = np.sign(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - p[:, 1] * np.roll(p[:, 0], -1)))
    normals = np.c_[-edges[:, 1], edges[:, 0]] / lengths[:, None] * direction
    width = PARAMS['seam_band_width_mm']
    safe = PARAMS['seam_clean_band_mm']
    radius = PARAMS['outer_top_radius_mm']
    # Sample the existing roof inside the seam at uniform perimeter spacing.
    arc = np.linspace(0, L, int(np.ceil(L / PARAMS['seam_arc_sample_mm'])), endpoint=False)
    idx = np.searchsorted(cum, arc, side='right') - 1
    pts = p[idx] + (arc - cum[idx])[:, None] / lengths[idx, None] * edges[idx]
    inner = pts + normals[idx] * width
    heights = []
    for q in inner:
        hits = distinct_hits(base.ray_cast([*q, 100], [*q, -1]))
        assert hits, (side, q)
        heights.append(hits[0].position[2])
    heights = gaussian_filter1d(heights, PARAMS['seam_arc_smoothing_mm'] / (L / len(arc)), mode='wrap')

    def project(xy):
        best = np.full(len(xy), np.inf)
        arcs = np.zeros(len(xy))
        for (i, (a, e, el)) in enumerate(zip(p, edges, lengths)):
            t = np.clip((xy - a) @ e / (el * el), 0, 1)
            d = np.linalg.norm(xy - a - t[:, None] * e, axis=1)
            take = d < best
            best[take] = d[take]
            arcs[take] = cum[i] + t[take] * el
        return (best, arcs)
    # Work beyond the silhouette, then trim once to avoid coincident walls.
    region = outline.offset(0.15, circular_segments=128) - outline.offset(-width, circular_segments=128)
    flat = region.extrude(1).refine_to_length(PARAMS['seam_mesh_edge_mm'])
    cache = {}

    def warp(v):
        (xy, inv) = np.unique(v[:, :2], axis=0, return_inverse=True)
        (dist, arcs) = project(xy)
        dist[~PolygonPath(p).contains_points(xy)] = 0
        reference = np.interp(arcs, arc, heights, period=L)
        radiusdrop = radius - np.sqrt(np.maximum(radius ** 2 - np.maximum(radius - dist, 0) ** 2, 0))
        target = reference - radiusdrop
        existing = []
        for (q, ref) in zip(xy, reference):
            hits = distinct_hits(base.ray_cast([*q, 100], [*q, -1]))
            existing.append(hits[0].position[2] if hits else ref)
        existing = np.array(existing)
        # Only the outside0.55mm uses the new guide exclusively.
        # Blend into the actual roof by1.5mm; leave its broad form intact.
        blend = smoothstep((dist - safe) / (width - safe))
        top = target * (1 - blend) + existing * blend
        floor = np.minimum(top, existing) - 2.5
        cache.update(top=top[inv])
        return np.c_[v[:, :2], floor[inv] + v[:, 2] * (top - floor)[inv]]
    addition = flat.warp_batch(warp)
    cutter = flat.warp_batch(lambda v: np.c_[v[:, :2], cache['top'] + v[:, 2] * (100 - cache['top'])])
    planes = json.loads((DEV / f'references/{side}-switch-planes.json').read_text())
    for pl in planes:
        addition -= local_box(pl, [19.2, 19.2, 19.8], 0.2)
        protected = local_box(pl, [17, 17, 4.5], -4.3)
        addition -= protected
        cutter -= protected
        addition -= local_box(pl, [19.6, 19.6, 7], -11)
    if side == 'right':
        for name in ['ball-mount-core.stl', 'ball35p2-sweep-v10.stl', 'trackball-top-assembly-v7.stl', 'trackball-btu-assembly-v7.stl', 'trackball-cover-assembly-v7.stl']:
            obj = manifold(trimesh.load(DEV / 'references' / name))
            addition -= obj
            cutter -= obj
    candidate = base + addition - cutter ^ outline.extrude(100)
    assert candidate.status() == mf.Error.NoError
    stats = {'band_width_mm': width, 'arc_samples': len(arc), 'added_mm3': float((candidate - base).volume()), 'removed_mm3': float((base - candidate).volume())}
    print(side, 'outer seam rebuild', stats, flush=True)
    return (candidate, stats)

def round_collar(base):
    """Refit the nonfunctional forward collar toward a concentric circular arc.

    Work in the unchanged ball-seat frame. Radius <=23.5mm, all switch/PCB
    prisms, the lower10mm interface and the opposite thumb-side collar remain
    fixed. Sample the actual old wall so old decorative lobes are not reused
    as a target. Refine long legacy triangles before applying the smooth map.
    """
    ball = json.loads((DEV / 'references/ball-surface.json').read_text())
    c = np.array(ball['center'])
    n = np.array(ball['normal'])
    u = np.array([n[2], 0, -n[0]])
    v = np.cross(n, u)
    frame = np.column_stack((u, v, n))
    p = (np.array(ball['outline']) - c) @ frame
    theta = np.arctan2(p[:, 1], p[:, 0])
    r = np.linalg.norm(p[:, :2], axis=1)
    order = np.argsort(theta)
    angles = np.linspace(-np.pi, np.pi, 1440, endpoint=False)
    radii = np.interp(angles, theta[order], r[order], period=2 * np.pi)
    for (i, ang) in enumerate(angles):
        direction = u * np.cos(ang) + v * np.sin(ang)
        hits = base.ray_cast(c - n * 0.25 + direction * 23.5, c - n * 0.25 + direction * 45)
        exits = [float((np.array(h.position) - c) @ direction) for h in hits if np.array(h.normal) @ direction > 0.1]
        radii[i] = exits[0] if exits else radii[i] + 3.0
    radii = gaussian_filter1d(radii, 1.5 / 0.25, mode='wrap')
    planes = json.loads((DEV / 'references/right-switch-planes.json').read_text())
    stats = {}

    def warp(vertices):
        q = (vertices - c) @ frame
        radius = np.linalg.norm(q[:, :2], axis=1)
        ang = np.arctan2(q[:, 1], q[:, 0])
        old = np.maximum(np.interp(ang, angles, radii, period=2 * np.pi), 24.0)
        target = np.minimum(old, PARAMS["ball_collar_target_radius_mm"])
        safe = PARAMS["ball_collar_fixed_radius_mm"]
        a = (target - safe) / (old - safe)
        t = np.clip((radius - safe) / (old - safe), 0, 1)
        mapped = safe + (target - safe) * t / (a + (1 - a) * t)
        # Match the inner map's radial derivative at the guide, then return
        # to identity over12mm. This avoids a crease at the round collar edge.
        tail = np.clip((radius-old)/12, 0, 1)
        tail_radius = ((2*tail**3-3*tail**2+1)*target
                       + (tail**3-2*tail**2+tail)*(a*a)*12
                       + (-2*tail**3+3*tail**2)*(old+12)
                       + (tail**3-tail**2)*12)
        delta = np.where(radius < old, mapped-radius,
                         np.where(radius < old+12, tail_radius-radius, 0))
        delta[radius <= safe] = 0
        depth = smoothstep((q[:, 2] + 40) / 15) * (1 - smoothstep((q[:, 2] - 1) / 5))
        weight = depth * smoothstep((vertices[:, 2] - 10) / 10) * smoothstep((np.degrees(ang) + 20) / 20) * (1 - smoothstep((np.degrees(ang) - 95) / 25))
        for pl in planes:
            (pc, pn, px) = (np.array(pl[k]) for k in ['center', 'normal', 'x'])
            py = np.cross(pn, px)
            loc = (vertices - pc) @ np.column_stack((px, py, pn))
            dist = np.maximum(np.maximum(abs(loc[:, 0]) - 10, abs(loc[:, 1]) - 10), np.maximum(-11 - loc[:, 2], loc[:, 2] - 20))
            weight *= smoothstep(dist / 3)
        delta *= weight
        q[:, :2] *= (1 + delta / np.maximum(radius, 1e-12))[:, None]
        stats.update(max_inward_displacement_mm=float(-delta.min()), affected_vertices=int((delta < -0.001).sum()))
        return c + q @ frame.T
    raw_warp = warp

    def checked_warp(vertices):
        output = raw_warp(vertices)
        keep = dict(stats)
        indices = np.where(np.linalg.norm(output - vertices, axis=1) > 0.001)[0]
        points = vertices[indices]
        q = (points - c) @ frame
        r = np.linalg.norm(q[:, :2], axis=1)
        direction = (q[:, 0, None] * u + q[:, 1, None] * v) / r[:, None]
        upper = raw_warp(points + direction * 0.005)
        lower = raw_warp(points - direction * 0.005)
        derivative = np.sum((upper - lower) * direction, axis=1) / 0.01
        stats.update(keep)
        stats['minimum_sampled_radial_derivative'] = float(derivative.min())
        print('radial Jacobian', derivative.min(), flush=True)
        assert derivative.min() > 0, 'Radial mapping folds'
        return output
    result = base.refine_to_length(PARAMS["ball_collar_refine_mm"]).warp_batch(checked_warp)
    print('warp', stats, 'status', result.status(), flush=True)
    np.savez_compressed(OUT / 'right-collar-guide.npz', angles_rad=angles, source_radius_mm=radii)
    return result.as_original().simplify(PARAMS['coplanar_cleanup_tolerance_mm']), stats


def write_stl(solid, path):
    m = solid.to_mesh64()
    np.savez_compressed(OUT / (path.stem + "-raw.npz"), vertices=m.vert_properties[:, :3], faces=m.tri_verts)
    vertices = np.array(m.vert_properties[:, :3])
    # Weld by distance, not decimal bins. Bin rounding can merge only one end
    # of a sub-nanometre sliver, leaving a non-manifold edge on STL reload.
    parent = np.arange(len(vertices))
    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index
    for a, b in cKDTree(vertices).query_pairs(2e-8, output_type="ndarray"):
        a, b = root(a), root(b)
        if a != b:
            parent[max(a, b)] = min(a, b)
    mapping = np.array([root(i) for i in range(len(vertices))])
    assert np.linalg.norm(vertices - vertices[mapping], axis=1).max() < 1e-6
    faces = mapping[m.tri_verts]
    noncollapsed = (faces[:, 0] != faces[:, 1]) & (faces[:, 1] != faces[:, 2]) & (faces[:, 0] != faces[:, 2])
    faces = faces[noncollapsed]
    # Welding a zero-thickness Boolean sliver can make its two opposite
    # faces coincide. Cancel opposing pairs, rather than keeping one face
    # (which would leave a spurious fin and three non-manifold edges).
    _, groups = np.unique(np.sort(faces, axis=1), axis=0, return_inverse=True)
    parity = ((faces[:, 0] > faces[:, 1]).astype(int)
              + (faces[:, 0] > faces[:, 2]) + (faces[:, 1] > faces[:, 2])) % 2
    orientation = 1 - 2 * parity
    balance = np.bincount(groups, weights=orientation)
    eligible = np.where(orientation * balance[groups] > 0)[0]
    _, first = np.unique(groups[eligible], return_index=True)
    faces = faces[eligible[first]]
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    mesh.remove_unreferenced_vertices()
    # ASCII retains float64 coordinates; binary STL rounds all original datums.
    path.write_text(trimesh.exchange.stl.export_stl_ascii(mesh))
    reread = trimesh.load(path)
    # Coplanar sidewall booleans can leave an extra near-collinear facet.
    # Remove only an isolated facet whose three edges are all non-manifold,
    # each has multiplicity one or three. This operation restores
    # multiplicity two (or removes unused edges) and moves no vertices; broad area filtering
    # would incorrectly remove legitimate small triangles.
    for cleanup_pass in range(4):
        if reread.is_watertight:
            break
        counts = np.bincount(reread.edges_unique_inverse)
        per_face = counts[reread.edges_unique_inverse.reshape((-1, 3))]
        candidates = np.where(np.all(np.isin(per_face, [1, 3]), axis=1))[0]
        keep = np.ones(len(reread.faces), dtype=bool)
        for index in candidates:
            triangle = reread.triangles[index]
            longest = np.max(np.linalg.norm(triangle - np.roll(triangle, 1, axis=0), axis=1))
            altitude = 2 * reread.area_faces[index] / longest
            if altitude < 1e-7:
                keep[index] = False
        before = reread.volume
        reread.update_faces(keep)
        reread.remove_unreferenced_vertices()
        assert abs(reread.volume - before) < 1e-6
        print("STL redundant collinear facets removed", int((~keep).sum()), flush=True)
        path.write_text(trimesh.exchange.stl.export_stl_ascii(reread))
        reread = trimesh.load(path)
    assert reread.is_watertight and reread.is_winding_consistent, path
    return reread


def build(side):
    source = ROOT / f"models/integrated-fr4/{side}-shell.stl"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    mesh = trimesh.load(source)
    assert mesh.is_watertight and mesh.is_winding_consistent
    base = manifold(mesh)
    planes = json.loads((DEV / f"references/{side}-switch-planes.json").read_text())
    main_hull = key_hull([p for i, p in enumerate(planes) if i not in THUMBS[side]], 5.5)
    thumb_hull = key_hull([planes[i] for i in THUMBS[side]], 2.8)
    # Reuse the actual V14 sidewall silhouette, including its float32 source
    # coordinates. No inset leaves an old shelf outside the raised shoulder.
    polygons = base.slice(.5).to_polygons()
    outline = max(polygons, key=lambda p: abs(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - p[:, 1] * np.roll(p[:, 0], -1))))
    # Remove sub-micron zigzags from STL sectioning before rebuilding walls.
    outer = mf.CrossSection([outline]).simplify(PARAMS["outline_cleanup_tolerance_mm"])
    field_data = np.load(DEV / f"references/{side}-fair-field-{'v7' if side == 'left' else 'v9'}.npz")
    field = RectBivariateSpline(field_data["y"], field_data["x"], field_data["z"])
    addition, cutter, stats = make_shoulder(side, base, planes, outer, main_hull, thumb_hull, field)
    # Full cap proxy, switch functional zones and under-plate socket clearance
    # are protected, independently of the 2D construction masks.
    for p in planes:
        addition -= local_box(p, [19.2, 19.2, 19.8], .2)
        addition -= local_box(p, [17.0, 17.0, 4.5], -4.3)
        cutter -= local_box(p, [17.0, 17.0, 4.5], -4.3)
        addition -= local_box(p, [19.6, 19.6, 7.0], -11.0)
    if side == "right":
        for name in ["ball-mount-core.stl", "ball35p2-sweep-v10.stl",
                     "trackball-top-assembly-v7.stl", "trackball-btu-assembly-v7.stl",
                     "trackball-cover-assembly-v7.stl"]:
            protected_mesh = trimesh.load(DEV / "references" / name)
            protected = manifold(protected_mesh)
            addition -= protected
            cutter -= protected
            if name == "trackball-btu-assembly-v7.stl":
                # Leave the underside of the BTU assembly accessible. A solid
                # cutout alone can create an enclosed pocket inside new roof.
                underside_access = protected.project().extrude(float(protected_mesh.bounds[1, 2]) + 1).translate([0, 0, -1])
                addition -= underside_access
    candidate = ((base + addition) - cutter) ^ outer.extrude(100)
    assert candidate.status() == mf.Error.NoError
    candidate, stats["outer_seam"] = repair_outer_seam(side, candidate, outer)
    composite_data = candidate.to_mesh64()
    np.savez_compressed(OUT / f"{side}-composite.npz", vertices=composite_data.vert_properties[:, :3], faces=composite_data.tri_verts)
    candidate = mf.Manifold(mf.Mesh64(np.array(composite_data.vert_properties[:, :3], copy=True),
                                     np.array(composite_data.tri_verts, copy=True)))
    parts = candidate.decompose()
    print(side, 'component volumes', [p.volume() for p in parts], flush=True)
    solid_parts = []
    zero_lines = 0
    for part in parts:
        if abs(part.volume()) < 1e-9:
            points = np.array(part.to_mesh64().vert_properties[:, :3])
            singular = np.linalg.svd(points - points.mean(0), compute_uv=False)
            assert singular[-1] < 1e-7, "Detached component is not a zero-thickness numerical sheet"
            zero_lines += 1
        else:
            solid_parts.append(part)
    assert len(solid_parts) == 1, "Do not discard disconnected surfaces or enclosed voids"
    candidate = solid_parts[0].as_original().simplify(PARAMS["coplanar_cleanup_tolerance_mm"])
    parts = solid_parts
    stats["discarded_zero_volume_degenerate_remnants"] = zero_lines
    path = OUT / f"{side}-shell.stl"
    final = write_stl(candidate, path)
    if side == "right":
        stats["pre_collar_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        rounded, stats["circular_ball_collar"] = round_collar(manifold(final))
        final = write_stl(rounded, path)
    final_solid = manifold(final)
    removed = (base - final_solid).volume()
    added = (final_solid - base).volume()
    assert removed >= -.001
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    return dict(source=str(source.relative_to(ROOT)), source_sha256=source_hash,
                output=str(path.relative_to(ROOT)), output_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                shoulder=stats, base_volume_mm3=base.volume(), output_volume_mm3=final_solid.volume(),
                removed_mm3=removed, added_mm3=added, components=len(parts),
                bounds_mm=final.bounds.tolist(), watertight=final.is_watertight,
                winding_consistent=final.is_winding_consistent)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report_path = OUT / "build.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {"parameters": PARAMS, "sides": {}}
    report["parameters"] = PARAMS
    for side in (sys.argv[1:] or ["left", "right"]):
        report["sides"][side] = build(side)
        report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
