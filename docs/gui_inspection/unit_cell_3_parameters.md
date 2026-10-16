# unit_cell_3.mph — GUI Inspection Notes
Inspected: 2026-10-13

---

## Screenshot 1: 3D geometry view

- Unit cell shape: **rhombus** (parallelogram base, oblique sides)
- Hole shape: **3-arm** (Y/Mercedes-Benz symmetry), NOT 6-arm
- Corners of hole: **smoothed/filleted** (matches f_r parameter)
- Axes (3D view):
  - x, y in-plane: ×10⁻⁷ m, span roughly −400 to +200 nm → consistent with a ≈ 478 nm
  - z vertical: ×10⁻⁶ m, span −1.5 to 0 µm → includes t_air padding above/below slab

---

## Screenshot 2 (Parameters 1)

| Name    | Expression                    | Value           |
|---------|-------------------------------|-----------------|
| scaling | 1.067                         | 1.067           |
| a       | 448[nm]*scaling + 409*0[nm]   | 4.7802E-7 m = **478 nm** |
| w       | 170[nm] + 0*85[nm]            | **170 nm**      |
| d       | 166[nm] + 0*157[nm]           | **166 nm**      |
| f_r     | 25[nm]                        | **25 nm**       |
| t       | 220[nm]                       | **220 nm**      |
| t_air   | 1.5[um]                       | 1500 nm         |
| kFx     | 0                             | 0               |
| kFy     | 0                             | 0               |
| N_mode  | 10                            | 10              |
| f_mech  | 7e9                           | 7 GHz           |
| f_op    | 192e12                        | 192 THz (~1560 nm) |

Notes:
- No explicit hole radius `r` parameter exists. Bridge width is implicit in d, w, f_r geometry.
- `scaling` scales only `a`; d and w are NOT expressed as ratios of a — Python must set all three independently.
- f_mech default 7 GHz; Python overrides per study. N_mode default 10; Python sets 20.
- Model has both Mech Study and OP Study (phoxonic model).

---

## Screenshot 3 (Materials → Silicon mat1)

**Material is ISOTROPIC Si — NOT anisotropic tensor.**

| Property | Variable | Value | Unit |
|----------|----------|-------|------|
| Density | rho | **2329** | kg/m³ |
| Young's modulus | E | **170 GPa** | Pa |
| Poisson's ratio | nu | **0.28** | — |
| Refractive index (real) | n_iso | 3.48 | — |
| Refractive index (imag) | ki_iso | 0 | — |
| Relative permittivity | epsilonr | 11.7 | — |

Derived transverse acoustic velocity:
- G = E / (2(1+ν)) = 170e9 / (2 × 1.28) = **66.4 GPa**
- v_TA = sqrt(G/ρ) = sqrt(66.4e9 / 2329) = **5340 m/s**

S&P 2014 uses anisotropic Si with C44=80 GPa → v_TA = sqrt(80e9/2329) = 5860 m/s.
Our model is **9% slower** than S&P due to isotropic vs anisotropic.

Property groups visible in model tree under mat1:
- Basic (def)
- Young's modulus and Poisson's ratio (Enu)  ← **this is what's used (isotropic)**
- Refractive index (nIi)

mat2 = Air (for optical cladding regions).

---

## Screenshot 4 (Definitions → Boundary System 1 / sys1)

- Label: Boundary System 1, Name: sys1
- Frame: Deformed configuration
- Coordinate names: First=t1, Second=t2, Third=n
- Create first tangent direction from: Global Cartesian (spatial)
- Axis: z

Under Definitions tree:
- Boundary System 1 (sys1)
- Rotated System 2 (sys2)
- View 1

Under Solid Mechanics (solid) tree:
- Linear Elastic Material 1
- Free 1
- Initial Values 1
- **Periodic Condition 1**  ← need to inspect
- **Periodic Condition 2**  ← need to inspect
- **Symmetry 1**            ← need to inspect (Python calls this 'sym1')
- **Antisymmetry 2**        ← need to inspect (Python calls this 'as1'?)
- Equation View

---

## Screenshot 5 (Definitions → Rotated System 2 / sys2)

- Label: Rotated System 2, Name: sys2
- Coordinate names: x1, x2, x3
- Rotation: Z-X-Z Euler, α=0, β=0, γ=0 (all zero → identity, same as global)
- Origin: Spatial (x,y,z) at (0,0,0)
- Work plane: xy-plane

---

## CONFIRMED corrections to prior assumptions

| Prior assumption | Reality (from GUI) |
|-----------------|--------------------|
| 6-arm snowflake | **3-arm snowflake** |
| Rectangular 2-atom supercell | **Rhombus primitive cell** |
| Bridge width b = a − 2r (explicit r) | **No r parameter; bridge implicit in d, w, f_r** |
| Anisotropic Si (C44=80 GPa) | **Isotropic Si: E=170 GPa, ν=0.28 → v_TA=5340 m/s** |
| Model is mechanics-only | **Phoxonic: mechanics + optics (ewfd)** |

---

---

## Screenshots 6-10 (Periodic Conditions, Symmetry/Antisymmetry, Geometry)

**Periodic Condition 1** (Screenshot 6):
- Boundaries: 5 (src) -> 9 (dst) -- one oblique rhombus face pair
- Type: Floquet periodicity
- k-vector: (kFx, kFy, 0) rad/m -- Cartesian X, Y, Z using global COMSOL parameters
- Confirms make_bz_path() is correct: it produces Cartesian (kx, ky) in rad/m

**Periodic Condition 2** (Screenshot 7):
- Boundaries: 4 (src) -> 23 (dst) -- other oblique rhombus face pair
- Type: Floquet periodicity
- k-vector: (kFx, kFy, 0) rad/m -- same parameters as Condition 1

**Symmetry 1** (Screenshot 8):
- Boundary: 7 -- z-normal face (top of modeled domain, z=0)
- Enforces u_z = 0 -> selects symmetric (in-plane) phonon modes

**Antisymmetry 2** (Screenshot 9):
- Boundary: 7 -- same z-normal face
- Enforces u_x = u_y = 0 -> selects antisymmetric (flexural) phonon modes
- PROGRAMMATIC NAME UNKNOWN: label is "Antisymmetry 2" but Python calls solid.feature('as1')
  Need to confirm the Name field in the settings panel

**Geometry 1** (Screenshot 10):
- Right-click menu was shown, not the expanded tree
- From other screenshots: wp1 -> ext1 -> wp2 -> ext2 -> Form Union (fin)
- GEOMETRY INTERNALS UNKNOWN: need wp1 sketch contents to know how d, w, f_r build the 3-arm hole

---

---

## Screenshots 11-12 (Antisymmetry name + wp1)

**Antisymmetry 2 programmatic name** (Screenshot 11 - Create Shortcut dialog):
- Name field shows: **as1**
- Python `solid.feature('as1')` is CORRECT

**Work Plane 1** (Screenshot 12):
- Plane type: Quick, Plane: xy-plane, z-coordinate: 0 m
- This is the mid-plane / top mirror surface of the model
- Unite objects: checked
- Built with COMSOL 6.2.0.658 (win64), Feb 7, 2026
- Code from "Copy as Code": model.component("comp1").geom("geom1") -- INCOMPLETE (just the header)
- SKETCH INTERNALS STILL UNKNOWN -- need wp1 child items or full code from wp1 node

---

## CONFIRMED -- ALL physics setup verified

| Item | Confirmed value |
|------|----------------|
| Antisymmetry 2 programmatic name | **as1** |
| Symmetry 1 programmatic name | **sym1** (assumed -- first Symmetry feature) |
| Periodic Condition 1 | boundaries 5->9, Floquet, k=(kFx,kFy,0) rad/m |
| Periodic Condition 2 | boundaries 4->23, Floquet, k=(kFx,kFy,0) rad/m |
| Symmetry + Antisymmetry boundary | boundary 7 (z=0 mid-plane) |
| Material | Isotropic Si: E=170 GPa, nu=0.28, rho=2329 kg/m3 |
| wp1 z-offset | 0 (xy-plane at mid-plane) |

## REMAINING UNKNOWN

**wp1 sketch contents**: Right-click Work Plane 1 node -> Copy as Code to Clipboard -> paste output.
This shows exactly how d, w, f_r build the 3-arm hole in 2D. Needed to fully document geometry.
