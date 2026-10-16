# Agent: COMSOL Specialist

**Domain:** COMSOL 6.x simulation setup via the mph Python library.  
**When to use:** Any question about COMSOL model construction, Floquet BCs, eigenfrequency solver settings, geometry operations, mesh, or troubleshooting COMSOL/mph errors.

---

## Machine / Environment (jv-adamantoise, 2026-10-12)

- **Machine:** jv-adamantoise, Tailscale <COMSOL_HOST>, user `abby`, profile `C:\Users\abby`
- **COMSOL:** 6.4, installed at `C:\Program Files\COMSOL\COMSOL64\Multiphysics_copy1\`
- **License:** Permanent node-locked (SN=<REDACTED>, hostid=<REDACTED>). No FlexLM server needed. Modules: MEMS (Structural Mechanics), Wave Optics, RF, ACDC.
- **Python:** `C:\Program Files\ANSYS Inc\v252\Lumerical\python-3.13.1\python.exe` (pip-installable, mph 1.4.0 installed)
- **PYTHON_CMD** in remote_runner.py: `"C:\Program Files\ANSYS Inc\v252\Lumerical\python-3.13.1\python.exe" -u`
- **Working dir:** `C:\Users\abby\comsol`
- **Model file:** `C:\Users\abby\comsol\unit_cell_3.mph` (Si snowflake, COMSOL 6.2 format, 754 MB)

## mph Workflow

```python
import mph
# mph autodiscovers COMSOL 6.4 in Multiphysics_copy1 — no path needed
client = mph.start()          # headless, no GUI window
model  = client.load('unit_cell_3.mph')
m      = model.java           # COMSOL Java API
```

- `mph.start()` with no arguments — mph.discovery finds COMSOL 6.4 automatically on this machine.
- Do NOT use `mph.connect()` (requires a manually started server) or `mph.start(comsol=...)` (not a valid arg in mph 1.4).
- Do NOT use `start_comsol_server.bat` — obsolete now that mph.start() works headlessly.
- `m.param().set('name', 'value', 'description')` — set global parameters.
- `m.study('std1').run()` — run all study steps.
- `client.clear()` when done (releases COMSOL server resources).

---

## Floquet Periodic Boundary Conditions

**Mathematical form** (from COMSOL blog "Modeling Phononic Band Gap Materials and Structures"):

```
u_dest = exp(-i * k_F . (r_dest - r_src)) * u_src
```

where `k_F = (kx, ky, 0)` is the Bloch wavevector, `r` is the position vector, `u` is the displacement field.

**COMSOL setup:**
```python
pc = solid_node.create(name, 'PeriodicCondition', 2)
pc.set('PeriodicType', 'Floquet')
pc.set('kFloquet', ['kx', 'ky', '0'])   # kx, ky are global parameters
pc.selection().named(src_sel)
dest = pc.create('dest', 'Destination', 2)
dest.selection().named(dst_sel)
```

**In unit_cell_3.mph (the model actually used):** rhombus primitive cell, two existing Floquet conditions (GUI-confirmed):
- Periodic Condition 1: boundaries 2,5 → 8,9 (bottom/top faces, along a1)
- Periodic Condition 2: boundaries 1,4 → 22,23 (left/right slanted faces, along a2)
- k_F = (kFx, kFy, 0) Cartesian global parameters. Python only sets kFx/kFy — it does NOT create BCs.
- z=0 midplane: sym1 (symmetric) / as1 (antisymmetric) toggled per run; top face free.

*(Legacy, archived circular-hole builder only:)* rectangular supercell used `pc_x` (x=0 → x=a) and `pc_y` (y=0 → y=a√3).

**Complex eigensolver note:** For k != 0, the phase factor is complex, so COMSOL invokes a complex eigensolver automatically. Eigenvalues (omega^2) remain real for an undamped system. `getData()` returns real frequencies — this is correct behavior.

**k=Gamma special case:** At kx=ky=0, matrices are real and zero-frequency rigid-body modes appear. Use `eig_shift_GHz > 0` to skip them.

---

## Box Face Selections (legacy — archived circular-hole builder only; not used with unit_cell_3.mph)

Used to select faces on a specific plane for periodic BC assignment:

```python
s = comp.selection().create(name, 'Box')
s.set('entitydim', 2)
s.set('condition', 'allvertices')   # face selected only if ALL vertices are in the box
s.set('xmin', f'({coord})-{tol}')
s.set('xmax', f'({coord})+{tol}')
s.set('ymin', '-a_lat*0.1'); s.set('ymax', 'a_lat*2.0')  # wide in non-axis directions
s.set('zmin', '-d_slab');    s.set('zmax', 'd_slab')
```

Tolerance `tol = 'a_lat*1e-4'` is tight enough to avoid picking up internal faces.  
Four selections needed: `sel_x0` (x=0), `sel_xa` (x=a), `sel_y0` (y=0), `sel_ya` (y=a*sqrt(3)).

---

## Eigenfrequency Study

```python
std = m.study().create('std1')
eig = std.create('eig1', 'Eigenfrequency')
eig.set('neigsactive', 'on')
eig.set('neigs', str(n_modes))       # number of eigenfrequencies to find
eig.set('shift', f'{shift_GHz}[GHz]')  # shift-invert center
```

**Shift rule:** Set shift to 30-70% of the expected gap center. Shift must be below the gap. If modes are missing, lower the shift. If DC modes clutter the plot, raise the shift.

**Extracting results:**
```python
ev = m.result().numerical().create('ev1', 'EvalGlobal')
ev.set('data', 'dset1')
ev.setIndex('expr', 'freq', 0)
ev.setIndex('unit', 'GHz', 0)
# after study.run():
raw = ev.getData()   # list of lists: outer=eigenmode, inner=expression
freqs = np.array([float(entry[0]) for entry in raw])
```

---

## Geometry: Triangular Lattice of Circular Holes (LEGACY — archived; current geometry is the snowflake in unit_cell_3.mph)

**Supercell:** Lx=a, Ly=a*sqrt(3), Lz=d (rectangular 2-atom cell of the hexagonal lattice).

**Holes:**
- 1 interior hole at (a/2, a*sqrt(3)/2) — fully inside cell
- 4 corner holes at (0,0), (a,0), (0,a*sqrt(3)), (a,a*sqrt(3)) — each a quarter-atom

```python
cyl = geom.create(name, 'Cylinder')
cyl.set('r', 'r_hole')
cyl.set('h', '1.1*d_slab')           # taller than slab so Boolean Difference clips it cleanly
cyl.set('pos', [x0_expr, y0_expr, '-0.55*d_slab'])
```

Union all holes, then Difference from slab block. Run `geom.run('fin')` to finalize.

**For parameter sweeps (updating geometry in-loop):**
```python
m.param().set('a_lat', str(a))
m.param().set('d_slab', str(d))
m.param().set('r_hole', str(r))
m.component('comp1').geom('geom1').run('fin')   # rebuild geometry
m.component('comp1').mesh('mesh1').run()         # re-mesh
```

Box face selections are parametric so they update automatically when `a_lat` changes.

---

## Snowflake geometry (unit_cell_3.mph) — what Python changes

Python never rebuilds geometry: it sets parameters `a`, `d`, `w`, `f_r`, `t` (and `scaling=1.0`, since a=448e-9*scaling by default) and calls `m.sol('sol1').runAll()`; COMSOL regenerates geometry + mesh. Confirmed working for varying d, w (diamond_dw_sweep) and a (diamond_mech_v1 a=300).

### Cell + hole geometry — READ FROM unit_cell_3.mph via mph (diag_geometry.py, 2026-10-14). Supersedes earlier descriptions.
- Hole: Rectangle r1 lx=w, ly=d, base=center, pos=(0, d/2) → arm runs from the hole center (origin) out to distance d, width w, pointing up. Rotate1 +120°, Rotate2 −120° about (0,0) → arms at 90°/210°/330°. Union → Fillet f_r on all vertices.
- Cell: Polygon pol1 = rhombus (a/2, −a/(2√3)), (−a/2, −a/(2√3)), (−a, a/√3), (0, a/√3). **Leans LEFT: a1=(a,0), a2=(−a/2, a√3/2).** The hole (origin) sits at the **centroid of the lower triangle** of the rhombus — NOT the rhombus center. Each arm points at a cell corner.
- Move mov1 shifts the cell by a **fixed (50 nm, −50/√3 nm)** — tuned for Si a=478 nm, does NOT scale with a. Exists in BOTH wp1 (slab) and wp2 (air, same pol1, t_air=1.5 µm); they must always be moved together.
- Model subtracts ONE hole. If the hole crosses the shifted cell boundary → mesh 'Copy Face 1' fails "Disconnected source not allowed" (topology 3–4 domains instead of 2 domains/30 boundaries). Predict with `scripts/cell_placement.py` (+ shapely with fillet); fix by choosing a per-geometry shift (physics-invariant; validated: same gap to 0.01 GHz).
- Floquet: pc1 = bottom/top faces (along a1), pc2 = slanted faces (along a2); explicit boundary numbers re-tracked by COMSOL as geometry changes.
- `archive/misc/sim_schematic.png` (right-leaning rhombus, centered hole) does NOT match the model's cell placement — the lattice is the same, but don't use it as the drawing reference.

---

## Known Issues / Gotchas

- **Windows encoding:** Never use Unicode in `print()` statements. Windows SSH uses cp1252; box-drawing characters cause `UnicodeEncodeError`.
- **Scripts must be on local Windows drive:** Network/cloud-synced paths (OneDrive, etc.) cause COMSOL to behave incorrectly.
- **getData() returns empty:** Check that `study.run()` completed without error. Check `eig_shift` is in range.
- **Box selections miss faces:** Increase `tol` slightly (try `a_lat*5e-4`). Verify face count with `len(solid_node.selection('geom1_...').entities(2))`.
- **Always rename material labels to match the actual material.** When overriding a library material (e.g., setting diamond properties on mat1 which defaults to "Silicon"), always call `m.material('mat1').label('Diamond')` immediately after the property override. Leaving the GUI label as "Silicon" while the properties are diamond is confusing and error-prone during GUI inspection. This applies to any material substitution.

## Material Override Pattern (confirmed from GUI, 2026-10-13)

When overriding Si (mat1) in unit_cell_3.mph with isotropic diamond:

```python
m.material('mat1').propertyGroup('def').set('rho', str(rho_diamond))   # local property only
m.material('mat1').propertyGroup('Enu').set('E',   str(E_diamond))
m.material('mat1').propertyGroup('Enu').set('nu',  str(nu_diamond))
m.material('mat1').propertyGroup('Enu').set('rho', str(rho_diamond))   # output property, belt+suspenders
m.material('mat1').label('Diamond')   # ALWAYS rename to avoid confusion
```

**Critical behavior difference between 'def' and 'Enu' property groups (confirmed GUI 2026-10-13):**
- `propertyGroup('Enu').set('E', ...)` → writes directly to **Output Properties** (shows in main table, what the solver uses)
- `propertyGroup('def').set('rho', ...)` → creates a **Local Property** only (does NOT update the Output Properties table; rho still shows 2329 in Output Properties)

**Why this matters:** COMSOL's GUI "Basic (def)" property group shows:
- Output Properties: rho = 2329[kg/m³] ← library Si value, NOT updated by our set() call
- Local Properties: rho = 3500.0 ← what our set() call creates

Empirically, the local property rho=3500 appears to be used by the solver (frequency scaling of N_mode=10 data is consistent with rho=3500, not rho=2329). But do NOT rely on this — always also set rho in the Enu group where it becomes an unambiguous Output Property.

**How to definitively verify material in GUI:**
Open the Enu property group → right-click → **Equation View**. This shows all variables exposed to the solver. Confirm you see `rho = 3500` (Global) and `material.Enu.rho = 3500` (Domain 2). E and nu appear similarly. The Equation View is the ground truth — "Local Properties" vs "Output Properties" in the Settings panel is a display distinction that does NOT determine what the solver uses.

**How to verify material is correct (frequency scaling test):**
With N_mode=N, shift=f_mech, run one k-point sweep and check max frequency.
For diamond at a=300nm: gap at ~23 GHz → 10th mode should be at ~21 GHz (just below gap).
For diamond stiffness + Si density: gap at ~28 GHz → 10th mode would be at ~26 GHz.
If max observed mode matches ~21 GHz, density is 3500 (correct). If ~26 GHz, density is wrong.

**Wrong property names (silently do nothing):**
```python
mat.propertyGroup('def').set('youngsmodulus', ...)  # wrong name + wrong group
mat.propertyGroup('def').set('poissonsratio', ...)  # wrong name + wrong group
mat.propertyGroup('def').set('density', ...)        # wrong name
```

## Geometry notes (unit_cell_3.mph)

- The snowflake unit cell has **3 arms** (not 6). This is correct for the design — do not confuse with the 6-arm snowflake in some literature.
- Hole is 3 rectangles (arm length d from hole center, width w) unioned, then filleted with f_r; arms at 90°/210°/330° (one arm up). Confirmed from r1 in the .mph (see above).
- **Geometric feasibility limit:** the hole must fit inside the (shifted) rhombus. With the default fixed shift the up-arm limit is d < a/√3 − 28.9 nm. d/a=0.48 with w/a=0.43 cannot fit ANY rhombus placement (bridges to neighbour holes 0–5 nm).

## Mech Mesh (read from .mph 2026-10-14)
- mesh1 "Mech Mesh": ftri1 (periodic source faces, size1 hmax t/8) → cpf1/cpf2 copy faces → ftet1 (size1 hmax t/7.5). Absolute sizes → cost ∝ a² at fixed t. For large a use `--mesh-tet t/5` (validated ≤5e-4 rel at a=1000). Don't coarsen past ~t/5 without re-checking: the half-slab (70 nm) needs ≥2–3 quadratic elements through thickness.
- Rule of thumb timing (N_mode=12, t/5): ~10–13 s per solve at a=1000; 2 solves per k-point.

## Sweep scripting conventions (2026-10-13, updated 2026-10-14)

- **New sweeps: use `scripts/sweep_plan.py` → `plan.json` → `scripts/plan_runner.py`** (see CLAUDE.md). Min-feature check on by default at 30 nm (bridge and arm width); `--no-min-feature` to run flagged combos.

- One .npz per combo, written immediately; skip existing files at start → resumable after crash.
- Wrap each combo's k-loop in try/except so one geometry/mesh failure doesn't kill an overnight run.
- Store all complete gaps + the tracked band 6–7 gap, not just a thresholded "first gap".
- Scale f_mech ∝ 1/a when sweeping a (f_mech = 10 GHz × 300 nm / a for diamond).
- No time guards on overnight sweeps — the user decides when to stop.
- `remote_runner.py` is run-aware (2026-10-14): a script at `runs/<name>/x.py` is uploaded as `<name>__x.py` (no collisions), sibling `*.json` go along, the log is `job_log_<name>__x.txt` (older logs kept), and `--status/--pull` fetch new files from `runs/<name>/data/` recursively.
- Check geometry topology before solving when changing geometry/cell placement: every valid combo so far has 2 domains / 30 boundaries (`geom.getNDomains()`, `geom.getNBoundaries()`); anything else → skip and log.
- Gap reporting: only count gaps below the complete-spectrum ceiling = min over k and symmetry class of the highest computed mode (N_mode truncation).

## N_mode / eigensolver shift guidelines

- With shift=f_mech and N_mode modes, ARPACK finds the N modes closest (in frequency) to f_mech.
- To capture a bandgap, you need modes on BOTH sides of the gap.
- Rule of thumb: set f_mech to ~40–50% of expected gap center; set N_mode large enough that the highest found mode is at least 20% above the gap center.
- **Default for diamond (known geometry): N_mode=10, f_mech=10 GHz.** Confirmed sufficient from diamond_mech_v1: max 6 modes per symmetry class below 50.5 GHz (top of highest gap). N_mode=10 gives comfortable margin.
- **Use N_mode=20 when:** gap location is unknown (new geometry/material), gap is not appearing despite parameter sweeps, or verifying a new geometry for the first time.


## 1D nanobeam full cavity (2026-10-14)
See docs/cavity_design_method.md and CLAUDE.md "1D nanobeam OMC track". Taper (Chan thesis): a(x)/a_m = 1 - d(2y^3-3y^2+1),
hole area 1-s = chi(1-a), aspect r = a^xi. Oh start values d 0.18, M 10, eta 1, xi 6, chi 3.5, 10 mirror cells/side.
Diamond photoelastic (p11,p12,p44) = (-0.25, 0.043, -0.172). Cavity optical mode from X dielectric band; mech from Y+Z+ band at Gamma.


## 1D full-cavity status (2026-10-14, late)
Pipeline: scripts/build_cavity_model.py, cavity_taper.py, cavity_eval.py, cavity_pipeline.py. Oh cavity reproduced
(runs/cavity_oh2026). 619 nm (a,d) map: 619 nm line found (a 195-214 nm for d .10-.22), Q up to 4e7 at d .10, breathing
stuck ~10.7-11.8 GHz -> taper-shape (xi, chi) sweeps queued at 60 nm and 80 nm (cells A/B). Min feature 60 nm (+80 nm track).
See CLAUDE.md "1D nanobeam OMC track" and docs/nanobeam_1d_summary.pdf.
COMSOL gotchas found: ewfd.freq real-only (use ewfd.Qfactor); mech Q from lambda; updateSolution() before evaluating
operators added after a solve; CrystalSystem value 'Qubic3' for cubic anisotropic; Interp feature has no 'coord' property and
returns 0 points via setInterpolationCoordinates -> use CutPlane dataset + Data export; mph evaluate OOMs on full 3D meshes.

## 1D cavity tooling added 2026-10-15
- `cavity_eval.setup()` now also creates `max_side` (Maximum over the sidewall boundaries `sel_side`); `sidewall_ratio(m, x_loc, k)` =
  max sidewall |real v| / max beam |real u| for mode k (breathing ≈ 1.0, hybrids ≈ 0.35). `Pipeline.solve()` stores `S` per mode.
- `Pipeline.bracket(d, a0, base_shape)` steps the period until 619.4 nm is bracketed (~2.3 nm resonance per nm of a).
- `scripts/cavity_fields.py export(m, z, dev, out_dir)`: CutPlane + Data export of optical Ey/normE (z = 1 nm) and the breathing mode u,v,w
  (top face) → fields_<dev>.npz. `scripts/cavity_designs.py`: numpy-only 619-line reduction + selection (shared Mac/Windows).
- `remote_runner.py` uploads cavity_fields.py and cavity_designs.py too. A RUNNING job keeps the module versions it imported — edits apply to
  new launches only; restart my own waiters (deliverables/fsp_builds) after editing them.
- Waiter chain 10/15: width run.py → deliverables.py (refinalize + bands) → fsp_builds.py → run_w700.py (which re-runs both).
- Lumerical runs: old PC DESKTOP-BBQLCD3 (`<USER>@<LUMERICAL_HOST>`, v211, `py -3.8`), never jv-adamantoise. Lumerical safe mode (API) blocks
  `system()` and `rm()`; detached launch there via a .bat + Invoke-CimMethod (inline cmd quoting breaks).
