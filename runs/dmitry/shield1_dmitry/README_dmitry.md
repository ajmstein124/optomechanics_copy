# shield1_dmitry — runs on the Dmitry cloud software

Dmitry cloud software (laghai/nanophotonics-cloud) run, authorized by the user 2026-10-22 (authorization 3: square-lattice cross phonon shield for 60nm_w650_d0.086_xi1.79_chi-6.97_gapconf). Diamond t 120 nm, isotropic E 1050 GPa nu 0.07 rho 3500 (same as COMSOL). Target: complete gap around the 9.81 GHz breathing mode. Min feature 60 nm.

All files in this folder were produced for/by the Dmitry cloud software (laghai/nanophotonics-cloud), not COMSOL or Lumerical.

- `sweep1_dmitry.json`: square-lattice cross unit cells, 36 points (a 350-650 nm, bridge a-h 60/85/115 nm, bar width 70/100/140 nm, fillet 20 nm), P2 screening, sym + antisym, G-X-M-G.

## Run (Dmitry cloud software), 2026-10-22
- User approved the sparser 12-cell version after the quote: `sweep1s_dmitry.json`, estimate $0.98 expected / $2.70 ceiling
  (`estimate1s_dmitry.json`); the 36-cell `sweep1_dmitry.json` was priced ($3.07 / $8.10, `estimate1_dmitry.json`) but NOT run.
- Submitted as sweep-c11edac992d7da32c9a8 (campaign abby-shield1), prod npc-api-00021-r4t, engine npc-elastic/0.1.0/ceffa180e6b5591b.
  `submit1s_dmitry.json`, `status1s_dmitry.json`; per-cell outputs in `cells_dmitry/a<a>_h<h>_w<w>_dmitry/`.
- `gaps_dmitry.py` -> `gaps_dmitry.json` (complete gaps > 0.8 GHz). Only a 450, h 390, w 140 covers both cavity modes:
  complete gap 9.40-11.47 GHz. Figures: `shield_sweep_dmitry.png`, `shield_bands_dmitry.png` (`plot_shield_dmitry.py`).
- COMSOL check of that cell (runs/shield_619/cross_cell_bands.py; COMSOL data stays in runs/shield_619): gap 9.397-11.472 GHz,
  985 modes median |df/f| 6.2e-4, max 1.8e-3 (`compare_comsol_dmitry.json`).
- Full cavity + shield: not supported by the Dmitry engine yet -> request laghai/nanophotonics-cloud#163. The full structure was run in
  COMSOL (runs/shield_619, not Dmitry data).


## sweep2_dmitry (65 nm minimum feature re-design; Dmitry cloud software)
Rows (a, h, w): 450/385/140, 450/385/160, 450/380/150, 440/375/150, 460/395/150, 450/380/170 (bridges 65-70 nm), same base as sweep1s.
Estimate (estimate2_dmitry.json): $0.40 expected, $0.67 ceiling. NOT submitted until the user approves.
