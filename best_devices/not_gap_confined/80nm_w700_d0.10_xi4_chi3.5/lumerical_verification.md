# Lumerical verification: 80nm_w700_d0.10_xi4_chi3.5

Independent FDTD check of the COMSOL design (`lumerical_verification.png`). Same hole layout (scripts/cavity_taper.py),
Lumerical FDTD v251 on the GPU computer (express mode), x/y anti-symmetric + z symmetric (COMSOL's mode class),
5 ps, Qanalysis (`runs/cavity_619/lumerical/lum_best_80nm.lsf`).

| | COMSOL | Lumerical |
|---|---|---|
| resonance | 619.29 nm | 618.73 nm (-0.56 nm, -0.09 %) |
| optical Q | 3.39e+06 | 8.64e+06 (lower bound: a 5 ps run cannot resolve the decay of Q > ~1e6) |

The field maps agree in shape and envelope; the spike at the center of the Lumerical map is the dipole source's near field.

Lumerical's Q (8.6e+06) is ABOVE the COMSOL value (3.4e+06). Possible cause: COMSOL's compact air/PML box (validated only on the w550 beam) may limit its Q for this wider device; not yet checked with a larger COMSOL box.
