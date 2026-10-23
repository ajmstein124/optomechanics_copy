# Optical mode volume and Q/V: 60nm_w650_d0.10_xi6_chi4

Estimated from SAVED field data (no new simulation): COMSOL midplane cut of the cavity mode (`runs/cavity_619_width/w650_mf60/data/fields_final.npz`).

| | |
|---|---|
| resonance | 619.50 nm |
| in-plane area A_xy = ∫ε\|E\|² dxdy / max(ε\|E\|²) (z = 0 plane, whole beam + air) | 0.2280 µm² |
| vertical length L_z (TE0 mode of a 120 nm diamond slab, n_eff 1.946) | 98.5 nm |
| **mode volume V = A_xy · L_z** | **0.0225 µm³ = 1.32 (λ/n)³**, n = 2.41 |
| peak of ε\|E\|² | in the diamond at x = 85 nm, y = 17 nm |
| Q (COMSOL) | 1.79e+07 → **Q/V = 1.35e+07 per (λ/n)³** |
| Q (Lumerical, lower bound) | 1.11e+07 → Q/V = 8.39e+06 per (λ/n)³ |

Purcell factor for an ideally placed and oriented dipole, F_P = (3/4π²)(λ/n)³ Q/V = 1.03e+06 (COMSOL Q).

**Accuracy (~20–30 %):** assumes the field separates into the midplane pattern times the vertical profile of a uniform
120 nm slab (the real beam is patterned and 650–700 nm wide, so the vertical tail differs somewhat), and that the 3D
maximum of ε|E|² lies on the midplane. The exact V needs one evaluation of the saved `final_w650_mf60.mph` solution
on the COMSOL machine (no re-solve).
