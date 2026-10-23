"""
make_shield_report.py  (Mac)  -- docs/shield_report
PDF: best gap-confined 1D nanobeam OMC (diamond, 619 nm), how it was made, band diagrams, full-cavity optics + mechanics
(displacement and strain), and the square-lattice cross phonon shield (designed on the Dmitry cloud software, checked in COMSOL)
added at the anchors, with the mechanical-Q comparison.
Run from the project root after `python runs/shield_619/plot_shield.py --pull`:
    python docs/shield_report/make_shield_report.py
"""
import json
from pathlib import Path

import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)
from PIL import Image as PILImage

OUT = Path('docs/shield_report/omc_shield_report.pdf')
DEV = Path('best_devices/60nm_w650_d0.086_xi1.79_chi-6.97_gapconf')
SH = Path('runs/shield_619'); DMD = Path('runs/dmitry/shield1_dmitry')
ss = getSampleStyleSheet()
H1, H2, B = ss['Heading1'], ss['Heading2'], ss['BodyText']
B.fontSize, B.leading = 9.5, 12.5
CAP = ParagraphStyle('cap', parent=B, fontSize=8, leading=10, textColor=colors.HexColor('#333333'))
SMALL = ParagraphStyle('small', parent=B, fontSize=8, leading=10)
W = 7.0 * inch


def fig(path, caption, width=W):
    im = PILImage.open(path); w, h = im.size
    return KeepTogether([Image(str(path), width=width, height=width * h / w), Paragraph(caption, CAP), Spacer(1, 8)])


def table(rows, widths=None, head=True):
    t = Table(rows, colWidths=widths, hAlign='LEFT')
    st = [('FONT', (0, 0), (-1, -1), 'Helvetica', 8), ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 2), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]
    if head:
        st += [('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8), ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8e8e8'))]
    t.setStyle(TableStyle(st))
    return t


def P(s, st=B):
    return Paragraph(s, st)


def main():
    S = json.load(open(DEV / 'summary.json')); c = S['cfg']
    Q = json.load(open(SH / 'data' / 'qm_summary.json'))
    G = json.load(open(DMD / 'gaps_dmitry.json')); cmpd = json.load(open(DMD / 'compare_comsol_dmitry.json'))
    est = json.load(open(DMD / 'estimate1s_dmitry.json'))
    story = []
    story += [P('Gap-confined diamond nanobeam optomechanical cavity with a cross phonon shield', ss['Title']),
              P('SnV (619 nm) optical mode and 9.8 GHz breathing mode; diamond t = 120 nm; 60 nm minimum feature. '
                'COMSOL unless marked "Dmitry cloud" (laghai/nanophotonics-cloud). Ideal geometry, vertical sidewalls, isotropic diamond '
                '(E 1050 GPa, ν 0.07, ρ 3500 kg/m³, n 2.41).', SMALL), Spacer(1, 6)]

    # ------------------------------------------------------------------ 1
    story += [P('1. Best design', H1)]
    mf = S['min_feature']
    rows = [['quantity', 'value'],
            ['beam width / thickness', f"{c['w']} nm / {c['t']} nm"],
            ['mirror cell', f"a {c['a_m']} nm, hole hx {c['hx_m']:.1f} nm (hx/a 0.40), hy {c['hy_m']:.0f} nm (hy/w 0.60)"],
            ['taper (Chan 2012 thesis form)', f"M {c['M']} cells, d {c['d']}, η {c['eta']:g}, ξ {c['xi']}, χ {c['chi']}; {c['n_mirror']} mirror cells per side"],
            ['optical mode', f"{S['lam']:.2f} nm, Q {S['Q']:.2g}"],
            ['breathing mode', f"{S['fb']:.3f} GHz (localization {S['loc']:.2f}, sidewall ratio {S['S']:.2f})"],
            ['mirror breathing-class (Y+Z+) gap', f"{S['gap'][0]:.2f}–{S['gap'][1]:.2f} GHz; mode sits {S['margin']:.2f} GHz below the top"],
            ['second localized mode', f"{S['others'][0]:.2f} GHz (also in the gap)"],
            ['m_eff / x_zpf', f"{S['meff_fg']:.0f} fg / {S['xzpf_fm']:.2f} fm"],
            ['zero-point strain (peak, midplane)', f"volumetric {S['eps_vol']:.1e}, εxx − εyy {S['eps_dif']:.1e}"],
            ['smallest features', f"bridge {mf['bridge']:.0f}, rail {mf['rail']:.0f}, hole {mf['hole']:.0f} nm"]]
    story += [table(rows, [2.2 * inch, 4.8 * inch]), Spacer(1, 6)]
    story += [P('Other gap-confined designs from the same study (all 60 nm, all with the breathing mode inside the mirror gap):', B)]
    rd = [l for l in Path('best_devices/README.md').read_text().splitlines() if l.startswith('| w')]
    rows = [['design', 'w', 'a', 'd, ξ, χ', 'λ (nm)', 'optical Q', 'breathing (GHz)', 'gap (GHz)', 'margin']]
    for l in rd:
        x = [s.strip() for s in l.strip('|').split('|')]
        rows.append(x[:9])
    story += [table(rows, [1.55 * inch, 0.4 * inch, 0.5 * inch, 1.05 * inch, 0.6 * inch, 0.65 * inch, 0.85 * inch, 0.85 * inch, 0.55 * inch])]

    # ------------------------------------------------------------------ 2
    story += [PageBreak(), P('2. How the design was made', H1)]
    for t in [
        '<b>Requirement.</b> The breathing mode must sit inside the mirror cell\'s breathing-class (Y+Z+) band gap, so the mirror '
        'confines it the way it confines light. The earlier best devices put the breathing mode above that gap.',
        '<b>Cavity form.</b> A 1D nanobeam with elliptical holes. Cells j = 0 (center) … M taper from the defect to the mirror cell, '
        'then n_mirror plain mirror cells (Chan PhD thesis 2012, eqs. 3.48–3.53, the form Oh 2026 used): '
        'a_j/a_m = 1 − d(2y³ − 3y² + 1), y = j/M; hole area 1 − s_j = χ(1 − a_j/a_m); aspect r_j = (a_j/a_m)^ξ. '
        'χ &lt; 0 makes the center holes LARGER than the mirror holes.',
        '<b>Unit-cell rule (gap-cell study, 336 cells).</b> (1) A small-hole mirror (hx/a 0.40, hy/w 0.60) raises the top of the '
        'Y+Z+ gap to ~10.9 GHz at w 650. (2) Large center holes (χ &lt; 0) soften the center cell and pull its Γ breathing band down. '
        'The cavity breathing mode lands at the center-cell Γ frequency minus ~0.23 GHz (calibrated on 72 full cavities, rms 0.24 GHz), '
        'so pairs were kept only when both near-degenerate center-cell Γ modes, minus 0.23 GHz, sit inside the mirror gap with margin. '
        'The pair gives (d, ξ, χ) directly: 1 − d = a_c/a_m, s = hx_c·hy_c/(hx_m·hy_m), χ = (1 − s)/d, ξ = ln r / ln(1 − d).',
        '<b>Full-cavity solve.</b> 1/8 COMSOL model (mirror planes x, y, z = 0), optics in an air box with PML (TE-like class, '
        'Ey odd about the center hole), mechanics with the beam end clamped. a_m was stepped until the cavity resonance bracketed '
        '619.4 nm, then one solve at the interpolated a. Breathing mode = localized (≥ 0.8 of |u|² within 1.5 µm), in-phase '
        'sidewalls (B &gt; 0.5), sidewall/axial amplitude ratio S ≥ 0.7; the deformed shape was inspected.',
        '<b>Mirror gaps</b> were recomputed with 13 k-points: the gap top comes from a band-2 dip near k ≈ 0.25 π/a, not Γ.',
        '<b>Selection.</b> All seven designs passed; the table is sorted by optical Q. The best has the highest Q (3.8e6), a 1.05 GHz margin '
        'and 70 nm narrowest bridge. Price paid for gap confinement: optical Q 3.8e6 vs 1–2e7 for the earlier non-gap-confined devices.']:
        story += [P(t), Spacer(1, 4)]

    # ------------------------------------------------------------------ 3
    story += [PageBreak(), P('3. Band diagrams', H1),
              fig(DEV / 'mirror_bands.png', 'Mirror-cell bands (solid) and center-cell bands (dashed). Left: optics, Γ→X, guided bands below '
                  'the light line; red line = cavity mode at 619.3 nm inside the cavity-class gap. Right: mechanics, all four symmetry '
                  'classes; red = breathing class (Y+Z+); shaded = Y+Z+ gap 7.47–10.87 GHz; green = cavity breathing mode 9.81 GHz.')]

    # ------------------------------------------------------------------ 4
    story += [PageBreak(), P('4. Full cavity: optical mode, breathing-mode displacement and strain', H1),
              fig(DEV / 'review.png', 'Full cavity (COMSOL). Top: band diagrams as in section 3. Then: optical Ey at z = 0; breathing mode on the '
                  'deformed top face (color |u|); breathing-mode zero-point volumetric strain εxx+εyy+εzz and shear-type εxx−εyy on the '
                  'midplane (scaled to x_zpf = 2.23 fm), with the optical |E|² = 50 % contour in black. Strain peaks inside the optical '
                  'mode, in the bridges next to the center hole.', width=6.3 * inch)]

    # ------------------------------------------------------------------ 5
    best = [r for r in G if r['covers_981']][0]
    story += [PageBreak(), P('5. Square-lattice cross phonon shield', H1)]
    for t in [
        '<b>Why.</b> The mirror confines the breathing mode only within its own symmetry class (Y+Z+) and only along the beam. '
        'Where the beam lands on the chip, the slab carries waves of every polarization in every direction. A 2D phononic crystal '
        'with a COMPLETE gap around the anchor (Chan et al., APL 2012; Oh et al. 2026 use square-lattice crosses) blocks all of them, '
        'including waves that disorder converts into other classes.',
        f'<b>Design on the Dmitry cloud.</b> Square lattice, cross-shaped holes (bar length h, bar width w, fillet 20 nm) in the same '
        f'120 nm diamond. 12 cells (sweep-c11edac992d7da32c9a8, Dmitry cloud, P2 elements, '
        f'z-symmetric + z-antisymmetric, Γ–X–M–Γ, 8 steps per segment): a 350/450/550/650 nm × bridge a − h 60/100 nm at w 100, '
        f'plus w 70/140 at a 450/550. Cost ${est["usd_expected"]:.2f} expected (${est["usd_ceiling"]:.2f} ceiling). '
        'Every feature ≥ 60 nm. Lattice constant moves the gap (~1/a), bridges set its width, bar width shifts it.',
        f'<b>Chosen cell:</b> a {best["a"]} nm, h {best["h"]} nm, w {best["w"]} nm (bridge {best["bridge"]} nm, solid block 310 nm). '
        f'Complete gap {best["cover"][0][0]:.2f}–{best["cover"][0][1]:.2f} GHz (20 %): it holds both localized modes '
        f'(9.81 and 10.57 GHz). It is the only cell of the 12 that does.',
        f'<b>COMSOL check of that cell</b> (independent model, copy-face Floquet mesh, P2, same k points): gap 9.397–11.472 GHz; '
        f'{cmpd["n"]} modes match the Dmitry cloud to median {cmpd["median"]:.1e}, max {cmpd["max"]:.1e} (relative).']:
        story += [P(t), Spacer(1, 4)]
    story += [fig(DMD / 'shield_sweep_dmitry.png', 'Complete gaps (> 0.8 GHz) of the 12 cross cells (Dmitry cloud). Green: covers both cavity modes.'),
              fig(SH / 'figures' / 'cell_compare.png', 'Bands of the chosen cross cell: COMSOL (lines) vs Dmitry cloud (circles); blue z-symmetric, '
                  'red z-antisymmetric. Shaded: complete gap. The gap edges are set at M (z-symmetric band below, z-antisymmetric band above).')]

    # ------------------------------------------------------------------ 6
    story += [PageBreak(), P('6. Full structure: cavity anchored into the slab, with and without the shield', H1)]
    story += [P('The beam (best design above, with 10, 4 or 2 mirror cells) runs 1 µm past its last mirror cell and lands on a 120 nm '
                'diamond slab; the slab edge next to the beam is free (trench). With the shield, cross holes fill the slab around a '
                '450 × 450 nm solid anchor pad (the pad is enclosed by 4 shield periods in x and y); without it the slab is plain. '
                'Outgoing slab waves are absorbed in 1.5 µm PML layers. Mechanics only (the optical mode is microns from the anchor). '
                'The breathing-mode Q_m here is anchor (clamping) loss of the ideal symmetric structure.'), Spacer(1, 4),
              fig(SH / 'figures' / 'structure.png', 'Top view of the modeled eighth (COMSOL). Gray = diamond, white = holes, purple = PML.')]
    rows = [['mirror cells', 'no shield: f (GHz)', 'no shield: Q_m', 'shield: f (GHz)', 'shield: Q_m', 'Q_m ratio']]
    for n, f0, q0, f1, q1 in Q:
        fmt = lambda v, s: '—' if v is None or not np.isfinite(v) else s.format(v)
        rows.append([str(n), fmt(f0, '{:.3f}'), fmt(q0, '{:.2e}'), fmt(f1, '{:.3f}'), fmt(q1, '{:.2e}'),
                     fmt(q1 / q0 if (q0 and q1 and np.isfinite(q0) and np.isfinite(q1)) else np.nan, '{:.1f}×')])
    story += [table(rows), Spacer(1, 6)]
    if (SH / 'figures' / 'qm_table.png').exists():
        story += [fig(SH / 'figures' / 'qm_table.png', 'Breathing-mode Q_m vs mirror cells, with and without the shield (COMSOL).', width=4.5 * inch)]
    if (SH / 'figures' / 'disp_maps.png').exists():
        story += [fig(SH / 'figures' / 'disp_maps.png', 'Breathing mode |u|² on the top face (log scale, normalized to the peak), without (left) and with '
                      '(right) the shield (COMSOL).')]
    conv = [('nm10_noshield', 'no shield, reference (PML 1.5 µm, slab mesh 30 nm)'), ('nm10_noshield_pml3k', 'no shield, PML 3 µm'),
            ('nm10_shield', 'shield, reference (4 periods, PML 1.5 µm, slab mesh 30 nm)'), ('nm10_shield_pml3k', 'shield, PML 3 µm'),
            ('nm10_shield_fine', 'shield, slab mesh 22 nm'), ('nm10_shield_Ns2', 'shield, 2 periods (same slab size)')]
    crow = [['case (10 mirror cells)', 'f (GHz)', 'Q_m', 'vs reference']]; ref = {}
    for c, lab in conv:
        fn = SH / 'data' / f'{c}.npz'
        if not fn.exists():
            continue
        z = np.load(fn, allow_pickle=True); ib = int(z['i_breath']); f, q = z['f'][ib - 1] / 1e9, z['Q'][ib - 1]
        key = 'shield' if '_shield' in c else 'noshield'; ref.setdefault(key, q)
        crow.append([lab, f'{f:.4f}', f'{q:.2e}', '—' if q == ref[key] and c.count('_') == 1 else f'{q / ref[key]:.2f}×'])
    if len(crow) > 1:
        story += [P('Convergence checks', H2), table(crow, widths=[3.6 * inch, 0.9 * inch, 0.9 * inch, 1.0 * inch]), Spacer(1, 6)]
    notes = Path('docs/shield_report/findings.md')
    if notes.exists():
        story += [P('Findings', H2)] + [P(l) for l in notes.read_text().split('\n\n') if l.strip()]

    # ------------------------------------------------------------------ 6b: 65 nm minimum feature
    q65 = SH / 'data' / 'qm_summary65.json'
    if q65.exists():
        c65 = json.load(open(SH / 'data' / 'cell_compare65.json')) if (SH / 'data' / 'cell_compare65.json').exists() else None
        story += [PageBreak(), P('6b. Fabrication-compliant shield: 65 nm minimum feature', H1),
                  P('The first shield cell has 60 nm bridges, and its first column sits 30 nm from the trench edge. Both are below the '
                    '65 nm minimum feature. A second Dmitry-cloud sweep (sweep-5ff274a306306db50948, 6 cells with 65–70 nm bridges, '
                    '$0.40 expected) found <b>a 460, h 395, w 150 nm, fillet 20</b> (bridge 65, bar 150, block 310 nm): complete gap '
                    '9.46–11.45 GHz (Dmitry cloud)' + (f', {c65["gap"][0]:.2f}–{c65["gap"][1]:.2f} GHz in COMSOL (median |Δf/f| '
                    f'{c65["median"]:.1e}, max {c65["max"]:.1e} over {c65["n"]} modes)' if c65 and c65.get('gap') else '') +
                    '. The lattice is shifted 35 nm away from the trench, so the edge strip is 67.5 nm. The plain-slab comparison uses '
                    'the same, slightly larger slab (2835 × 2800 nm before the PML).'), Spacer(1, 4)]
        if (SH / 'figures' / 'cell_compare65.png').exists():
            story += [fig(SH / 'figures' / 'cell_compare65.png', 'Bands of the 65 nm cross cell: COMSOL (lines) vs Dmitry cloud (circles).')]
        rows = [['mirror cells', 'no shield: f (GHz)', 'no shield: Q_m', 'shield: f (GHz)', 'shield: Q_m', 'Q_m ratio']]
        for n, f0, q0, f1, q1 in json.load(open(q65)):
            ok = all(v is not None and np.isfinite(v) for v in (q0, q1))
            fmt = lambda v, s_: '—' if v is None or not np.isfinite(v) else s_.format(v)
            rows.append([str(n), fmt(f0, '{:.3f}'), fmt(q0, '{:.2e}'), fmt(f1, '{:.3f}'), fmt(q1, '{:.2e}'), f'{q1 / q0:.0f}×' if ok else '—'])
        story += [P('Full structure with the 65 nm shield (COMSOL)', H2), table(rows), Spacer(1, 6)]
        pz = SH / 'data' / 'nm10_shield65_pml3k.npz'
        if pz.exists():
            z = np.load(pz, allow_pickle=True); ib = int(z['i_breath'])
            story += [P(f'PML check (10 mirror cells, 65 nm shield, d_pml 3 µm): f {z["f"][ib-1]/1e9:.4f} GHz, Q_m {z["Q"][ib-1]:.2e}.')]
        for f_, cap in (('structure65', 'Modeled eighth with the 65 nm shield (lattice 35 nm from the trench).'),
                        ('qm_table65', 'Q_m vs mirror cells, 65 nm shield vs plain slab.'),
                        ('disp_maps65', 'Breathing mode |u|² (log), plain slab (left) vs 65 nm shield (right).')):
            if (SH / 'figures' / f'{f_}.png').exists():
                story += [fig(SH / 'figures' / f'{f_}.png', cap, width=4.5 * inch if f_ == 'qm_table65' else W)]
        story += [P('GDS: best_devices/60nm_w650_d0.086_xi1.79_chi-6.97_gapconf/*_shield.gds (fabrication layout, 65 nm checked); '
                    'runs/shield_619/gds/ref_*.gds (exactly the COMSOL geometries incl. PML layers, for solver cross-checks).')]

    # ------------------------------------------------------------------ 7
    story += [P('Not covered here', H2),
              P('Fabrication disorder (it breaks the mirror symmetry and is where the shield matters most), sidewall angle, anisotropic '
                '(cubic) diamond, material/TLS/thermoelastic loss, optical Q convergence, g0. Full cavity + shield on the Dmitry cloud: '
                'its new structure route (GDS input, laghai/nanophotonics-cloud #176) reproduces the plain-anchor COMSOL Q_m; the shielded '
                'case is pending on their side.')]
    SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.7 * inch,
                      bottomMargin=0.7 * inch, title='Gap-confined OMC with cross phonon shield').build(story)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
