"""
gapconf.py  (remote)  -- runs/surrogate_explore
First gap-confined designs (user 2026-10-19: the breathing mode must sit INSIDE the mirror cell's Y+Z+ gap).
Designs come from analyze_gap_cells.py --mf 60 --strict: small-hole mirror (hx/a .40, hy/w .60-.66, gap top ~10.6 GHz at
w700 / ~11.3 at w650) + large-hole center (chi < 0: center holes LARGER than the mirror's -> softer center cell).
Per design: Pipeline.bracket() steps a_m until 619.4 nm is bracketed, then one solve on the interpolated 619 nm point.
Input surrogate_explore__gapconf.json (uploaded from runs/surrogate_explore/gapconf.json); output
runs/surrogate_explore/gapconf/<tag>/data/{ad_*.npz, final.npz}.
"""
import json
from pathlib import Path

from cavity_pipeline import Pipeline, p

DES = json.load(open('surrogate_explore__gapconf.json'))['designs']
for k, g in enumerate(DES):
    tag = g['tag']
    P = Pipeline(f'runs/surrogate_explore/gapconf/{tag}', dict(w=g['w'], t=120, hx_a=g['hx_a'], hy_w=g['hy_w']),
                 59.5, 'gapconf')                      # one shared vertical-wall model file (set_layout updates w)
    try:
        fin = P.dd / 'final.npz'
        if fin.exists():
            p(f'[gapconf] {tag}: done already'); continue
        a619 = P.bracket(g['d'], g['a0'], (g['xi'], g['chi']), max_solves=5)
        cfg = P.cfg(a619, g['d'], g['xi'], g['chi'])
        r = P.point(cfg, fin, dict(a=round(a619, 1), d=g['d'], xi=g['xi'], chi=g['chi'], tag=tag,
                                   gap_lo=g['gap_lo'], gap_hi=g['gap_hi'], fb_pred=g['fb_pred']))
        p(f"[gapconf] {k+1}/{len(DES)} {tag}: a {a619:.1f} -> {r} | mirror gap {g['gap_lo']:.2f}-{g['gap_hi']:.2f}, "
          f"predicted breathing {g['fb_pred']:.2f}")
    except Exception as e:
        p(f'[gapconf] {tag} failed: {str(e)[:300]}')
    finally:
        P.close()
p('gapconf done.')
