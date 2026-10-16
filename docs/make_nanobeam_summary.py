"""
make_nanobeam_summary.py  (Mac)
Build docs/nanobeam_1d_summary.pdf: the 1D diamond nanobeam optomechanical-crystal study, step by step,
with the figures and numbers from each step. Sections whose data are not in yet are kept as titled
placeholders. Re-run any time; figures are read from the run folders as they exist.

Usage (from project root):
    python docs/make_nanobeam_summary.py
"""
import datetime
import json
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path('.')
OUT = ROOT / 'docs' / 'nanobeam_1d_summary.pdf'
ss = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=ss['Heading1'], fontSize=15, spaceBefore=6, spaceAfter=6)
H2 = ParagraphStyle('H2', parent=ss['Heading2'], fontSize=12, spaceBefore=8, spaceAfter=4)
B = ParagraphStyle('B', parent=ss['BodyText'], fontSize=9.5, leading=12.5)
CAP = ParagraphStyle('CAP', parent=B, fontSize=8.5, textColor=colors.HexColor('#444444'), alignment=TA_CENTER)
PEND = ParagraphStyle('PEND', parent=B, textColor=colors.HexColor('#888888'), fontName='Helvetica-Oblique')
story = []


def h1(t): story.append(Paragraph(t, H1))
def h2(t): story.append(Paragraph(t, H2))
def p(t): story.append(Paragraph(t, B))
def bullets(items): [story.append(Paragraph('&bull; ' + i, B)) for i in items]


def fig(path, caption, max_w=6.8, max_h=8.2):
    f = ROOT / path
    if not f.exists():
        pending(f'figure {path} not available yet'); return
    w, h = PILImage.open(f).size
    W = max_w * inch; H = W * h / w
    if H > max_h * inch:
        H = max_h * inch; W = H * w / h
    story.append(KeepTogether([Image(str(f), width=W, height=H), Paragraph(caption, CAP), Spacer(1, 8)]))


def table(rows, widths=None):
    t = Table(rows, colWidths=widths, hAlign='CENTER')
    t.setStyle(TableStyle([('FONT', (0, 0), (-1, -1), 'Helvetica', 8.5),
                           ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8.5),
                           ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                           ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEEEEE')),
                           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    story.append(t); story.append(Spacer(1, 8))


def pending(what):
    t = Table([[Paragraph('Pending: ' + what, PEND)]], colWidths=[6.8 * inch], rowHeights=[0.9 * inch])
    t.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#BBBBBB')),
                           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    story.append(t); story.append(Spacer(1, 8))


# ------------------------------------------------------------------ title
story.append(Paragraph('1D diamond nanobeam optomechanical crystal for the SnV center', ParagraphStyle(
    'T', parent=H1, fontSize=18, alignment=TA_CENTER)))
story.append(Paragraph(f'Study summary &mdash; Abby &mdash; generated {datetime.date.today().isoformat()}', CAP))
story.append(Spacer(1, 10))
p('<b>Goal.</b> A diamond nanobeam cavity whose fundamental TE-like optical mode sits at the SnV zero-phonon line '
  '(619 nm, 484 THz, n = 2.41) and whose co-localized mechanical breathing mode sits at or below 10 GHz, following '
  'the design approach of Oh et al., Optica 13, 485 (2026): symmetry-protected optical and mechanical '
  '<i>quasi</i>-band gaps in an elliptical-hole mirror cell, with a smooth taper to a central defect cell '
  '(the Chan, Caltech PhD thesis 2012 parameterization). A complete mechanical gap (for Q<sub>m</sub>) comes later from a 2D shield.')
p('<b>Tools.</b> COMSOL 6.4 driven from Python (mph) on the lab Windows machine; isotropic diamond '
  '(E = 1050 GPa, &nu; = 0.07, &rho; = 3500 kg/m&sup3;); Lumerical FDTD for independent optical verification (later).')
p('<b>Contents.</b> 1 Mirror-cell model &nbsp; 2 Validation: Oh mirror cell &nbsp; 3 Mirror-cell design at 619 nm &nbsp; '
  '4 Full-cavity method &nbsp; 5 Full-cavity model &nbsp; 6 Validation: Oh cavity &nbsp; 7 619 nm cavity: (a, d) sweep &nbsp; '
  '8 Taper-shape sweep, 60 nm &nbsp; 9 Breathing-mode identification &nbsp; 10 Beam-width study (60 and 80 nm) &nbsp; '
  '11 Selection and final devices &nbsp; 12 Lumerical verification &nbsp; 13 Open items')

# ------------------------------------------------------------------ 1
story.append(PageBreak()); h1('1. Mirror-cell model')
p('One period of the nanobeam (period a, width w, thickness t, elliptical hole hx &times; hy), modeled as a quarter cell '
  'with Floquet periodicity along x and symmetry planes at y = 0 and z = 0 (scripts/build_nanobeam_model.py). '
  'Mechanics on the beam only, in four vector-symmetry classes (Symmetry/Antisymmetry on each plane: Y&plusmn;Z&plusmn;); '
  'Y+Z+ is the breathing class. Optics on beam + 1.5 &micro;m air: TE-like class = PEC on y = 0, PMC on z = 0; guided '
  'modes below the light line f = ck/2&pi;.')
fig('runs/nanobeam_1d/figures/schematic_proposed.png', 'Mirror-cell model: geometry, domains and boundary conditions.')

# ------------------------------------------------------------------ 2
story.append(PageBreak()); h1('2. Validation: Oh 2026 mirror cell')
p('Oh mirror cell (a, w, hx, hy, t) = (650, 800, 343, 617, 250) nm, compared with Oh Fig. 1(d, e) digitized point by point.')
table([['', 'me', 'Oh 2026'],
       ['Y+Z+ mechanical quasi-gap (GHz)', '3.62 - 7.16', '3.59 - 7.15'],
       ['TE band edges at X (THz), n = 2.39', '174.4 / 212.5', '175.2 / 213.8'],
       ['mesh convergence (t/5 vs t/8, mech)', 'median 5e-4', ''],
       ['optical mesh convergence', '6e-5', '']], [2.8 * inch, 1.6 * inch, 1.6 * inch])
fig('runs/nanobeam_oh2026/figures_compare.png', 'Mechanical bands, me vs Oh Fig. 1(e).', max_h=4.2)
fig('runs/nanobeam_oh2026/figures_compare_optical.png', 'TE optical bands, me vs Oh Fig. 1(d).', max_h=4.2)
h2('2b. Elastic model (isotropic vs cubic anisotropic)')
p('Oh does not state his elastic model. Test: mirror-cell bands with cubic diamond (C11, C12, C44 = 1076, 125, 578 GPa), '
  'beam along [100] and along [110], vs every digitized point. Isotropic so far: median error 45 MHz (Y+Z+), 50 MHz (others).')
pending('anisotropic [100] / [110] band comparison (script runs/nanobeam_oh2026/bands_aniso.py; parked)')

# ------------------------------------------------------------------ 3
story.append(PageBreak()); h1('3. Mirror-cell design at 619 nm (t = 120 nm)')
p('<b>Stage 1 (optics at X).</b> 144 cells: w 350-650, a 220-295, hx/a 0.45-0.60, hy/w 0.60-0.77. 68 contain 619 nm in the TE gap.')
fig('runs/nanobeam_619/stage1_optical.png', 'TE gap at X (nm); color = gap center - 619 nm; hatched = 619 nm outside the gap.', max_h=6.0)
p('<b>Stage 2 (breathing-class mechanics).</b> Y+Z+ bands for the 68 cells; 48 also hold 10 GHz in the band 1-2 quasi-gap. '
  'The beam width sets the gap: w 650 ~5-10 GHz, w 550 ~6-12.5 GHz, w 450 ~7-15 GHz, w 350 ~9-19 GHz.')
fig('runs/nanobeam_619/stage2_mech.png', 'Y+Z+ quasi-gap (bands 1-2), GHz; color = gap center - 10 GHz; hatched = 10 GHz outside.', max_h=6.0)
fig('runs/nanobeam_619/candidates_bands.png', 'Optical (top) and mechanical Y+Z+ (bottom) bands of the three candidate cells.', max_h=5.0)
p('Favored cell: <b>w 550, a 220, hx/a 0.53, hy/w 0.77</b> (breathing gap 6.2-11.6 GHz, optical 551-712 nm). Its breathing band '
  'at &Gamma; (11.7 GHz) needs only ~15 % pull to reach 10 GHz.')

# ------------------------------------------------------------------ 4
story.append(PageBreak()); h1('4. Full-cavity method')
p('Cells j = 0 (defect, beam center) ... M (mirror), then n<sub>mirror</sub> mirror cells (Chan thesis &sect;3.4; Oh Supplement S3):')
bullets(['period: a<sub>j</sub>/a<sub>m</sub> = 1 - d (2y&sup3; - 3y&sup2; + 1), y = &eta;-remap(j/M)',
         'hole area: 1 - s<sub>j</sub> = &chi; (1 - a<sub>j</sub>/a<sub>m</sub>);  hole aspect (hy/hx): r<sub>j</sub> = (a<sub>j</sub>/a<sub>m</sub>)<super>&xi;</super>',
         'optical cavity mode: X-point dielectric band pushed up into the gap by the smaller defect period',
         'mechanical cavity mode: Y+Z+ breathing band at &Gamma; pulled down by flatter center holes',
         'diamond photoelastic constants (p11, p12, p44) = (-0.25, 0.043, -0.172) (Burek 2016, citing Lang 2009)'])
pr = ROOT / 'runs/nanobeam_oh2026/reference/oh2026_cavity_profile.json'
if pr.exists():
    r = json.load(open(pr))
    p('<b>Oh taper measured from his Fig. 1(b)</b> (45 nm/pixel): 41 holes = center + ~10 taper + ~10 mirror cells per side; '
      f"Chan cubic fit d = {r['chan_taper_fit']['d']}, M = {r['chan_taper_fit']['M']}, &eta; = {r['chan_taper_fit']['eta']} "
      f"(rms {r['chan_taper_fit']['rms']}); center hy &asymp; 208 nm, hx &asymp; 400 &plusmn; 45 nm &rarr; &xi; &asymp; 6, &chi; &asymp; 3.5. "
      'Optical E<sub>y</sub> is odd about the center hole (x = 0 node).')

# ------------------------------------------------------------------ 5
h1('5. Full-cavity model')
p('One-eighth of the beam (scripts/build_cavity_model.py): symmetry planes x = 0 (mech Symmetry / optics PEC), y = 0 '
  '(Symmetry / PEC), z = 0 (Symmetry / PMC); air + PML on +x, +y, +z; the beam runs into the +x PML (light through the '
  'mirrors is absorbed); mechanics fixed at the beam end; one shared mesh for both physics. Optical Q from the complex '
  'eigenfrequency; cavity mode = most localized mode with Q > 10&sup3;; breathing mode = localized, in-phase sidewall '
  'motion and large sidewall amplitude (section 9).')
fig('runs/cavity_oh2026/schematic.png', 'Full-cavity model (Oh 2026 cavity shown).', max_h=5.2)

# ------------------------------------------------------------------ 6
story.append(PageBreak()); h1('6. Validation: Oh 2026 cavity')
table([['', 'me', 'Oh sim', 'Oh measured'],
       ['optical mode (THz)', '188.9', '192', '190.1'],
       ['breathing mode (GHz)', '6.51', '6.34', '6.23'],
       ['optical Q', '1.0e5', '-', '3.8e4'],
       ['mechanical Q', '1.9e11 (ideal geometry)', 'not simulated', '1.9e6']], [1.9 * inch, 1.8 * inch, 1.3 * inch, 1.3 * inch])
fig('runs/cavity_oh2026/verification.png', 'Oh cavity: optical E<sub>y</sub> (a), first and second breathing modes on the deformed beam (b, c), comparison (d).', max_h=6.5)
fig('runs/cavity_oh2026/mech_modes.png', 'All localized mechanical modes (deformed top face) and their sidewall motion; modes 15-16 breathe.', max_h=7.5)
h2('6b. Mechanical Q benchmark')
p('Ideal symmetric geometry gives Q<sub>m</sub> ~ 10<super>10</super>-10<super>11</super> (quasi-gap protection). Realistic Q<sub>m</sub> needs '
  'symmetry breaking (fabrication disorder) and Oh\'s cross-shaped acoustic shield (SEM pitch ~0.8 &micro;m).')
pending('Q<sub>m</sub> vs hole disorder (&sigma; = 1, 2, 4, 8 nm), without and with the cross shield')

# ------------------------------------------------------------------ 7
story.append(PageBreak()); h1('7. 619 nm cavity: (a, d) sweep')
p('Favored mirror cell (w 550, t 120, hx/a 0.53, hy/w 0.77) with Oh\'s taper shape (M 10, &eta; 1, &xi; 6, &chi; 3.5, 10 mirror cells); '
  'mirror period a 190-235 nm &times; taper depth d 0.10-0.22. Air/PML box reduced to 600/500 nm after a check '
  '(resonance change 2.4e-6, Q change 0.4 %).')
fig('runs/cavity_619/schematic.png', '619 nm cavity template (a 220, d 0.18).', max_h=4.6)
fig('runs/cavity_619/ad_sweep.png', 'Optical resonance (nm), optical Q, breathing frequency (GHz), breathing localization. Hatched: a feature below 60 nm.', max_h=3.0)
ad = ROOT / 'runs/cavity_619/ad_summary.csv'
p('<b>619 nm line</b> (interpolated along a):')
table([['taper depth d', 'a for 619 nm', 'optical Q', 'breathing (GHz)', 'fabricable at 60 nm'],
       ['0.10', '195.2 nm', '3.7e7', '11.14', 'yes'], ['0.13', '200.7 nm', '4.1e6', '10.95', 'no (bridges 51-56 nm)'],
       ['0.16', '205.7 nm', '~1.3e5', '10.86', 'no'], ['0.19', '210.1 nm', '~2e4', '10.93', 'no'],
       ['0.22', '213.7 nm', '~8e3', '11.42', 'no']], [1.1 * inch, 1.1 * inch, 1.0 * inch, 1.2 * inch, 1.9 * inch])
p('Findings: a and d set the resonance (~2 nm per nm of a; deeper d shortens it); shallower tapers give much higher Q; the breathing '
  'mode stays at 10.7-11.6 GHz everywhere and is well localized (0.98-1.00 except at the grid corners). Best point: d 0.10, a 195.2: '
  '619.35 nm, Q 3.0e7 (confirmation solve), breathing 11.14 GHz, 62 nm minimum feature.')

# ------------------------------------------------------------------ 8
story.append(PageBreak()); h1('8. Taper-shape sweep (minimum feature 60 nm)')
p('Center-hole aspect &xi; and area &chi; at d = 0.10, 0.13 and 0.16 on the 619 nm line (2-3 periods per shape, interpolated to 619 nm); '
  'every point checked against the 60 nm minimum feature. Goal: breathing mode &le; 10 GHz at the highest optical Q.')
fig('docs/design_process/18_619_shape_sweep_w550_60nm.png', 'Taper shapes on the 619 nm line, one column per d: optical Q, breathing frequency, '
    'breathing localization, minimum feature. x = &chi;, y = &xi;; outlined = Oh shape from the (a, d) step; hatched = below 60 nm; grey = not run.', max_h=6.5)
p('<b>Result.</b> No fabricable taper shape brings the breathing mode below ~10.9 GHz at w = 550; stronger pulls mostly cost optical Q '
  'or mechanical localization. Best w 550 device: the (a, d) design d 0.10, a 195.2 (Q 3.0e7, 11.14 GHz). The taper is not enough: '
  'widen the beam (breathing frequency ~ 1/w; section 10).')

# ------------------------------------------------------------------ 9
story.append(PageBreak()); h1('9. Breathing-mode identification')
p('Three checks, refined as the sweeps exposed failure modes (2026-10-15):')
bullets(['<b>localization</b> (fraction of |u|&sup2; within 1.5 &micro;m of the center) &ge; 0.8;',
         '<b>sidewall coherence</b> B &gt; 0.5 (the two sidewalls move in phase). The earlier "largest optomechanical overlap among '
         'localized modes" rule picked weak non-breathing modes whenever the breathing mode fell outside the eigenvalue window '
         '(a false 8.2 GHz result); the window is now 60 modes around 11 GHz;',
         '<b>sidewall amplitude ratio</b> S = max sidewall |v| / max |u| &ge; 0.7. B is amplitude-blind: at w 650, d 0.13 a '
         'hole-centered hybrid (S = 0.35) passed it. Clean breathing modes have S = 1.0. Stored for every solve from now on; '
         'older points get it from their field maps and from the confirmation solves (section 11).'])
fig('runs/cavity_619/mech_eval.png', 'w 550: every mechanical mode of the best device (frequency vs localization, color = B); (a, d) map of the '
    'breathing frequency / localization; all points.', max_h=3.2)
fig('docs/design_process/20_mode_profiles_w550.png', 'w 550: optical E<sub>y</sub> and breathing mode on the deformed beam. Top: clean (a, d) design. '
    'Bottom: a shape variant whose "breathing" mode is a double-lobed mode leaking into the mirrors (localization 0.62).', max_h=3.6)

# ------------------------------------------------------------------ 10
story.append(PageBreak()); h1('10. Beam-width study (60 and 80 nm minimum feature)')
p('Same mirror-cell ratios at w = 650 and 600 (650 first): 60 nm cell hx/a 0.53, hy/w 0.77; 80 nm cell hx/a 0.45, hy/w 0.70 '
  '(the earlier w 550 80 nm cell A, hx/a 0.53, had almost no fabricable tapers and a weakly localized breathing mode; dropped). '
  'Per d (0.10, 0.13, 0.16) the period is stepped until 619.4 nm is bracketed (base shape &xi; 4, &chi; 3.5), then up to 8 taper '
  'shapes on the 619 nm line (runs/cavity_619_width/run.py).')
fig('docs/design_process/21_width_w650_60nm.png', 'w 650, 60 nm: taper-shape maps (as section 8). Red slash = field map shows a hybrid, not a breathing mode.', max_h=6.5)
p('<b>w 650, 60 nm.</b> The breathing mode drops by ~1.3 GHz to 9.7-10.4 GHz with no loss of optical Q (3e7 at d 0.13, 1.8e7 at '
  'd 0.10 / &xi; 6 / &chi; 4). Best: <b>d 0.10, &xi; 6, &chi; 4.0, a 190.3: 619.50 nm, Q 1.8e7, breathing 9.67 GHz (localization 0.95, '
  'S 1.0), 64 nm minimum feature.</b> The d 0.13 base design (Q 3.0e7, 9.82 GHz) is a hybrid (S 0.35).')
fig('docs/design_process/25_mode_profiles_w650_60nm.png', 'w 650 finalists: (a, d) design (top; hybrid, sidewalls barely move) vs the shape pick (bottom; clean breathing mode).', max_h=3.6)
p('<b>w 650, 80 nm.</b> 619 nm needs a 184-193 nm; there no taper shape beyond the base keeps every bridge &ge; 80 nm. Best: base shape '
  'd 0.10, a 183.8: Q 5.7e6, breathing 10.53 GHz (localization 0.85): 0.5 GHz above target. Reaching &le; 10 GHz at 80 nm likely '
  'needs a wider beam (w ~700) or a cell with smaller holes.')
for f_, lab in (('22_width_w600_60nm', 'w 600, 60 nm'), ('23_width_w650_80nm', 'w 650, 80 nm'), ('24_width_w600_80nm', 'w 600, 80 nm')):
    fig(f'docs/design_process/{f_}.png', f'{lab}: taper-shape maps.', max_h=6.0)

# ------------------------------------------------------------------ 11
story.append(PageBreak()); h1('11. Selection and final devices (one per minimum feature)')
p('Rule (scripts/cavity_designs.py): fabricable; breathing localization &ge; 0.8; not a field-checked hybrid; breathing &le; 10 GHz '
  'first, highest optical Q; if none meets 10 GHz, lowest breathing frequency. The top 3 per pipeline are re-solved with the '
  'sidewall-amplitude check before the pick (runs/cavity_619_final/deliverables.py, after the width study).')
fig('docs/design_process/26_design_space.png', 'All fabricable 619 nm designs: breathing frequency vs optical Q (marker = width, color = localization). '
    'Star = selected; red x = hybrid; green = target.', max_h=3.6)
fig('docs/design_process/27_selection.png', 'Best design per width and minimum feature (interim, before the confirmation solves).', max_h=2.6)
for mf in ('60 nm', '80 nm'):
    h2(f'Final device, {mf} minimum feature')
    pending('confirmation solve, mirror-cell optical bands (both y-parities: single-mode check) and mechanical bands (4 classes), '
            'device field maps')

# ------------------------------------------------------------------ 12
story.append(PageBreak()); h1('12. Lumerical FDTD verification')
p('Independent optics check (full beam or 1/8 symmetry; Lumerical\'s Qanalysis method, as in the lab\'s nanobeam Q sweeps). All files in '
  'C:\\Users\\abby\\lumerical. Built: lum_w650_mf60_best_check.fsp (current best 60 nm device: w 650, d 0.10, &xi; 6, &chi; 4.0, a 190.3). Sweep replicas, point for point with COMSOL \u03bb and Q alongside: lum_ad_mf60 (50), lum_shape_mf60 (52), '
  'lum_w650_mf60_ad (6), lum_w650_mf60_shape (17) (runs/cavity_619/lumerical/make_lsf.py). Run after COMSOL is idle, with '
  'use_symmetry = 1 and ~1.5 ps (Q ~ 10<super>7</super> cannot be resolved in practical FDTD time; it bounds Q from below).')
pending('.fsp files of the two final devices (build only; queued after the deliverables)')
pending('Lumerical vs COMSOL: resonance and Q heat maps for each sweep, field-map comparison')

# ------------------------------------------------------------------ 13
h1('13. Open items')
bullets(['80 nm device &le; 10 GHz: wider beam (w ~700) or a smaller-hole cell',
         'bridge-centered (even hole count) cavity: field maximum and breathing strain maximum both at the exact center '
         '(now both peak in the first bridge, ~30 nm apart, two mirror sites at x &asymp; &plusmn;95 nm); test on the w 650 finalists',
         'optomechanical coupling (g<sub>0</sub>) in the sweeps is mis-normalized (~10<super>8</super> too small); frequencies and Q unaffected; to debug',
         'mechanical Q benchmark (disorder + cross shield) on the Oh cavity; anisotropic elastic model test on the Oh mirror cell',
         'taper optimization (Oh: genetic algorithm on a g<sub>0</sub>Q<sub>o</sub> fitness) after the final shapes',
         '2D phononic shield at the final breathing frequency (snowflake / cross); 2D snowflake sweep diamond_a_large paused at 6/45'])

doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                        topMargin=0.7 * inch, bottomMargin=0.7 * inch, title='1D nanobeam OMC study', author='Abby')
doc.build(story, onFirstPage=lambda c, d: None,
          onLaterPages=lambda c, d: (c.setFont('Helvetica', 8), c.drawRightString(7.75 * inch, 0.45 * inch, f'{d.page}')))
print(f'Saved {OUT}')
