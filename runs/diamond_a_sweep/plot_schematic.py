"""
plot_schematic.py  (runs locally on Mac)
Simulation-setup schematic for diamond_a_sweep. Geometry-exact (scripts/schematic.py).
Panels A-C: a=200 nm, d/a=0.41, w/a=0.36 (default mov1 shift).
Panel D: all 9 (d/a, w/a) combos at a=200 nm drawn with the cell shift actually used,
coloured by status across the whole a range (from fill_plan.json).

Usage (from project root):
    python runs/diamond_a_sweep/plot_schematic.py
"""
import sys
import json
sys.path.insert(0, 'scripts')
from schematic import make_schematic, panel_grid, DEFAULT_SHIFT_NM

PLAN = json.load(open('runs/diamond_a_sweep/fill_plan.json'))
DA = [0.48, 0.41, 0.35]
WA = [0.28, 0.36, 0.43]
A0 = 200


def status(da, wa):
    if da == 0.48 and wa == 0.43:
        return 'infeasible', 'infeasible\n(bridge 0-5 nm)'
    if da == 0.48:
        return 'shifted', 're-shifted\n(all a)'
    if da == 0.41:
        return 'ok', 'default;\nre-shifted at a=150'
    return 'ok', 'default\n(all a)'


cells = []
for i, da in enumerate(DA):
    for j, wa in enumerate(WA):
        st, txt = status(da, wa)
        tag = f'a{A0}_da{int(round(da*100)):02d}_wa{int(round(wa*100)):02d}'
        shift = (PLAN[tag]['shift_x'] * 1e9, PLAN[tag]['shift_y'] * 1e9) if st == 'shifted' else DEFAULT_SHIFT_NM
        cells.append(dict(row=i, col=j, a=A0, d=da * A0, w=wa * A0, fr=16, shift=shift,
                          text=txt, status='nominal' if (da, wa) == (0.41, 0.36) else st))

make_schematic(
    a_nm=A0, d_nm=0.41 * A0, w_nm=0.36 * A0, fr_nm=16, t_nm=140,
    title='Diamond snowflake phononic crystal -- lattice-constant sweep (diamond_a_sweep)\n'
          'a = 150-275 nm (step 25) x d/a {0.35, 0.41, 0.48} x w/a {0.28, 0.36, 0.43} | t=140, f_r=16 nm fixed\n'
          'E=1050 GPa, nu=0.07, rho=3500 kg/m^3 | N_mode=10, f_mech=10 GHz x 300/a | '
          'panels A-C drawn at a=200 nm, d/a=0.41, w/a=0.36',
    out_stem='runs/diamond_a_sweep/figures/schematic',
    panel_d=lambda ax: panel_grid(ax, cells, [f'd/a = {x}' for x in DA], [f'w/a = {x}' for x in WA],
                                  'arm length d/a', 'arm width w/a',
                                  f'(D)  Ratio grid at a={A0} nm -- cell placement used',
                                  note='orange = cell re-shifted so the hole fits (physics-invariant, validated); '
                                       'hatched = cannot be modelled\n'
                                       'with this rhombus cell (hole meets its periodic images); red = panels A-C'))
