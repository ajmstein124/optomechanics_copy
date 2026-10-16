"""
Generate parameter_reference.pdf — phononic crystal simulation parameter guide.
Run: python3 docs/generate_param_reference.py
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

OUT = os.path.join(os.path.dirname(__file__), 'parameter_reference.pdf')

doc = SimpleDocTemplate(
    OUT,
    pagesize=letter,
    leftMargin=1.1 * inch,
    rightMargin=1.1 * inch,
    topMargin=1.0 * inch,
    bottomMargin=1.0 * inch,
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'Title2',
    parent=styles['Title'],
    fontSize=16,
    spaceAfter=4,
    textColor=colors.HexColor('#1a1a2e'),
)
subtitle_style = ParagraphStyle(
    'Subtitle',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.HexColor('#555555'),
    spaceAfter=18,
    alignment=TA_CENTER,
)
h1_style = ParagraphStyle(
    'H1',
    parent=styles['Heading1'],
    fontSize=13,
    textColor=colors.HexColor('#1a1a2e'),
    spaceBefore=18,
    spaceAfter=4,
    borderPad=0,
)
h2_style = ParagraphStyle(
    'H2',
    parent=styles['Heading2'],
    fontSize=11,
    textColor=colors.HexColor('#2e4057'),
    spaceBefore=12,
    spaceAfter=2,
)
body_style = ParagraphStyle(
    'Body2',
    parent=styles['Normal'],
    fontSize=9.5,
    leading=14,
    spaceAfter=6,
    textColor=colors.HexColor('#222222'),
)
ref_style = ParagraphStyle(
    'Ref',
    parent=styles['Normal'],
    fontSize=8.5,
    leading=12,
    textColor=colors.HexColor('#555555'),
    leftIndent=12,
    spaceAfter=4,
)
eq_style = ParagraphStyle(
    'Eq',
    parent=styles['Normal'],
    fontSize=9.5,
    leading=14,
    textColor=colors.HexColor('#1b4f72'),
    leftIndent=18,
    spaceAfter=4,
)
warn_style = ParagraphStyle(
    'Warn',
    parent=styles['Normal'],
    fontSize=9,
    leading=13,
    textColor=colors.HexColor('#7d3c00'),
    leftIndent=12,
    backColor=colors.HexColor('#fef9e7'),
    borderPad=4,
    spaceAfter=6,
)

def hr():
    return HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=4)

def sp(n=6):
    return Spacer(1, n)

def h1(txt):
    return Paragraph(txt, h1_style)

def h2(txt):
    return Paragraph(txt, h2_style)

def body(txt):
    return Paragraph(txt, body_style)

def ref(txt):
    return Paragraph(txt, ref_style)

def eq(txt):
    return Paragraph(txt, eq_style)

def warn(txt):
    return Paragraph(txt, warn_style)


# ── Summary table data ───────────────────────────────────────────────────────

summary_data = [
    ['Parameter', 'Symbol', 'Default', 'Typical range'],
    ['Lattice constant', 'a', '500 nm', '100 – 2000 nm'],
    ['Slab thickness ratio', 'd/a', '0.44', '0.20 – 0.60'],
    ['Hole radius ratio', 'r/a', '0.35', '0.10 – 0.48'],
    ['k-points per segment', 'n_seg', '15', '8 – 30'],
    ['Eigenfrequencies', 'n_modes', '20', '10 – 40'],
    ['Eig. shift', 'shift', '3.0 GHz', '>0, below gap'],
    ["Young's modulus (diamond)", 'E', '1050 GPa', '-- (material const.)'],
    ["Poisson's ratio (diamond)", 'nu', '0.07', '-- (material const.)'],
    ['Mass density (diamond)', 'rho', '3500 kg/m^3', '-- (material const.)'],
]

t_style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
    ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
    ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE',   (0, 0), (-1, -1), 9),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f4f6f8'), colors.white]),
    ('GRID',       (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
    ('LEFTPADDING',  (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING',   (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
    ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
])

summary_table = Table(
    summary_data,
    colWidths=[2.1*inch, 0.9*inch, 1.1*inch, 1.6*inch],
    style=t_style,
)


# ── Build story ──────────────────────────────────────────────────────────────

story = []

story.append(Paragraph(
    'Phononic Crystal Simulation — Parameter Reference',
    title_style,
))
story.append(Paragraph(
    'Triangular lattice of circular holes in a diamond slab &bull; COMSOL 6.x / mph',
    subtitle_style,
))
story.append(hr())
story.append(sp(6))

story.append(body(
    'This document explains each simulation parameter in the context of computing the '
    'phononic band structure of a two-dimensional triangular (hexagonal) lattice of '
    'circular holes in a free-standing diamond slab. The geometry and approach follow '
    '<b>Safavi-Naeini &amp; Painter (2010)</b> for the snowflake crystal and '
    '<b>Chan PhD thesis (Caltech 2012)</b> for the nanobeam phononic shield, adapted '
    'here to a 2D slab with circular holes as a pipeline-validation geometry before '
    'upgrading to the snowflake unit cell.'
))
story.append(sp(4))
story.append(body(
    '<b>Geometry.</b> The primitive cell of the hexagonal lattice is rhombic, but COMSOL '
    'requires orthogonal periodic boundaries. We therefore simulate a <i>rectangular '
    '2-atom supercell</i>: L<sub>x</sub> = a, L<sub>y</sub> = a&radic;3. This supercell '
    'contains one full hole at (a/2, a&radic;3/2) and four quarter-holes at the corners, '
    'giving 2 holes per cell and preserving the triangular lattice exactly.'
))
story.append(sp(8))

story.append(Paragraph('Quick-reference table', h2_style))
story.append(summary_table)
story.append(sp(12))


# ── Section 1: Geometry ──────────────────────────────────────────────────────

story.append(hr())
story.append(h1('1. Geometry Parameters'))

# --- a ---
story.append(h2('1.1  Lattice constant  a  [nm]'))
story.append(body(
    'The lattice constant <i>a</i> is the distance between nearest-neighbor hole centers. '
    'It is the primary frequency-scaling knob: because phonon wavelengths at the '
    'bandgap scale with <i>a</i>, the gap center frequency scales as'
))
story.append(eq('f_gap  ~  0.5 * v_LA / a'))
story.append(body(
    'where v_LA is the longitudinal acoustic velocity of the slab material. '
    'For diamond, v_LA ~ 17,500 m/s (derived from the isotropic elastic constants below); '
    'for comparison Si has v_LA ~ 9,000 m/s, so diamond gaps appear at roughly 2x '
    'higher frequency for the same a.'
))
story.append(body(
    'The calibration constant 0.5 comes from fitting to the Si snowflake result in '
    'Safavi-Naeini &amp; Painter (2010): their a = 500 nm gives a ~9.5 GHz gap, '
    'consistent with alpha = f*a/v_LA ~ 0.49 ~ 0.5. '
    'To hit a target frequency f_target, the required lattice constant is:'
))
story.append(eq('a_est  =  0.5 * v_LA / f_target'))
story.append(body(
    'For the pipeline test at a = 500 nm diamond, the expected gap center is '
    '~17 GHz. To reach 5 GHz requires a ~ 1750 nm, which conflicts with the photonic '
    'lattice constraint for 619 nm light (see co-design notes below).'
))
story.append(ref(
    'Chan thesis Sec. 3.1.4 (frequency scaling with lattice constant); '
    'Safavi-Naeini &amp; Painter 2010 Fig. 1 (snowflake band structure, a = 500 nm Si, '
    '~9.5 GHz gap).'
))

# --- d/a ---
story.append(h2('1.2  Slab thickness ratio  d/a'))
story.append(body(
    'The slab thickness d controls which phonon modes are guided versus radiative. '
    'For a free-standing slab, guided modes exist in three families: symmetric (S), '
    'antisymmetric (A), and shear-horizontal (SH). The phononic bandgap of the '
    'patterned slab opens between branches of these guided Lamb waves.'
))
story.append(body(
    '<b>Too thin</b> (d/a &lt; ~0.2): The slab barely confines acoustic modes; '
    'branch separations shrink and no clear bandgap forms. '
    '<b>Too thick</b> (d/a &gt; ~0.6): Higher-order Lamb modes fill in the gap. '
    'The optimal range is d/a ~ 0.3 to 0.55 for circular holes.'
))
story.append(body(
    'The default d/a = 0.44 (d = 220 nm at a = 500 nm) is the value used by '
    'Safavi-Naeini &amp; Painter for their snowflake slab, and is a good starting point. '
    'This is also close to the value used in Chan thesis for the Si nanobeam (d = 220 nm, '
    'a = 500 nm, d/a = 0.44).'
))
story.append(warn(
    'Note on thickness and photonic co-design: the photonic TE bandgap in a 2D PCC '
    'slab also depends on d/a. The photonic gap window a/lambda = 0.25-0.38 was '
    'estimated at d/a ~ 0.44. A different d/a shifts the photonic gap boundary; '
    'a full legume bandstructure sweep is needed to pin down the exact range for '
    'a given d/a. The phononic gap frequency estimate (f ~ 0.5*v/a) does NOT '
    'depend on d.'
))
story.append(ref(
    'Safavi-Naeini &amp; Painter 2010 Table 1: d/a = 0.44 for snowflake Si slab; '
    'Chan thesis Sec. 3.4: d/a choices for nanobeam phononic shield.'
))

# --- r/a ---
story.append(h2('1.3  Hole radius ratio  r/a'))
story.append(body(
    'The hole radius r controls the acoustic fill fraction f = 2*pi*r^2 / (a^2*sqrt(3)), '
    'which is the fraction of the unit cell removed by drilling. Larger r/a means '
    'more material removed, stronger acoustic contrast, and generally a wider bandgap '
    '-- up to a limit.'
))
story.append(body(
    '<b>Lower bound:</b> Below r/a ~ 0.10 the holes are too small to create '
    'significant scattering; no gap opens. '
    '<b>Upper bound:</b> At r/a = 0.5 (circular holes), adjacent holes in the '
    'triangular lattice touch. The slab becomes mechanically fragile and the '
    'continuum elastic model breaks down. The practical limit is r/a ~ 0.45-0.48.'
))
story.append(body(
    'For triangular-lattice circular holes, a phononic bandgap for the fundamental '
    'Lamb modes typically requires r/a ~ 0.30-0.45. The default r/a = 0.35 is a '
    'conservative starting point. The snowflake geometry (Safavi-Naeini &amp; Painter) '
    'achieves a wider gap with an effectively larger fill fraction per unit cell.'
))
story.append(body(
    'The fill fraction as a percentage is:'
))
story.append(eq('fill%  =  2 * pi * (r/a)^2 / sqrt(3)  *  100'))
story.append(body(
    'At r/a = 0.35: fill ~ 44%. At r/a = 0.45: fill ~ 73%.'
))
story.append(ref(
    'Chan thesis Fig. 3.9: cross unit cell r/w ratio sets gap width; '
    'Safavi-Naeini &amp; Painter 2010 Fig. 2: snowflake parameter r_s controls '
    'simultaneous phononic + photonic bandgap width.'
))

story.append(sp(4))
story.append(hr())
story.append(h1('2. COMSOL / Floquet Setup'))

story.append(h2('2.0  How Floquet periodic BCs work'))
story.append(body(
    'The Floquet (Bloch) boundary condition imposes a phase relationship between '
    'displacement fields on opposite faces of the unit cell. For a wave with Bloch '
    'vector <b>k</b><sub>F</sub> = (k<sub>x</sub>, k<sub>y</sub>, 0), the condition on '
    'each pair of periodic faces is:'
))
story.append(eq(
    'u_dest  =  exp( -i * k_F . (r_dest - r_src) ) * u_src'
))
story.append(body(
    'where u is the displacement vector field. In COMSOL Solid Mechanics this is the '
    '"Floquet" PeriodicCondition type, with kFloquet = [kx, ky, 0] set as a '
    'global parameter. Two such conditions are applied: pc_x pairs the x=0 and x=a '
    'faces; pc_y pairs y=0 and y=a*sqrt(3) faces.'
))
story.append(body(
    '<b>Complex eigensolver:</b> Because the Floquet factor is complex, the FE '
    'stiffness and mass matrices become complex Hermitian (not real symmetric) for '
    'k != 0. COMSOL automatically invokes a complex eigensolver in this case. '
    'The eigenvalues (squared angular frequencies omega^2) remain real because the '
    'system is Hermitian — no damping. This is why getData() returns real '
    'frequencies even though the underlying math is complex.'
))
story.append(body(
    '<b>k = 0 special case (Gamma point):</b> At k = (0, 0) the Floquet factor '
    'is 1 and the matrices are real. However, the zero-frequency acoustic modes '
    '(rigid-body translations) appear here, which is why eig_shift_GHz > 0 is '
    'essential to skip them.'
))
story.append(ref(
    'COMSOL Multiphysics Blog: "Modeling Phononic Band Gap Materials and Structures" '
    '(comsol.com/blogs/...): Floquet BC formulation, complex eigensolver requirement, '
    'IBZ path construction; '
    'Chan thesis App. F: COMSOL implementation details for Floquet BVP.'
))

story.append(h2('2.0b  Brillouin zone path'))
story.append(body(
    'The k-path must cover the irreducible Brillouin zone (IBZ) — the region of '
    'k-space not related by symmetry to any other region. Bandgaps are complete '
    'only if they span the gap for ALL k in the IBZ, not just the high-symmetry path. '
    'The standard practice is to sweep the full IBZ boundary (high-symmetry path) '
    'as a necessary but not sufficient check; gaps found on the path are expected '
    'to be complete for geometries with the full lattice symmetry.'
))
story.append(body(
    'For a <b>square lattice</b> (COMSOL blog example), the IBZ boundary is '
    'Gamma -> X -> M -> Gamma. For our <b>hexagonal lattice</b> simulated as a '
    'rectangular 2-atom supercell, the reciprocal lattice is also rectangular and '
    'the high-symmetry path of the rectangular BZ is:'
))
story.append(eq(
    'Gamma (0,0) -> X (pi/a, 0) -> S (pi/a, pi/(a*sqrt(3))) '
    '-> Y (0, pi/(a*sqrt(3))) -> Gamma (0,0)'
))
story.append(body(
    'This rectangular path folds the hexagonal BZ into the rectangular supercell BZ. '
    'The S point corresponds to the M point of the hexagonal BZ. The X and Y points '
    'are the midpoints of the rectangular BZ edges. This path is standard for '
    '2-atom rectangular supercells of hexagonal lattices.'
))
story.append(ref(
    'COMSOL blog: IBZ path for square lattice (Gamma-X-M-Gamma); '
    'Standard solid-state physics: rectangular BZ of hexagonal supercell; '
    'Safavi-Naeini & Painter 2010 supplementary: k-path for snowflake lattice.'
))

story.append(h2('2.0c  Gap formation mechanism'))
story.append(body(
    'Phononic bandgaps arise from two distinct mechanisms, and the geometry '
    'determines which one dominates:'
))
story.append(body(
    '<b>Bragg scattering</b> (our case): When the wavelength is comparable to the '
    'lattice constant (lambda_acoustic ~ a), destructive interference of scattered '
    'waves opens a gap at the BZ boundary. This is exactly the mechanism in our '
    'triangular lattice of holes in a diamond slab. The gap frequency scales as '
    'f ~ v/a (velocity over lattice constant). Requires periodic order but not '
    'necessarily high acoustic contrast.'
))
story.append(body(
    '<b>Local resonance</b> (COMSOL blog example): Inclusions with a strong '
    'impedance mismatch (stiff core / soft matrix) create local resonances. '
    'The gap frequency is set by the resonance of individual inclusions, '
    'independent of lattice constant. The COMSOL example uses E_core/E_matrix = 100:1 '
    'and rho_core/rho_matrix = 8:1 to achieve a gap at 60-72 kHz with a 1 cm cell. '
    'This mechanism is NOT what we are using — our holes-in-diamond geometry has '
    'no matrix material, so it is purely Bragg-type.'
))
story.append(body(
    'The circular-hole slab geometry may produce only a partial phononic bandgap '
    '(gaps only for certain polarizations) because circular holes have less '
    'scattering contrast than the snowflake geometry, which acts more like a '
    'local resonator at each site. Upgrading to snowflake (Safavi-Naeini & Painter) '
    'restores a complete bandgap through enhanced scattering geometry.'
))
story.append(ref(
    'COMSOL blog: local resonance mechanism, material contrast (E_core/E_matrix ~ 100); '
    'Safavi-Naeini & Painter 2010: Bragg + resonance hybridization in snowflake; '
    'Chan thesis Sec. 3.1: Bragg gap mechanism in cross unit cell.'
))

story.append(sp(4))
story.append(hr())
story.append(h1('3. Solver Parameters'))

# --- n_seg ---
story.append(h2('3.1  k-points per BZ segment  n_seg'))
story.append(body(
    'The band structure is computed along the high-symmetry path '
    'Gamma -> X -> S -> Y -> Gamma in the rectangular Brillouin zone '
    'of the hexagonal supercell. The path has 4 segments; n_seg points are '
    'sampled on each, giving 4*n_seg + 1 total k-points.'
))
story.append(body(
    'The BZ boundary points are:'
))
story.append(eq(
    'Gamma = (0, 0)    X = (pi/a, 0)    '
    'S = (pi/a, pi/(a*sqrt(3)))    Y = (0, pi/(a*sqrt(3)))'
))
story.append(body(
    'More k-points give a smoother dispersion relation and more accurate '
    'bandgap boundaries, but each k-point requires a separate COMSOL '
    'eigenfrequency solve. Typical trade-off: '
    'n_seg = 8 for quick survey (33 points total), '
    'n_seg = 15 for production runs (61 points), '
    'n_seg = 25+ for publication-quality figures (101 points).'
))
story.append(ref(
    'Chan thesis Appendix F: Floquet BVP formulation and k-path for rectangular '
    'BZ of hexagonal lattice; standard solid-state physics BZ construction.'
))

# --- n_modes ---
story.append(h2('3.2  Number of eigenfrequencies  n_modes'))
story.append(body(
    'At each k-point, COMSOL solves for the n_modes eigenfrequencies nearest to '
    'the shift value (shift-invert Lanczos). This must be large enough to cover '
    'all bands in the frequency range of interest, including the gap.'
))
story.append(body(
    'Too few modes: the top of the gap may be truncated (missing the lower edge of '
    'the upper band). Too many: longer solve time, but otherwise harmless. '
    'n_modes = 20 is sufficient for the first ~10 phononic branches in diamond at '
    'the target frequency range.'
))
story.append(body(
    'Check: after running, plot all bands and verify the gap is not cut off at the top '
    'of the computed frequency range. Increase n_modes if you see only an '
    '"open" gap (band plotted but top not visible).'
))
story.append(ref(
    'COMSOL Documentation: Eigenfrequency Study, neigsactive/neigs settings; '
    'Chan thesis App. F: number of modes needed for phononic band convergence.'
))

# --- eig_shift ---
story.append(h2('3.3  Eigenfrequency shift  eig_shift_GHz'))
story.append(body(
    'The COMSOL eigenfrequency solver uses a shift-invert strategy: it finds the '
    'n_modes eigenvalues closest to omega_shift^2 (squared frequency). '
    'Setting a nonzero shift serves two purposes:'
))
story.append(body(
    '<b>(1) Skip near-zero modes:</b> At k = 0 (Gamma point), the acoustic '
    'branches have zero frequency by symmetry (rigid-body translations). These '
    '"DC" modes dominate the search window if shift = 0, crowding out the '
    'physically interesting modes in the GHz range.'
))
story.append(body(
    '<b>(2) Center the search on the gap region:</b> Setting shift ~ 0.5 * f_est '
    'ensures that the bands just below the gap are well-resolved. If shift is '
    'much higher than the gap, modes below the gap may be missed.'
))
story.append(body(
    'Rule of thumb: set shift to 30-70% of the expected gap center frequency. '
    'For diamond at a = 500 nm (expected gap ~ 17 GHz), shift = 3 GHz is '
    'intentionally low to also capture the acoustic branches well below the gap. '
    'Raise to ~8 GHz if the gap is around 17 GHz and low modes are cluttering the plot.'
))
story.append(warn(
    'If getData() returns unexpected frequencies or misses modes, try adjusting '
    'eig_shift_GHz. The shift must be below the gap center, and the window '
    'eig_shift +/- range must cover all bands you care about.'
))
story.append(ref(
    'COMSOL Documentation: Eigenfrequency Study > Shift (linearization point); '
    'Chan thesis App. F: eigenfrequency search settings for phononic band structure.'
))

story.append(sp(4))
story.append(hr())
story.append(h1('3. Material Parameters (Diamond)'))

story.append(body(
    'An isotropic elastic model is used as the first approximation. '
    'Diamond has cubic symmetry (point group O_h); the isotropic '
    'approximation replaces the three independent elastic constants '
    '(c11, c12, c44) with the two isotropic Lame parameters derived from '
    'an orientational average. The error in gap frequency is typically &lt;10% '
    'and acceptable for pipeline validation and initial parameter surveys.'
))

# --- E ---
story.append(h2('3.1  Young\'s modulus  E  [GPa]'))
story.append(body(
    'E = 1050 GPa for diamond (isotropic approximation). '
    'This is derived from the cubic elastic constants as an orientational average: '
    'c11 = 1076 GPa, c12 = 125 GPa, c44 = 578 GPa (Grimsditch &amp; Ramdas 1975). '
    'The Voigt average gives E ~ 1050 GPa, nu ~ 0.07.'
))
story.append(body(
    'For comparison: Si has E ~ 170 GPa, Al2O3 ~ 400 GPa. '
    'Diamond\'s high E is why v_LA is ~2x that of Si, pushing phononic gaps '
    'to higher frequencies for the same lattice constant.'
))
story.append(body(
    'The longitudinal acoustic velocity of the isotropic approximation is:'
))
story.append(eq('v_LA  =  sqrt( E*(1-nu) / (rho*(1+nu)*(1-2*nu)) )'))
story.append(body(
    'For E = 1050 GPa, nu = 0.07, rho = 3500 kg/m^3: v_LA ~ 17,450 m/s. '
    'The true c11-based velocity is sqrt(c11/rho) ~ sqrt(1076e9/3500) ~ 17,540 m/s, '
    'so the isotropic approximation is accurate to &lt;1% for v_LA.'
))
story.append(ref(
    'Grimsditch &amp; Ramdas (1975) Phys. Rev. B 11, 3139: elastic constants of diamond; '
    'Safavi-Naeini &amp; Painter 2010 supplementary: material constants used for Si; '
    'Chan thesis App. F: material properties and their effect on phononic gaps.'
))

# --- nu ---
story.append(h2('3.2  Poisson\'s ratio  nu'))
story.append(body(
    'nu = 0.07 for diamond. This is exceptionally low (Si ~ 0.28, most metals 0.25-0.35). '
    'A small Poisson\'s ratio means the material resists lateral expansion under '
    'longitudinal stress, so transverse and longitudinal sound velocities are '
    'closer in value than in most materials.'
))
story.append(body(
    'In the context of phononic crystals, a smaller nu tends to widen the frequency '
    'ratio v_LA/v_TA. For diamond:'
))
story.append(eq('v_TA  =  sqrt( E / (2*rho*(1+nu)) )  ~  8,440 m/s'))
story.append(body(
    'The ratio v_LA/v_TA ~ 17,450/8,440 ~ 2.07 for diamond vs ~1.73 for Si (v_LA/v_TA = sqrt(2) '
    'in the Debye limit). This anisotropy in velocity partially determines the '
    'frequency range over which phononic bandgaps can open.'
))
story.append(ref(
    'Standard elasticity: Lame parameters from E and nu; '
    'Grimsditch &amp; Ramdas 1975 for diamond elastic tensor.'
))

# --- rho ---
story.append(h2('3.3  Mass density  rho  [kg/m^3]'))
story.append(body(
    'rho = 3500 kg/m^3 for single-crystal diamond (literature value 3515 kg/m^3; '
    '3500 is the standard round value used in simulations). '
    'This value enters the dispersion relation through the acoustic velocity '
    'v = sqrt(C/rho): higher density lowers v and hence lowers gap frequencies '
    'for the same geometry. Diamond is denser than Si (2330 kg/m^3) but its much '
    'higher elastic moduli more than compensate, giving the 2x higher velocity.'
))
story.append(ref(
    'Standard diamond material databases; '
    'Safavi-Naeini &amp; Painter 2010: diamond material properties for co-design feasibility.'
))

story.append(sp(4))
story.append(hr())
story.append(h1('4. Key Physical Insights and Co-design Notes'))

story.append(h2('4.1  Phononic gap scaling (diamond)'))
story.append(body(
    'Using f_gap ~ 0.5 * v_LA / a with v_LA = 17,450 m/s:'
))
data = [
    ['a (nm)', 'f_gap (GHz)', 'Note'],
    ['150',  '58',  'Photonic range for 619 nm (a/lambda ~ 0.24)'],
    ['200',  '44',  'Lower photonic bound at 619 nm'],
    ['500',  '17',  'Pipeline test point (default in scripts)'],
    ['1000', '8.7', 'Sub-10 GHz gap; too large for 619 nm photonics'],
    ['1750', '5.0', 'Target 5 GHz; incompatible with photonics at 619 nm'],
]
t2 = Table(data, colWidths=[1.0*inch, 1.3*inch, 3.4*inch], style=t_style)
story.append(t2)
story.append(sp(6))

story.append(h2('4.2  Phononic-photonic conflict at 619 nm'))
story.append(body(
    'The photonic TE bandgap in a triangular-lattice 2D PCC slab requires '
    'a/lambda ~ 0.25-0.38 (estimated at d/a ~ 0.44). For the SnV ZPL at 619 nm:'
))
story.append(eq('a_phot  in  [0.25*619, 0.38*619]  ~  [155, 235] nm'))
story.append(body(
    'The phononic gap center frequency at a in this photonic range is:'
))
story.append(eq('f_phon  ~  0.5 * 17450 / (155e-9 to 235e-9)  ~  37 -- 56 GHz'))
story.append(body(
    'This is far above the 5 GHz target. Reconciliation strategies include: '
    '(1) accept the ~50 GHz natural gap and target a high-frequency phonon mode; '
    '(2) use the snowflake geometry which has a simultaneous phononic + photonic gap '
    'at the same a (Safavi-Naeini &amp; Painter 2010 demonstrate this for Si at ~9.5 GHz '
    'but photonic + phononic co-design at 619 nm in diamond has not been done); '
    '(3) decouple the lattice constants (superlattice or quasi-periodic design).'
))
story.append(ref(
    'Safavi-Naeini &amp; Painter (2010) Opt. Express 18, 19659: '
    'simultaneous phononic + photonic bandgap in Si snowflake crystal; '
    'Chan thesis Ch. 4: co-design strategy for nanobeam optomechanical crystal.'
))

story.append(h2('4.3  Upgrade path: circles -> snowflake'))
story.append(body(
    'The circular-hole geometry used in the current scripts is a pipeline validation '
    'step. Circular holes in a triangular lattice may produce only a narrow or partial '
    'phononic bandgap for Lamb waves (the gap depends critically on r/a and d/a). '
    'The snowflake geometry (6 arms at 60-degree rotations, each arm a rounded rectangle) '
    'is known to produce a wide simultaneous phononic + photonic bandgap '
    '(Safavi-Naeini &amp; Painter 2010, Fig. 1, ~30% fractional gap for phonons). '
    'Once the COMSOL pipeline is validated with circles, upgrading the unit cell to '
    'snowflake requires only modifying the geometry section of phononic_band.py.'
))
story.append(ref(
    'Safavi-Naeini &amp; Painter 2010 Fig. 1, Table 1: snowflake geometry parameters '
    '(a, r_s, t_s, d/a) and resulting bandgap map; '
    'Chan thesis Fig. 3.9: cross unit cell as comparison.'
))

story.append(sp(8))
story.append(hr())
story.append(Paragraph(
    'References',
    h1_style,
))
refs = [
    ('[1] J. Chan, PhD thesis, Caltech (2012). '
     '"Laser cooling of an optomechanical crystal resonator to its quantum ground state of motion." '
     'Key sections: Sec. 3.1.4 (Bloch states, frequency scaling), '
     'App. F (COMSOL Floquet BVP setup), Fig. 3.9 (cross unit cell phononic shield).'),
    ('[2] A. H. Safavi-Naeini and O. Painter, Opt. Express 18, 19659 (2010). '
     '"Design of optomechanical cavities and waveguides on a simultaneous bandgap phononic-photonic crystal slab." '
     'Key content: snowflake geometry, simultaneous phoxonic bandgap, Si slab a=500 nm example.'),
    ('[3] M. Grimsditch and A. K. Ramdas, Phys. Rev. B 11, 3139 (1975). '
     '"Brillouin scattering in diamond." '
     'Elastic constants: c11=1076, c12=125, c44=578 GPa.'),
    ('[4] COMSOL Multiphysics Documentation. '
     'Solid Mechanics module: Floquet periodic conditions, Eigenfrequency study settings.'),
]
for r_text in refs:
    story.append(ref(r_text))
    story.append(sp(4))

doc.build(story)
print('Saved: ' + OUT)
