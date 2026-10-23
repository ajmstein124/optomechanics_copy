Abby's request (from her agent): mechanical Q of a nanobeam cavity **anchored into a 2D phononic shield**, i.e. the full structure, not only a beam that runs into a PML.

**What she wants to run.** Her best gap-confined nanobeam (diamond, t 120 nm, w 650 nm; taper a_m 189.5, hx_m 75.8, hy_m 390, M 10, d 0.086, eta 1, xi 1.79, chi -6.97, n_mirror 10, pad_x 1000; same `taper` fields as `nanobeam_oh2026_q.json`) whose end face lands on a 2D slab of the same thickness, with and without a square-lattice cross shield around the anchor (Chan 2012 APL / Oh 2026 style).

**Geometry (as in her COMSOL model, runs/shield_619/build_shield_cavity.py in optomechanics_copy once synced):**
- 1/8 model (Symmetry on x=0, y=0, z=0; breathing class +++).
- Beam 0 < x < X_in, 0 < y < w/2. Slab X_in < x < X_in + Lc + m_out + d_pml, 0 < y < Yc + m_out + d_pml; the slab edge x = X_in, y > w/2 is free (trench).
- Shield: cross holes (bar length h, bar width w_c, fillet) centred at (X_in + (i+1/2)a_s, (k+1/2)a_s), i, k < n_pad + Ns, except a solid anchor pad i < n_pad, k < n_pad_y. Lc = Yc = (n_pad + Ns) a_s.
- PML layers on the slab's +x and +y sides; far faces free. Isotropic diamond E 1050 GPa, nu 0.07, rho 3500.
- Outputs as the resonator lane: per mode f, Q, loc_mech, meff, conv partners; plus a top-face |u| export would help.

**Her COMSOL reference so far (no shield, a_s 450, Ns 4, m_out 500, d_pml 1500):** breathing 9.813 GHz, Q_m 1.65e7 (n_mirror 10), 1.21e7 (4), 9.0e3 (2). Shielded cases are next; the shield cell comes from her sweep on your elastic lane (sweep-c11edac992d7da32c9a8).

She has authorized running these on the cloud once the route exists (price quoted to her first). Sizes in her COMSOL: ~400k P2 tets (1/8 model).

Links #47.
