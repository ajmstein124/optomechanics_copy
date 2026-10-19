# Checks to run on the best devices

New simulations are fine for these (user, 2026-10-16). Status: [x] done, [~] partial, [ ] to do.
Devices: `60nm_w650_d0.10_xi6_chi4`, `80nm_w700_d0.10_xi4_chi3.5`.

## Optics
- [x] Lumerical FDTD cross-check of resonance, Q and field (`lumerical_verification.md`): -0.12 % / -0.09 % in λ.
- [~] **Optical mode volume V and Q/V.** Estimate from saved midplane fields (`mode_volume.md`: 1.32 / 1.55 (λ/n)³).
      To do: exact 3D V, either evaluated on the saved `final_<label>.mph` or with a 3D field + index monitor in Lumerical.
- [ ] **Optical Q convergence:** COMSOL with a larger air/PML box (80 nm device: Lumerical 8.6e6 > COMSOL 3.4e6), and
      Lumerical with a longer run (Q > ~1e6 is a lower bound).
- [x] Single-mode check: y-odd optical family lies above the cavity mode at X (`mirror_bands.png`).

## Mechanics
- [ ] **Strain profile of the breathing mode, not only the displacement:** strain tensor components (ε_xx, ε_yy, ε_zz,
      shear) on the midplane and through the thickness, at zero-point amplitude (ε_zpf); where it peaks relative to the
      optical field maximum; values at candidate SnV sites. This is what the emitter couples to.
- [ ] **Physical mechanical Q:** mechanical PML / support / cross-shield model. The present Q_m is numerical noise (clamped,
      no PML). Priority, because the breathing mode lies ABOVE the mirror's breathing-class quasi-gap in both devices
      (`mirror_bands.png`) and so is not gap-protected.
- [ ] Q_m vs mirror count, and a design variant with the breathing mode inside the quasi-gap (e.g. ~7-8.5 GHz).

## Optomechanics
- [ ] **g0** (moving boundary + photoelastic): fix the normalization bug in the sweep code (g0 ~1e8 too small) and recompute.

## Fabrication tolerance
- [ ] Disorder Monte Carlo (hole size / position σ 1-8 nm, as Oh 2026 supplement): spread of λ, Q_o, f_m, g0.
