# Agent: Lumerical FDTD Specialist (shared)

**Shared by:** optomechanics, sic_diamond_nanobeams, invdes_bragg. Canonical copy:
`~/Documents/shared_agents/lumerical_specialist.md`; each project's `agents/lumerical_specialist.md` is a symlink to it.
Edit it here only, and keep project-specific results in each project's CLAUDE.md. Created 2026-10-21 from the SiC version.
**Domain:** Lumerical FDTD via lumapi Python and .lsf: building .fsp/.lsf files, Bloch band structures, Qanalysis cavities,
lumopt adjoint runs (the method side lives in invdes_bragg/agents/inverse_design_specialist.md), remote sweeps.
**Global rules:** also see `~/.claude/CLAUDE.md` "Lumerical Scripting". Its metalens machine (`<USER>@<LAB_HOST>`, v242)
timed out on 2026-10-15, so don't rely on it.

---

## Machines

| Machine | Access | Lumerical | Python | Use |
|---|---|---|---|---|
| **GPU computer** <GPU_HOSTNAME> | `<USER>@<GPU_HOST>` | v251 + **v261** (`C:\Program Files\Lumerical\v261`, python `v261\python-3.13.1`, lumopt2 OK, 2026-10-21) | `C:\Program Files\ANSYS Inc\v251\Lumerical\python-3.9.9-embed-amd64\python.exe` | SiC runs since 2026-10-16 (RTX 5070 Ti, about 12x faster than the old PC) |
| **Old PC** DESKTOP-BBQLCD3 | `<USER>@<LUMERICAL_HOST>` | v211 | `py -3.8` (anaconda) | optomechanics queue, 8 cores |
| jv-adamantoise | `<USER>@<COMSOL_HOST>` | v252 (builds only) | | **COMSOL machine. NEVER run Lumerical solves here** (user rule) |

- All access is over Tailscale with key `~/.ssh/id_ed25519`. Licenses work over SSH (sedna). On adamantoise, SSH lands in a TEMP
  profile, so set `ANSYSLMD_LICENSE_FILE=<PORT>@<LICENSE_SERVER>` in-process.
- Work dirs: `C:\Users\<user>\Documents\<project>\lumerical`, always on local drives (never OneDrive or other synced drives).
- **GPU computer is a shared lab machine.** Do NOT edit `%APPDATA%\Lumerical\FDTD Solutions.ini` there. Since 10/16, GPU runs started
  from the GUI or API return instantly with no data, so `lum_run.py --gpu` does the following:
  1. pass 1 builds `<name>_check.fsp`;
  2. `fdtd-engine.exe -t 16 -gpu <file>` runs it;
  3. pass 2 loads the results.
  GPU runs need express mode plus `setresource` device type GPU. Results were validated against the CPU and the optomechanics finals.
- **Disk:** full-cavity work files reach up to 4.5 GB each, and C: on the GPU computer filled to 0 on 10/16. Delete `<name>_work.fsp`
  and `_work/` after each point (`lum_run.py` does this by default; `--keep-work` keeps them). Check free space before long queues.
- **Launching:** for detached runs, write a .bat and start it with `Invoke-CimMethod Win32_Process Create`. Inline cmd quoting
  breaks, and `Start-Process -WindowStyle Hidden` gives 0-byte logs. Synchronous SSH is fine for short jobs. Helper:
  `sic_diamond_nanobeams/scripts/oldpc_runner.py block|launch|status|pull [--gpu]` with remote `lum_run.py`, which is
  per-point resumable (try/except, skips an existing .mat, writes `<name>_failed.txt`). Copy it rather than rewriting it.
- Ask before using a machine that another project's queue is on. Optomechanics and SiC have had shared queues on the old PC.

## v261 on the GPU computer (2026-10-21)

- v261 GPU solves work through the engine: build with the v261 API, then run `C:\Program Files\Lumerical\v261\bin\fdtd-engine.exe -t 16
  -gpu <file>` from Python, then load. Express mode, Bloch + Qanalysis OK (about 3.5 min per toblerone unit cell, 1.5 ps).
  There is **no v261 CPU license** on that machine (user 2026-10-21), so run GPU only.
- The v261 bundled python 3.13 has a SyntaxWarning in the v251 lumapi.py; harmless, but a sign that the wrong lumapi was imported.
- Mode source n_eff without a run: `select('src'); updatesourcemode()` then `getresult('src', 'neff')` (dataset: lambda, neff).
  `get('effective index')` does not exist.
- DFT monitor at one wavelength: set `frequency points` 1, `frequency span` 0 and `frequency center` c/lam. Setting `wavelength center`
  with span 0 read back as a different wavelength (601.7 instead of 637 nm).
- Stopping a .bat queue but letting the current job finish: kill ONLY the queue's `cmd.exe` (taskkill /F /PID, without /T). The
  running python child keeps going and nothing after it starts. With /T the whole tree dies. Rename the .bat afterwards.

### lumopt2 / v261 object notes (2026-10-21)
- `express mode` is OBSOLETE in v261 (get/set errors). Choose the GPU with the resource manager or `fdtd-engine -gpu`.
- `addfieldregion` creates a FieldRegion. Its properties are like a DFT monitor (monitor type Point / Linear Y / 2D X-normal ...,
  frequency settings, `source mode`, `base amplitude`). There is NO down-sample property.
- Ports: `addport` inside `FDTD::ports`. `setnamed('FDTD::ports', 'source port', '')` is accepted (no port source;
  a mode source drives).
- lumopt2 `Project.generate()` builds in memory but does NOT save a .fsp. Save one yourself for inspection. It adds
  optimization_mesh / optimization_dft / optimization_index / optimization_nk (Import).
- lumopt2's LocalRunner uses fdtd.run / addjob + runjobs (job manager). On the GPU computer, subclass it to call the engine
  directly (invdes_bragg/runs/invdes_test/engine_runner.py).

## lumapi rules

- One session per sweep: `with lumapi.FDTD(hide=True) as fdtd:`, with `switchtolayout()` between runs.
- Before `import lumapi`, add `<install>\api\python` to sys.path and `<install>\bin` to PATH, using the version paths above.
- **Call `fdtd.save(path)` before the first `run()`.** Without it, a "save as" dialog hangs headless runs.
- Materials touching a boundary (substrate, waveguide ports) must extend THROUGH the FDTD region and PML, never end flush with it.
- Keep boundaries more than about 1 lambda from monitors in the normal direction.
- Use ASCII-only `print()` on Windows (cp1252).
- **Safe mode (API) blocks `system()` and `rm()`.** Pre-create output dirs from Python and delete files from Python.
- To post-process a finished .fsp without re-running: `lumapi.FDTD(filename=..., hide=True)`.
- `.mat` files written by .lsf `matlabsave` are v7.3, so read them with h5py and convert scalars with `np.array(x).ravel()[0]`.
- **Monitor data comes back UNFOLDED across symmetry planes**, e.g. y spans -ymax..+ymax even when y min is 0. Index with
  argmin(|y|) and use |y| in masks.
- Symmetry BC naming (verified 10/20): Anti-Symmetric means tangential E odd and normal E even. Check it against the intended mode
  parity on the first run.
- Running jobs keep the code they imported, so edits apply only to new launches.

## Full cavities (Qanalysis)

- Portable .lsf replicas use `basedir = ""` (meaning pwd) and output files prefixed `<name>_`. Per-point reference values
  (COMSOL lambda and Q) go in `<name>_points.json`. Template: `optomechanics/runs/cavity_619/lumerical/make_lsf.py`.
  The SiC version is `sic_diamond_nanobeams/scripts/cavity_lsf.py`, with v3 monitors and a bridge-centered option.
- For suspended beams, use symmetry (x/y anti-symmetric, z symmetric). **With a substrate, drop the z symmetry**: the diamond runs
  into the bottom PML.
- With symmetry on, put the Qanalysis probes inside the simulated octant.
- A Qanalysis Q at 1.5 ps is only a lower bound once Q is about 1e6 or higher. Lengthen the run or fit the field decay.
- Field maps must use the fine grid and a monitor at the resonance; coarse maps came out off resonance.
- Benchmarks:
  - optomechanics best diamond device: Lumerical 618.88 nm vs COMSOL 619.50 nm (-0.1 %);
  - GPU reproductions of the optomechanics finals: 618.77 / 618.73 nm;
  - about 10 min per full-cavity point (1/8 symmetry, 1.5 ps) on the old PC.

## Mirror-cell bands (Bloch)

- Unit cell a in x with Bloch BCs and kx set on the FDTD region. Use y parity via the y0 BC; z uses PML, or symmetry if suspended.
- Excite with several randomly placed and oriented dipoles away from symmetry planes, and use several time monitors. The FFT of
  the time signals gives the bands. Frequency resolution is about 1/sim_time.
- A screen only needs kx = pi/a (X point). Run the full Gamma to X sweep for shortlisted cells only.
- Mark the air and substrate light lines on band plots. Modes above a light line show up as broad, decaying peaks.
- Validated 10/16: SiC-project diamond cell vs COMSOL agreed to +0.14 % / +0.07 %. Fast screen settings (mesh 10 / pad 800 / 0.5 ps)
  were within 0.07 %.

## lumopt (adjoint inverse design): solver-side notes

- **lumopt2** (`ansys.lumerical.core.lumopt2`, Lumerical 2026 R1 v261) is what the user's library `alexsunthesun/lumerical-invdes`
  (`~/Documents/lumerical-invdes`) uses, on Linux. The GPU computer has v261 since 2026-10-20 (lumopt2 import verified 2026-10-21).
  **sys.path.insert(0, v261 api\python)**: with append, the v251 lumapi loads first.
- Duplicate object names (e.g. several `GDS_LAYER_1:0` groups): `set('name')` / `setnamed(..., 'name', ...)` fail and `groupscope` picks the
  first match. Read them with `getnamed(name, prop, index)` / `getnamednumber(name)`, and children with `getnamed('grp::poly', prop, k)`.
- Legacy lumopt ships with Lumerical under `<install>\api\python\lumopt`. **Check that it imports on each machine (v211 old PC,
  v251 GPU) before scripting.** The API changed between releases.
- It opens its own FDTD sessions: per iteration, a forward run plus an adjoint run. GPU use with lumopt is **untested**, because
  the GPU engine workaround above may not apply to lumopt-managed runs. Test on one iteration first.
- Base-script conventions (verify on the installed version): the source is named `source`, the design-region field monitor
  is `opt_fields`, and the FOM monitor is a mode-expansion or power monitor named in the FOM object.
