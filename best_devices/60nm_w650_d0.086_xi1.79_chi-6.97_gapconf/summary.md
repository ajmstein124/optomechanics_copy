# 60nm_w650_d0.086_xi1.79_chi-6.97_gapconf

Gap-confined 60 nm device (design tag `w650_m186_c455_d086`, `runs/surrogate_explore/gapconf/w650_m186_c455_d086`).

| | |
|---|---|
| beam width / thickness | 650 nm / 120 nm |
| mirror cell | a 189.5 nm, hx 75.8 (hx/a 0.40), hy 390.0 (hy/w 0.60) |
| taper | M 10, d 0.086, η 1.0, ξ 1.79, χ -6.97 (center holes larger than the mirror's); 10 mirror cells |
| resonance / optical Q | 619.31 nm / 3.8e+06 |
| breathing mode | 9.81 GHz, localization 0.99, sidewall ratio S 1.00 |
| mirror Y+Z+ gap | 7.47–10.87 GHz (13 k-points); breathing mode 1.05 GHz below the top |
| displacement fraction in the last 500 nm | 7.4e-08 (decays inside the mirror) |
| other localized breathing-like modes | 10.57 GHz |
| m_eff / x_zpf | 172 fg / 2.23 fm |
| zero-point strain (midplane peak) | volumetric 1.5e-08, εxx−εyy 1.8e-08 |
| smallest features | bridge 70, rail 97, hole 76 nm |

## Figures
- `mirror_bands.png`: mirror-cell bands (solid) and center-cell bands (dashed), optics and mechanics, with the cavity modes drawn where they sit.
- `review.png`: bands + optical Ey + breathing mode on the deformed top face + midplane strain maps (volumetric, εxx−εyy) with the optical |E|² = 50 % contour.
- `60nm_w650_d0.086_xi1.79_chi-6.97_gapconf.gds` / `.png`: layout, plain anchors; `60nm_w650_d0.086_xi1.79_chi-6.97_gapconf_shield.gds` / `.png`: with the cross shield (layers 1 diamond, 2 etch, 10 label; `python best_devices/make_gds.py`).
- `shield_cell_bands.png`, `shield_structure.png`, `shield_disp_maps.png`, `shield_qm.png`: shield cell bands (COMSOL vs Dmitry cloud), modeled structure, breathing-mode |u|² with/without shield, Q_m vs mirror cells. Full report: `docs/shield_report/omc_shield_report.pdf`.
- **Fab note:** the first shield column leaves a 30 nm strip at the trench edge (cross center a/2 = 225 nm, bar half-length 195 nm), below the 60 nm rule; same in the COMSOL model. Fix (needs a re-run): shift the lattice ≥ 30 nm away from the trench or shorten the edge crosses.

## Phonon shield (2026-10-22)
- Cross shield (a 450, h 390, w 140 nm; gap 9.40–11.47 GHz) around the anchor: Q_m 1.65e7 → 2.8e9 (10 mirror cells, COMSOL anchor loss; PML/mesh converged). `runs/shield_619`, `docs/shield_report/omc_shield_report.pdf`.

## Not yet done
- Disorder (σ 1–2 nm), Lumerical check, g0 (bug), longer mirror, sidewall angles. See `../CHECKS.md`.
