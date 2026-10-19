"""fullgap_screen.py: 80 nm mirror cells for wide beams -- full-k guided gap (band-1 max = edge at X, band-2 MIN over guided k)
around 484 THz (619 nm). Margin = min(484 - f1X, f2min - 484) / 484. Rails and bridges >= 80 nm. legume, rough COMSOL scaling."""
import itertools
import time
import numpy as np
from even_bands import even_bands

rows = []
t0 = time.time()
for w, hxa, hyw in itertools.product((700, 730, 760, 790), (0.42, 0.46, 0.50, 0.54), (0.66, 0.71, 0.76)):
    a = 189.0
    if a * (1 - hxa) < 80 or w * (1 - hyw) / 2 < 80:
        continue
    B = even_bands(w, a, hxa * a, hyw * w, nk=7, numeig=6)
    f1X = B[-1][1][0]
    f2 = [r[1] for _, r in B if len(r) >= 2]
    f2min = min(f2) if f2 else np.nan
    m = min(484 - f1X, f2min - 484) / 484
    rows.append((w, hxa, hyw, f1X, f2min, m))
    print(f'w {w} hx/a {hxa} hy/w {hyw}: f1X {f1X:.0f}, f2min {f2min:.0f} THz, margin {m*100:+.1f} %  ({time.time()-t0:.0f} s)', flush=True)
np.save('fullgap_screen.npy', np.array(rows))
