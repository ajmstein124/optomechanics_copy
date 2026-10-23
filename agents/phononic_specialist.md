# Agent: Phononic Crystal Specialist

**Domain:** Phononic crystal design, bandgap analysis, and parameter space navigation for 2D slab geometries.  
**When to use:** Questions about phononic gap formation, parameter choices (a, d/a, r/a), bandgap analysis, frequency scaling, geometry trade-offs, and upgrade path from circles to snowflake.

---

## Current Geometry: 3-Arm Snowflake (unit_cell_3.mph)

**Lattice:** Triangular, simulated as the **rhombus primitive cell** a1=(a,0), a2=(−a/2, a√3/2) (leans left), ONE hole at the centroid of the rhombus's lower triangle, cell offset by mov1. NOT a rectangular supercell. Full read-from-.mph geometry: comsol_specialist.md → "Cell + hole geometry".  
**Unit cell:** The hole is defined by 3 rounded rectangles at 0°/120°/240° — arm length d, arm width w, fillet radius f_r. **3 arms, NOT 6** (do not confuse with 6-arm snowflake in some literature).  
**No separate hole radius r** — the hole geometry is fully determined by (d, w, f_r).

**Validated Si parameters (GUI-confirmed 2026-10-13):**
- a=478nm, d=166nm, w=170nm, f_r=25nm, t=220nm
- Gap: 6.534–7.551 GHz (center 7.042 GHz, 14.5% fractional)
- Normalized: f·a/v_TA = 0.582 (v_TA=5340 m/s, isotropic Si)

**Diamond mech v1 parameters:**
- a=300nm, d=104nm, w=107nm, f_r=16nm, t=140nm (same d/a, w/a, f_r/a ratios as Si)
- Material: E=1050 GPa, nu=0.07, rho=3500 kg/m³, v_TA=11840 m/s
- Predicted gap center from Si scaling: 23.0 GHz. **Actual: 29.3 GHz** (26.6–32.0 GHz). Si→diamond scaling of the normalized gap position does not hold at these ratios (0.742 vs 0.582); don't use the table below for prediction — use the measured diamond results.

**diamond_dw_sweep results (a=300 nm, t=140, f_r=16, band 6–7 gap):**

| d \ w (nm) | 85 | 107 | 128 |
|---|---|---|---|
| 124 | 26.1 / 7.95 (30%) | **25.9 / 8.61 (33%)** | 24.8 / 7.78 (31%) |
| 104 | 29.1 / 5.59 (19%) | 29.3 / 5.38 (18%) | 28.6 / 2.65 (9%) |
| 85  | 31.9 / 3.16 (10%) | 31.7 / 2.09 (7%) | 31.3 / 0.10* |

(center GHz / width GHz; * = at 21-k-point resolution, effectively closed)
- Longer arms d: gap widens strongly and moves down. Best at grid edge → push d/a above 0.41.
- Width w: weak effect at d=124; at shorter d, wider arms shrink the gap.

**Gap tracking:** the fundamental gap is between sorted bands 6 and 7 (sym+antisym combined) in all diamond combos so far. Always report that pair; a "first gap > threshold" detector can silently jump to a higher-order gap.

---

## diamond_a_sweep results (2026-10-14; a=150-275 nm, t=140, f_r=16 nm, band 6-7 gap)

48/54 combos run (6 infeasible: d/a=0.48 & w/a=0.43). Figures: runs/diamond_a_sweep/figures/.

**Trends (fixed ratios, t fixed):**
- **a up -> center down ~1/a.** f·a ≈ 8900 (d/a 0.35), ≈ 8000 (0.41), ≈ 6500-7400 GHz·nm (0.48). At d/a 0.41 f·a drifts DOWN slightly with a; at 0.48 it drifts UP (fillet effect) → do not extrapolate 1/a blindly.
- **d/a up (longer arms) -> center DOWN and gap MUCH wider:** fractional width 10-22% (0.35) → 28-34% (0.41) → 44-73% (0.48).
- **w/a up (wider arms) -> center slightly down (~5%), gap narrower** (e.g. 33% → 28% at d/a 0.41).
- Fractional width ~flat vs a for a ≥ 200 at d/a 0.41; drops at small a (fixed 16 nm fillet + 140 nm slab no longer scale).

**Fabrication (user min feature 30 nm):** the narrowest slab bridge (where three holes' arm tips converge) is the limiting feature. ALL d/a=0.48 results (the 60-73% gaps) have 9-20 nm bridges → not fabricable. d/a=0.41 with w/a=0.43 at a ≤ 225 (23-29 nm) and w/a=0.36 at a=150 (28 nm) also fail. Wide gap ⇔ thin bridges is an intrinsic trade-off; at fixed ratios bridges scale ∝ a, so large-a designs are easier to fabricate.

**Best fabricable so far (≥30 nm):** d/a=0.41, w/a=0.28-0.36: ~33% fractional at a=200-275 (e.g. a=250: 27.2-37.8 GHz, bridge ~39-49 nm).

**User goal (2026-10-14): gap center ≤ 10 GHz** → needs a ≈ 650-850 nm (thin-slab regime t/a ≈ 0.17-0.2, gap survival unknown). Next sweep: diamond_a_large (a=400-1000, d/a {0.41,0.45,0.48} × w/a {0.22,0.26,0.30}, N_mode=20, 30 nm check → 56/63 run).

## Frequency Scaling

Gap formation mechanism: **Bragg scattering**. The gap opens when the acoustic wavelength is comparable to the lattice period.

**Calibrated from validated Si simulation (2026-10-13):**
```
f_gap = 0.582 × v_TA / a
```
where 0.582 is the normalized gap position for our 3-arm snowflake geometry (d/a=0.347, w/a=0.356, f_r/a=0.052). This factor is geometry-specific — wider arms than S&P 2014 (w/a=0.15) shift it down from 0.70.

**Diamond velocities** (isotropic, E=1050 GPa, nu=0.07, rho=3500):
```
v_TA = sqrt(E / (2*rho*(1+nu))) = sqrt(491e9/3500) = 11,840 m/s
v_LA = sqrt(E*(1-nu) / (rho*(1+nu)*(1-2*nu)))      = 17,450 m/s
```

**Diamond gap center by lattice constant (same d/a, w/a ratios):**

| a (nm) | f_gap (GHz) |
|--------|-------------|
| 190    | 36.2        |
| 300    | **23.0** ← diamond_mech_v1 |
| 400    | 17.2        |
| 500    | 13.8        |

**Si gap center by lattice constant (v_TA=5340 m/s, same geometry):**

| a (nm) | f_gap (GHz) |
|--------|-------------|
| 300    | 10.4        |
| 478    | **6.5** ← validated |

## N_mode and eigensolver shift

- Rule: set shift f_mech to 40–50% of expected gap center. Set N_mode large enough that the highest found mode is >20% above gap center.
- **Default for diamond sweeps (same geometry): N_mode=10.** Confirmed from diamond_mech_v1 data: only 6 modes per symmetry class appear below 50.5 GHz (top of the highest detected gap). N_mode=10 provides comfortable margin.
- **Use N_mode=20 when:** gap location is unknown (first run of a new geometry or material), predicted gap is not found despite sweeping, or you suspect modes are being missed.
- **diamond_mech_v1 calibration (a=300nm, same d/a, w/a, f_r/a, t/a as Si):** Gap structure confirmed as 29.3 GHz (5.4 GHz wide), 34.6 GHz (1.1 GHz), 49.0 GHz (2.8 GHz). N_mode=20 was used to find this; N_mode=10 is sufficient for future sweeps of the same geometry.
- **Frequency scaling test to verify material**: Run N_mode=10 at any k-path. Max mode frequency with diamond (rho=3500) should be ~21 GHz; with Si density (rho=2329) would be ~26 GHz.

---

## BZ Path (hexagonal BZ of the rhombus primitive cell)

```
Gamma (0,0) -> M (pi/a, pi/(a*sqrt(3))) -> K (4*pi/(3a), 0) -> Gamma
```

With a1=(a,0): K=(4π/3a, 0) is a hexagon **vertex** on the kx axis; M is an **edge midpoint** at 30°. kFx/kFy are Cartesian and go straight into the COMSOL Floquet BCs.

Caveat: the 3-arm snowflake has C3v (not C6v) symmetry, so Γ–M–K–Γ is not guaranteed to cover the full irreducible zone. Gaps found here are "complete along the path"; a 2D k-scan would be needed to prove full completeness.

**k-points per segment:** n_seg=7 (parameter sweeps, 21 unique k), 9 (diamond_mech_v1, 27 k), 15 (Si validation).

---

## Parameter Sensitivity

> The d/a and r/a notes below are from the archived circular-hole geometry (d = slab thickness there). For the snowflake, d = arm length, w = arm width, t = slab thickness — see diamond_dw_sweep results above.

**a (lattice constant):** Primary frequency knob. f_gap ~ 1/a at fixed ratios. Increase a to lower the gap frequency. diamond_a_sweep (running 2026-10-13) maps a=150–275 nm.

**d/a (slab thickness):**
- Too thin (< ~0.2): modes not well-confined, no clear gap.
- Optimal: 0.30–0.55.
- Default 0.44 (Safavi-Naeini & Painter reference value).
- Does NOT affect the gap center frequency estimate — only affects whether a gap opens and how wide it is.
- Note: d/a is also the dominant photonic parameter — changing it shifts the photonic TE gap window.

**r/a (hole radius):**
- Too small (< ~0.10): insufficient scattering, no gap.
- Optimal for circular holes in triangular lattice: 0.30–0.45.
- Upper limit: r/a = 0.5 → adjacent holes touch.
- Default 0.35 → fill fraction ~44%.
- Fill fraction: `fill% = 2*pi*(r/a)^2/sqrt(3)*100`

---

## Bandgap Detection

```python
def find_bandgaps(freqs, tol=0.02):
    # freqs: (n_k, n_modes) array in GHz
    gaps = []
    for b in range(freqs.shape[1] - 1):
        f_top = np.nanmax(freqs[:, b])
        f_bot = np.nanmin(freqs[:, b + 1])
        if f_bot > f_top:
            fc = 0.5 * (f_top + f_bot)
            gf = (f_bot - f_top) / fc
            if gf > tol:
                gaps.append((f_top, f_bot, gf))
    return gaps  # list of (f_lo, f_hi, fractional_gap)
```

A gap is "complete" if it spans ALL k-points in the IBZ path. The tol=0.02 (2%) filter removes numerical noise and near-zero crossings.

---

## Sweep Strategy

**Current (snowflake):** (a, d/a, w/a) with t, f_r fixed. diamond_dw_sweep (a=300, done) → diamond_a_sweep (a=150–275, 3×3 ratios each, running). Scale f_mech ∝ 1/a so N_mode=10 brackets the gap.

**Archived (circular holes):** Parameter space: (a, d/a, r/a).

1. Fix a=500 nm, sweep r/a in [0.30, 0.35, 0.40, 0.45] at d/a=0.44 to find which r/a opens a gap.
2. Once gap is confirmed, sweep d/a in [0.35, 0.44, 0.50, 0.55] to optimize gap width.
3. Scale a to hit the target frequency.

Use `scripts/phononic_sweep.py` (builds COMSOL model once, updates parameters per combo).  
Results: `sweep_results.csv` + per-combo `.npz` files.

---

## Upgrade Path: Snowflake Geometry

Safavi-Naeini & Painter (2010) snowflake parameters (Si, 1550 nm photonic gap):
- d/a = 0.44, r/a ~ 0.35 (snowflake arm parameters r_s, t_s, d/a)
- Simultaneous phononic gap ~9.5 GHz + photonic TE gap at ~1550 nm
- Fractional phononic gap width ~30%

For diamond at 619 nm:
- Need to re-optimize snowflake arm parameters for the diamond/619 nm system
- Expected: wider fractional gap than circles (snowflake has stronger scattering per site)
- The simultaneous phoxonic gap at 619 nm in diamond is the research target

**What changes in the code:** Replace the 5-Cylinder geometry with 6 rotated arm shapes per hole site in `phononic_band.py`. Everything else (supercell, BCs, study, k-path) stays the same.

---

## References

- Safavi-Naeini & Painter (2010) Opt. Express 18, 19659: snowflake crystal, simultaneous phoxonic gap, parameters
- Chan thesis (Caltech 2012) Sec. 3.1.4: frequency scaling, Bragg mechanism
- COMSOL blog "Modeling Phononic Band Gap Materials and Structures": Bragg vs local resonance mechanism, IBZ path


## 1D nanobeam full cavity (2026-10-14)
See docs/cavity_design_method.md and CLAUDE.md "1D nanobeam OMC track". Taper (Chan thesis): a(x)/a_m = 1 - d(2y^3-3y^2+1),
hole area 1-s = chi(1-a), aspect r = a^xi. Oh start values d 0.18, M 10, eta 1, xi 6, chi 3.5, 10 mirror cells/side.
Diamond photoelastic (p11,p12,p44) = (-0.25, 0.043, -0.172). Cavity optical mode from X dielectric band; mech from Y+Z+ band at Gamma.


## 1D full-cavity status (2026-10-14, late)
Pipeline: scripts/build_cavity_model.py, cavity_taper.py, cavity_eval.py, cavity_pipeline.py. Oh cavity reproduced
(runs/cavity_oh2026). 619 nm (a,d) map: 619 nm line found (a 195-214 nm for d .10-.22), Q up to 4e7 at d .10, breathing
stuck ~10.7-11.8 GHz -> taper-shape (xi, chi) sweeps queued at 60 nm and 80 nm (cells A/B). Min feature 60 nm (+80 nm track).
See CLAUDE.md "1D nanobeam OMC track" and docs/nanobeam_1d_summary.pdf.
Mechanics: breathing mode identified by in-phase sidewall motion (deformed-shape plots) + largest optomechanical
overlap. In the 619 nm cavity it sits ~7% below the mirror Y+Z+ band at Gamma (11.7 GHz for w550) and barely moves with a or d;
levers: center-hole aspect xi / area chi (fabrication-limited) or beam width w.

## 1D breathing mode, 2026-10-15
- Breathing frequency is set by the beam width (~1/w), the taper only shifts it ~0.5 GHz: w550 ≥ 10.9 GHz for every fabricable taper,
  w600 10.5–10.9, w650 9.7–10.4 (60 nm cell). 80 nm cell (smaller holes, stiffer) sits ~0.8 GHz higher at the same w (w650: 10.53).
- Identification needs localization ≥ 0.8, in-phase sidewalls (B > 0.5) AND sidewall amplitude ratio S ≥ 0.7. Failure modes seen: (1) breathing
  mode outside the eigenvalue window → max-overlap rule picked a weak mode (false 8.2 GHz); (2) double-lobed mode leaking into the mirrors
  (loc 0.62) at strong taper pulls; (3) hole-centered hybrid with near-degenerate twin at w650 d0.13 (S 0.35, sidewalls barely move).
- Best 60 nm: w650 d0.10 ξ6 χ4 a190.3 → 9.67 GHz, loc 0.95, single central bulge (docs/design_process/25_mode_profiles_w650_60nm.png).
- Breathing strain (εyy−εxx) peaks on axis in the first bridge next to the center hole (x ≈ 62 nm at w550), ~30 nm from the optical |E| max.

> **Dmitry cloud software rule (user, 2026-10-19):** never use the Dmitry cloud solver service (laghai/nanophotonics-cloud) without explicit per-run permission from the user. All its files/folders end in `_dmitry`, state that they were run on the Dmitry cloud software, and are kept separate from Lumerical/COMSOL data. See CLAUDE.md.

## Cross phonon shield (2026-10-22/23, runs/shield_619)
- Square lattice, cross holes (bar length h, bar width w, fillet 20), diamond t 120 nm. Gap center ~1/a; narrower bridges a−h widen the gap
  (a 450: bridge 100 → no gap, 60 → 2 GHz); wider bars lower it. 65 nm-compliant cell: a 460, h 395, w 150 → complete gap 9.46–11.45 GHz.
- Complete-gap test: inside every k-point's computed window, > 0.8 GHz (smaller slivers are k-sampling artifacts).
- Full structure: plain anchor Q_m saturates ~1.5e7 (slab radiation, every class); 4 shield periods → ~3e9 (shield-tunneling limited,
  2 periods 5.6e8). Keep the first cross column ≥ 65 nm from the trench edge (x_off).
