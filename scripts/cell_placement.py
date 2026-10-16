"""
cell_placement.py
=================
Geometry helper for unit_cell_3.mph (read from the .mph by
runs/diamond_a_sweep/diag_geometry.py, 2026-10-14):

  Hole  : Rectangle r1 (lx=w, ly=d, base=center, pos=(0, d/2)) -> arm from the hole
          center (origin) to distance d, pointing up; Rotate +/-120 deg about (0,0);
          Union; Fillet f_r on all vertices.  Arms at 90 / 210 / 330 deg.
  Cell  : Polygon pol1 = rhombus (a/2, -a/(2*sqrt3)), (-a/2, -a/(2*sqrt3)),
          (-a, a/sqrt3), (0, a/sqrt3)   [a1=(a,0), a2=(-a/2, a*sqrt3/2)]
          The hole (origin) sits at the centroid of the lower triangle of the rhombus.
          Move mov1 shifts the CELL by (displx, disply); default (50 nm, -50/sqrt3 nm),
          a fixed absolute offset tuned for Si a=478 nm.
  The model subtracts ONE hole (dif1). If the hole crosses the shifted cell boundary,
  the geometry is no longer periodic -> mesh 'Copy Face 1' fails ("Disconnected source
  not allowed").

For an infinite crystal the placement of the cell relative to the hole does not change
the physics, so we can choose (displx, disply) per geometry to keep the hole inside
with maximum clearance.

clearance(): min distance from the hole to the cell boundary (negative = crossing).
  Hole approximated by the union of the three un-filleted rectangles. Fillets only
  round convex corners inward, so this is conservative. For a convex cell, the minimum
  signed distance over a polygon is attained at a vertex, so checking the rectangle
  vertices is exact.
"""

import numpy as np

SQ3 = np.sqrt(3.0)
DEFAULT_SHIFT = (50e-9, -50e-9 / SQ3)


def hole_vertices(d, w):
    base = np.array([[-w / 2, 0.0], [w / 2, 0.0], [w / 2, d], [-w / 2, d]])
    out = []
    for ang in (0.0, 120.0, -120.0):
        t = np.deg2rad(ang)
        R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
        out.append(base @ R.T)
    return np.vstack(out)


def cell_vertices(a, shift=DEFAULT_SHIFT):
    v = np.array([[a / 2, -a / (2 * SQ3)],
                  [-a / 2, -a / (2 * SQ3)],
                  [-a, -a / (2 * SQ3) + a * SQ3 / 2],
                  [0.0, -a / (2 * SQ3) + a * SQ3 / 2]])
    return v + np.asarray(shift)


def _edge_lines(cell):
    """Inward unit normals n and offsets c so that n.x - c >= 0 inside (convex, any winding)."""
    ctr = cell.mean(axis=0)
    ns, cs = [], []
    for i in range(len(cell)):
        p0, p1 = cell[i], cell[(i + 1) % len(cell)]
        e = p1 - p0
        n = np.array([-e[1], e[0]]) / np.linalg.norm(e)
        if n @ (ctr - p0) < 0:
            n = -n
        ns.append(n)
        cs.append(n @ p0)
    return np.array(ns), np.array(cs)


def clearance(a, d, w, shift=DEFAULT_SHIFT):
    hv = hole_vertices(d, w)
    n, c = _edge_lines(cell_vertices(a, shift))
    return float((hv @ n.T - c).min())


def best_shift(a, d, w, n_grid=241):
    """Grid search over cell shifts (within one cell size) maximising clearance."""
    hv = hole_vertices(d, w)
    n, c = _edge_lines(cell_vertices(a, (0.0, 0.0)))
    # shifting the cell by s changes each line offset: n.x - (c + n.s)
    sx = np.linspace(-a, a, n_grid)
    SX, SY = np.meshgrid(sx, sx)
    S = np.stack([SX.ravel(), SY.ravel()], axis=1)          # (G, 2)
    base = hv @ n.T - c                                     # (V, E)
    shift_term = S @ n.T                                    # (G, E)
    clr = (base[None, :, :] - shift_term[:, None, :]).min(axis=(1, 2))
    g = int(np.argmax(clr))
    # refine around the best grid point
    step = sx[1] - sx[0]
    fx = np.linspace(S[g, 0] - step, S[g, 0] + step, 41)
    fy = np.linspace(S[g, 1] - step, S[g, 1] + step, 41)
    FX, FY = np.meshgrid(fx, fy)
    F = np.stack([FX.ravel(), FY.ravel()], axis=1)
    clr2 = (base[None, :, :] - (F @ n.T)[:, None, :]).min(axis=(1, 2))
    g2 = int(np.argmax(clr2))
    return (float(F[g2, 0]), float(F[g2, 1])), float(clr2[g2])


def min_bridge(a, d, w):
    """Min slab width between the hole and its 6 nearest periodic images (fab-relevant),
    from the un-filleted rectangle union. Exact polygon distance via sampled edges."""
    hv = hole_vertices(d, w).reshape(3, 4, 2)
    pts = []
    for rect in hv:
        for i in range(4):
            p0, p1 = rect[i], rect[(i + 1) % 4]
            pts.append(p0 + np.linspace(0, 1, 60)[:, None] * (p1 - p0))
    pts = np.vstack(pts)

    def inside(q):
        # q inside any rectangle of the hole at origin
        res = np.zeros(len(q), bool)
        for ang in (90.0, 210.0, 330.0):
            t = np.deg2rad(ang)
            u = np.array([np.cos(t), np.sin(t)])
            v = np.array([-u[1], u[0]])
            s, p = q @ u, q @ v
            res |= (s >= 0) & (s <= d) & (np.abs(p) <= w / 2)
        return res

    a1 = np.array([a, 0.0])
    a2 = np.array([-a / 2, a * SQ3 / 2])
    best = np.inf
    for L in (a1, a2, a1 + a2, -a1, -a2, -a1 - a2):
        img = pts + L
        if inside(img).any():
            return 0.0   # hole overlaps its image -> slab fragments
        dd = np.linalg.norm(img[:, None, :] - pts[None, :, :], axis=2).min()
        best = min(best, dd)
    return float(best)


if __name__ == '__main__':
    # Check the model against the observed diamond_a_sweep pass/fail pattern
    failed = {(150, 0.41)} | {(a, 0.48) for a in (150, 175, 200, 225, 250, 275)}
    print(f'{"a":>4} {"d/a":>5} {"w/a":>5} | {"clr default":>11} {"pred":>5} {"obs":>5} | '
          f'{"best shift (nm)":>17} {"clr best":>9} | {"bridge":>7}')
    mismatches = 0
    for a_nm in (150, 175, 200, 225, 250, 275, 300):
        for da in (0.35, 0.41, 0.48):
            for wa in (0.28, 0.36, 0.43):
                a = a_nm * 1e-9
                c0 = clearance(a, da * a, wa * a)
                pred = 'FAIL' if c0 <= 0 else 'ok'
                obs = '' if a_nm == 300 else ('FAIL' if (a_nm, da) in failed else 'ok')
                if obs and obs != pred:
                    mismatches += 1
                s, cb = best_shift(a, da * a, wa * a)
                br = min_bridge(a, da * a, wa * a)
                print(f'{a_nm:4d} {da:5.2f} {wa:5.2f} | {c0*1e9:9.2f}nm {pred:>5} {obs:>5} | '
                      f'({s[0]*1e9:7.2f},{s[1]*1e9:7.2f}) {cb*1e9:7.2f}nm | {br*1e9:5.1f}nm')
    print(f'\nprediction mismatches vs observed: {mismatches}')


def best_shift_filleted(a, d, w, fr, n_refine=(2e-9, 0.5e-9, 0.1e-9)):
    """Fillet-aware optimum (needs shapely; Mac-side only). Starts from the conservative
    best_shift() and refines with the filleted hole. Returns (shift, clearance, bridge)
    in metres; clearance < 0 means the hole fits no placement found."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from shapely import affinity
    rects = hole_vertices(d, w).reshape(3, 4, 2)
    u = unary_union([Polygon(r) for r in rects])
    h = (u.buffer(-fr, join_style=1).buffer(fr, join_style=1)
          .buffer(fr, join_style=1).buffer(-fr, join_style=1))

    def clr(s):
        c = Polygon(cell_vertices(a, s))
        return c.exterior.distance(h) if c.contains(h) else -h.difference(c).area / a

    s0, _ = best_shift(a, d, w)
    best = (clr(s0), s0)
    for step in n_refine:
        sx, sy = best[1]
        for dx in np.arange(-8, 9) * step:
            for dy in np.arange(-8, 9) * step:
                c = clr((sx + dx, sy + dy))
                if c > best[0]:
                    best = (c, (sx + dx, sy + dy))
    a1, a2 = np.array([a, 0.0]), np.array([-a / 2, a * SQ3 / 2])
    br = min(h.distance(affinity.translate(h, *(sg * L))) for L in (a1, a2, a1 + a2) for sg in (1, -1))
    return best[1], best[0], br
