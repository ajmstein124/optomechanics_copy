"""
Generate docs/phononic_guide.pdf

Run from the optomechanics/ project root:
    python docs/generate_phononic_guide.py
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from pathlib import Path

OUT = Path(__file__).parent / 'phononic_guide.pdf'

# ── Styles ─────────────────────────────────────────────────────────────────────

styles = getSampleStyleSheet()
base = styles['Normal']

def S(name, **kw):
    return ParagraphStyle(name, parent=base, **kw)

title_style   = S('Title',   fontSize=18, leading=24, spaceAfter=6,  alignment=TA_CENTER, fontName='Helvetica-Bold')
sub_style     = S('Sub',     fontSize=11, leading=14, spaceAfter=16, alignment=TA_CENTER, fontName='Helvetica', textColor=colors.HexColor('#444444'))
h1_style      = S('H1',      fontSize=14, leading=18, spaceBefore=18, spaceAfter=6, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a1a2e'))
h2_style      = S('H2',      fontSize=11, leading=14, spaceBefore=12, spaceAfter=4, fontName='Helvetica-Bold', textColor=colors.HexColor('#333333'))
body_style    = S('Body',    fontSize=10, leading=14, spaceAfter=6,  alignment=TA_JUSTIFY)
bullet_style  = S('Bullet',  fontSize=10, leading=14, spaceAfter=3,  leftIndent=18, bulletIndent=6)
code_style    = S('Code',    fontSize=8.5, leading=12, spaceAfter=6, fontName='Courier', leftIndent=18,
                             backColor=colors.HexColor('#f4f4f4'), borderPadding=4)
caption_style = S('Caption', fontSize=8.5, leading=11, spaceAfter=8, alignment=TA_CENTER,
                             textColor=colors.HexColor('#555555'), fontName='Helvetica-Oblique')

def h1(text): return Paragraph(text, h1_style)
def h2(text): return Paragraph(text, h2_style)
def p(text):  return Paragraph(text, body_style)
def b(text):  return Paragraph(f'• {text}', bullet_style)
def code(text): return Paragraph(text.replace('\n','<br/>').replace(' ','&nbsp;'), code_style)
def sp(n=6):  return Spacer(1, n)
def hr():     return HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=4)

# ── Table helper ───────────────────────────────────────────────────────────────

def make_table(headers, rows, col_widths=None):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0),  colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR',    (0,0), (-1,0),  colors.white),
        ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 9),
        ('LEADING',      (0,0), (-1,-1), 13),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f7f7f7')]),
        ('GRID',         (0,0), (-1,-1), 0.4, colors.HexColor('#cccccc')),
        ('LEFTPADDING',  (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
        ('VALIGN',       (0,0), (-1,-1), 'TOP'),
    ]))
    return t

# ── Content ────────────────────────────────────────────────────────────────────

story = []

# Title
story += [
    sp(20),
    Paragraph('Phononic Band Structure Simulations', title_style),
    Paragraph('Concept, Code, and Si→Diamond Parameter Translation', sub_style),
    hr(),
    sp(4),
]

# ══════════════════════════════════════════════════════════════════
# PART 1 — THEORY
# ══════════════════════════════════════════════════════════════════

story += [h1('1.  Phononic Crystals and Band Gaps')]

story += [p(
    'A <b>phononic crystal</b> is a structure with a spatially periodic elastic modulus '
    'and/or density. Because elastic waves (phonons) scatter at each period, they '
    'interfere constructively or destructively depending on wavelength. At certain '
    'frequencies, destructive interference is total for <i>every</i> direction of '
    'propagation — creating a <b>complete phononic bandgap</b>: a range of frequencies '
    'in which no acoustic mode can exist in the bulk crystal.'
)]

story += [p(
    'For cavity QED with the SnV center, the phonon bath is a primary decoherence '
    'channel. Embedding the emitter inside a phononic crystal whose bandgap covers the '
    'relevant phonon frequencies suppresses that coupling, increasing coherence time '
    'without relying on cryogenic temperature alone.'
)]

story += [h2('1.1  Bloch–Floquet Theory')]

story += [p(
    'Just as electrons in a crystal obey Bloch\'s theorem, elastic waves in a '
    'periodic medium satisfy the <b>Floquet–Bloch condition</b>:'
)]

story += [p('<i>u</i>(<b>r</b>) = <i>u<sub>k</sub></i>(<b>r</b>) e<sup>i<b>k</b>·<b>r</b></sup>')]

story += [p(
    'where <b>k</b> is the Bloch wavevector (quasi-momentum) and '
    '<i>u<sub>k</sub></i>(<b>r</b>) has the same periodicity as the lattice. '
    'Substituting into the elastic wave equation gives an eigenvalue problem at each '
    '<b>k</b>:'
)]

story += [p('<b>D</b>(<b>k</b>) <b>u</b> = ω²<b>M</b> <b>u</b>')]

story += [p(
    'where <b>D</b> is the stiffness operator (depends on <b>k</b> through the '
    'Floquet BCs), <b>M</b> is the mass matrix, and ω is the angular frequency. '
    'Solving this for a set of <b>k</b>-points sweeping the <b>irreducible Brillouin '
    'zone (IBZ)</b> produces the <b>phononic band structure</b> ω(<b>k</b>).'
)]

story += [p(
    'A <b>complete bandgap</b> exists if there is a frequency interval [ω₁, ω₂] such '
    'that no eigenvalue falls in that interval for <i>any</i> <b>k</b> in the full BZ. '
    'The gap is characterised by its center frequency '
    'f<sub>gap</sub> = (ω₁+ω₂)/(4π) and fractional width '
    'Δf/f<sub>gap</sub> = (ω₂−ω₁)/((ω₁+ω₂)/2).'
)]

story += [h2('1.2  Snowflake Unit Cell and Brillouin Zone')]

story += [p(
    'The structure studied here is a hexagonal lattice of snowflake-shaped holes in a '
    'free-standing slab (the Safavi-Naeini & Painter 2010 geometry). Each snowflake has '
    '6-fold symmetry and is parametrised by lattice constant <i>a</i>, '
    'arm length <i>d</i>, arm width <i>w</i>, fillet radius <i>f_r</i>, and slab '
    'thickness <i>t</i>.'
)]

story += [p(
    'Because COMSOL requires <i>orthogonal</i> Floquet boundary pairs, the hexagonal '
    'unit cell is replaced by a <b>rectangular 2-atom supercell</b> with '
    'L<sub>x</sub> = a and L<sub>y</sub> = a√3. The reciprocal-space path follows '
    'the high-symmetry points of the hexagonal BZ:'
)]

story += [p('<b>Γ = (0, 0)  →  M = (π/a, π/(a√3))  →  K = (4π/3a, 0)  →  Γ</b>')]

story += [p(
    'This covers all symmetry-inequivalent wavevectors; a gap confirmed along this '
    'path is a complete bandgap for the hexagonal lattice.'
)]

story += [h2('1.3  Symmetric and Antisymmetric Modes')]

story += [p(
    'For a slab with mid-plane mirror symmetry, modes decouple into '
    '<b>symmetric</b> (even, in-plane dominated) and <b>antisymmetric</b> '
    '(odd, flexural) families with respect to the mid-plane z = 0. '
    'Solving these separately halves the matrix size and avoids spurious '
    'mixed solutions. In COMSOL this is implemented by activating either '
    'the symmetry BC (<tt>sym1</tt>) or the antisymmetry BC (<tt>as1</tt>) '
    'on the mid-plane cut, running the eigensolver twice per k-point, and '
    'combining the results.'
)]

story += [h2('1.4  Eigensolver Shift and Frequency Window')]

story += [p(
    'COMSOL\'s eigenfrequency solver uses a <b>shift-invert</b> method: it finds the '
    'N eigenvalues <i>nearest to a user-specified shift frequency</i> f<sub>mech</sub>. '
    'This has two important consequences:'
)]

story += [
    b('Setting f<sub>mech</sub> near the expected gap center ensures the solver captures '
      'bands both below and above the gap — critical for confirming a complete gap.'),
    b('Requesting N<sub>freqs</sub> modes per symmetry type must be large enough that the '
      'returned set spans the gap. If the gap sits between bands 14 and 15 globally, '
      'fewer than ~15 modes per symmetry will miss it.'),
]

story += [sp(4)]

# ══════════════════════════════════════════════════════════════════
# PART 2 — CODE
# ══════════════════════════════════════════════════════════════════

story += [PageBreak(), h1('2.  Code Overview')]

story += [h2('2.1  comsol_utils.py — Shared Utilities')]

story += [p('<b>start_client(model_file)</b>')]
story += [p(
    'Calls <tt>mph.start()</tt> to launch a headless COMSOL 6.4 server '
    '(auto-discovered by mph 1.4.0 on Windows), then loads the .mph model file. '
    'Returns a (client, model) pair.'
)]

story += [sp(4), p('<b>make_bz_path(a, N_ks)</b>')]
story += [p(
    'Constructs the k-point path Γ→M→K→Γ for lattice constant <i>a</i>, '
    'with N_ks points per segment. The total number of k-points is 3×N_ks − 2 '
    '(endpoints shared). Returns a (2, n_kpts) array of (k_x, k_y) vectors. '
    'N_ks = 5 gives 13 k-points (fast sweeps); N_ks = 13 gives 37 k-points '
    '(higher-resolution validation).'
)]

story += [sp(4), p('<b>mphglobal(m_java, expr, dataset)</b>')]
story += [p(
    'Extracts eigenfrequencies from a solved COMSOL dataset. The COMSOL 6.4 Java API '
    'does not accept <tt>solnum=\'all\'</tt> for EvalGlobal nodes — it raises '
    '"only constant expressions allowed." The workaround is to loop '
    '<tt>solnum = \'1\', \'2\', ...</tt> until COMSOL raises an out-of-range exception, '
    'collecting one complex eigenfrequency per iteration. Returns a numpy array of '
    'complex frequencies (imaginary part is numerical damping, negligible for real gaps).'
)]

story += [h2('2.2  Per-k-point Simulation Loop')]

story += [p('For each k-point in the BZ path, the script does the following:')]
story += [
    b('Set COMSOL parameters kFx, kFy to the current Bloch wavevector components.'),
    b('Run symmetric solve: activate sym1, deactivate as1, call sol1.runAll().'),
    b('Extract N_freqs eigenfrequencies via mphglobal → store in freqs[ii, :N_freqs].'),
    b('Run antisymmetric solve: swap sym1/as1, repeat.'),
    b('Store combined in freqs[ii, N_freqs:] and save incrementally to .mat.'),
]

story += [p(
    'Saving after every k-point means results are recoverable if the run crashes '
    'mid-sweep. The final file (ii_13 or ii_37) contains the complete 2D array.'
)]

story += [h2('2.3  Gap Detection (find_gap)')]

story += [code(
    'def find_gap(freqs_arr):\n'
    '    sb = np.sort(np.real(freqs_arr), axis=1) * 1e-9  # GHz, sort per k-point\n'
    '    for n in range(sb.shape[1] - 1):\n'
    '        top = sb[:, n].max()      # highest freq of band n across all k\n'
    '        bot = sb[:, n+1].min()    # lowest freq of band n+1 across all k\n'
    '        if bot > top:             # no overlap -> complete gap\n'
    '            cen = (top + bot) / 2\n'
    '            wid = bot - top\n'
    '    return best_cen, best_wid, best_frac'
)]

story += [p(
    'Modes are sorted across both symmetry types at each k-point. For each consecutive '
    'band pair (n, n+1), a complete gap requires that the <i>maximum</i> of band n '
    '(over all k) is strictly less than the <i>minimum</i> of band n+1. The largest '
    'such gap is returned.'
)]

story += [h2('2.4  Remote Execution (remote_runner.py)')]

story += [p(
    'Scripts run on the Windows COMSOL machine (jv-adamantoise, <USER>@<COMSOL_HOST> '
    'via Tailscale). The runner copies the script and comsol_utils.py via SCP, then '
    'launches the job <i>detached</i> using <tt>Invoke-CimMethod Win32_Process Create</tt> '
    '— a Windows API that creates a process completely outside the SSH session\'s job '
    'object, so the job survives SSH/laptop disconnection. Output is redirected to '
    '<tt>job_log.txt</tt> via a bat wrapper. '
    'Check progress with: <tt>python scripts/remote_runner.py --status</tt>'
)]

# ══════════════════════════════════════════════════════════════════
# PART 3 — PARAMETER TRANSLATION
# ══════════════════════════════════════════════════════════════════

story += [PageBreak(), h1('3.  Si → Diamond Parameter Translation')]

story += [h2('3.1  Material Properties')]

story += [p(
    'The COMSOL model (unit_cell_3.mph) has Silicon as its built-in material. '
    'Diamond is applied by overriding three scalar properties at runtime:'
)]

story += [make_table(
    ['Property', 'Silicon', 'Diamond', 'Notes'],
    [
        ['Young\'s modulus E', '130 GPa', '1050 GPa', 'From c11=1076, c12=125, c44=578 GPa (Grimsditch & Ramdas 1975)'],
        ['Poisson\'s ratio ν', '0.28',    '0.07',     'Isotropic approximation'],
        ['Density ρ',          '2329 kg/m³', '3500 kg/m³', ''],
        ['v_LA = √(E(1−ν)/ρ(1+ν)(1−2ν))', '8,430 m/s', '17,450 m/s', '~2× faster in diamond'],
    ],
    col_widths=[1.5*inch, 1.1*inch, 1.1*inch, 2.8*inch]
)]

story += [h2('3.2  Geometric Scaling')]

story += [p(
    'The Si validation run used parameters from the Safavi-Naeini & Painter (2010) '
    'snowflake geometry, which simultaneously supports a phononic gap at ~9.5 GHz '
    'and a photonic TE gap at 1550 nm in silicon. The diamond design targets the '
    'SnV zero-phonon line at <b>λ = 619 nm</b>. The lattice constant is set so that '
    'a/λ is the same as in the original Si/1550 nm design — placing the structure in '
    'the same photonic TE gap regime:'
)]

story += [p(
    'a<sub>Si</sub>/λ<sub>1562nm</sub> = 478/1562 = <b>0.306</b>  →  '
    'a<sub>diamond</sub> = 0.306 × 619 nm = <b>190 nm</b>'
)]

story += [p(
    'All other geometric parameters are then scaled by the same ratio '
    'a<sub>d</sub>/a<sub>Si</sub> = 190/478 = 0.397, preserving the dimensionless '
    'ratios d/a, w/a, and f_r/a that determine the band topology:'
)]

story += [make_table(
    ['Parameter', 'Si (validated)', 'Diamond', 'Ratio / Rule'],
    [
        ['Lattice constant a',  '478 nm', '190 nm', 'a/λ = 0.307 (photonic TE gap condition)'],
        ['Slab thickness t',    '220 nm', '140 nm', 'User-specified (available diamond film)'],
        ['Arm length d',        '182 nm', '72 nm',  'd/a = 0.381 preserved'],
        ['Arm width w',         '99 nm',  '39 nm',  'w/a = 0.207 preserved'],
        ['Fillet radius f_r',   '25 nm',  '10 nm',  'f_r/a = 0.052 preserved'],
        ['Eigensolver shift f0','7 GHz',  '36 GHz', 'Bragg scaling: 0.74 × v_LA/(2a)'],
        ['Modes per symmetry',  '10',     '20',     'Gap at higher band index; need more modes'],
    ],
    col_widths=[1.5*inch, 1.1*inch, 0.8*inch, 3.1*inch]
)]

story += [h2('3.3  Expected Phononic Gap Frequency')]

story += [p(
    'The phononic gap center scales with the acoustic velocity and inversely with '
    'lattice constant (Bragg condition f ≈ α × v<sub>LA</sub> / a). Calibrating α '
    'from the validated Si result:'
)]

story += [p(
    'α = f<sub>gap,Si</sub> × a<sub>Si</sub> / v<sub>LA,Si</sub> = '
    '6.50 GHz × 478 nm / 8,430 m/s = <b>0.369</b>'
)]

story += [p(
    'Applying to diamond:'
)]

story += [p(
    'f<sub>gap,d</sub> = α × v<sub>LA,d</sub> / a<sub>d</sub> = '
    '0.369 × 17,450 m/s / 190 nm = <b>33.9 GHz</b>'
)]

story += [p(
    'The eigensolver shift is set to f<sub>mech</sub> = 36 GHz (slightly above this '
    'estimate to ensure the full gap sits within the returned mode window). '
    'N<sub>freqs</sub> = 20 per symmetry type (40 total) versus 10 in Si, because '
    'the first v1 run showed the gap appearing near band 14–15 of 20 — requiring '
    'more modes to confirm it is a complete gap across all k-points.'
)]

story += [h2('3.4  Note on t/a Ratio')]

story += [p(
    'The slab thickness ratio t/a = 140/190 = 0.74 for diamond versus 0.46 for '
    'Si. This is significantly thicker in units of the lattice constant, which '
    'shifts the band structure and may change which band pair the gap appears at. '
    'A future sweep could explore t/a by varying a at fixed t=140 nm — trading '
    'gap frequency for better-matched slab aspect ratio.'
)]

# ══════════════════════════════════════════════════════════════════
# PART 4 — CURRENT STATUS
# ══════════════════════════════════════════════════════════════════

story += [PageBreak(), h1('4.  Current Simulation Status')]

story += [make_table(
    ['Run', 'Material', 'a', 't', 'f_mech', 'N_freqs/sym', 'Status', 'Result'],
    [
        ['reproduce_Si', 'Si', '478 nm', '220 nm', '7 GHz', '10', 'Complete',
         'f_gap=6.50 GHz, Δf=1.09 GHz (17%)'],
        ['Si 3×3 sweep', 'Si', '478 nm', '220 nm', '7 GHz', '10', 'Complete',
         'Heatmap generated'],
        ['diamond v1', 'Diamond', '190 nm', '140 nm', '36 GHz', '10', 'Complete',
         'No gap detected — insufficient N_freqs'],
        ['diamond v2 (running)', 'Diamond', '190 nm', '140 nm', '36 GHz', '20',
         'Running overnight', 'Expected: ~34 GHz gap'],
    ],
    col_widths=[0.9*inch, 0.7*inch, 0.6*inch, 0.6*inch, 0.7*inch, 0.8*inch, 0.9*inch, 1.8*inch]
)]

story += [sp(8), p(
    '<b>Why v1 found no gap:</b> With only 10 modes per symmetry (20 total), and the '
    'gap appearing near band 14–15, the band topology around the gap was not fully '
    'captured. Doubling to N<sub>freqs</sub>=20 (40 total) in v2 should resolve this. '
    'The eigensolver shift f<sub>mech</sub>=36 GHz was correct in v1 and is unchanged — '
    'it ensures the returned modes are centered on the expected gap at every k-point.'
)]

# ══════════════════════════════════════════════════════════════════
# BUILD
# ══════════════════════════════════════════════════════════════════

doc = SimpleDocTemplate(
    str(OUT),
    pagesize=letter,
    leftMargin=0.9*inch, rightMargin=0.9*inch,
    topMargin=0.9*inch,  bottomMargin=0.9*inch,
)
doc.build(story)
print(f'Saved: {OUT}')
