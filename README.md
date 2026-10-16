# optomechanics (diamond-only public copy)

Public snapshot of the diamond work from a private project: 2D diamond snowflake phononic crystals and a 1D diamond
nanobeam optomechanical crystal cavity at 619 nm (SnV ZPL) with a ~10 GHz breathing mode.

**What is omitted relative to the private repo**
- All silicon COMSOL validation work (`runs/si_validation`, `runs/si_dw_sweep`, `archive/Si_validation`, Si reproduction data, Si tests and slide figures).
  `CLAUDE.md` and `agents/` still mention the Si validation as history.
- Journal PDFs (only the two arXiv preprints are included in `docs/papers/`; see References).
- Lab infrastructure details are replaced by placeholders (`<USER>@<COMSOL_HOST>`, `<USER>@<LUMERICAL_HOST>`, `<PORT>@<LICENSE_SERVER>`, `<REDACTED>`).
  Fill these in locally to run the remote scripts.
- COMSOL `.mph` models and Lumerical `.fsp` files (never tracked; the base model `unit_cell_3.mph` is not distributed).

## References (not included as PDFs)
- J. Chan *et al.*, "Optimized optomechanical crystal cavity with acoustic radiation shield," Appl. Phys. Lett. 101, 081115 (2012). doi:10.1063/1.4747726
- A. H. Safavi-Naeini *et al.*, "Two-dimensional phononic-photonic band gap optomechanical crystal cavity," Phys. Rev. Lett. 112, 153603 (2014). doi:10.1103/PhysRevLett.112.153603
- F. M. Mayor *et al.*, "High photon-phonon pair generation rate in a two-dimensional optomechanical crystal," Nat. Commun. 16, 2576 (2025). doi:10.1038/s41467-025-57948-7
- K. Kuruma *et al.*, "Controlling interactions between high-frequency phonons and single quantum systems using phononic crystals," Nat. Phys. 21, 77 (2025). doi:10.1038/s41567-024-02697-5
- G. Joe, M. Haas *et al.*, "Purcell-enhanced spin–phonon coupling with a single colour centre," Nature 653, 378 (2026). doi:10.1038/s41586-026-10495-7
- H. Oh, V. Dharod, C. Padgett *et al.*, "Spin-embedded diamond optomechanical resonator with a mechanical quality factor exceeding one million," Optica 13, 485 (2026). doi:10.1364/OPTICA.577541 (supplement: doi:10.6084/m9.figshare.31236007)
- S. Meesala, *Quantum acoustics with diamond color centers*, PhD thesis, Harvard University (2019).

Included preprints: M. J. Burek *et al.*, "Diamond optomechanical crystals," arXiv:1512.04166 (Optica 3, 1404, 2016);
F. Moraes *et al.*, "Optimization of diamond optomechanical crystal cavities," arXiv:2207.00951.

---

Co-designed photonic/phononic crystal structures for SnV (619 nm) cavity QED in diamond.
COMSOL 6.4 band-structure simulations driven from Python (`mph`) on a remote Windows machine.

**Start with [`CLAUDE.md`](CLAUDE.md)**: project stages, current state, confirmed model geometry,
material-override pattern, infrastructure notes, and the decision log.

## Layout

| Path | What |
|------|------|
| `CLAUDE.md` | Project driver: state, parameters, geometry ground truth, decisions |
| `agents/` | Domain context: COMSOL, phononic, photonic, co-design |
| `scripts/` | Shared utilities: `comsol_utils.py` (client, eigenvalue extraction), `remote_runner.py` (SSH launch/status/pull), `cell_placement.py` (hole-in-cell feasibility + cell shift), `schematic.py` (geometry-exact setup figures); 1D: `build_nanobeam_model.py`, `build_cavity_model.py`, `cavity_taper.py`, `cavity_eval.py`, `cavity_pipeline.py`, `cavity_designs.py`, `cavity_fields.py`, `plot_cavity_sweeps.py` |
| `runs/<name>/` | One folder per simulation run: `sweep.py`, analysis/plot scripts, `data/`, `figures/` (incl. `schematic.png`) |
| `tests/` | `test_sweep_plan.py` (sweep-plan feasibility checks) |
| `COMSOL_screenshots/` | GUI screenshots used to confirm model settings |
| `docs/gui_inspection/` | Parameter notes from GUI inspection |
| `archive/` | Superseded scripts/results (circular-hole era, old diamond runs, MATLAB, legacy UI) |

## Runs

| Run | Status |
|-----|--------|
| `diamond_mech_v1` | Done: a=300 nm nominal |
| `diamond_dw_sweep` | Done: 3x3 d x w at a=300 nm |
| `diamond_a_sweep` | a = 150-275 nm x 3x3 (d/a, w/a); see its `analyze.py` |
| `diamond_a_large` | Paused 6/45 (a 600-1000 nm) |
| `nanobeam_oh2026` | Done: Oh 2026 mirror cell reproduced (mech + optics) |
| `nanobeam_619` | Done: 619 nm mirror-cell screen (optics) + breathing-class bands |
| `cavity_oh2026` | Done: Oh 2026 full cavity reproduced (verification.png) |
| `cavity_619` | Done (w 550, 60 nm): (a, d) map 50/50, taper-shape sweep; field maps; Lumerical replicas in `lumerical/` (runs on the old PC, `lumerical/oldpc/`) |
| `cavity_619_mf80` | Stopped 10/15 (w 550, 80 nm; superseded by the width study) |
| `cavity_619_width` | Width study: w650/w600 x 60/80 nm (best 60 nm device: w650 d0.10 ξ6 χ4, Q 1.8e7, 9.67 GHz); w700/80 nm queued |
| `cavity_619_final` | Queued: re-finalize (confirmation solves) + final devices (bands both y-parities, fields) + .fsp builds |

1D nanobeam summary: [`docs/nanobeam_1d_summary.pdf`](docs/nanobeam_1d_summary.pdf). Slide figures for the whole design process: `docs/design_process/` (`python docs/design_process/make_all.py --pull`).

## Running

```bash
python scripts/remote_runner.py runs/<name>/sweep.py   # launch detached on the COMSOL machine
python scripts/remote_runner.py --status               # job status + log tail + pull runs/<name>/data
python runs/<name>/analyze.py                          # local analysis
```
