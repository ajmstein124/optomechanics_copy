# Lumerical verification: 60nm_w650_d0.10_xi6_chi4

Independent FDTD check of the COMSOL design (`lumerical_verification.png`). Same hole layout (scripts/cavity_taper.py),
Lumerical FDTD v251 on the GPU computer (express mode), x/y anti-symmetric + z symmetric (COMSOL's mode class),
5 ps, Qanalysis (`runs/cavity_619/lumerical/lum_best_60nm.lsf`).

| | COMSOL | Lumerical |
|---|---|---|
| resonance | 619.50 nm | 618.77 nm (-0.74 nm, -0.12 %) |
| optical Q | 1.79e+07 | 1.11e+07 (lower bound: a 5 ps run cannot resolve the decay of Q > ~1e6) |

The field maps agree in shape and envelope; the spike at the center of the Lumerical map is the dipole source's near field.

The w650 / 60 nm taper-shape sweep that found this device was also replicated point by point in Lumerical (old PC, CPU, 1.5 ps): `lumerical_sweep_replica.png`.
