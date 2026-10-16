# Full 1D OMC cavity: design + optimization method

Sources: J. Chan PhD thesis (Caltech 2012) §3.4 (`~/Downloads/JC_Thesis_Electronic_v1.pdf`);
Chan et al. APL 101, 081115 (2012) (`docs/papers/081115_1_online.pdf`);
Oh et al. 2026 Supplement §3 (`docs/papers/oh_OMC_supplement.pdf`) — Oh states they follow Chan's thesis parameterization.

## Mode choice (Chan thesis §3.4.1)
- Optical: TE-like (y-odd, z-even) **dielectric band at X**. Reducing a pushes it UP into the gap.
- Mechanical: Y+Z+ **breathing band at Γ**. X-point modes have a π phase per cell -> g0 cancels.
  Lowering hy/hx (squishing the hole) pushes it DOWN into the gap.
- Defect cell = smaller a + smaller hy/hx than the mirror cell. Chan 2012: mirror (a, w, hx, hy) = (436, 529, 165, 366),
  defect (327, 529, 199, 170) nm -> a 25% smaller, hy/hx 2.2 -> 0.85.

## Taper parameterization (Chan thesis eqs. 3.48-3.53)
- Cells j = 0 (defect) ... M (mirror), x = j/M.
- Lattice scale: a(x)/a_nom = 1 - d (2x^3 - 3x^2 + 1)   (zero slope at both ends; d = defect depth)
- Slope control: x -> y(x) = 0.5 (2x)^eta for x <= 0.5;  1 - 0.5 (2(1-x))^eta for x > 0.5
- Hole area scale s_j: 1 - s_j = chi (1 - a_j)
- Hole aspect scale r_j (hy/hx): r_j = a_j^xi
- Constraints: 0 < r_j < r_{j+1}, 0 < a_j < a_{j+1}, r_M = s_M = a_M = 1; hx, hy > min feature; hy < w; d in (0, 1).
- Full design: (hx, hy, a_nom, t, w, M, d, chi, xi, eta). t fixed by the membrane; a_nom rescales to hit the target wavelength.
- Mirror cells beyond j = M: not given in the text. **Oh 2026 Fig. 1(b) measured** (runs/nanobeam_oh2026/reference/oh2026_cavity_profile.json):
  41 holes = center + ~10 taper + ~10 mirror per side. Chan's cubic fits Oh's pitch profile with d = 0.18, M ~ 11, eta ~ 1 (rms 0.5%).
  Center hole: hy ~ 208 nm (0.34 x mirror), hx ~ 400 nm (+/-45) -> xi ~ 6, chi ~ 3.5.
- Moraes et al. 2022 (diamond OMC optimization, arXiv 2207.00951, docs/papers/): 1/8 nanobeam, N = 8 defect + 5 mirror cells per side, PML, GA (Dakota) then pattern search.

## Figures of merit
- g0 = g_MB + g_PE: moving boundary (surface integral, Chan 2012 eq. 1) + photoelastic (volume integral, eq. 2-3).
  Diamond photoelastic constants **(p11, p12, p44) = (-0.25, 0.043, -0.172)**: Burek et al. Optica 2016 (arXiv 1512.04166, docs/papers/) citing
  A. R. Lang, Diamond Relat. Mater. 18, 1 (2009) review; same set in Moraes 2022. Older Ramachandran 1947 values differ (0.125, -0.325, 0.11) -- superseded.
  Formula is for x || [100]; Burek's devices had x || [110] and rotated the tensor. Our isotropic elastic model -> use [100] form.
- Q_o: radiation-limited, from the full-structure optical eigenmode. Capped at Q_cutoff.
- Fitness: Chan 2012 F = g * min(Q_o, Q_cut)/Q_cut (Q_cut 3e6); thesis F = -g * min(Q_o, Q_cut)^2 (Q_cut 5e6);
  Oh: F = g0 Q_o * G(w_o; mu_o, D_o/6) * G(w_m; mu_m, D_m/6) — Gaussians keep both modes near their mirror-gap centers.
- Optimizer: Chan Nelder-Mead with random restarts; Oh genetic algorithm (PyGAD) on HPC.
- Oh two stages: (1) grid-search mirror cell for widest gaps [we did this], (2) optimize the taper/defect profile.

## Robustness / mechanical Q
- Oh: Monte Carlo disorder, sigma = 1-8 nm on hole position + size, 50 runs each. Q_o is very sensitive, g0 is not.
- Chan: Q_m in a quasi-gap is limited by symmetry-breaking leakage into other classes -> needs the 2D shield;
  clamping loss simulated with random hole offsets and energy radiated at the clamp.

## S&P 2014 (2D snowflake, for later)
- Line defect waveguide, then a 3% quadratic variation of snowflake hole radius along it localizes both modes.
