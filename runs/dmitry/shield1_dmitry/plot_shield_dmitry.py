"""plot_shield_dmitry.py -- figures for the Dmitry-cloud shield sweep (shield1_dmitry). Ran on the Dmitry cloud software.
shield_bands_dmitry.png: chosen cell bands (sym + antisym) with the complete gap and the cavity modes.
shield_sweep_dmitry.png: complete gaps of all 12 cells."""
import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

FB = (9.81, 10.57)
def load(d):
    out = {}
    for s in ('sym', 'antisym'):
        A = np.loadtxt(f'cells_dmitry/{d}/shield_dmitry_{s}.csv', delimiter=',', usecols=(0, 1, 2))
        ks, idx = np.unique(A[:, :2], axis=0, return_inverse=True)
        out[s] = (A[:, :2], A[:, 2] / 1e9)
    return out

def path_pos(k, a):
    k = k * a * 1e-9 / np.pi                       # units of pi/a
    kx, ky = k[:, 0], k[:, 1]
    s = np.where(ky < 1e-9, kx, np.where(np.abs(kx - 1) < 1e-6, 1 + ky, 2 + (1 - kx) * np.sqrt(2)))
    on_diag = (np.abs(kx - ky) < 1e-6) & (kx < 1 - 1e-6) & (kx > 1e-9)
    s = np.where(on_diag, 2 + (1 - kx) * np.sqrt(2), s)
    return s

def bands(ax, d, a, title, gap):
    B = load(d)
    for s, c, mk in (('sym', 'tab:blue', 'o'), ('antisym', 'tab:red', 's')):
        k, f = B[s]; x = path_pos(k, a)
        ax.plot(x, f, mk, ms=2.2, color=c, label=f'z-{s}', ls='none')
    L = 2 + np.sqrt(2)
    if gap:
        ax.axhspan(*gap, color='gold', alpha=0.35, lw=0, label=f'complete gap {gap[0]:.2f}–{gap[1]:.2f} GHz')
    for f, ls in zip(FB, ('-', '--')):
        ax.axhline(f, color='k', ls=ls, lw=1)
        ax.text(L * 0.99, f, f'{f} GHz cavity mode', ha='right', va='bottom', fontsize=7)
    ax.set_xticks([0, 1, 2, L]); ax.set_xticklabels(['Γ', 'X', 'M', 'Γ']); ax.set_xlim(0, L); ax.set_ylim(0, 20)
    for xv in (1, 2): ax.axvline(xv, color='0.7', lw=0.6)
    ax.set_ylabel('frequency (GHz)'); ax.set_title(title, fontsize=9); ax.legend(fontsize=7, loc='upper left')

def cell_sketch(ax, a, h, w):
    ax.add_patch(Rectangle((0, 0), a, a, color='0.75'))
    for lx, ly in ((h, w), (w, h)):
        ax.add_patch(Rectangle((a/2 - lx/2, a/2 - ly/2), lx, ly, color='white'))
    ax.set_xlim(-20, a + 20); ax.set_ylim(-20, a + 20); ax.set_aspect('equal'); ax.axis('off')
    ax.set_title(f'a {a}, h {h}, w {w} nm\nbridge {a-h} nm, t 120 nm', fontsize=8)

if __name__ == '__main__':
    G = json.load(open('gaps_dmitry.json'))
    best = [r for r in G if r['covers_981']][0]
    fig = plt.figure(figsize=(9, 4.6)); ax = fig.add_axes([0.08, 0.11, 0.62, 0.8]); ax2 = fig.add_axes([0.74, 0.3, 0.24, 0.5])
    bands(ax, f"a{best['a']}_h{best['h']}_w{best['w']}_dmitry", best['a'], 'shield cell bands (Dmitry cloud, P2)', tuple(best['cover'][0]))
    cell_sketch(ax2, best['a'], best['h'], best['w'])
    fig.savefig('shield_bands_dmitry.png', dpi=170); plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.2))
    lab = [f"a{r['a']}\nb{r['bridge']} w{r['w']}" for r in G]
    for i, r in enumerate(G):
        for lo, hi in r['gaps']:
            ax.add_patch(Rectangle((i - 0.35, lo), 0.7, hi - lo, color='tab:green' if lo < 9.81 < hi and lo < 10.57 < hi else 'tab:gray'))
    for f, ls in zip(FB, ('-', '--')): ax.axhline(f, color='k', ls=ls, lw=1)
    ax.set_xticks(range(len(G))); ax.set_xticklabels(lab, fontsize=6.5); ax.set_xlim(-0.6, len(G) - 0.4); ax.set_ylim(4, 26)
    ax.set_ylabel('complete gap (GHz)'); ax.set_title('Cross-cell sweep, 120 nm diamond (Dmitry cloud). a, bridge b = a − h, bar width w (nm); green = covers both cavity modes', fontsize=8)
    fig.tight_layout(); fig.savefig('shield_sweep_dmitry.png', dpi=170); plt.close(fig)
    print('ok')
