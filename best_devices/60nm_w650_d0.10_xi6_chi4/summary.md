# Best 60nm device: w 650 nm, d 0.10, ξ 6, χ 4, a 190.3 nm

Final 60nm-minimum-feature device of the 1D nanobeam OMC track (diamond, t 120 nm, suspended), selected by
`scripts/cavity_designs.py` (fabricable, breathing localization ≥ 0.8, sidewall ratio S ≥ 0.7,
breathing ≤ 10 GHz first by highest optical Q). COMSOL confirmation solve: `runs/cavity_619_width/w650_mf60/data/confirm1.npz`.

## Geometry
| | |
|---|---|
| beam width w / thickness t | 650 / 120 nm |
| mirror period a | 190.3 nm |
| mirror hole hx × hy | 100.8 × 500.5 nm (hx/a 0.53, hy/w 0.77) |
| taper | Chan thesis: d 0.10, M 10, η 1, ξ 6, χ 4; 10 mirror cells per side |
| center cell | a 171.3, hx 107.2, hy 282.6 nm |
| min features | bridge 64.4, rail 74.8, hole 100.8 nm (min 64.4) |

## Optical cavity mode
| | |
|---|---|
| resonance | **619.50 nm** (483.92 THz) |
| optical Q (radiation, COMSOL) | **1.79e+07** |
| localization (∫\|E\|² near center) | 0.99 |

## Mechanical breathing mode
| | |
|---|---|
| frequency | **9.667 GHz** |
| mechanical Q | **not computed**: the mechanical model is clamped with no mechanical PML, so its eigenvalues are real (any Q it prints is numerical noise). A physical Q_m needs a mechanical PML / support / shield model. Breathing localization stands in for it. |
| localization | 0.95 |
| sidewall coherence B / sidewall ratio S | 0.80 / 1.00 (clean breathing: B > 0.5, S ≈ 1) |
| effective mass (max \|u\| normalization) | 166 fg |
| zero-point motion x_zpf | 2.3 fm |
| thermal occupation n_th | 0.0098 (0.1 K), 3.2 (1.7 K), 8.1 (4 K) |

## Mirror-cell band gaps (`mirror_bands.png`)
Optics (TE-like, y-even = cavity family, at X):
- dielectric band 459.3 THz (653 nm), next mode 577.9 THz (519 nm):
  gap 118.6 THz (23 %); cavity mode at 483.9 THz sits 24.6 THz above the band edge
- air light line at X 788 THz (gap below it)
- center (defect) cell band edge at X: 495.0 THz
- y-odd family lowest at X: 527.7 THz (568 nm), above the cavity mode

Mechanics:
- breathing class (Y+Z+) quasi-gaps below 30 GHz: 5.21–8.77 GHz, 19.61–25.39 GHz
- breathing mode 9.67 GHz NOT inside a Y+Z+ quasi-gap: it overlaps a breathing-class band of the mirror cell, so the mirror does not forbid it from leaking along the beam. Its confinement over the simulated beam (localization above) comes from the taper and the finite mirror; the real Q_m is the open question this raises.
- complete gap (all four symmetry classes) below 30 GHz: none

## Sweep that found it
Pipeline `runs/cavity_619_width/w650_mf60`: (a, d) step with the base taper shape → 619 nm line a(d) → taper shapes (ξ, χ) on that line.
`sweep_ad.png` (a, d) step, `sweep_shapes.png` shape maps (outlined = base shape, hatched = below min feature,
red slash = not a breathing mode), `sweep_designs.csv` every design on the 619 nm line with flags and rank (rank 1 = this device).
Comparison across all widths: `../selection.png`, `../design_space.png`, `../all_designs.csv`.

## Figures
- `modes.png`: optical Ey on the z = 0 midplane; breathing mode on the deformed top face (color \|u\|)
- `mode_spectrum.png`: every optical and mechanical mode of the solve; stars = cavity / breathing modes
- `mirror_bands.png`: mirror-cell bands, optics and mechanics
