"""gaps_dmitry.py -- complete gaps of the shield cells run on the Dmitry cloud software (shield1_dmitry).
CSV rows: kx, ky, f, f (Hz), n_modes nearest the shift per k. A gap must lie inside every k-point's computed window."""
import glob, json, re, sys
import numpy as np
rows = []
for d in sorted(glob.glob('cells_dmitry/a*_dmitry')):
    a, h, w = map(int, re.findall(r'a(\d+)_h(\d+)_w(\d+)', d)[0])
    if not all(glob.glob(f'{d}/shield_dmitry_{s}.csv') for s in ('sym', 'antisym')):
        print('incomplete fetch, skipped:', d); continue
    lo_ok, hi_ok, allf = 0.0, np.inf, []
    for s in ('sym', 'antisym'):
        A = np.loadtxt(f'{d}/shield_dmitry_{s}.csv', delimiter=',', usecols=(0, 1, 2))
        for k in np.unique(A[:, :2], axis=0):
            f = A[(A[:, 0] == k[0]) & (A[:, 1] == k[1]), 2]
            lo_ok = max(lo_ok, f.min()); hi_ok = min(hi_ok, f.max()); allf.append(f)
    f = np.sort(np.concatenate(allf)); f = f[(f >= lo_ok) & (f <= hi_ok)]
    g = [(f[i], f[i+1]) for i in range(len(f)-1) if f[i+1]-f[i] > 0.8e9]
    best = max(g, key=lambda x: x[1]-x[0]) if g else None
    cover = [x for x in g if x[0] < 9.81e9 < x[1]]
    rows.append(dict(a=a, h=h, w=w, bridge=a-h, gaps=[(x[0]/1e9, x[1]/1e9) for x in g], window=(lo_ok/1e9, hi_ok/1e9),
                     covers_981=bool(cover), cover=[(x[0]/1e9, x[1]/1e9) for x in cover]))
    gs = ', '.join(f'{x[0]/1e9:.2f}-{x[1]/1e9:.2f}' for x in g)
    print(f'a {a} h {h} w {w} (bridge {a-h}): window {lo_ok/1e9:.1f}-{hi_ok/1e9:.1f} GHz | gaps {gs}' + ('  <-- covers 9.81' if cover else ''))
json.dump(rows, open('gaps_dmitry.json', 'w'), indent=1)
