# CLAUDE.md — Optomechanics Project Driver

This is the top-level agent context file. All sub-agent files are registered here and deferred to for their respective domains.

---

## Project Overview

**Project:** Co-designed photonic/phononic crystal structures for SnV cavity QED  
**Owner:** ajmstein  
**Created:** 2026-10-08  

Build and simulate diamond photonic crystal structures for cavity QED with the tin vacancy (SnV) center. The project has three sequential stages with increasing complexity.

**Physical system**
- Emitter: Tin vacancy (SnV) center in diamond
  - Zero-phonon line (ZPL): ~619 nm
  - Debye-Waller factor: ~57%
  - Excited-state lifetime (bulk): ~4.5 ns
  - Spin-orbit splitting: ~850 GHz
- Host: Diamond thin film (free-standing slab)
  - Refractive index: n = 2.41 at 619 nm

---

## Project Stages

### Stage 1 — Phononic bandgap pipeline (CURRENT)
**Goal:** Get COMSOL working. Simulate phononic band structure of a 2D diamond slab and confirm a bandgap exists.  
**No photonic constraints.** Geometry, lattice constant, and frequency are free parameters chosen for simulation convenience.  
**Success criterion:** COMSOL runs, band structure looks reasonable, bandgap detected and plotted.  
**Current geometry:** 3-arm snowflake (unit_cell_3.mph), rhombus primitive cell, diamond material override, t=140 nm. (The circular-hole a=500 nm geometry is archived in `archive/`.)

### Stage 2 — Phononic bandgap in a photonic crystal structure
**Goal:** Co-design a structure that is simultaneously:
- A **photonic crystal cavity** at 619 nm (SnV ZPL), AND
- A **phononic crystal** with a complete bandgap at a target frequency (~10–40 GHz, set by lattice constant compatible with 619 nm photonics)

The phononic bandgap acts as an **acoustic radiation shield** — it suppresses leakage of the localized mechanical mode into the bulk (Stage 3), analogous to the cross-crystal phononic shield in Chan 2012. It may also partially suppress phonon-bath decoherence of the SnV spin at GHz spin-transition frequencies.

**Collaborator framing (slide "Phonon bath engineering & quantum emitters", shown 2026-10-16):** 2×2 grid, rows = transition (orbital >50 GHz / spin 1–15 GHz),
columns = phononic Purcell [leakage] / phononic bandgap [protection]. Filled: orbital×bandgap = Kuruma 2025; spin×Purcell = Joe 2026. Target box =
**spin × bandgap**: "Nobody has coherently coupled a high-Q phonon mode to a group-IV spin transition" → a complete GHz gap around a defect mode AT the
spin frequency does both jobs (shields the mode → high Q_m, and removes the spin's phonon continuum) → coherent spin–phonon coupling (g_sm > κ_m, γ_spin).
So shield and bath suppression are the same gap here. Open with user/collaborator: SiV or SnV? (SnV spin–strain coupling ~10× weaker than SiV, ∝ 1/Δgs.)

**Note on SnV decoherence:** SnV orbital splitting ~850 GHz → one-phonon processes at this frequency are exponentially suppressed at low T (n_th ≈ 1e-9 at 1.7 K, ~4e-5 at 4 K), not literally "frozen out"; two-phonon Raman still dephases above ~10 K. Fabricable PnCs cannot reach 850 GHz (a ≈ 9 nm). The PnC targets the GHz spin / mechanical-mode frequency, not this. Kuruma 2025 (SiV orbital at 50 GHz) is a different regime.

**This is where the photonic/phononic lattice constant conflict matters** (see co-design mediator).

### Stage 3 — Full optomechanical crystal cavity
**Goal:** Extend Stage 2 so the structure also has a **localized mechanical mode** co-localized with the optical mode — forming a full optomechanical crystal.  
**Target:** ~10–15 GHz breathing mode co-localized with 619 nm optical mode, high g₀.  
**Adds:** mechanical cavity design (defect engineering), optomechanical coupling rate g_0, mechanical Q.  
**Direct template:** Joe et al. 2026 (Nature) — diamond OMC at 737 nm (SiV) with 12 GHz mode, g_so=3.6 GHz, acoustic Purcell effect. Scale to 619 nm (SnV ZPL).  
**This is the full phoxonic co-design problem** (photonic cavity + phononic bandgap + mechanical cavity mode, all in one structure).

---

## Key figures of merit (by stage)

- Stage 1: fractional phononic gap width (f_bot - f_top) / f_center
- Stage 2: phononic gap at target frequency + photonic Q/V at 619 nm
- Stage 3: Purcell factor F_P = (3/4pi^2)(lambda/n)^3(Q/V); cooperativity C = g^2/(kappa*gamma); mechanical Q

---

## Current State

**Stage 1 (active):**
- [x] Shared utilities: `scripts/comsol_utils.py` (mphglobal, make_bz_path, start_client)
- [x] Remote execution: `scripts/remote_runner.py` — detach mode via Invoke-CimMethod (overnight-safe)
- [x] SSH working: Mac → jv-adamantoise via Tailscale (<USER>@<COMSOL_HOST>), key auth working
- [x] unit_cell_3.mph in C:\Users\abby\comsol (754 MB, 3-arm snowflake unit cell, Si material base)
- [x] Python: C:\Program Files\ANSYS Inc\v252\Lumerical\python-3.13.1\python.exe (mph 1.4.0)
- [x] COMSOL 6.4: C:\Program Files\COMSOL\COMSOL64\Multiphysics_copy1\
  - Permanent node-locked license (SN=<REDACTED>, hostid=<REDACTED>)
  - Modules: MEMS + Wave Optics + RF + ACDC + Semiconductor
- [x] **Si validation complete** (2026-10-13): gap 6.534–7.551 GHz (center 7.042 GHz, 14.5%) at a=478nm, d=166nm, w=170nm, f_r=25nm, t=220nm. Python matches GUI to <1 MHz.
- [x] **Si 3×3 d×w sweep**: partial (4/9 combos), results in `runs/si_dw_sweep/data/`
- [x] **Project reorganized** (2026-10-13): runs-based layout — each sweep gets `runs/<name>/{sweep.py, data/, figures/, schematic}`
- [x] **diamond_mech_v1**: 3-arm snowflake, a=300nm, d=104nm, w=107nm, f_r=16nm, t=140nm. Material override (diamond: E=1050 GPa, nu=0.07, rho=3500). Setup verified via GUI (2026-10-13). N_mode=20, f_mech=10 GHz.
- [x] **diamond_mech_v1 sweep COMPLETE** (2026-10-13): complete gaps 26.6–32.0 GHz (primary, 5.4 GHz wide), 34.1–35.2, 47.6–50.5 GHz.
- [x] **diamond_dw_sweep COMPLETE** (2026-10-13): a=300 nm, d∈{85,104,124} × w∈{85,107,128} nm. Best: **d=124, w=107 → 25.9 GHz center, 8.6 GHz wide (33%)**. Longer arms → wider and lower gap; w matters little at d=124 but shrinks the gap at shorter d. Figures: `runs/diamond_dw_sweep/figures/diamond_dw_heatmap.png`, `diamond_dw_bands_grid.png`.
  - **Gap tracking rule:** the fundamental gap is between sorted bands 6 and 7 (sym+antisym combined) in every combo. Track that pair. The old "first gap > 0.5 GHz" detector in `diamond_dw_sweep/sweep.py` (and the `gap_cen`/`gap_wid` stored in its .npz) jumps to a 51 GHz higher-order gap at d=85, w=128 where the 6–7 gap narrowed to 0.10 GHz — don't use those stored values.
- [x] **diamond_a_sweep COMPLETE** (2026-10-14): 48/54 combos (6 geometrically infeasible: d/a=0.48, w/a=0.43). 33 overnight + 15 via sweep_fill.py (shifted cell). Figures in runs/diamond_a_sweep/figures/ (30 nm fab overlay).
- [ ] **diamond_a_large PAUSED** (user, 2026-10-14 ~13:45, to do the 1D setup) — **REMIND USER TO RESUME.** 6/45 done (a=1000: d/a 0.41 ×3, 0.45 ×3). All a=1000 cells have complete gaps ≤10 GHz; best d/a=0.45, w/a=0.30: 5.25–5.92 GHz (12%). Resume = relaunch the same command (`python scripts/remote_runner.py runs/diamond_a_large/sweep.py`); finished combos are skipped. Remaining ~39 combos ≈ 5.5 h (a=1000 ~10 min/combo, a=600 ~7–8).

**Pending tasks (in priority order):**
0. **Remind user: resume diamond_a_large** (paused for 1D setup; needs its own COMSOL slot after the 1D overnight chain).
0b. 1D nanobeam: see "1D nanobeam OMC track" below (10/15 evening: width study → refinalize/deliverables → w700/80 nm; Lumerical sweeps on the old PC).
1. diamond_a_large: `python scripts/remote_runner.py --status` (pulls runs/diamond_a_large/data) then `python scripts/analyze_plan.py diamond_a_large`. Check whether the gap survives in the thin-slab regime (t/a 0.14–0.35) and where it crosses 10 GHz.
2. ~~Confirm snowflake arm geometry~~ DONE 2026-10-14 (read from .mph; all schematics regenerated).
2b. **Infra (user action needed):** fix abby's profile path (`C:\Users\abby\comsol\fix_abby_profile.ps1`, run with no abby session open) and Windows Update active hours / restart policy so overnight sweeps aren't rebooted. Disable Tailscale key expiry for jv-adamantoise in the admin console.
3. Optical (OP) study for diamond at 619 nm: confirm refractive-index node in GUI before overriding (n=2.41, f_op ≈ 484 THz).
4. Resume Si d×w sweep (5/9 combos remaining): `runs/si_dw_sweep/sweep_resume.py`
5. Offered (not started): Q_m of the finals with a mechanical PML / support / cross shield; strain tensor at candidate SnV sites in final_60nm.mph
   (replaces the ε_zpf / g_e guesses below); literature search (emitter-driven mechanical sideband cooling; driven sidebands of group-IV centers in GHz OMC modes).

**Stage 2 (not started):**
- [ ] Photonic bandgap simulation set up
- [ ] Phononic/photonic lattice constant conflict resolved (see co-design mediator)
- [ ] Simultaneous bandgap demonstrated in a single structure

**Stage 3 (not started):**
- [ ] Mechanical cavity mode design
- [ ] Optomechanical coupling rate computed

---

## Repository Structure

```
optomechanics/
├── CLAUDE.md                          <- this file
├── agents/                            <- sub-agent context files
│   ├── comsol_specialist.md
│   ├── phononic_specialist.md
│   ├── photonic_specialist.md
│   └── codesign_mediator.md
├── scripts/                           <- shared utilities only
│   ├── comsol_utils.py                <- start_client, mphglobal, make_bz_path
│   ├── remote_runner.py               <- SSH runner (detach/block/status/pull); run-aware (runs/<name>/)
│   ├── cell_placement.py              <- hole-in-rhombus feasibility + optimal mov1 shift (fillet-aware)
│   ├── sweep_plan.py                  <- Mac: build runs/<run>/plan.json (feasibility + min-feature flag)
│   ├── plan_runner.py                 <- Windows: execute a plan.json
│   ├── schematic.py                   <- geometry-exact setup schematics (shared by all runs)
│   └── unit_cell_3.mph                <- COMSOL model base (also on remote)
├── runs/                              <- one subfolder per simulation run
│   ├── si_validation/                 <- [DONE] Si mech+OP band structure validation
│   │   ├── sweep.py
│   │   ├── plot_mech_bands.py
│   │   ├── plot_op_bands.py
│   │   ├── data/                      <- 13 CSV files (GUI + Python, mech + OP)
│   │   ├── figures/
│   │   └── schematic.{png,pdf}
│   ├── si_dw_sweep/                   <- Si d×w parameter sweep (4/9 done)
│   │   ├── sweep.py
│   │   ├── sweep_resume.py
│   │   ├── analyze.py
│   │   └── data/
│   ├── diamond_mech_v1/               <- [DONE] Diamond mech band structure (a=300 nominal)
│   │   ├── sweep.py                   <- N_mode=20, f_mech=10 GHz, diamond params
│   │   ├── setup_verify.py            <- generates verify .mph for GUI check before sweep
│   │   ├── plot_bands.py
│   │   ├── plot_schematic.py
│   │   ├── data/
│   │   └── figures/
│   ├── diamond_dw_sweep/              <- [DONE] Diamond 3x3 d x w sweep at a=300
│   │   ├── sweep.py
│   │   ├── analyze.py                 <- heatmaps (tracks band 6-7 gap)
│   │   ├── plot_bands_grid.py         <- 3x3 band-structure grid
│   │   ├── plot_schematic.py
│   │   ├── data/                      <- 9 .npz
│   │   └── figures/
│   └── diamond_a_sweep/               <- lattice-constant sweep a=150-275 nm
│       ├── sweep.py                   <- main sweep (default cell shift)
│       ├── diag_geometry.py           <- read-only dump of .mph geometry/BCs + failure diagnosis
│       ├── fill_plan.json             <- per-combo cell shifts / feasibility for the fill-in
│       ├── sweep_fill.py              <- re-runs failed combos with shifted cell (+ validation)
│       ├── pull.py                    <- lists remote data/, scp's only new .npz, prints log tail + errors
│       ├── analyze.py                 <- gap_vs_a, heatmaps_per_a, summary.csv (truncation ceiling, flags)
│       ├── plot_bands_grid.py         <- one 3x3 band grid per a
│       ├── plot_schematic.py
│       ├── data/  (+ data/validation/)
│       └── figures/
└── archive/                           <- old scripts superseded by runs/ layout (incl. legacy_ui_docs/: app.py, old docs generators)
```

**Planning a new sweep (2026-10-14 — use this for all future snowflake sweeps):**
```bash
python scripts/sweep_plan.py --name <run> --a 400:1000:100 --da 0.41,0.45,0.48 --wa 0.22,0.26,0.30 \
       --n-mode 20 [--min-feature 30 | --no-min-feature] [--dry-run]
python scripts/remote_runner.py runs/<run>/sweep.py
```
- Writes `runs/<run>/plan.json` (+ a 3-line `sweep.py` that calls `scripts/plan_runner.py`). Per combo: fillet-aware cell shift, clearance, narrowest bridge, arm width, status `ok` / `infeasible_geom` / `below_min_feature`, and `run` flag.
- **Minimum-feature check: ON by default at 30 nm** (user setting, 2026-10-14; diamond_a_large uses 20 nm via --min-feature 20; constant `DEFAULT_MIN_FEATURE_NM` in sweep_plan.py). Features checked: narrowest slab bridge and arm width w. `--no-min-feature` runs flagged combos anyway (still flagged in the plan/npz for analysis). Geometrically infeasible combos never run.
- plan_runner: shifts BOTH wp1/wp2 mov1, checks 2 domains/30 boundaries before solving, resumable, saves all complete gaps below the truncation ceiling.

**Remote runner usage:**
```bash
python scripts/remote_runner.py runs/foo/sweep.py       # launch detached (overnight-safe)
python scripts/remote_runner.py --block runs/foo/sweep.py  # blocking (short runs)
python scripts/remote_runner.py --status                # check job + pull results
python scripts/remote_runner.py --pull                  # pull results only
```

**Pull CSV results manually** (scp glob broken on Windows — use explicit paths):
```bash
scp -i ~/.ssh/id_ed25519 "<USER>@<COMSOL_HOST>:C:/Users/abby/comsol/simu_data/Python_diamond_Gamma_sym.csv" runs/diamond_mech_v1/data/
scp -i ~/.ssh/id_ed25519 "<USER>@<COMSOL_HOST>:C:/Users/abby/comsol/simu_data/Python_diamond_Gamma_antisym.csv" runs/diamond_mech_v1/data/
```

Remote machine: `<USER>@<COMSOL_HOST>` (jv-adamantoise, Tailscale)  
Remote path: `C:\Users\abby\comsol`  
Python: `C:\Program Files\ANSYS Inc\v252\Lumerical\python-3.13.1\python.exe`

---

## 1D nanobeam OMC track (2026-10-14) — Oh 2026 approach, 619 nm optical + <=10 GHz breathing mode

**Summary PDF:** `docs/nanobeam_1d_summary.pdf` (generator `docs/make_nanobeam_summary.py`; re-run as data lands).

**Steps and status**
1. **Mirror-cell model** `scripts/build_nanobeam_model.py` (quarter cell; Y±/Z± mech classes; TE optics y0 PEC / z0 PMC).
   Validated vs Oh 2026 Fig. 1(d,e) (`runs/nanobeam_oh2026`): Y+Z+ quasi-gap 3.62–7.16 vs 3.59–7.15 GHz; TE X edges −0.4/−0.6 % at n=2.39.
2. **Mirror-cell design at 619 nm** (`runs/nanobeam_619`, t=120): stage 1 optics at X (68/144 contain 619 nm) → stage 2 Y+Z+ bands
   (48/68 also hold 10 GHz in the band 1–2 quasi-gap). w sets the breathing gap (w650 ~5–10, w550 ~6–12.5, w450 ~7–15 GHz).
   Favored cell **w550 a220 hx/a .53 hy/w .77** (6.2–11.6 GHz, 551–712 nm). Figures stage1_optical.png, stage2_mech.png, candidates_bands.png.
3. **Full-cavity method** `docs/cavity_design_method.md`: Chan thesis §3.4 taper (Oh says he used it): a/a_m = 1−d(2y³−3y²+1), y = η-remap(j/M);
   hole area 1−s = χ(1−a/a_m); aspect r = (a/a_m)^ξ. Cavity optical mode = X-point dielectric band pushed up; mech = Y+Z+ breathing band at Γ pulled down.
   Oh taper measured from his Fig. 1(b) (`runs/nanobeam_oh2026/reference/oh2026_cavity_profile.json`): 41 holes = center + ~10 taper + ~10 mirror/side,
   d 0.18, M 10, η 1, ξ≈6, χ≈3.5. Diamond photoelastic (p11,p12,p44) = (−0.25, 0.043, −0.172) (Burek 2016 / Lang 2009).
4. **Full-cavity model** `scripts/build_cavity_model.py` (+ `cavity_taper.py`, `set_layout()`): 1/8 model, x0 Sym/PEC (Ey odd about the center hole,
   checked on Oh Fig. 1b), y0 Sym/PEC, z0 Sym/PMC; PML +x+y+z; beam runs into +x PML; mech fixed at X_in; one shared mesh. Evaluation helpers
   `scripts/cavity_eval.py`; generic resumable pipeline `scripts/cavity_pipeline.py` (template → (a,d) → 619 nm line → (ξ,χ) shapes → finalize).
5. **Oh cavity reproduced** (`runs/cavity_oh2026`, verification.png, mech_modes.png): optical 188.9 THz (Oh 192) Q_o 1.0e5; cavity breathing mode
   = first breathing mode 6.506 GHz (Oh sim 6.34, meas 6.23; user choice), Q_m 1.9e11 is NUMERICAL NOISE, not physical: the mech model is clamped at X_in with no mechanical PML → lossless, real eigenvalues (Oh measured 1.9e6). **No cavity sweep has a physical Q_m**; sweeps store real f_mech only. Real Q_m needs a mech PML/support/shield.
   Breathing ID = in-phase sidewall motion on the deformed beam + largest coupling; modes 10–14 are torsion/shear.
   Pending benchmark: Q_m with disorder (σ 1–8 nm) + cross shield (SEM pitch ~0.8 µm); anisotropic elasticity test (`bands_aniso.py`, fix CrystalSystem 'Qubic3').
6. **619 nm cavity (a, d) sweep, w 550** (`runs/cavity_619`, sweep_ad.py, analyze_ad.py → ad_sweep.png, 4 panels incl. breathing localization;
   50/50 done): small air/PML box 600/500 nm validated (df/f 2.4e-6, dQ 0.4 %). 619 nm line a = 195.2/200.7/205.7/210.1/213.7 nm for
   d = .10/.13/.16/.19/.22; Q 3.7e7/4.1e6/1.3e5/2.2e4/8.2e3; breathing 10.7–11.6 GHz everywhere, localization 0.98–1.00. Best w550 device:
   d 0.10, a 195.2 (Oh shape ξ6/χ3.5): 619.35 nm, Q 3.0e7, breathing 11.14 GHz, 62 nm (confirmed, mode_profiles.png). Oh shape at d ≥ .13 < 60 nm.
7. **Taper-shape sweep, w 550 / 60 nm** (sweep_shape.py, sweep_shape_d10.py; done 10/15): no fabricable (ξ, χ) gets the breathing mode below
   ~10.9 GHz; stronger pulls cost Q or mechanical localization (e.g. the old "best" d .10/ξ6/χ4 has a double-lobed leaky mode, loc 0.62).
   **Conclusion: the taper can't reach ≤ 10 GHz at w 550 → widen the beam (breathing ~ 1/w).**
8. **Beam-width study** (`runs/cavity_619_width/run.py`, user 10/15; the w550 80 nm chain `runs/cavity_619_mf80` was stopped, cell A dropped):
   per (w, min feature): `Pipeline.bracket()` steps a until 619.4 nm is bracketed per d (0.10/0.13/0.16, base shape ξ4/χ3.5), then ≤ 8 shapes.
   60 nm cell hx/a .53 hy/w .77; 80 nm cell B hx/a .45 hy/w .70.
   - **w650 / 60 nm: BEST 60 nm DEVICE = d 0.10, ξ 6, χ 4.0, a 190.3: 619.50 nm, Q 1.8e7, breathing 9.67 GHz (loc 0.95, S 1.0), 64 nm.**
     Optical Q is NOT hurt by w 650 (3e7 at d .13). d 0.13/a 194 (Q 3e7, 9.82 GHz) is a hole-centered **hybrid** (S 0.35) → rejected.
   - w600 / 60 nm: 10.5–10.9 GHz, best d .10/ξ8/χ5 a 190.6 Q 5.3e5 10.52 GHz → w650 wins.
   - w650 / 80 nm: no fabricable shape beyond the base (619 nm needs a 184–193); best base d .10 a 183.8: Q 5.7e6, 10.53 GHz (loc .85).
   - w600 / 80 nm: running 10/15 afternoon. **w700 / 80 nm queued** (`run_w700.py`, user yes): mirror check (optics both y-parities +
     Y+Z+ bands at a 180), d .07/.10/.13, then re-runs deliverables + fsp builds.
9. **Breathing-mode identification** (all three needed; `cavity_pipeline.breathing_index`, `scripts/cavity_designs.py`): localization ≥ 0.8;
   sidewall coherence B > 0.5 (in-phase sidewalls); **sidewall amplitude ratio S = max sidewall |v| / max |u| ≥ 0.7** (B is amplitude-blind;
   clean breathing S = 1.0, the w650 d.13 hybrid 0.35). S is computed in every new solve (`cavity_eval.sidewall_ratio`, `max_side` operator) and
   from field maps for older points. History: max-|g| rule picked weak modes when the breathing mode was outside the window (false 8.2 GHz) →
   window 60 modes @ 11 GHz. **Always look at the deformed mode shape before calling a device "best".**
10. **Selection + final devices** (`scripts/cavity_designs.py` rank/select; `runs/cavity_619_final/deliverables.py`): fabricable, loc ≥ 0.8, not a
   field-checked hybrid; breathing ≤ 10 GHz first by highest Q, else lowest breathing. deliverables waits for 'Width study done.', then
   `refinalize()` = confirmation solves of the top 3 per pipeline (with S) → `<run>/data/selected.json`, `final_<label>.mph`, `fields_final.npz`;
   then mirror-cell bands for the 2 finals: optics Γ→X in BOTH y-parities (y0 PEC = cavity family, y0 PMC = higher-order family → user's
   single-mode concern at wider w) + mech 4 classes → `runs/cavity_619_final/data/{final,bands}_<mf>.*`; then `fsp_builds.py` (build only).
   Field exports: `scripts/cavity_fields.py` (CutPlane + Data export). Plot: `runs/cavity_619/plot_fields.py <data_dir> <out.png> dev=title …`
   (optical Ey + breathing mode on the DEFORMED top face, |u| color — user's preferred view).
11. **Slides / summary:** `docs/design_process/make_all.py [--pull]` → numbered slide figures (2D snowflake → mirror cells → Oh repro → 619 sweeps
   → width study → design space → selection → finals) + README captions; heat maps via `scripts/plot_cavity_sweeps.py` (shape maps on the 619
   nm line: Q, breathing, localization, min feature; red slash = hybrid). Summary PDF `docs/nanobeam_1d_summary.pdf` (13 sections; regenerate
   with `python docs/make_nanobeam_summary.py` after new data). User's own draft deck: ~/Downloads/omc_design.pdf.
12. **Lumerical** (`runs/cavity_619/lumerical`): `make_lsf.py` writes portable sweep replicas (outputs prefixed `<name>_` in `basedir`, "" = pwd;
   defaults use_symmetry 1, sim_time 1.5 ps; COMSOL λ/Q per point in `<name>_points.json`): lum_ad_mf60 (50), lum_shape_mf60 (52),
   lum_w650_mf60_ad (6), lum_w650_mf60_shape (17). **Runs happen on the OLD PC DESKTOP-BBQLCD3** (`<USER>@<LUMERICAL_HOST>`, Lumerical v211,
   8 cores, `py -3.8`, work dir `C:\Users\JVadmin\Documents\optomechanics\lumerical`; runner `oldpc/run_sweeps.py` + `launch_sweeps.bat`,
   detached via Invoke-CimMethod) — **never on the COMSOL machine** (user). Safe mode blocks `system()` AND `rm()`. ~10 min/point.
   First check: best 60 nm device Lumerical 618.89 nm vs COMSOL 619.49 (−0.1 %), Q 1.3e6 (lower bound at 1.5 ps). Launched 10/15 ~15:20:
   w650_shape → ad_mf60 → shape_mf60 (~20 h). Compare: `plot_lum_vs_comsol.py <name> --pull` (heat maps both solvers + parity).
   **10/16:** queue crashed 10/15 19:27 at lum_ad_mf60 pt 8 (a 225 d .10 -> ~684 nm, outside the window -> no Qanalysis result); make_lsf.py now
   guards with haveresult(); resumed 10/16 10:45 (`run_sweeps.py lum_ad_mf60:8:50 lum_shape_mf60`, log run_sweeps_log2.txt), then the SiC project's screens.
   .fsp files on jv-adamantoise: `C:\Users\abby\lumerical\` (moved out of comsol\ by user); best 60 nm: lum_w650_mf60_best_check.fsp.

**Min feature:** 60 nm (user) and 80 nm, one final device each. 80 nm cell hy/w .70 (rails ≥ 82 nm); taper freedom at 80 nm shrinks with a.
**Figures:** g0 kept OUT of figures (user); label results "me" (not "Abby", not "ours"); few words, American spelling.
**Ideas pending (user):** even-hole (bridge-centered) cavity so optical and breathing-strain maxima coincide at x = 0 (now both peak in the first
bridge, ~30 nm apart, two sites at x ≈ ±95 nm): needs a layout option + x0 PMC optics; test on the w650 finalists. 140 nm thickness: answered
qualitatively (slightly better optics, no help for mechanics, z-odd TE1 cutoff ~141 nm, harder etch) — not run.
**Localization** (selection metric, stands in for Q_m): loc = ∫_{beam, x<X_LOC}|u|² / ∫_{beam}|u|², X_LOC = 1500 nm fixed (≈ ±7 cells at a 220, ~8 at a 190;
not scaled with a); optical analogue ∫|E|² over beam+air picks the optical cavity mode. **Selection table** (`plot_cavity_sweeps.selection_table` → design_process/28_selection.png,
user 10/16): columns width (nm) | taper | a | optical Q at 619 nm | breathing (GHz) | min feat.; no localization / Q_m / "meets" columns (loc still drives the green pick).
w650/60 nm breathing mode: m_eff 166 fg (cavity_eval normalization: max |u|), x_zpf ≈ 2.3 fm.
**Known issues:** g0 in the sweeps is ~1e8 too small (normalization bug; frequencies/Q fine) — debug on a saved model when COMSOL is free.
**COMSOL gotchas:** `ewfd.freq` is real-only → `ewfd.Qfactor`; mech Q = |Im λ|/(2|Re λ|); call `m.sol(..).updateSolution()` before evaluating
operators added after a solve; mph `evaluate` OOMs on full meshes and rejects derived datasets → CutPlane + Data export; remote_runner pulls only NEW
files (and only runs/<last job>/data — use scp or make_all --pull for other runs). Python modules loaded by a running job don't see later edits.
**Lumerical on jv-adamantoise:** v252; SSH lands in TEMP profile → set `ANSYSLMD_LICENSE_FILE=<PORT>@<LICENSE_SERVER>` per process. Build-only there.

## Physics / motivation notes (discussions 2026-10-15/16)

- **Notes PDF:** `docs/scaling_and_shield_notes.pdf` (f_o/f_m scaling 1D vs 2D, why the cavity mode sits at k = π/a, η, radiation shield vs bath
  suppression with the SnV phonon-process table, paper takeaways). Generator was in a session scratchpad (not in repo).
- **User conclusion:** PnC bath suppression of SnV decoherence is not feasible (relevant phonons ~850 GHz / ~3 THz / broadband Raman). User wants a
  phononic structure that interacts with the emitter–cavity system and **an easy first measurement win**.
- **Three couplings in the device:** (1) photon–phonon g₀ = readout/drive tool (first measurement: thermal-motion sidebands); (2) **ZPL (orbital/optical)
  strain coupling, strong for SnV** (d ~ 1 PHz/strain assumed from SiV; not suppressed by Δgs) → first emitter result; (3) spin–phonon, ~10× weaker
  for SnV, possibly tunable with large static transverse strain (Guo PRX 2023 strain-enabled MW control — verify) → long-term SnV-specific angle.
- **AC (acoustic) ZPL modulation:** resolved-sideband regime (f_m 9.67 GHz ≫ Γ ≈ 35 MHz) → comb at ω₀ + n·ω_m with weights J_n(β)², β = δ/ω_m,
  δ = 2 g_e √n; no net shift; steps 9.67 GHz = 0.0124 nm (1 nm ≈ 783 GHz at 619 nm). Estimates for w650/60 nm: ε_zpf ~1–2e-8, g_e ~15 MHz,
  η ~1.5e-3. n = 1e4/1e6/1e8 → δ ≈ 3/30/300 GHz → ±0.004/0.04/0.4 nm; strain 1e-3 → ~1 THz (±1.3 nm, ceiling). Practical limit = optical
  saturation 2g₀√n ~ κ_o (n ~1e7–1e8) + heating, not Q_m. Q_m 1e6 (κ_m 9.7 kHz) mainly lowers power (n ∝ Q_m²) and self-oscillation threshold
  (~100 intracavity photons at Q_o 1e6, g₀ 100 kHz assumed). Useful points: J₁ max at β 1.8 (34 %), carrier off at β 2.4.
- **Candidate experiments (sidebands):** calibrate g_e (Bessel vs drive power); acoustic carrier switching off/onto the cavity (β 2.4); sideband-mediated
  emitter–cavity coupling; sideband excitation for laser rejection; HOM of frequency-mismatched emitters; red/blue sideband thermometry; emitter-driven
  cooling of the mode (needs C = 4(ηΩ)²/(γκ_m) > 1 → high Q_m, the shield); long-term transduction, phonon bus. Novelty of switching / HOM / cooling
  needs a literature check.
- **Platform (user):** diamond membrane bonded to a Si carrier, devices undercut (suspended, air-clad). Si is not piezoelectric. Plan: DC electrostatic
  strain tuning of the emitter (doped carrier as electrode) + optical (radiation-pressure) GHz drive. Open questions to user: cryostat T, carrier doping,
  trench depth, metal before undercut, DC/RF lines.
- **Public copy (user, 2026-10-16):** diamond-only public GitHub repo `optomechanics_copy` (Si files, journal PDFs omitted); see README there.

## Sub-Agents

Sub-agent files live in `agents/`. Each handles a specific domain.

| File | Domain | Status |
|------|--------|--------|
| `agents/comsol_specialist.md` | COMSOL/mph simulation setup, Floquet BCs, eigensolvers | Active |
| `agents/phononic_specialist.md` | Phononic crystal design, gap analysis, parameter space | Active |
| `agents/photonic_specialist.md` | Photonic crystal design, SnV at 619 nm, legume GME | Initialized (not yet used) |
| `agents/codesign_mediator.md` | Phoxonic co-design, photonic/phononic conflict resolution | Active |

---

## Key Parameters and Constants

```python
# Optical
lambda_ZPL      = 619e-9     # SnV zero-phonon line [m]
n_diamond       = 2.41       # refractive index at 619 nm
DWF             = 0.57       # Debye-Waller factor
tau_bulk        = 4.5e-9     # bulk excited-state lifetime [s]

# Mechanical (diamond isotropic approximation used in COMSOL overrides)
E_d    = 1050e9    # Young's modulus [Pa]   (from c11=1076, c12=125, c44=578 GPa)
nu_d   = 0.07      # Poisson's ratio
rho_d  = 3500.0    # density [kg/m^3]
v_LA_d = 17450     # longitudinal acoustic velocity [m/s]
v_TA_d = 12680     # transverse acoustic velocity [m/s] (sqrt(c44/rho) = sqrt(578e9/3500))

# Silicon material in unit_cell_3.mph — CONFIRMED from GUI (2026-10-13):
#   ISOTROPIC: E = 170 GPa, nu = 0.28, rho = 2329 kg/m^3, epsilon_r = 11.7, n = 3.48
#   (NOT the anisotropic C tensor used in S&P 2014 / Chan 2012)
#   G = E/(2*(1+nu)) = 170/(2*1.28) = 66.4 GPa
#   v_TA = sqrt(G/rho) = sqrt(66.4e9/2329) = 5340 m/s
#   Anisotropic reference: C44=80 GPa -> v_TA=5860 m/s  (9% faster)
#   n_Si = 3.48 is used in the OP Study (ewfd physics, Refractive Index node)

# Frequency scaling (from actual S&P 2014 PRL measurements)
# S&P 2014: Si snowflake a=500nm, r/a=0.40, w/a=0.15: gap center 8.2 GHz
#   Normalized (anisotropic): f*a/v_TA = 8.2e9*500e-9/5860 = 0.70
# Our Si: a=478nm, d=166nm, w=170nm: gap center 6.5 GHz (GUI confirmed)
#   Normalized (our isotropic): f*a/v_TA = 6.5e9*478e-9/5340 = 0.582
# Remaining discrepancy vs S&P (0.582 vs 0.70, ~17%) is geometric:
#   w/a = 0.356 in our model vs w/a = 0.15 in S&P — much wider arms = wider bridge = smaller gap

# Default simulation parameters — unit_cell_3.mph CONFIRMED from GUI (2026-10-13)
a_Si         = 478e-9    # lattice constant [m]  (Parameters node: a)
d_arm_Si     = 166e-9    # arm length [m]         (Parameters node: d) -- NOT S&P's "d" (slab thickness)
w_Si         = 170e-9    # arm width [m]          (Parameters node: w)
f_r_Si       = 25e-9     # fillet radius [m]      (Parameters node: f_r)
t_Si         = 220e-9    # slab thickness [m]     (Parameters node: t) -- this IS S&P's "d" parameter
# No separate r (hole radius) parameter exists in this model.
# The hole is defined entirely by d, w, f_r (3 rounded rectangles at 0/120/240 deg).

n_seg        = 9         # k-points per segment (27 unique k-points along Γ→M→K→Γ)
n_modes      = 10        # eigenfrequencies per k-point — DEFAULT for diamond sweeps (known geometry)
                         # diamond_mech_v1 confirmed: max 6 modes/symmetry below 50.5 GHz; N_mode=10 sufficient
                         # Use N_mode=20 only for first run of new geometry or if gap is not found
eig_shift    = 10e9      # Hz -- shift-invert center for diamond (10 GHz, well below 29 GHz gap)
# Si validation used: n_seg=15, n_modes=10, eig_shift=7e9 Hz
```

## Material Override Pattern (COMSOL Java API)

**Critical:** `propertyGroup('def').set('rho', ...)` creates only a LOCAL PROPERTY — does NOT update
the Output Property for density (which stays at 2329 kg/m³ from Si library). The physics reads
"From material" → Output Properties → so rho must also be set explicitly in the Enu group.

```python
# Correct pattern (belt + suspenders for density):
m.material('mat1').propertyGroup('def').set('rho', str(rho_diamond))    # local property
m.material('mat1').propertyGroup('Enu').set('E',   str(E_diamond))      # output property ✓
m.material('mat1').propertyGroup('Enu').set('nu',  str(nu_diamond))     # output property ✓
m.material('mat1').propertyGroup('Enu').set('rho', str(rho_diamond))    # output property ✓
m.material('mat1').label('Diamond')                                       # always rename label
```

**Always run setup_verify.py before a sweep** and confirm in GUI that:
- Basic (def) Output Properties: Density = 3500 kg/m³
- Young's modulus and Poisson's ratio (Enu) Output Properties: E = 1050e9, nu = 0.07, rho = 3500

---

## Background Reading

Papers read and analyzed as of 2026-10-12. PDFs in ~/Downloads/.

### Primary references (read in full)

- **Safavi-Naeini, Hill et al. (2014)** PRL 112, 153603 — *Two-Dimensional Phononic-Photonic Band Gap Optomechanical Crystal Cavity* (Painter group, Caltech). **Our closest Si reference.**
  - Si snowflake, parameters **(d, r, w, a) = (220, 200, 75, 500) nm** where **d = slab thickness** (NOT arm length), r = snowflake hole radius, w = arm width.
  - Bridge width b = a − 2r = **100 nm** (b/a = 0.20) — this narrow bridge is the key to the wide gap.
  - Full **anisotropic** Si elastic tensor in COMSOL: **(C11, C12, C44) = (166, 64, 80) GPa** (same confirmed in Chan 2012).
  - Phononic bandgap: **6.9–9.5 GHz** (center 8.2 GHz, width 2.6 GHz, **32% fractional**).
  - Localized mechanical mode: 9.31 GHz, g₀/2π = 220 kHz.
  - Optical pseudo-gap: 185–235 THz (1275–1620 nm), λ₀ = 1530 nm, Q = 1.8×10⁵.

- **Chan, Safavi-Naeini et al. (2012)** APL 101, 081115 — *Optimized optomechanical crystal cavity with acoustic radiation shield* (Painter group).
  - Si 1D nanobeam OMC: a=436nm, t=220nm. Mechanical mode: **5.1 GHz**, Qm = 6.8×10⁵ (10 K), g₀/2π = 1.1 MHz.
  - Uses full anisotropic Si tensor (C11=166, C12=64, C44=80 GPa), [100] crystal orientation.
  - 2D **cross phononic shield** around nanobeam: parameters (ca, ch, ct, t) = (534, 454, 134, 220) nm, complete gap centered at 5.1 GHz. Key for Stage 3 (acoustic radiation shielding).

- **Mayor, Malik et al. (2025)** Nature Comms 16, 2576 — *High photon-phonon pair generation rate in a 2D optomechanical crystal* (Safavi-Naeini group, Stanford).
  - Si 2D "b-dagger" OMC: **a = 448 nm**, w = 93 nm, r = 172 nm, t = 220 nm, fillet = 25 nm.
  - Mechanical mode: **7.4 GHz**, g₀/2π = 880 kHz (measured) / 950 kHz (simulated), Qm = 3.6×10⁴.
  - **Ground-state cooling from 3 K** (nm = 0.32); photon-phonon pairs at 147 kHz.
  - Strong coupling regime demonstrated (first for wavelength-scale Si OMC).
  - Most relevant for Stage 3 design direction — our a=448nm neighbor.

- **Kuruma, Pingault et al. (2025)** Nature Physics 21, 77 — *Controlling interactions between high-frequency phonons and single quantum systems using phononic crystals* (Lončar group, Harvard).
  - Diamond 1D **block-tether PnC**: a = 130 nm, block w×h = 96×90 nm, tether t = 22 nm, slab d = 70 nm.
  - COMSOL FEM (anisotropic diamond). Complete bandgap: **50–70 GHz** (center 59.1 GHz, width 17.3 GHz, 29%).
  - Targets **SiV orbital splitting ~50 GHz** (T₁,orbit). 18× longer T₁ demonstrated at 4.4 K.
  - Feature sizes ~20 nm — near fabrication limit. **Not the snowflake geometry.**
  - Note: SnV orbital splitting ~850 GHz — NOT addressable with any practical PnC. Kuruma's approach is SiV-specific.

- **Joe, Haas et al. (2026)** Nature 653, 378 — *Purcell-enhanced spin–phonon coupling with a single colour center* (Lončar group, Harvard). **Closest analog to our Stage 3 goal.**
  - Diamond 1D photonic crystal cavity at **737 nm (SiV ZPL)**, rectangular cross-section waveguide with eye-shaped holes.
  - Localized **12 GHz breathing mode** co-localized with optical mode at 406 THz.
  - Optical: Q = 27,000, g_so/2π = 3.6 GHz (cooperativity C_o = 31).
  - Mechanical: Qm = 34,000 (4 K), κm/2π = 350 kHz.
  - **Acoustic Purcell effect**: 10× faster spin relaxation on resonance with 12 GHz mode. g_sm/2π = 300 kHz measured, 9 MHz theory max.
  - Spin–phonon cooperativity C_T1 ≈ 10, C_T2* ≈ 0.01.
  - **Direct template for Stage 3**: scale to 619 nm (SnV ZPL) with analogous design.

- **Meesala (2019)** Harvard PhD thesis — *Quantum acoustics with diamond color centers*.
  - Ch. 6: Diamond OMC with Q ≈ 10⁵ mechanical resonances at cryogenic temperatures in diamond. Precursor work to Joe 2026.
  - Establishes SiV strain susceptibility d ≈ 100 THz/strain (4 orders of magnitude larger than NV).
  - Motivates SiV/SnV (not NV) as the target for spin-phonon coupling.

### Supporting references

- **Safavi-Naeini & Painter (2010)** Opt. Express 18, 19659: Original snowflake design paper. Simultaneous phoxonic gap in Si slab, phononic ~9.5 GHz + photonic TE at ~1550 nm.
- **Grimsditch & Ramdas (1975)** Phys. Rev. B 11, 3139: Diamond elastic constants (c11=1076, c12=125, c44=578 GPa).
- **Jasper Chan PhD thesis** (Caltech 2012): Ground-state cooling of Si nanobeam OMC. Phononic Bloch theory, COMSOL Floquet BC setup, cavity design via smooth defect modulation.
- **COMSOL Blog** "Modeling Phononic Band Gap Materials and Structures": Floquet BC formulation, complex eigensolver for k≠0.

---

## Diamond Snowflake Parameters

| Param | Si (validated, GUI) | Diamond nominal (diamond_mech_v1) | Diamond best so far (dw sweep) |
|-------|---------------------|-----------------------------------|--------------------------------|
| a | 478 nm | 300 nm | 300 nm |
| d | 166 nm | 104 nm | 124 nm (d/a=0.41) |
| w | 170 nm | 107 nm | 107 nm (w/a=0.36) |
| f_r | 25 nm | 16 nm | 16 nm |
| t | 220 nm | 140 nm | 140 nm |
| fundamental gap | 6.53–7.55 GHz | 26.6–32.0 GHz | 21.6–30.2 GHz (8.6 GHz, 33%) |

Photonic-compatible a range under exploration: diamond_a_sweep (a=150–275 nm, a/λ≈0.24–0.44 at 619 nm).
(An older table here listed a=190 nm with d/w values that did not match the GUI-confirmed Si model — removed 2026-10-13.)

Material override: use the pattern in **Material Override Pattern** above. The old `'density'/'youngsmodulus'/'poissonsratio'` names silently do nothing.

## Infra Notes

**Remote detached launch**: `Start-Process -WindowStyle Hidden` fails silently on this machine (0-byte logs). `wmic` not available (removed in newer Windows 11). **Use `Invoke-CimMethod Win32_Process Create`** — creates a process completely outside any job object, truly survives SSH disconnect. This is implemented in `remote_runner.py`'s default detach mode.

**mphglobal eigenvalue extraction**: `ev.set('solnum', 'all')` → "only constant expressions". Loop `solnum='1','2',...` and break on exception — this is the correct approach for COMSOL 6.4.

## OP Study (Optical Band Structure) — Confirmed from GUI 2026-10-13

**Study solver** (Step 1: Eigenfrequency):
- Solver: ARPACK, Around shift
- Number of eigenfrequencies: `N_mode` (same parameter as Mech)
- Shift: `f_op` Hz — confirmed 192e12 Hz (192 THz, λ=1562 nm, Si photonic bandgap region)
- Physics solved: ewfd = Eigenfrequency; solid = Stationary (solid is effectively ignored)

**Floquet BCs** (same boundary pairs as Mech Study, same kFx/kFy parameters):
- Periodic Condition 1 (ewfd): boundaries 2,5 (src) → 8,9 (dst); k_F = (kFx, kFy, 0)
- Periodic Condition 2 (ewfd): boundaries 1,4 (src) → 22,23 (dst); k_F = (kFx, kFy, 0)

**Symmetry plane BCs** (boundary 7 = z=0 midplane, boundary 12 = top face of slab domain):
- **PMC 1** (boundaries 7, 12): n×H=0 — **TE-like modes** (even z-symmetry). DEFAULT active.
  - Overrides PEC 2 on those boundaries.
- **PEC 2** (boundaries 7, 12): n×E=0 — **TM-like modes** (odd z-symmetry). Active when PMC 1 is deactivated.
- **PEC 1**: All boundaries (background). Active only on boundary 3 (all others overridden).

**Python sweep pattern** (analogous to Mech sym1/as1):
```python
ewfd = m.component('comp1').physics('ewfd')
# TE-like run (default state — PMC active):
ewfd.feature('pec2').active(False)   # ensure PEC 2 doesn't interfere
ewfd.feature('pmc1').active(True)
m.sol('sol???').runAll()             # sol tag TBD — run discover_op_study.py
freqs = mphglobal(m, 'ewfd.freq', 'dset???')  # dset tag TBD

# TM-like run:
ewfd.feature('pmc1').active(False)
ewfd.feature('pec2').active(True)
m.sol('sol???').runAll()
freqs = mphglobal(m, 'ewfd.freq', 'dset???')
```

**Confirmed tags (discover_op_study.py, 2026-10-13):**
- f_op = 192e12 Hz = 192 THz (λ = 1562 nm — Si photonic bandgap region)
- Mech Study: std1, solver sol1, dataset dset1, expression `solid.freq`
- OP Study: std2, solver sol2, dataset dset2, expression `ewfd.freq`
- dset3 = Mech Study/Parametric Solutions 1 (GUI parametric sweep results — not used by Python)
- sol3-sol33: previous GUI parametric sweep solutions stored in model (not used by Python sweep)
- ewfd feature tags: pec1, pec2, pmc1, pc1, pc2, wee1, wee2, init1, dcont1
- Python TE run: `ewfd.feature('pmc1').active(True)`, `ewfd.feature('pec2').active(False)`
- Python TM run: `ewfd.feature('pmc1').active(False)`, `ewfd.feature('pec2').active(True)`
- OP Study has NO parametric sweep (unlike Mech Study). Python must loop k-points manually.
  GUI validation uses spot-checks at Gamma, M, K only (6 runs: 3 k-pts x 2 symmetry classes).

## Mech Mesh (mesh1) — read from unit_cell_3.mph, 2026-10-14

- Size (default): hmax 82.5 nm, hmin 6 nm. Free Triangular (periodic source faces) Size1 hmax = **t/8**; Copy Face 1/2 → Floquet destinations; Free Tetrahedral Size1 hmax = **t/7.5** (18.7 nm at t=140). OP Mesh (mesh2) adds t_air/10 in air, t/6 in slab. Mech Study (std1) uses mesh1.
- Sizes are **absolute (tied to t)**, so element count ∝ cell area: 20k (a=300), 50k (600), 118k (1000) → solve time 12 / 14 / 33 s at N_mode=12.
- Convergence at a=1000 (Γ + M, sym1+as1, N_mode=12) vs original: **tet t/5**: median 2–9e-5, max 4.7e-4 on the 30 nm-bridge cell (one 125 MHz outlier on the easy cell, likely window-edge mode swap); 4× faster. t/3.75: max 1.6e-3 on the thin cell. Override per plan with `sweep_plan.py --mesh-tet t/5 --mesh-tri t/5.33`. Scripts: runs/diamond_a_large/diag_mesh*.py.

## Cell + hole geometry (read from unit_cell_3.mph via mph, 2026-10-14 — ground truth)

- **Hole:** Rectangle r1 `lx=w, ly=d, base=center, pos=(0, d/2)` → arm from the hole center (origin) to distance d, width w, pointing up. Rotate ±120° about (0,0) → arms 90°/210°/330°. Union → Fillet f_r on all vertices.
- **Cell:** Polygon pol1 rhombus `(a/2, −a/(2√3)), (−a/2, −a/(2√3)), (−a, a/√3), (0, a/√3)` → **a1=(a,0), a2=(−a/2, a√3/2), leans LEFT**. Hole at the **centroid of the lower triangle**, not the rhombus center; each arm points at a cell corner.
- **Cell offset:** mov1 shifts the cell by a **fixed (50 nm, −50/√3 nm)** — tuned for Si a=478, not scaled with a. Present in **both wp1 (slab) and wp2 (air block, t_air=1.5 µm)**; always move both together.
- **Feasibility:** the model subtracts one hole, so the hole must lie inside the shifted rhombus. Otherwise: mesh "Copy Face 1 … Disconnected source not allowed" (topology 3–4 domains instead of 2 domains / 30 boundaries). `scripts/cell_placement.py` predicts this (0/54 mismatches vs the a-sweep); per-combo shifts restore feasibility and are physics-invariant (validated: identical gap, a200_da35_wa28).
- Default shift limit for the up-arm: d < a/√3 − 28.9 nm. **d/a=0.48 with w/a=0.43 cannot fit any rhombus placement** (bridges to neighbouring holes 0–5 nm).
- `archive/misc/sim_schematic.png` draws a right-leaning rhombus with a centered hole — same lattice but NOT the model's cell; don't use as drawing reference.

## Known Differences from S&P 2014 in unit_cell_3.mph (all confirmed from GUI 2026-10-13)

1. **No separate hole radius r** — S&P 2014 uses circular-tip arms with radius r (b = a−2r = 100 nm).
   Our model has no r parameter. The hole is 3 rounded rectangles (d×w with f_r corner fillet).
   w/a = 0.356 in our model vs w/a = 0.15 in S&P — much wider arms, less phonon confinement → smaller gap.

2. **Isotropic Si vs anisotropic** — Our model: E=170 GPa, ν=0.28 → v_TA=5340 m/s.
   S&P 2014 / Chan 2012: anisotropic C44=80 GPa → v_TA=5860 m/s.
   Effect: ~9% lower frequencies in our model vs anisotropic reference.

Gap discrepancy breakdown (normalized f·a/v_TA): 0.582 ours vs 0.70 S&P.
Residual ~17% after correcting for material is purely geometric (w/a difference).

---

## Design Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-10-08 | Project created | Starting point for SnV phoxonic cavity design |
| 2026-10-08 | 2D slab PCC geometry (not 1D nanobeam) | User decision |
| 2026-10-09 | Snowflake unit cell (unit_cell_3.mph) | From Safavi-Naeini & Painter 2010; simultaneous phoxonic gap demonstrated in Si |
| 2026-10-09 | Rhombus primitive cell | (CORRECTED 2026-10-14 from the .mph: a1=(a,0), a2=(−a/2,a√3/2), hole at lower-triangle centroid, cell offset by fixed mov1 — see Cell + hole geometry.) Originally logged as: a1=(a,0), a2=(a/2,a√3/2): 1 hole/cell at centroid. Floquet BCs on bottom/top (a1) and slanted (a2) faces. kFx/kFy Cartesian. k-path Γ→M→K→Γ in hexagonal BZ. CORRECTION 2026-10-13: was mistakenly described as rectangular 2-atom supercell — it is the rhombus primitive cell, confirmed from GUI (Polygon 1 in work plane geometry, reference schematic archive/misc/sim_schematic.png). |
| 2026-10-12 | Si pipeline validated | gap_cen=6.50 GHz, width=1.09 GHz (17%) confirmed; mphglobal solnum loop working |
| 2026-10-12 | Stage 3 template = Joe 2026 (Nature) | Diamond OMC at 737nm + 12 GHz mode + SiV; scale to 619nm for SnV |
| 2026-10-12 | SnV orbital decoherence (850 GHz) not targeted by PnC | PnC targets ~10-15 GHz spin-phonon coupling (acoustic Purcell), not 850 GHz orbital |
| 2026-10-13 | Si material confirmed isotropic from GUI | mat1: E=170 GPa, ν=0.28, ρ=2329, n=3.48. NOT anisotropic C tensor. v_TA=5340 m/s. |
| 2026-10-13 | Project reorganized into runs/ layout | Cleaner: each run has its own sweep.py, data/, figures/, schematic. Utilities in scripts/. |
| 2026-10-13 | diamond_mech_v1: a=300nm, N_mode=20 | a=300nm chosen for photonic compatibility (a/λ=0.307). N_mode=10 insufficient — modes max at 21 GHz, gap at 23 GHz not visible. N_mode=20 required to bracket gap. |
| 2026-10-13 | Material override: rho in Enu group | propertyGroup('def').set('rho',...) creates Local Property only. Add rho to Enu group too. Verify via Equation View (not Settings panel — that shows "Local Property" for everything set this way). |
| 2026-10-13 | Track band 6–7 gap, not "first gap > 0.5 GHz" | dw sweep: threshold detector jumped to an unrelated 51 GHz gap when the fundamental narrowed to 0.1 GHz (d=85, w=128). Same gap pair across combos keeps heatmaps comparable. |
| 2026-10-13 | diamond_a_sweep: mech only, ratios scaled with a, t fixed | Explore photonic-compatible periods overnight; optical deferred until diamond OP setup confirmed in GUI. User: never stop an overnight sweep early unless explicitly told. |
| 2026-10-13 | BZ schematic: K is a hexagon vertex on kx axis | With a1=(a,0), K=(4π/3a,0) is a vertex and M=(π/a, π/(√3a)) an edge midpoint. Earlier diamond schematic had the hexagon rotated 30°. |
| 2026-10-14 | Cell placement is a free numerical choice | Model subtracts one hole from a rhombus shifted by a fixed mov1 offset; long arms/small a cross the boundary → mesh failure. Per-combo shift of BOTH wp1 and wp2 mov1 restores periodic geometry. Validated: same combo, shifted cell → max 4.1 MHz deviation (1e-4 rel), identical gap. |
| 2026-10-14 | d/a=0.48 & w/a=0.43 dropped from a-sweep | Hole cannot fit any rhombus placement; bridges to neighbouring holes 0–5 nm (unfabricable, would need a hexagonal/Wigner–Seitz cell to model). |
| 2026-10-14 | Gaps only counted below the complete-spectrum ceiling | With N_mode per symmetry class, the spectrum is complete only below min over k and class of the highest computed mode. A 103 GHz "gap" was a truncation artifact. |
| 2026-10-14 | Schematics regenerated from .mph geometry | Old schematics drew a right-leaning rhombus with a centered hole; actual pol1 leans left, hole at lower-triangle centroid, cell offset by mov1. Shared scripts/schematic.py. |
| 2026-10-13 | Equation View is ground truth for material | Settings panel "Output Properties" vs "Local Properties" distinction is a display artifact. Equation View shows what the solver actually uses. E, nu, rho all confirmed at diamond values via Equation View. |
| 2026-10-14 | 1D nanobeam follows Oh 2026 (quasi-gap, not complete gap) | User decision; shield gives the complete gap later |
| 2026-10-14 | Full cavity = Chan thesis taper, start values measured from Oh Fig. 1(b) | Oh's text gives only the mirror cell; supplement points to Chan thesis |
| 2026-10-14 | Diamond photoelastic p = (−0.25, 0.043, −0.172) | Burek 2016 / Lang 2009; Ramachandran 1947 values superseded |
| 2026-10-14 | Oh cavity mode = first breathing mode (6.506 GHz) | User: single central bulge like Oh Fig. 1(c) |
| 2026-10-14 | 619 nm cavity: sweep (a, d) before the rest of the taper | User: d also tunes the resonance |
| 2026-10-14 | Min feature 60 nm now, 80 nm track in parallel | User; best device per min feature (2 total) |
| 2026-10-14 | Lumerical: build/write only, run after COMSOL with authorization | User: avoid compute contention |
| 2026-10-15 | Widen the beam (w 650/600) instead of more taper shapes | w550 breathing floor ~10.9 GHz for every fabricable taper; user OK as long as optical Q stays high (it does) |
| 2026-10-15 | 80 nm uses cell B only; w550 80 nm chain stopped | cell A had no taper freedom and weakly localized breathing modes |
| 2026-10-15 | Breathing ID adds sidewall amplitude ratio S ≥ 0.7 | in-phase check B is amplitude-blind; a hole-centered hybrid passed it at w650 d0.13 |
| 2026-10-15 | Best 60 nm device: w650 d0.10 ξ6 χ4 a190.3 (Q 1.8e7, 9.67 GHz) | clean breathing mode; higher-Q d0.13 design is a hybrid |
| 2026-10-15 | Queue w700 / 80 nm | w650/80 nm stuck at 10.53 GHz |
| 2026-10-15 | Lumerical runs on the old PC DESKTOP-BBQLCD3 | user: run the replicas there; no contention with COMSOL |
| 2026-10-15 | Lumerical files at C:\Users\abby\lumerical; .lsf outputs portable (basedir/pwd, name prefix) | user moved the folder; scripts must run on any PC |
