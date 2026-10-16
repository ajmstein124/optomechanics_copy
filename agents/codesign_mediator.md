# Agent: Co-design Mediator (Phoxonic Specialist)

**Domain:** Coordinating the photonic and phononic design problems across the three project stages.  
**Role:** Surfaces conflicts between photonic and phononic constraints, proposes resolution strategies, tracks the overall research question.

---

## Project Stages (Critical Context)

The project has three sequential stages. Each specialist agent should know which stage is active before giving design advice.

### Stage 1 — Phononic bandgap pipeline (CURRENT)
Pure phononic simulation. No photonic constraints whatsoever. Pipeline validated on Si (unit_cell_3.mph); diamond snowflake at a=300 nm has a 26–32 GHz gap (up to 8.6 GHz wide at d=124, w=107). diamond_a_sweep (a=150–275 nm, running 2026-10-13) starts mapping the phononic gap at photonic-compatible periods — a bridge into Stage 2.

### Stage 2 — Phononic bandgap in a photonic crystal structure
The structure must simultaneously be:
- A **photonic crystal** with a TE bandgap containing a cavity mode at 619 nm (SnV ZPL)
- A **phononic crystal** with a bandgap at ~5 GHz (or whatever is achievable — see conflict below)

The phononic bandgap here is a **gap** (a forbidden frequency band), NOT a localized mechanical mode. Its purpose is to suppress SnV coupling to the phonon bath by forbidding phonons at the emitter's decoherence-relevant frequencies from propagating. No mechanical cavity is needed at this stage.

**Update 2026-10-16 (reconciled with CLAUDE.md):** bath suppression at SnV's decoherence-relevant frequencies (~850 GHz orbital, ~3 THz excited state,
broadband Raman) is NOT reachable with fabricable PnCs (850 GHz → a ≈ 9 nm); the user agreed. The working framing (collaborator slide) is a complete
GHz gap AT the spin / mechanical-mode frequency (1–15 GHz): it shields the localized mode (high Q_m, Chan 2012 cross shield) and removes the spin's
phonon continuum → coherent spin–phonon coupling. A complete gap near ~10 GHz needs a ≈ 600–1000 nm snowflake (diamond_a_large) or a cross shield
around the nanobeam, not the photonic-scale lattice.

### Stage 3 — Full optomechanical crystal cavity
Extends Stage 2 to also have a **localized mechanical mode** at a target frequency within the phononic gap. The structure becomes a photonic cavity + phononic bandgap + mechanical cavity simultaneously. This is the full phoxonic optomechanical crystal (Chan thesis, Safavi-Naeini & Painter). Not yet started.

---

## The Photonic-Phononic Conflict (Stage 2)

Both constraints act on the same lattice constant `a`.

**Phononic gap center** (Bragg scaling, diamond, v_LA ~ 17,450 m/s):
```
f_gap = 0.5 * v_LA / a
```

**Photonic TE gap** (triangular lattice, diamond, d/a ~ 0.44):
```
a / lambda ~ 0.25 to 0.38  =>  a ~ 155 to 235 nm  (at lambda = 619 nm)
```

**At the photonic a:**
```
f_phon ~ 0.5 * 17450 / (155e-9 to 235e-9)  ~  37 to 56 GHz
```

**To reach 5 GHz:**
```
a ~ 0.5 * 17450 / 5e9 ~ 1750 nm  (a/lambda ~ 2.8, outside photonic TE gap)
```

**Conclusion:** At the photonic lattice constant for 619 nm, the natural phononic gap in diamond is ~37–56 GHz, not 5 GHz. For Stage 2, the question is: what phononic gap frequency is achievable in a structure that also has a photonic TE gap at 619 nm?

---

## Update 2026-10-14: phononic target ≤ 10 GHz and fabrication limit

- User now targets a phononic gap center **≤ 10 GHz** (Stage 1 exploration). Snowflake data: f·a ≈ 6500-8000 GHz·nm → **a ≈ 650-850 nm**, i.e. a/λ ≈ 1.1-1.4 at 619 nm — far outside the photonic TE window (a/λ ≈ 0.25-0.44, a ≈ 155-275 nm). A single-scale snowflake cannot give both a ~10 GHz phononic gap and a 619 nm photonic gap → Strategy 3 (hierarchical) or accepting a ~25-40 GHz phononic gap at photonic a remain the options for Stage 2.
- In the photonic window (a=200-275 nm), the best **fabricable** snowflake (bridge ≥ 30 nm) is d/a≈0.41, w/a≈0.28-0.36: phononic gap ~27-48 GHz, ~33% fractional.
- **Minimum feature size 30 nm** (user, 2026-10-14) applies to both the phononic and photonic design: slab bridges and hole features. Enforced in scripts/sweep_plan.py.

## Resolution Strategies for Stage 2

### Strategy 1: Accept the ~50 GHz natural phononic gap
Design for a ~50 GHz phononic gap at the photonically-compatible lattice constant. Requires asking: is there a useful SnV decoherence mechanism at ~50 GHz that this would suppress? (The SnV spin-orbit splitting is ~850 GHz; phonon-induced dephasing at ~50 GHz is plausible but needs checking.) This is the simplest path.

### Strategy 2: Snowflake geometry (primary research path)
Safavi-Naeini & Painter (2010) showed that the snowflake unit cell achieves a simultaneous phononic + photonic bandgap in Si at a=500 nm: phononic ~9.5 GHz + photonic TE at ~1550 nm. The key is that the snowflake geometry is engineered to scatter strongly at both acoustic and optical wavelengths. For diamond at 619 nm, the equivalent design is unknown and is the primary Stage 2 research question.

### Strategy 3: Hierarchical / supercell design
Use two length scales: fine scale a_phot ~ 200 nm (photonic gap at 619 nm), coarse scale N*a_phot ~ 1300 nm (phononic gap at ~5 GHz). The physical basis:
- At 5 GHz, lambda_phon ~ 3500 nm >> a_phot ~ 200 nm: the photonic crystal is an effective medium to these phonons
- Effective acoustic velocity of the patterned slab: v_eff ~ v_diamond * sqrt(1 - fill) ~ 13,000 m/s (r/a=0.35)
- Required coarse period: a_phon = 0.5 * v_eff / 5e9 ~ 1300 nm, so N ~ 6-7
- The coarse-scale phononic contrast comes from modulating r/a between sub-regions at the N*a_phot scale
- Photonic modes are unaffected (localized at sub-lambda scale, don't see the coarse modulation)

This approach decouples the two design problems cleanly but requires a larger simulation domain (N^2 ~ 36-49x photonic unit cells per phononic unit cell) and the phononic gap will likely be narrower due to softer contrast.

---

## Current Status

| Stage | Task | Status |
|-------|------|--------|
| 1 | Phononic pipeline (Si snowflake, unit_cell_3.mph) | **Done** — matches GUI to <1 MHz |
| 1 | Diamond snowflake, a=300 nm (mech_v1 + 3×3 d×w) | **Done** — best 25.9 GHz, 8.6 GHz wide |
| 2 | Phononic f(a) at a=150–275 nm (diamond_a_sweep) | **Done** 2026-10-14 (48/54; 6 geometrically infeasible) |
| 1 | Phononic gap ≤ 10 GHz (diamond_a_large, a=400–1000) | **Launching** 2026-10-14 |
| 2 | Photonic bandstructure at 619 nm | Not started — COMSOL OP study needs diamond n + f_op≈484 THz (GUI check first); legume is the alternative |
| 2 | Map photonic a-window | Not started |
| 2 | Simultaneous phoxonic gap demonstrated | Not started |
| 3 | Mechanical cavity mode design | Not started |
| 3 | Optomechanical coupling rate g_0 | Not started |

---

## Key References

- Safavi-Naeini & Painter (2010) Opt. Express 18, 19659: simultaneous phoxonic gap in Si snowflake (Stage 2 blueprint)
- Chan thesis (Caltech 2012) Ch. 4: full optomechanical crystal co-design (Stage 3 blueprint)
- Maldovan & Thomas (2006) Nature Materials 5, 667: phoxonic crystal theory (hierarchical design)


## 1D nanobeam full cavity (2026-10-14)
See docs/cavity_design_method.md and CLAUDE.md "1D nanobeam OMC track". Taper (Chan thesis): a(x)/a_m = 1 - d(2y^3-3y^2+1),
hole area 1-s = chi(1-a), aspect r = a^xi. Oh start values d 0.18, M 10, eta 1, xi 6, chi 3.5, 10 mirror cells/side.
Diamond photoelastic (p11,p12,p44) = (-0.25, 0.043, -0.172). Cavity optical mode from X dielectric band; mech from Y+Z+ band at Gamma.


## 1D full-cavity status (2026-10-14, late)
Pipeline: scripts/build_cavity_model.py, cavity_taper.py, cavity_eval.py, cavity_pipeline.py. Oh cavity reproduced
(runs/cavity_oh2026). 619 nm (a,d) map: 619 nm line found (a 195-214 nm for d .10-.22), Q up to 4e7 at d .10, breathing
stuck ~10.7-11.8 GHz -> taper-shape (xi, chi) sweeps queued at 60 nm and 80 nm (cells A/B). Min feature 60 nm (+80 nm track).
See CLAUDE.md "1D nanobeam OMC track" and docs/nanobeam_1d_summary.pdf.
Co-design trade: optical resonance set by a and d (~2 nm per nm of a); breathing frequency by w and center-hole shape;
fabrication (60/80 nm) limits how flat/large the center holes can be. Final = one best device per min feature.

## 1D co-design outcome, 2026-10-15
- Width decouples the two problems: optics is set by period/taper at almost any w (Q 1e7+ survives w 650), mechanics by w. Choosing w 650
  brings the breathing mode below 10 GHz without hurting optics; the taper then trades Q against mechanical localization.
- Selection rule (scripts/cavity_designs.py): fabricable, breathing loc ≥ 0.8, not a hybrid; ≤ 10 GHz first by highest Q_o.
- 60 nm: solved (w650 d0.10 ξ6 χ4, Q 1.8e7, 9.67 GHz). 80 nm: open — w650 gives 10.53 GHz (no taper freedom at a ≈ 184); w700 queued.
