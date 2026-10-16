"""
plot_schematic.py  (runs locally on Mac)
Simulation-setup schematic for diamond_dw_sweep (3x3 d x w at a=300 nm). Geometry-exact.

Usage (from project root):
    python runs/diamond_dw_sweep/plot_schematic.py
"""
import sys
sys.path.insert(0, 'scripts')
from schematic import make_schematic, panel_grid, DEFAULT_SHIFT_NM

D = [124, 104, 85]
W = [85, 107, 128]
cells = [dict(row=i, col=j, a=300, d=d, w=w, fr=16, shift=DEFAULT_SHIFT_NM,
              text=f'd={d}, w={w}', status='nominal' if (d, w) == (104, 107) else 'ok')
         for i, d in enumerate(D) for j, w in enumerate(W)]

make_schematic(
    a_nm=300, d_nm=104, w_nm=107, fr_nm=16, t_nm=140,
    title='Diamond snowflake phononic crystal -- d x w sweep (diamond_dw_sweep)\n'
          'unit_cell_3.mph | a=300, f_r=16, t=140 nm | E=1050 GPa, nu=0.07, rho=3500 kg/m^3 | N_mode=10, n_seg=7 (21 k-pts)\n'
          'panels A-C: nominal d=104, w=107 nm',
    out_stem='runs/diamond_dw_sweep/figures/schematic',
    panel_d=lambda ax: panel_grid(ax, cells, [f'd = {d} nm' for d in D], [f'w = {w} nm' for w in W],
                                  'arm length d', 'arm width w',
                                  '(D)  3x3 sweep grid (cells to scale, default mov1 shift)',
                                  note='red = nominal (diamond_mech_v1)'))
