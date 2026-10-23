# Best 80nm device: w 700 nm, d 0.10, ξ 4, χ 3.5, a 182.8 nm

Final 80nm-minimum-feature device of the 1D nanobeam OMC track (diamond, t 120 nm, suspended), selected by
`scripts/cavity_designs.py` (fabricable, breathing localization ≥ 0.8, sidewall ratio S ≥ 0.7,
breathing ≤ 10 GHz first by highest optical Q). COMSOL confirmation solve: `runs/cavity_619_width/w700_mf80/data/confirm1.npz`.

## Geometry
| | |
|---|---|
| beam width w / thickness t | 700 / 120 nm |
| mirror period a | 182.8 nm |
| mirror hole hx × hy | 82.3 × 490.0 nm (hx/a 0.45, hy/w 0.7) |
| taper | Chan thesis: d 0.10, M 10, η 1, ξ 4, χ 3.5; 10 mirror cells per side |
| center cell | a 164.5, hx 81.9, hy 320.0 nm |
| min features | bridge 82.8, rail 105.0, hole 81.9 nm (min 81.9) |

## Optical cavity mode
| | |
|---|---|
| resonance | **619.29 nm** (484.09 THz) |
| optical Q (radiation, COMSOL) | **3.39e+06** |
| localization (∫\|E\|² near center) | 0.99 |

## Mechanical breathing mode
| | |
|---|---|
| frequency | **9.726 GHz** |
| mechanical Q | **not computed**: the mechanical model is clamped with no mechanical PML, so its eigenvalues are real (any Q it prints is numerical noise). A physical Q_m needs a mechanical PML / support / shield model. Breathing localization stands in for it. |
| localization | 0.86 |
| sidewall coherence B / sidewall ratio S | 0.54 / 1.00 (clean breathing: B > 0.5, S ≈ 1) |
| effective mass (max \|u\| normalization) | 233 fg |
| zero-point motion x_zpf | 1.9 fm |
| thermal occupation n_th | 0.0095 (0.1 K), 3.2 (1.7 K), 8.1 (4 K) |

## Mirror-cell band gaps (`mirror_bands.png`)
Optics (TE-like, y-even = cavity family, at X):
- dielectric band 460.5 THz (651 nm), next mode 550.4 THz (545 nm):
  gap 89.9 THz (18 %); cavity mode at 484.1 THz sits 23.6 THz above the band edge
- air light line at X 820 THz (gap below it)
- center (defect) cell band edge at X: 495.9 THz
- y-odd family lowest at X: 519.8 THz (577 nm), above the cavity mode

Mechanics:
- breathing class (Y+Z+) quasi-gaps below 30 GHz: 5.47–9.01 GHz, 21.67–25.58 GHz
- breathing mode 9.73 GHz NOT inside a Y+Z+ quasi-gap: it overlaps a breathing-class band of the mirror cell, so the mirror does not forbid it from leaking along the beam. Its confinement over the simulated beam (localization above) comes from the taper and the finite mirror; the real Q_m is the open question this raises.
- complete gap (all four symmetry classes) below 30 GHz: none

## Sweep that found it
Pipeline `runs/cavity_619_width/w700_mf80`: (a, d) step with the base taper shape → 619 nm line a(d) → taper shapes (ξ, χ) on that line.
`sweep_ad.png` (a, d) step, `sweep_shapes.png` shape maps (outlined = base shape, hatched = below min feature,
red slash = not a breathing mode), `sweep_designs.csv` every design on the 619 nm line with flags and rank (rank 1 = this device).
Comparison across all widths: `../selection.png`, `../design_space.png`, `../all_designs.csv`.

## Figures
- `modes.png`: optical Ey on the z = 0 midplane; breathing mode on the deformed top face (color \|u\|)
- `mode_spectrum.png`: every optical and mechanical mode of the solve; stars = cavity / breathing modes
- `mirror_bands.png`: mirror-cell bands, optics and mechanics
