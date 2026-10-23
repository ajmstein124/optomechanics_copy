"""
run_cases.py  (remote)  -- runs/shield_619
Solve the cases in shield_619__cases.json (uploaded from runs/shield_619/cases.json) with build_shield_cavity.py:
best gap-confined 60 nm device (gapconf w650_m186_c455_d086) anchored into a diamond slab, with / without a cross shield,
for several mirror lengths. Output runs/shield_619/data/<name>.npz (+ top-face field export). Resumable.
"""
import json
from pathlib import Path

import mph
import numpy as np
from build_shield_cavity import build, solve, export_top, p

J = json.load(open('shield_619__cases.json'))
DD = Path('runs/shield_619/data'); DD.mkdir(parents=True, exist_ok=True)
client = mph.start()
for c in J['cases']:
    fn = DD / f"{c['name']}.npz"
    if fn.exists():
        p(f"[{c['name']}] done already"); continue
    cfg = dict(J['cavity'], n_mirror=c['n_mirror'], f_target=J['f_target'], N_mode=c.get('N_mode', 40))
    sh = dict(J['shield'], use=c['shield'], **c.get('shield_override', {}))
    p(f"=== {c['name']}: n_mirror {c['n_mirror']}, shield {c['shield']} {sh}")
    try:
        model, info = build(client, cfg, sh, name=c['name'])
        r = solve(model, J['f_target'])
        out = dict(r, **{k: v for k, v in info.items()}, cfg=json.dumps(cfg), shield=json.dumps(sh))
        np.savez(str(fn), **out)                         # save the modes first; the field export is extra
        if r['i_breath'] > 0 and c.get('fields', True):
            xmax = info['X_in'] + info['Lc'] + sh['m_out']; ymax = info['Yc'] + sh['m_out']
            try:
                out['top_xy'], out['top_val'] = export_top(model, r['i_breath'], DD / f"{c['name']}_top.txt", xmax, ymax, cfg['t'] / 2 - 1)
                np.savez(str(fn), **out)
            except Exception as e:
                p(f"[{c['name']}] field export failed: {str(e)[:200]}")
        ib = r['i_breath']
        if ib > 0:
            p(f"[{c['name']}] breathing {r['f'][ib-1]/1e9:.4f} GHz, Q_m {r['Q'][ib-1]:.3g}, loc {r['loc'][ib-1]:.3f}")
        client.remove(model)
    except Exception as e:
        p(f"[{c['name']}] FAILED: {str(e)[:400]}")
        try:
            client.clear()
        except Exception:
            pass
client.clear()
p('shield cases done.')
