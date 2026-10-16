"""
make_all.py  (Mac)  -- docs/design_process
Slide-ready figures for the whole 1D nanobeam design process, numbered in order, from mirror-cell
co-design through final cavity selection. Re-run any time; stages whose data isn't in yet get a
'pending' placeholder. Captions: README.md (written here too).

Usage (from project root):
    python docs/design_process/make_all.py          # local data only
    python docs/design_process/make_all.py --pull   # first fetch the cavity sweep data from the COMSOL machine
"""
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, 'scripts')
import plot_cavity_sweeps as S   # noqa: E402

OUT = Path('docs/design_process')
HOST, KEY = '<USER>@<COMSOL_HOST>', str(Path('~/.ssh/id_ed25519').expanduser())
PIPES = [('w550 / 60 nm', 'runs/cavity_619', 60),
         ('w650 / 60 nm', 'runs/cavity_619_width/w650_mf60', 60),
         ('w600 / 60 nm', 'runs/cavity_619_width/w600_mf60', 60),
         ('w650 / 80 nm', 'runs/cavity_619_width/w650_mf80', 80),
         ('w600 / 80 nm', 'runs/cavity_619_width/w600_mf80', 80),
         ('w700 / 80 nm', 'runs/cavity_619_width/w700_mf80', 80)]

# (file name, source png or callable, caption)
FIGS = []


def copy(slug, src, caption):
    """Register a figure; numbers are assigned in registration order (insert stages anywhere)."""
    FIGS.append((f'{len(FIGS) + 1:02d}_{slug}.png', src, caption))


def pending(dst, text):
    fig, ax = plt.subplots(figsize=(10, 3)); ax.axis('off')
    ax.text(0.5, 0.5, f'{text}\n(pending)', ha='center', va='center', fontsize=16, color='0.4')
    fig.savefig(dst, dpi=100, facecolor='white'); plt.close(fig)


def pull():
    for _, rd, _ in PIPES:
        Path(rd, 'data').mkdir(parents=True, exist_ok=True)
        r = subprocess.run(['scp', '-q', '-i', KEY, f'{HOST}:C:/Users/abby/comsol/{rd}/data/*.npz', f'{rd}/data/'],
                           capture_output=True, text=True)
        print(f'pull {rd}: {"ok" if r.returncode == 0 else "nothing yet"}')
    for p in Path('runs').glob('cavity_619_width/*/data'):
        if not any(p.glob('*.npz')):
            p.rmdir(); p.parent.rmdir() if not any(p.parent.iterdir()) else None


# ---------------------------------------------------------------- stage list
# A. 2D snowflake phononic crystal (pipeline + diamond co-design limit)
copy('si_snowflake_cell', 'runs/si_validation/schematic.png',
     'Si snowflake unit cell (a 478, t 220): rhombus primitive cell, Floquet BCs, symmetric / antisymmetric classes.')
copy('si_bands', 'runs/si_validation/figures/Si_band_annotated.png',
     'Si snowflake phononic bands: complete gap 6.5-7.6 GHz; COMSOL-from-Python matches the GUI to < 1 MHz.')
copy('si_validation', 'runs/si_validation/figures/Si_validation_summary.png',
     'Validation: Python-driven COMSOL vs GUI (mechanical spot checks at Gamma, M, K; optical at Gamma).')
copy('diamond_snowflake_bands', 'runs/diamond_mech_v1/figures/diamond_mech_bands.png',
     'Diamond snowflake at a 300 nm (photonic-compatible scale): complete gap 26.6-32.0 GHz.')
copy('diamond_snowflake_dw', 'runs/diamond_dw_sweep/figures/diamond_dw_heatmap.png',
     'Diamond arm length d x arm width w at a 300: gap center 24.8-31.9 GHz.')
copy('diamond_snowflake_a', 'runs/diamond_a_sweep/figures/gap_vs_a.png',
     'Lattice constant sweep: at 619 nm-compatible a the 2D gap stays at ~20-30 GHz -> go to 1D nanobeams, '
     'where the beam width tunes the mechanics nearly independently of the optics.')
# B. 1D nanobeam
copy('mirror_cell_model', 'runs/nanobeam_1d/figures/schematic_proposed.png',
     'Mirror (unit) cell model: quarter cell, Floquet in x, symmetry planes y = 0 / z = 0 select the mode classes.')
copy('oh_mirror_validation_mech', 'runs/nanobeam_oh2026/figures_compare.png',
     'Validation vs Oh 2026 Fig. 1(e): mechanical bands of his mirror cell (breathing class Y+Z+).')
copy('oh_mirror_validation_optics', 'runs/nanobeam_oh2026/figures_compare_optical.png',
     'Validation vs Oh 2026 Fig. 1(d): TE optical bands of his mirror cell.')
copy('mirror_screen_optics', 'runs/nanobeam_619/stage1_optical.png',
     'Mirror-cell screen at 619 nm, t = 120: TE gap at X over (w, a, hx/a, hy/w); white = gap centered on 619 nm.')
copy('mirror_screen_mechanics', 'runs/nanobeam_619/stage2_mech.png',
     'Same cells: breathing-class mechanical quasi-gap; wider beams pull the gap down (w 650 ~5-10 GHz).')
copy('candidate_mirror_bands', 'runs/nanobeam_619/candidates_bands.png',
     'Optical and mechanical bands of the strongest candidate mirror cells.')
copy('cavity_model', 'runs/cavity_oh2026/schematic.png',
     'Full-cavity model: 1/8 symmetry, Chan-thesis taper (period, hole area chi, hole aspect xi), PML, beam into PML.')
copy('oh_cavity_verification', 'runs/cavity_oh2026/verification.png',
     'Oh 2026 full cavity reproduced (me vs Oh sim/meas): optical mode, breathing mode, Q.')
copy('oh_cavity_mech_modes', 'runs/cavity_oh2026/mech_modes.png',
     'Localized mechanical modes of the Oh cavity; cavity mode = first breathing mode.')
copy('619_cavity_model', 'runs/cavity_619/schematic.png',
     '619 nm cavity template (w 550, t 120, hx/a 0.53, hy/w 0.77).')
copy('619_ad_sweep_w550', 'runs/cavity_619/ad_sweep.png',
     'Step 1 at 619 nm: mirror period a x taper depth d (Oh taper shape). Sets the 619 nm line a(d).')
copy('619_shape_sweep_w550_60nm', lambda dst: S.shape_maps('runs/cavity_619', 60, 'w 550, 60 nm min feature: taper shapes on the 619 nm line', dst),
     'Step 2: taper shape (xi, chi) on the 619 nm line. Breathing stays >= 10.9 GHz at w 550 -> widen the beam.')
copy('mech_evaluation_w550', 'runs/cavity_619/mech_eval.png',
     'Breathing-mode identification: in-phase sidewall motion + localization (shape variants often leak).')
copy('mode_profiles_w550', 'runs/cavity_619/mode_profiles.png',
     'Optical Ey and deformed breathing mode on the device: clean (a, d) design vs a leaky shape variant.')
for label, rd, mf in PIPES[1:]:
    tag = label.replace(' / ', '_').replace(' nm', 'nm')
    copy(f'width_{tag}',
         (lambda dst, rd=rd, mf=mf, label=label: S.shape_maps(rd, mf, f'{label} min feature: taper shapes on the 619 nm line', dst)
          if Path(rd, 'data').exists() and S.designs(rd) else pending(dst, label)),
         f'Step 3, width study {label}: same maps. Outlined = base shape of the (a, d) step; red slash = field map shows a hybrid, not a breathing mode.')
copy('mode_profiles_w650_60nm',
     lambda dst: (subprocess.run([sys.executable, 'runs/cavity_619/plot_fields.py', 'runs/cavity_619_width/w650_mf60/data',
                                  str(dst), 'ad=(a, d) design', 'shape=shape-sweep pick'], check=True)
                  if Path('runs/cavity_619_width/w650_mf60/data/fields_ad.npz').exists() else pending(dst, 'w650 mode profiles')),
     'w650 / 60 nm finalists: the (a, d) design\'s 9.82 GHz mode is a hole-centered hybrid (sidewalls barely move); the shape pick d 0.10 / xi 6 / chi 4 is a clean breathing mode at 9.67 GHz -> selected.')
copy('design_space', lambda dst: S.design_space(PIPES, dst),
     'All fabricable 619 nm designs, breathing vs optical Q (marker = width, color = localization); green = target.')
copy('selection', lambda dst: S.selection_table(PIPES, dst),
     'Best design per width / min feature; selected (green): breathing <= 10 GHz, localization >= 0.8, sidewall ratio >= 0.7 where checked, highest Q.')
for mf in ('60nm', '80nm'):
    src = f'runs/cavity_619_final/figures/final_{mf}.png'
    copy(f'final_device_{mf}', src if Path(src).exists() else (lambda dst, mf=mf: pending(dst, f'final {mf} device: bands + fields')),
         f'Final {mf} device: mirror-cell bands (incl. higher-order optical family), optical + breathing field maps.')


if __name__ == '__main__':
    if '--pull' in sys.argv:
        pull()
    for old in OUT.glob('[0-9][0-9]_*.png'):
        old.unlink()
    lines = ['# 1D nanobeam design process: figures', '',
             'Generated by `python docs/design_process/make_all.py [--pull]`; numbered in presentation order.', '']
    for name, src, cap in FIGS:
        dst = OUT / name
        try:
            if callable(src):
                src(dst)
            elif Path(src).exists():
                shutil.copy(src, dst)
            else:
                pending(dst, name)
            print('ok  ', name)
        except Exception as e:                       # one broken stage never blocks the rest
            pending(dst, f'{name}: {e}')
            print('FAIL', name, e)
        lines.append(f'- **{name}**: {cap}')
    (OUT / 'README.md').write_text('\n'.join(lines) + '\n')
    print(f'wrote {OUT}/README.md')
