"""
digitize_reference.py  (Mac)
Digitize Oh et al. 2026 (Optica 13, 485) Fig. 1(e) mirror-cell mechanical bands and Fig. 1(d)
optical TE band from 600-dpi renders of the vector figure (reference/fig1e.png, fig1d.png).

Axis calibration: plot frame detected from the thick black border; frequency axis 0..12 GHz (e)
and 0..250 THz (d); k axis Gamma (left frame) .. X (right frame) linear in k.
Red  = modes even in y and z (our Y+Z+ class); blue = all other classes. Shaded band = their
quasi-gap; dashed line = their cavity mode frequency.

Output: reference/oh2026_fig1e_digitized.csv (k_frac, f_GHz, color), fig1d likewise, plus a
check plot overlaying the digitized points on the image.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

REF = Path('runs/nanobeam_oh2026/reference')


def frame(img):
    dark = img[..., :3].sum(axis=2) < 0.3
    cols = np.where(dark.sum(axis=0) > 0.5 * dark.shape[0] * 0.6)[0]
    rows = np.where(dark.sum(axis=1) > 0.5 * dark.shape[1] * 0.6)[0]
    # frame = outermost long dark lines; take inner edges of the thick border
    xl, xr = cols.min(), cols.max()
    yt, yb = rows.min(), rows.max()
    # move to inner edge of border
    while dark[(yt + yb) // 2, xl + 1]: xl += 1
    while dark[(yt + yb) // 2, xr - 1]: xr -= 1
    while dark[yt + 1, (xl + xr) // 2]: yt += 1
    while dark[yb - 1, (xl + xr) // 2]: yb -= 1
    return xl, xr, yt, yb


def digitize(fn, fmax, colors):
    img = plt.imread(str(REF / fn))
    xl, xr, yt, yb = frame(img)
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    masks = {'red': (r > 0.85) & (g < 0.25) & (b < 0.25),
             'blue': (b > 0.75) & (r < 0.3) & (g < 0.3)}
    out = []
    for name in colors:
        mk = masks[name]
        for x in range(xl + 2, xr - 1, 3):
            ys = np.where(mk[yt:yb, x])[0] + yt
            if ys.size == 0:
                continue
            # group contiguous pixels -> one point per curve crossing
            groups = np.split(ys, np.where(np.diff(ys) > 2)[0] + 1)
            for gp in groups:
                yc = gp.mean()
                out.append(((x - xl) / (xr - xl), (yb - yc) / (yb - yt) * fmax, name))
    shade = (r > 0.95) & (g > 0.6) & (g < 0.8) & (b > 0.6) & (b < 0.8)      # pink quasi-gap fill
    # quasi-gap: rows where most of the frame width is pink shading (crossing lines don't matter)
    frac = shade[yt:yb, xl:xr].mean(axis=1)
    rows = np.where(frac > 0.35)[0] + yt
    gap = ((yb - rows.max()) / (yb - yt) * fmax, (yb - rows.min()) / (yb - yt) * fmax) if rows.size else None
    return img, (xl, xr, yt, yb), out, gap


for fn, fmax, unit, cols in (('fig1e.png', 12.0, 'GHz', ('red', 'blue')), ('fig1d.png', 250.0, 'THz', ('red',))):
    img, (xl, xr, yt, yb), pts, gap = digitize(fn, fmax, cols)
    stem = 'oh2026_' + fn.replace('.png', '')
    with open(REF / f'{stem}_digitized.csv', 'w') as fh:
        fh.write(f'# digitized from {fn}; frame px x {xl}-{xr}, y {yt}-{yb}; quasi-gap shading {gap} {unit}\n')
        fh.write(f'k_over_kX,f_{unit},class\n')
        for k, f, c in pts:
            fh.write(f'{k:.4f},{f:.4f},{c}\n')
    print(f'{fn}: frame x {xl}-{xr}, y {yt}-{yb}; {len(pts)} points; quasi-gap shading = '
          f'{gap[0]:.2f}-{gap[1]:.2f} {unit}' if gap else f'{fn}: no clean shading run (overlaps light cone)')
    red = np.array([(k, f) for k, f, c in pts if c == 'red'])
    near_X = red[red[:, 0] > 0.97]
    if near_X.size:
        fs = np.sort(near_X[:, 1]); groups = np.split(fs, np.where(np.diff(fs) > 0.02 * fmax)[0] + 1)
        print('   red bands at X:', ', '.join(f'{g.mean():.2f}' for g in groups), unit)
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.imshow(img, extent=[-xl / (xr - xl), (img.shape[1] - xl) / (xr - xl),
                           -(img.shape[0] - yb) / (yb - yt) * fmax, yb / (yb - yt) * fmax], alpha=0.45, aspect='auto')
    for c, mk in (('red', 'o'), ('blue', 's')):
        P = np.array([(k, f) for k, f, cc in pts if cc == c])
        if P.size:
            ax.plot(P[:, 0], P[:, 1], mk, ms=2.5, color='k' if c == 'red' else 'c', label=f'digitized {c}')
    ax.set_xlim(0, 1); ax.set_ylim(0, fmax); ax.set_xlabel('k / k_X'); ax.set_ylabel(unit)
    ax.legend(fontsize=8); ax.set_title(f'digitization check: {fn}')
    fig.savefig(REF / f'{stem}_digitize_check.png', dpi=130, facecolor='white')
