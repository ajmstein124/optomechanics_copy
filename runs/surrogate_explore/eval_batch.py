"""
eval_batch.py  (remote)  -- runs/surrogate_explore
Evaluate one proposal batch from propose.py: one full-cavity solve per point (period already solved for 619.4 nm by
the surrogate). One cavity model for all widths (set_layout updates w). Output data/bo<batch>_<i>.npz (+ predictions).
Usage (remote): python surrogate_explore__eval_batch.py <batch>   (batch_<n>.json uploaded as surrogate_explore__batch_<n>.json)
Launch from the Mac: python runs/surrogate_explore/launch_batch.py <n>
"""
import json
import sys
import time
from pathlib import Path

from cavity_pipeline import Pipeline, p

n = int(sys.argv[1]) if len(sys.argv) > 1 else int(Path('surrogate_explore__current_batch.txt').read_text().strip())
AFTER = sys.argv[2:]          # optional: batch numbers of THIS stream to run afterwards (chained)
B = json.load(open(f'surrogate_explore__batch_{n}.json'))
D = Path('runs/surrogate_explore/data'); D.mkdir(parents=True, exist_ok=True)
groups = {}
for i, pt in enumerate(B['points']):
    c = pt['cfg']; groups.setdefault((int(c.get('M', 10)), int(c.get('n_mirror', 10)), 'swa' in c), []).append((i, pt))
t0 = time.time()
for (M, nm, full), pts in sorted(groups.items()):
    c0 = pts[0][1]['cfg']
    P = Pipeline('runs/surrogate_explore', dict(w=c0['w'], t=120, hx_a=c0['hx_m'] / c0['a_m'], hy_w=c0['hy_m'] / c0['w']),
                 B['min_feature'] - 0.5, f'bo{n}_M{M}_n{nm}' + ('_full' if full else ''), n_mirror=nm, M=M,
                 swa=0.0 if full else None)
    try:
        for i, pt in pts:
            fn = D / f'bo{n}_{i}.npz'
            extra = {f'pred_{k}': v for k, v in pt['pred'].items()}
            extra.update(why=pt['why'], batch=n, index=i)
            r = P.point(pt['cfg'], fn, extra)
            pr = pt['pred']
            p(f"[bo{n}] {i} M{M} n{nm} ({pt['why'][:20]}): got {r} | pred lam {pr.get('lam', float('nan')):.1f} "
              f"logQ {pr.get('logQ', float('nan')):.2f} fb {pr.get('fb', float('nan')):.2f} ({time.time()-t0:.0f} s)")
    except Exception as e:
        p(f'[bo{n}] group M{M} n{nm} failed: {str(e)[:300]}')
    finally:
        P.close()
p(f'batch {n} done.')
for nxt in AFTER:
    import subprocess
    subprocess.run([sys.executable, '-u', 'surrogate_explore__eval_batch.py', nxt], check=False)
