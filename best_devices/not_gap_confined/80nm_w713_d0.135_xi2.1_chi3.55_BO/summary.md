# Best 80 nm device (surrogate search): w 713 nm, d 0.135, ξ 2.10, χ 3.55, a 189.6 nm

Found by the surrogate-guided (Bayesian) search, `runs/surrogate_explore` (batch 2, point 0), at fixed length M 10, 10 mirror cells.
Confirmation solve `runs/surrogate_explore/data/confirm_bo2_0.npz`; field maps `modes.png`.

## Geometry
| | |
|---|---|
| beam width w / thickness t | 713.2 / 120 nm |
| mirror period a | 189.56 nm |
| mirror hole hx × hy | 95.6 × 545.6 nm (hx/a 0.504, hy/w 0.765) |
| taper | Chan: d 0.1351, M 10, ξ 2.103, χ 3.552; 10 mirror cells per side (gentle taper: ξ, χ below the grid sweeps' range) |
| center cell | a 164.0, hx 80.3, hy 337.8 nm |
| min features | bridge 83.6, rail 83.8, hole 80.3 nm |

## Modes
| | |
|---|---|
| resonance | **619.32 nm** |
| optical Q (ideal geometry) | **2.15e+07** (6.3× the previous 80 nm final, 3.4e6) |
| breathing | **9.840 GHz**: localization 0.86 (x < 1.5 µm) / 0.99 (x < 3 µm), clamp fraction 2.8e-04, S 1.00 |
| effective mass / x_zpf | 386 fg / 1.49 fm (broader, heavier than the previous final's 233 fg → ~22 % less strain per phonon) |
| relative g0 | same as the previous 80 nm final (+6 %), mostly photoelastic (g0 values carry the known normalization bug; ratios assumed valid) |
| thermal occupation | 0.009 (0.1 K), 3.1 (1.7 K), 8.0 (4 K) |
| mechanical Q | not computed (clamped, lossless model) |

## Fabrication disorder (`../disorder.png`)
σ = 2 nm per-hole size, 1 nm position, 8 seeds (symmetric about the model planes): median Q **7.2e+04**
(range 1.1e+04–1.7e+05), the same as the previous 80 nm final and ~1.6× the 60 nm final.
Breathing shifts ≤ 0.05 GHz. At this disorder level the ideal-Q advantage disappears.
