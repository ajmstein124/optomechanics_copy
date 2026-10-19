# Results summary

Tracks the best devices and key learnings. COMSOL, ideal geometry, diamond, t = 120 nm, target 619 nm. Last updated 2026-10-16 23:00.

## Best devices

| | 60 nm min feature | 80 nm min feature |
|---|---|---|
| beam width | 650 nm | 700 nm |
| mirror cell (hx/a, hy/w) | 0.53, 0.77 | 0.45, 0.70 |
| taper | d 0.10, ξ 6, χ 4 | d 0.10, ξ 4, χ 3.5 (base) |
| a | 190.3 nm | 182.8 nm |
| resonance / optical Q | 619.50 nm / 1.8e7 | 619.29 nm / 3.4e6 |
| breathing mode | 9.67 GHz (loc 0.95, S 1.0) | 9.73 GHz (loc 0.86, S 1.0) |
| smallest feature | 64 nm | 82 nm |
| Lumerical check (GPU, v251) | 618.77 nm / Q 1.1e7 | 618.73 nm / Q ≥ 8.6e6 |
| mode volume (estimate) | 1.32 (λ/n)³, Q/V 1.4e7 | 1.55 (λ/n)³, Q/V 2.2e6 |
| details | `best_devices/60nm_w650_d0.10_xi6_chi4/` | `best_devices/80nm_w700_d0.10_xi4_chi3.5/` |

Both meet breathing ≤ 10 GHz. Both optical Qs are far above typical fabricated diamond nanobeams (1e4–1e5).

## Learnings

- **Width sets the breathing frequency** (roughly 1/w). At w 550, no fabricable taper gets below about 10.9 GHz. Widening to 650/700 nm fixes this without hurting optical Q.
- **The 80 nm Q is lower** because it needs a smaller-hole mirror cell (weaker mirror) and only the base taper is fabricable. At the same taper and d 0.13, the 80 nm cell gives Q about 3e6 against 3e7 for the 60 nm cell.
- **The binding 80 nm feature is the bridges near the cavity center**, not the rails. The period shrinks there while hole length stays about the same, so the x-fill rises.
- **Taller holes (hy/w 0.77) don't help at 80 nm.** They widen the mirror gap (457–562 vs 466–556 THz), but cavity Q doesn't rise and the breathing mode moves up to 10.0–10.2 GHz.
- **15 mirror cells instead of 10 doubles Q** for the 80 nm device (3.4e6 → 6.8e6) at no feature cost. The breathing-mode check on that model still needs a wider mode window.
- **A breathing mode must pass all three checks:** localization ≥ 0.8, in-phase sidewalls (B > 0.5), and sidewall amplitude ratio S ≥ 0.7. A hole-centered hybrid at w650 d 0.13 (Q 3e7, 9.82 GHz) passed B but failed S. Always look at the deformed mode shape.
- **Localization** = fraction of ∫|u|² within x < 1.5 µm. It stands in for mechanical Q in design selection.
- **Mechanical Q has not been computed.** The cavity model clamps the beam end with no loss, so any Q_m it reports, such as the 1.9e11 for the Oh reproduction, is numerical noise.
- **The g₀ values in the sweeps are wrong** (a normalization bug, about 1e8 too small). Frequencies and Qs are fine.
- **Validation:** the Oh 2026 mirror cell and cavity are reproduced: 188.9 THz against 192 THz, and breathing 6.51 GHz against 6.34 GHz simulated / 6.23 GHz measured. Lumerical agrees with COMSOL on both finals to about 0.1% in wavelength (table above); Lumerical Q values depend on simulation time, so treat them as rough.

## Width study, best per pipeline

| width / min feature | taper | a (nm) | optical Q | breathing (GHz) |
|---|---|---|---|---|
| 550 / 60 | d 0.10, ξ 6, χ 3.5 | 195.2 | 3.7e7 | 11.14 |
| **650 / 60** | d 0.10, ξ 6, χ 4 | 190.3 | 1.8e7 | **9.67** |
| 600 / 60 | d 0.10, ξ 8, χ 5 | 190.6 | 5.4e5 | 10.51 |
| 650 / 80 | d 0.10, ξ 4, χ 3.5 | 183.8 | 5.7e6 | 10.53 |
| 600 / 80 | d 0.10, ξ 4, χ 3.5 | 185.0 | 7.5e6 | 11.47 |
| **700 / 80** | d 0.10, ξ 4, χ 3.5 | 182.8 | 3.4e6 | **9.73** |
| 700 / 80, hy/w 0.77 (C1) | base | 183.7 | about 2e6 | 10.19 |
| 700 / 80, hx/a 0.48, hy/w 0.77 (C2) | can't reach 619 nm at 80 nm | | | 10.0 |

## Surrogate-guided search (started 2026-10-16 night; `runs/surrogate_explore`)

Method follows Roman's guide and his pccsim `strip_pcw_bayes` scaffolding: Gaussian-process surrogates on every solved cavity point, validated by cross-validation, then constrained expected improvement for log Q with P(breathing ≤ 10 GHz), with the exact min-feature check applied first. Batches mix improvement, exploration, hypothesis and replicate points.
- **Surrogate accuracy (CV):** resonance via λ/a 0.025 nm; log Q 0.10 decade; breathing 0.15 GHz on clean modes (useless until wrong-family modes were removed: R² 0.4 → 0.93).
- **The period is solved from the λ/a surrogate**, so each candidate is one COMSOL solve landing within about 0.6 nm of 619.4 nm, with no bracket. This fails for `lock_x` (only 6 training points), which missed by 5–10 nm.
- **New best 80 nm candidate (bo2_0):** w 713, hx/a 0.504, hy/w 0.765, d 0.135, ξ 2.1, χ 3.55, a 189.6, M 10, n 10. **619.32 nm, Q 2.15e7, breathing 9.84 GHz** (loc ≥ 0.8). 6× the current 80 nm final; to be confirmed (fields, bands).
- Other high-Q 80 nm points: bo1_2 Q 1.4e7 at 9.80 GHz (w 714, d 0.13, ξ 2.1, χ 3.2); bo2_6 Q 4.9e6 at **9.20 GHz** (w 757). Many gentle tapers reach Q 1–3e7 at 10.0–10.5 GHz.
- **Gentle tapers (ξ 2–3, χ 2.7–3.7)** were never sampled by the grid sweeps (ξ ≥ 4, χ ≥ 3.5) and give 5–8× higher Q at 80 nm.
- **Localization metric was biased:** the fixed 1.5 µm window penalizes broad gentle-taper modes. These score 0.6–0.75 there but 0.9–0.99 within 3 µm, with 1e-4 to 6e-3 of the energy near the clamp. New solves also save `loc_mech3` (x < 3 µm) and `clamp_frac` (last 500 nm).
- **Model check:** re-solving the 80 nm final in the shared variable-width model reproduces it exactly (619.29 nm, 3.39e6, 9.73 GHz).

## Robustness and width limits (2026-10-18)

- **Fabrication disorder dominates Q.** σ = 2 nm per-hole size and 1 nm position disorder (symmetric, 8 paired seeds):
  final 60 nm median Q about 4.5e4; final 80 nm about 8e4; bo2_0 about 7e4 (range 1e4–2e5). Ideal Q differences (1.8e7 / 3.4e6 / 2.15e7) vanish.
  Breathing frequency is robust (≤ 0.05 GHz shift); resonance shifts ±0.8 nm. **Optimizing ideal Q beyond about 1e6 doesn't pay at 2 nm disorder.**
  The 80 nm designs are about 1.7× more robust than the 60 nm design. σ = 1 nm comparison running.
- **The width ceiling comes from the full-k mirror gap.** The air band (band 2) has its minimum away from X. As w grows, that minimum drops onto 619 nm
  (w 790, hx/a 0.49, hy/w 0.75: about 490 THz), while the gap at X still looks fine. Batch 4 at w 778–784 collapsed to Q 2–3e5.
  Longer and taller holes restore the margin (legume screen `runs/legume_proxy/fullgap_screen.py`; fit `runs/surrogate_explore/gap_margin_fit.json`).
  Proposals now require margin ≥ 3%. X-point-only mirror checks miss this.
- **Fixed-length comparison** (user): designs are compared at M 10, n 10; length is extended only on the winner.
- **bo2_0 confirmed:** clean single-lobe breathing mode (loc 0.86 / 0.99, clamp 3e-4, S 1.0) and Gaussian-like optical mode (`runs/surrogate_explore/figures/bo_fields.png`).
  Relative g₀ (assuming the g₀ bug is a constant factor) is the same as the 80 nm final (+6%), but m_eff is 386 fg against 233, so there's less strain per phonon.

## Sidewall angle (2026-10-19, `runs/sidewall`, campaign running)

Model: full-thickness 1/4 model (`build_cavity_model`, `cfg['swa']`). The mask is the top surface; holes narrow and the beam flares toward the bottom by t·tanθ per side.
Min features are checked at the top; holes must stay ≥ 20 nm open at the bottom. Validated at 0° against the 1/8 model (619.32 nm, Q 2.30e7 vs 2.15e7, 9.84 GHz).
Same bo2_0 mask at an angle:

| angle | resonance | optical Q | breathing |
|---|---|---|---|
| 0° | 619.32 nm | 2.3e7 | 9.84 GHz (loc 0.86) |
| 5° | 626.94 nm | 7.3e6 | 10.04 GHz (loc 0.76 / 0.99) |
| 10° | 633.01 nm | 1.2e6 | 10.22 GHz (loc 0.57 / 0.72) |

So the angle red-shifts about 1.4 nm/deg, cuts Q quickly (broken z-symmetry mixes TE and TM), and stiffens and delocalizes the breathing mode.
Each angle needs its own design. BO campaigns at 60 and 80 nm × 5° and 10° are running; 15° follows.
At 80 nm the bottom-opening rule leaves few candidates (376 at 5°, 190 at 10°).

**First angled search results (80 nm, 10°, batch 32):** the resonance correction works (620–623 nm), but Q is only 4e5–1.5e6 and breathing 10.3–10.9 GHz.
None reach ≤ 10 GHz yet; a second round (wider beams) is queued.
**80 nm at 15° is infeasible at 619 nm** for t = 120 nm. The walls red-shift about 21 nm, so a ≈ 170–180 nm, and holes need ≥ 84 nm at the top (to stay ≥ 20 nm open
at the bottom) while bridges stay ≥ 80 nm. Relaxing the bottom-opening rule, measuring min features at mid-depth, or a thinner membrane would change this.
**Compute note:** only ONE full-thickness model fits in memory on the COMSOL machine at a time (about 23 min per solve).

**Disorder σ = 1 nm:** median Q final60 about 2.1e5, final80 about 3.6e5, bo2_0 about 3.9e5 (4 seeds). That's about 4–5× the 2 nm values; still disorder-limited, and the 80 nm designs are about 1.8× more robust.
**Disorder σ = 1 nm (partial, superseded):** Q is about 4× higher than at 2 nm (1.2e5–7e5). The 80 nm designs are again ahead of the 60 nm design.

## Physics proxies

- **Optical bands, legume (pccsim `nanobeam()`, worktree `~/Documents/pccsim_main`):** about 0.2 s per cell on the Mac. After calibration against 72 COMSOL cells (w ≥ 550) it agrees to 1.0 nm (band 1) and 0.4 nm (band 2). Raw legume is 6–7% high on band 1, growing at small w/a (`runs/legume_proxy`).
- **Optical Q tracks taper smoothness, not mirror-strength linearity.** Correlation of log Q with the largest cell-to-cell band-edge jump is −0.66; with linearity of mirror strength, −0.10. Strong mirrors (large d) give small modes and low Q. The resonance sits 4.3 ± 1.1% below the center cell's band-1 edge.
- **Mechanics, COMSOL unit-cell proxy (20 s per cell):** the cavity breathing mode sits 0.23 GHz below the center cell's first breathing-class mode at Γ (rms 0.24 GHz, R² 0.84). The mirror cell matters little (R² 0.48).
- **Center-cell breathing ∝ w^−1.4 · a^−0.2 · rail^0.25 · bridge^0.4** (w ≥ 650). At 80 nm the bridges and rails are pinned, so **width is the lever for breathing ≤ 10 GHz**: w 700 → 760 is about −11%.
- **The higher-order (y-odd) family stays above 619 nm up to w about 800** (legume, with the band edge at X falling toward about 510 THz). Confirm in COMSOL.
- **Taller holes (C1/C2) and the locked-x taper don't help:** Q about 3e6 with breathing pinned near 10.05 GHz for every locked-x shape tried.

## Running

- **Locked x-fill taper (`lock_x`), w700, hx/a 0.50, hy/w 0.77, 80 nm** (`runs/cavity_619_width/w700_mf80_LX`). Mirror gap 458–568 THz, breathing window at Γ 7.94–10.17 GHz.
  Base shape on the 619 nm line: d 0.10 a 184.3 (Q about 2.9e6, 10.04 GHz, loc about 0.9); d 0.13 a 188.3 (Q about 3.3e6, 10.05 GHz, loc about 0.85); d 0.16 a 192.5 (Q about 1.3e6, loc < 0.8).
  So far level with the current 80 nm device on Q, breathing just above 10 GHz.
  **Running (10/16 22:55):** taper shapes, `run_w700_lockx_shapes.py`: (ξ, χ) = (2, 4), (4, 4.5), (6, 4), (6, 5), (8, 5) at d 0.10 and 0.13, bracketed upward. The first run bracketed downward, and with lock_x the center holes go below 80 nm there, so 0 shapes ran. With lock_x, ξ and χ only change the center hole height.

## Next / ideas

- Taper variants: a constant-period hole-only (quadratic) taper; η and M sweeps; more mirror cells; rounded-rectangle holes; a wider beam at the center only.
- Mechanical Q with a PML, support or cross shield. Strain tensor at likely SnV sites. Fix the g₀ bug. Even-hole cavity. Full check list for the finals: `best_devices/CHECKS.md`.
- Tabled: `diamond_a_large`, the 2D snowflake sweep for a complete gap ≤ 10 GHz (6 of 45 done).

> **Dmitry cloud software rule (user, 2026-10-19):** never use the Dmitry cloud solver service (laghai/nanophotonics-cloud) without explicit per-run permission from the user. All its files/folders end in `_dmitry`, state that they were run on the Dmitry cloud software, and are kept separate from Lumerical/COMSOL data. See CLAUDE.md.
