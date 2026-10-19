# Agent: Photonic Crystal Specialist

**Domain:** Photonic crystal cavity design for SnV at 619 nm in diamond.  
**Status:** Initialized but not yet active. Will be used when photonic simulation work begins.  
**When to use:** Questions about photonic bandgap, cavity mode design (Q/V), TE/TM gap requirements, legume GME simulation setup, or photonic crystal geometry choices for 619 nm.

---

## Target System

- **Emitter:** Tin vacancy (SnV) center in diamond
- **ZPL:** ~619 nm (vacuum)
- **Host material:** Diamond, n = 2.41 at 619 nm
- **Goal:** Photonic crystal cavity with high Purcell factor at 619 nm, co-designed with phononic shield

---

## Photonic Bandgap (Triangular Lattice, TE Modes)

For a triangular lattice of circular holes in a diamond slab, the TE photonic bandgap requires:

```
a / lambda ~ 0.25 to 0.38   (at d/a ~ 0.44, estimated)
```

For lambda = 619 nm:
```
a ~ 155 to 235 nm
```

This range is where the first TE bandgap opens. The exact bounds depend on r/a and d/a; a full photonic bandstructure sweep via legume is needed to map the gap precisely.

**Snowflake geometry** (Safavi-Naeini & Painter 2010) has a TE photonic bandgap at a/lambda ~ 0.42 (for Si at 1550 nm). The equivalent diamond/619 nm value needs to be computed.

---

## Figure of Merit

Purcell factor:
```
F_P = (3 / 4*pi^2) * (lambda/n)^3 * (Q/V)
```

where V is the mode volume in units of (lambda/n)^3.

For SnV cavity QED:
- Target Q ~ 10^5 to 10^6
- Target V ~ 1 (lambda/n)^3
- F_P ~ 10^4 to 10^5

Cooperativity: C = g^2 / (kappa * gamma), where g ~ sqrt(1/V), kappa ~ omega/Q, gamma = 1/tau_bulk.

---

## Simulation Tool: legume (GME)

The `pccsim` package (Documents/pccsim) uses legume for GME (Guided Mode Expansion) of 2D PCC slabs. It is the primary tool for photonic bandgap and cavity mode simulation.

**Key settings for 2D triangular lattice:**
- `gmax = 2` (truncation in reciprocal space; larger = more accurate but slower)
- `truncate_g = 'tbt'` (truncation type)
- k=0 only for cavity modes (heterostructure PCC)

See `Documents/pccsim/src/pccsim/` for the existing implementation.

---

## COMSOL OP study (unit_cell_3.mph) — option alongside legume

The model already has an optical study (std2/sol2/dset2, `ewfd.freq`), validated for Si at Γ/M/K (TE via pmc1, TM via pec2). For diamond at 619 nm it would need: refractive index → 2.41 (node/property not yet GUI-confirmed — check before scripting), f_op → ~484 THz, and probably an OP mesh check at the shorter wavelength. Same kFx/kFy and a parameters as the mech study, so a photonic a-sweep can reuse the diamond_a_sweep geometry grid directly.

## Constraints carried over from the phononic work (2026-10-14)

- **Minimum feature 30 nm** (slab bridges, hole widths) — user fab limit; scripts/sweep_plan.py enforces it for snowflake sweeps.
- Fabricable snowflakes in the photonic window (a=200-275 nm): d/a ≈ 0.41, w/a ≈ 0.28-0.36 (bridges ~34-53 nm), d/a=0.35 any w/a. d/a=0.48 is NOT fabricable at these a.
- Snowflake cell geometry ground truth: CLAUDE.md "Cell + hole geometry" (rhombus leans left, hole at lower-triangle centroid, mov1 shift).

## Photonic Simulation — Pending Tasks

1. Run photonic bandstructure for triangular lattice of holes in diamond at 619 nm via legume
2. Map TE/TM gap as function of (r/a, d/a) — specifically find a/lambda range for TE gap
3. Compare circular holes vs snowflake: does snowflake open a larger TE gap at the same fill fraction?
   - Priority: snowflake TE gap vs a for the diamond_a_sweep grid (a=150–275 nm, d/a 0.35–0.48, w/a 0.28–0.43, t=140 nm) so phononic and photonic maps line up.
4. Determine cavity mode Q and V for a point-defect cavity in the triangular lattice
5. Feed photonic-compatible a range to the co-design mediator

---

## References

- Safavi-Naeini & Painter (2010) Opt. Express 18, 19659: snowflake crystal, photonic TE gap at 1550 nm in Si
- Johnson & Joannopoulos (2001) Opt. Express 8, 173: MPB photonic band structure
- legume documentation (github.com/fancompute/legume): GME for 2D PCC slabs
- `Documents/pccsim/`: existing legume-based simulation package for heterostructure PCCs


## 1D nanobeam full cavity (2026-10-14)
See docs/cavity_design_method.md and CLAUDE.md "1D nanobeam OMC track". Taper (Chan thesis): a(x)/a_m = 1 - d(2y^3-3y^2+1),
hole area 1-s = chi(1-a), aspect r = a^xi. Oh start values d 0.18, M 10, eta 1, xi 6, chi 3.5, 10 mirror cells/side.
Diamond photoelastic (p11,p12,p44) = (-0.25, 0.043, -0.172). Cavity optical mode from X dielectric band; mech from Y+Z+ band at Gamma.


## 1D full-cavity status (2026-10-14, late)
Pipeline: scripts/build_cavity_model.py, cavity_taper.py, cavity_eval.py, cavity_pipeline.py. Oh cavity reproduced
(runs/cavity_oh2026). 619 nm (a,d) map: 619 nm line found (a 195-214 nm for d .10-.22), Q up to 4e7 at d .10, breathing
stuck ~10.7-11.8 GHz -> taper-shape (xi, chi) sweeps queued at 60 nm and 80 nm (cells A/B). Min feature 60 nm (+80 nm track).
See CLAUDE.md "1D nanobeam OMC track" and docs/nanobeam_1d_summary.pdf.
Optics: cavity TE mode Q_o 1e5 (Oh repro); 619 nm cavity Q 8e3-4e7 depending on taper depth d (shallower = higher Q).
Spurious Q~8 localized modes exist in the PML model -> cavity mode = most localized with Q > 1e3. Lumerical replicas via
Qanalysis (runs/cavity_619/lumerical/make_lsf.py), build-only until user authorizes runs.

## 1D cavity optics, 2026-10-15
- Widening the beam to w 650 does NOT reduce the cavity Q (3e7 at d .13, 1.8e7 for the best device); the resonance needs a smaller period
  (a ≈ 190 at d .10 for w650 vs 195 for w550). Single-mode check pending: deliverables compute mirror-cell bands in both y-parities
  (y0 PEC cavity family, y0 PMC higher-order family); w700 mirror check runs first in run_w700.py.
- Optical |E| max of the (odd-about-center-hole) cavity mode sits on axis in the first bridges (x ≈ ±95 nm); even-hole (bridge-centered) variant
  would put it at x = 0 with x0 PMC (user idea, not built).
- Lumerical vs COMSOL, best 60 nm device: 618.89 vs 619.49 nm (−0.1 %); Lumerical Q 1.3e6 at 1.5 ps is a lower bound (photon lifetime ~10 ns).
  .lsf defaults: use_symmetry 1 (x/y anti-symmetric, z symmetric), sim_time 1.5 ps, Qanalysis probes inside the simulated octant.
- 140 nm thickness (user question): slightly better confinement/Q, z-odd TE1 slab cutoff ≈ 141 nm at 619 nm, no help for the breathing frequency.

> **Dmitry cloud software rule (user, 2026-10-19):** never use the Dmitry cloud solver service (laghai/nanophotonics-cloud) without explicit per-run permission from the user. All its files/folders end in `_dmitry`, state that they were run on the Dmitry cloud software, and are kept separate from Lumerical/COMSOL data. See CLAUDE.md.
