"""
plot_schematic.py  (runs locally on Mac)
Simulation-setup schematic for diamond_mech_v1. Geometry-exact (see scripts/schematic.py).

Usage (from project root):
    python runs/diamond_mech_v1/plot_schematic.py
"""
import sys
sys.path.insert(0, 'scripts')
from schematic import make_schematic

make_schematic(
    a_nm=300, d_nm=104, w_nm=107, fr_nm=16, t_nm=140,
    title='Diamond snowflake phononic crystal -- diamond_mech_v1 simulation setup\n'
          'unit_cell_3.mph | a=300, d=104, w=107, f_r=16, t=140 nm | '
          'E=1050 GPa, nu=0.07, rho=3500 kg/m^3 | N_mode=20, f_mech=10 GHz',
    out_stem='runs/diamond_mech_v1/figures/schematic')
