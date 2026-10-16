"""
app.py  --  Local Streamlit UI for phononic crystal parameter setup and results viewing.

Run with:
    streamlit run app.py

Dependencies (local Mac only):
    pip install streamlit matplotlib numpy pandas
"""

import json
import time
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

RESULTS_DIR = Path(__file__).parent / 'results'
CONFIGS_DIR = Path(__file__).parent / 'configs'

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title='Phononic Crystal',
    layout='wide',
    initial_sidebar_state='expanded',
)
st.title('Phononic Crystal — Diamond Slab')

# ── Sidebar: single-run parameters (shared across tabs) ───────────────────────

with st.sidebar:
    st.header('Geometry')
    st.caption('100 – 3000 nm')
    a_nm = st.number_input('a  Lattice constant (nm)', min_value=100, max_value=3000,
                            value=500, step=10)
    st.caption('0.20 – 0.60')
    da   = st.number_input('d/a  Slab thickness', min_value=0.20, max_value=0.60,
                            value=0.44, step=0.01)
    st.caption('0.10 – 0.48  (holes touch at r/a = 0.50)')
    ra   = st.number_input('r/a  Hole radius', min_value=0.10, max_value=0.48,
                            value=0.35, step=0.01)

    d_nm     = da * a_nm
    r_nm     = ra * a_nm
    fill_pct = 2 * np.pi * ra**2 / np.sqrt(3) * 100
    st.caption(f'd = {d_nm:.0f} nm  ·  r = {r_nm:.0f} nm  ·  fill = {fill_pct:.1f}%')

    st.divider()
    st.header('Simulation')
    st.caption('5 – 40')
    n_seg         = st.number_input('k-points per segment', min_value=5, max_value=40,
                                     value=15, step=1)
    st.caption('5 – 40')
    n_modes       = st.number_input('Modes per k-point', min_value=5, max_value=40,
                                     value=20, step=1)
    st.caption('0 – 30 GHz')
    eig_shift_GHz = st.number_input('Eigenfreq shift (GHz)', min_value=0.0, max_value=30.0,
                                     value=3.0, step=0.5)

    st.divider()
    st.header('Material')
    st.caption('Diamond ~1050 · Si ~130 · 4H-SiC ~400 GPa')
    E_GPa = st.number_input('E  Young\'s modulus (GPa)', min_value=1.0,
                             value=1050.0, step=10.0)
    st.caption('0.0 – 0.50  ·  Diamond ~0.07 · Si ~0.28 · 4H-SiC ~0.21')
    nu    = st.number_input('ν  Poisson\'s ratio', min_value=0.0, max_value=0.50,
                             value=0.07, step=0.01)
    st.caption('Diamond ~3500 · Si ~2329 · 4H-SiC ~3210 kg/m³')
    rho   = st.number_input('ρ  Density (kg/m³)', min_value=1.0,
                             value=3500.0, step=10.0)

    E_Pa  = E_GPa * 1e9
    v_LA  = np.sqrt(E_Pa * (1 - nu) / (rho * (1 + nu) * (1 - 2 * nu)))
    f_est = v_LA / (a_nm * 1e-9) / 1e9
    st.caption(f'v_LA ≈ {v_LA/1000:.1f} km/s')
    st.metric('Band center estimate', f'{f_est:.1f} GHz', help='v_LA / a')

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_bs, tab_sweep, tab_est = st.tabs(['Band Structure', 'Parameter Sweep', 'Starting Point'])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — BAND STRUCTURE
# ════════════════════════════════════════════════════════════════════════════════

with tab_bs:
    col_cell, col_band = st.columns([1, 2])

    # ── Unit cell visualization ───────────────────────────────────────────────

    with col_cell:
        st.subheader('Unit cell')

        Lx = float(a_nm)
        Ly = float(a_nm) * np.sqrt(3)
        rp = float(r_nm)

        fig_uc, ax_uc = plt.subplots(figsize=(3.2, 3.2 * np.sqrt(3)))
        ax_uc.set_aspect('equal')
        ax_uc.set_xlim(0, Lx)
        ax_uc.set_ylim(0, Ly)

        ax_uc.add_patch(mpatches.Rectangle((0, 0), Lx, Ly, color='#b8c9e0', zorder=0))
        for hx, hy in [(Lx/2, Ly/2), (0, 0), (Lx, 0), (0, Ly), (Lx, Ly)]:
            ax_uc.add_patch(mpatches.Circle((hx, hy), rp, color='white', zorder=1, clip_on=True))

        ax_uc.annotate('', xy=(Lx/2 + rp, Ly/2), xytext=(Lx/2, Ly/2),
                       arrowprops=dict(arrowstyle='<->', color='#c0392b', lw=1.2))
        ax_uc.text(Lx/2 + rp/2, Ly/2 + Ly*0.025, f'r = {rp:.0f} nm',
                   ha='center', va='bottom', fontsize=8, color='#c0392b')

        for sp in ax_uc.spines.values():
            sp.set_linewidth(1.5)
            sp.set_edgecolor('#2c3e50')
        ax_uc.set_xlabel('x  (nm)', fontsize=9)
        ax_uc.set_ylabel('y  (nm)', fontsize=9)
        ax_uc.set_title(
            f'a = {Lx:.0f} nm   d = {d_nm:.0f} nm\n'
            f'r/a = {ra:.2f}   d/a = {da:.2f}   fill = {fill_pct:.1f}%',
            fontsize=9,
        )
        ax_uc.tick_params(labelsize=8)
        plt.tight_layout()
        st.pyplot(fig_uc)
        plt.close(fig_uc)

        st.caption('k-path: Γ → X → S → Y → Γ  (rectangular BZ)')
        fig_bz, ax_bz = plt.subplots(figsize=(3.0, 1.8))
        kx_max_bz = 1.0
        ky_max_bz = 1.0 / np.sqrt(3)
        pts_bz  = {'G': (0, 0), 'X': (kx_max_bz, 0),
                   'S': (kx_max_bz, ky_max_bz), 'Y': (0, ky_max_bz)}
        lbl_bz  = {'G': 'Γ', 'X': 'X', 'S': 'S', 'Y': 'Y'}
        path_bz = ['G', 'X', 'S', 'Y', 'G']
        xs_bz   = [pts_bz[k][0] for k in path_bz]
        ys_bz   = [pts_bz[k][1] for k in path_bz]
        ax_bz.fill([0, kx_max_bz, kx_max_bz, 0], [0, 0, ky_max_bz, ky_max_bz],
                   color='#eaf0fb', zorder=0)
        ax_bz.plot(xs_bz, ys_bz, 'o-', color='#2c3e50', lw=1.5, ms=5, zorder=2)
        offsets_bz = {'G': (-0.12, 0.03), 'X': (0.04, 0.03),
                      'S': (0.04, 0.03),  'Y': (-0.14, 0.03)}
        for k, (px, py) in pts_bz.items():
            ox, oy = offsets_bz[k]
            ax_bz.text(px + ox, py + oy, lbl_bz[k], fontsize=9, color='#2c3e50')
        ax_bz.set_aspect('equal')
        ax_bz.set_xlim(-0.2, 1.35)
        ax_bz.set_ylim(-0.15, 0.85)
        ax_bz.set_xlabel('kx  (π/a)', fontsize=8)
        ax_bz.set_ylabel('ky  (π/a√3)', fontsize=8)
        ax_bz.tick_params(labelsize=7)
        ax_bz.set_title('Brillouin zone', fontsize=9)
        plt.tight_layout()
        st.pyplot(fig_bz)
        plt.close(fig_bz)

    # ── Band structure viewer ─────────────────────────────────────────────────

    with col_band:
        st.subheader('Band structure')

        hdr_col, btn_col = st.columns([5, 1])
        with btn_col:
            if st.button('↺ Refresh', key='refresh_bs'):
                st.rerun()

        npz_files = (
            sorted(RESULTS_DIR.glob('phononic_band_*.npz'),
                   key=lambda p: p.stat().st_mtime, reverse=True)
            if RESULTS_DIR.exists() else []
        )

        if not npz_files:
            st.info('No results yet — pull .npz files into results/ and hit Refresh.')
        else:
            with hdr_col:
                chosen = st.selectbox('Result file', [p.name for p in npz_files],
                                      label_visibility='collapsed')
            chosen_path = RESULTS_DIR / chosen
            data        = np.load(chosen_path, allow_pickle=True)

            freqs    = data['freqs_GHz']
            k_dist   = data['k_dist']
            tick_idx = data['tick_idx']
            tick_lbl = [str(s).replace('G', 'Γ') for s in data['tick_lbl']]
            tick_x   = k_dist[tick_idx]

            gaps = []
            for b in range(freqs.shape[1] - 1):
                f_top = np.nanmax(freqs[:, b])
                f_bot = np.nanmin(freqs[:, b + 1])
                if f_bot > f_top:
                    fc    = 0.5 * (f_top + f_bot)
                    gfrac = (f_bot - f_top) / fc
                    if gfrac > 0.02:
                        gaps.append((f_top, f_bot, gfrac))

            fig_bs, ax_bs = plt.subplots(figsize=(6.5, 5))
            for mi in range(freqs.shape[1]):
                ax_bs.plot(k_dist, freqs[:, mi], color='steelblue', lw=0.9, alpha=0.8)
            for fl, fu, _ in gaps:
                ax_bs.axhspan(fl, fu, color='tomato', alpha=0.18)
            for xv in tick_x:
                ax_bs.axvline(xv, color='gray', lw=0.5, ls='--')
            ax_bs.set_xticks(tick_x)
            ax_bs.set_xticklabels(tick_lbl, fontsize=11)
            ax_bs.set_xlabel('Wavevector', fontsize=11)
            ax_bs.set_ylabel('Frequency (GHz)', fontsize=11)
            ax_bs.set_xlim(k_dist[0], k_dist[-1])
            ax_bs.set_ylim(0)
            ax_bs.grid(alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig_bs)
            plt.close(fig_bs)

            if gaps:
                st.markdown('**Complete bandgaps:**')
                for fl, fu, gf in gaps:
                    st.markdown(
                        f'- {fl:.3f}–{fu:.3f} GHz &nbsp;·&nbsp; '
                        f'center {0.5*(fl+fu):.3f} GHz &nbsp;·&nbsp; '
                        f'gap/midgap {gf*100:.1f}%'
                    )
            else:
                st.caption('No complete bandgap (gap/midgap > 2%) found.')

            mtime = chosen_path.stat().st_mtime
            st.caption(f'{chosen}  ·  {time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))}')

    # ── Run configuration ─────────────────────────────────────────────────────

    with st.expander('Run configuration'):
        st.markdown('Paste into the **PARAMETERS** block of `scripts/phononic_band.py`:')
        st.code(
            f'# Geometry\n'
            f'a  = {a_nm}e-9    # lattice constant [m]\n'
            f'd  = {d_nm:.1f}e-9    # slab thickness [m]  (d/a = {da:.2f})\n'
            f'r  = {r_nm:.1f}e-9    # hole radius [m]     (r/a = {ra:.2f})\n\n'
            f'# Simulation\n'
            f'n_seg         = {n_seg}\n'
            f'n_modes       = {n_modes}\n'
            f'eig_shift_GHz = {eig_shift_GHz}\n\n'
            f'# Material\n'
            f'E_d   = {E_Pa:.3e}   # Pa\n'
            f'nu_d  = {nu}\n'
            f'rho_d = {rho}',
            language='python',
        )
        st.code('python scripts/remote_runner.py scripts/phononic_band.py', language='bash')

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — PARAMETER SWEEP
# ════════════════════════════════════════════════════════════════════════════════

with tab_sweep:
    col_cfg, col_res = st.columns([1, 2])

    # ── Sweep configuration ───────────────────────────────────────────────────

    with col_cfg:
        st.subheader('Sweep definition')

        # Lattice constant a
        sweep_a = st.checkbox('Sweep a?', value=False)
        if sweep_a:
            st.caption('100 – 3000 nm')
            a_lo  = st.number_input('a min (nm)', min_value=100, max_value=3000,
                                     value=300, step=50, key='a_lo')
            a_hi  = st.number_input('a max (nm)', min_value=100, max_value=3000,
                                     value=1000, step=50, key='a_hi')
            st.caption('2 – 15')
            a_n   = st.number_input('a  points', min_value=2, max_value=15,
                                     value=4, step=1, key='a_n')
            a_arr = np.linspace(a_lo, a_hi, int(a_n)).tolist()
        else:
            a_arr = [float(a_nm)]

        st.divider()

        # Hole radius r/a
        sweep_ra = st.checkbox('Sweep r/a?', value=True)
        if sweep_ra:
            st.caption('0.10 – 0.48')
            ra_lo = st.number_input('r/a  min', min_value=0.10, max_value=0.48,
                                     value=0.25, step=0.01, key='ra_lo')
            ra_hi = st.number_input('r/a  max', min_value=0.10, max_value=0.48,
                                     value=0.46, step=0.01, key='ra_hi')
            st.caption('2 – 25')
            ra_n  = st.number_input('r/a  points', min_value=2, max_value=25,
                                     value=10, step=1, key='ra_n')
            ra_arr = np.linspace(ra_lo, ra_hi, int(ra_n)).tolist()
        else:
            ra_arr = [float(ra)]

        st.divider()

        # Slab thickness d/a
        sweep_da = st.checkbox('Sweep d/a?', value=False)
        if sweep_da:
            st.caption('0.20 – 0.60')
            da_lo = st.number_input('d/a  min', min_value=0.20, max_value=0.60,
                                     value=0.36, step=0.02, key='da_lo')
            da_hi = st.number_input('d/a  max', min_value=0.20, max_value=0.60,
                                     value=0.52, step=0.02, key='da_hi')
            st.caption('2 – 10')
            da_n  = st.number_input('d/a  points', min_value=2, max_value=10,
                                     value=4, step=1, key='da_n')
            da_arr = np.linspace(da_lo, da_hi, int(da_n)).tolist()
        else:
            da_arr = [float(da)]

        st.divider()
        st.markdown('**Solver settings (sweep)**')
        st.caption('3 – 20  (coarser k-path is fine for parameter search)')
        n_seg_sw   = st.number_input('k-points per segment', min_value=3, max_value=20,
                                      value=8, step=1, key='n_seg_sw')
        st.caption('5 – 30')
        n_modes_sw = st.number_input('Modes per k-point', min_value=5, max_value=30,
                                      value=20, step=1, key='n_modes_sw')
        st.caption('0 – 30 GHz')
        eig_sw     = st.number_input('Eigenfreq shift (GHz)', min_value=0.0, max_value=30.0,
                                      value=float(eig_shift_GHz), step=0.5, key='eig_sw')

        st.divider()
        st.markdown('**Save path (Windows machine)**')
        st.caption('Local drive only — avoid OneDrive/network paths')
        save_path = st.text_input(
            'Remote save directory',
            value=r'C:\Users\USERNAME\Documents\optomechanics',
            key='save_path_sw',
        )

        n_combos = len(a_arr) * len(ra_arr) * len(da_arr)
        st.metric('Total combinations', n_combos)
        if n_combos > 100:
            st.warning(f'{n_combos} combos is large. Consider fewer points per axis.')

        if st.button('Write sweep config', type='primary'):
            CONFIGS_DIR.mkdir(exist_ok=True)
            sweep_cfg = {
                'sweep': {
                    'a_nm': [round(x, 1) for x in a_arr],
                    'ra':   [round(x, 4) for x in ra_arr],
                    'da':   [round(x, 4) for x in da_arr],
                },
                'simulation': {
                    'n_seg':         int(n_seg_sw),
                    'n_modes':       int(n_modes_sw),
                    'eig_shift_GHz': float(eig_sw),
                },
                'material': {
                    'E_GPa':    float(E_GPa),
                    'nu':       float(nu),
                    'rho_kgm3': float(rho),
                },
                'save_dir': save_path,
            }
            cfg_path = CONFIGS_DIR / 'sweep_config.json'
            with open(cfg_path, 'w') as f:
                json.dump(sweep_cfg, f, indent=2)
            st.success(f'Written: {cfg_path}')

        st.markdown('Run command:')
        st.code('python scripts/remote_runner.py scripts/phononic_sweep.py',
                language='bash')

    # ── Sweep results ─────────────────────────────────────────────────────────

    with col_res:
        st.subheader('Sweep results')

        _, refresh_col = st.columns([5, 1])
        with refresh_col:
            if st.button('↺ Refresh', key='refresh_sw'):
                st.rerun()

        csv_files = (
            sorted(RESULTS_DIR.glob('sweep_results*.csv'),
                   key=lambda p: p.stat().st_mtime, reverse=True)
            if RESULTS_DIR.exists() else []
        )

        if not csv_files:
            st.info('No sweep results yet — run the sweep and pull results/ back.')
        else:
            try:
                import pandas as pd
            except ImportError:
                st.error('pandas not installed. Run: pip install pandas')
                st.stop()

            chosen_csv = st.selectbox('Results file', [p.name for p in csv_files],
                                      label_visibility='collapsed')
            df = pd.read_csv(RESULTS_DIR / chosen_csv)
            st.caption(f'{len(df)} / {df["combo"].max() if "combo" in df.columns else "?"} combos computed')

            if df.empty:
                st.info('File exists but is empty — sweep may still be running.')
            else:
                # Best result
                best = df.loc[df['gap1_frac'].idxmax()]
                st.markdown(
                    f'**Best gap:** a={best["a_nm"]:.0f} nm, '
                    f'r/a={best["ra"]:.3f}, d/a={best["da"]:.3f}  →  '
                    f'**{best["gap1_frac"]*100:.1f}%** gap/midgap at '
                    f'{best["gap1_center_GHz"]:.2f} GHz'
                )

                # Visualize: auto-detect what was swept
                n_a  = df['a_nm'].nunique()
                n_ra = df['ra'].nunique()
                n_da = df['da'].nunique()

                if n_ra > 1 and n_da > 1 and n_a == 1:
                    # 2D heatmap: r/a vs d/a
                    pivot = df.pivot_table(index='ra', columns='da',
                                           values='gap1_frac', aggfunc='max')
                    fig_hm, ax_hm = plt.subplots(figsize=(6, 4.5))
                    im = ax_hm.imshow(
                        pivot.values * 100, aspect='auto', origin='lower',
                        extent=[pivot.columns.min(), pivot.columns.max(),
                                pivot.index.min(),   pivot.index.max()],
                        cmap='viridis',
                    )
                    plt.colorbar(im, ax=ax_hm, label='Gap/midgap (%)')
                    ax_hm.set_xlabel('d/a', fontsize=11)
                    ax_hm.set_ylabel('r/a', fontsize=11)
                    ax_hm.set_title(
                        f'Phononic bandgap map  (a = {df["a_nm"].iloc[0]:.0f} nm)',
                        fontsize=11,
                    )
                    plt.tight_layout()
                    st.pyplot(fig_hm)
                    plt.close(fig_hm)

                elif n_ra > 1 and n_da == 1:
                    # 1D: r/a sweep
                    for a_val in sorted(df['a_nm'].unique()):
                        sub = df[df['a_nm'] == a_val].sort_values('ra')
                        fig_1d, ax_1d = plt.subplots(figsize=(6, 3.5))
                        ax_1d.plot(sub['ra'], sub['gap1_frac'] * 100,
                                   'o-', color='steelblue', lw=1.5, ms=5)
                        ax_1d.axhline(0, color='gray', lw=0.5)
                        ax_1d.set_xlabel('r/a', fontsize=11)
                        ax_1d.set_ylabel('Gap/midgap (%)', fontsize=11)
                        ax_1d.set_title(
                            f'Bandgap vs r/a  '
                            f'(a={a_val:.0f} nm, d/a={sub["da"].iloc[0]:.2f})',
                            fontsize=11,
                        )
                        ax_1d.grid(alpha=0.3)
                        plt.tight_layout()
                        st.pyplot(fig_1d)
                        plt.close(fig_1d)

                elif n_a > 1:
                    # 1D: a sweep
                    sub = df.sort_values('a_nm')
                    fig_a, ax_a = plt.subplots(figsize=(6, 3.5))
                    ax_a.plot(sub['a_nm'], sub['gap1_center_GHz'],
                              'o-', color='steelblue', lw=1.5, ms=5, label='center')
                    ax_a.fill_between(sub['a_nm'], sub['gap1_lo_GHz'],
                                      sub['gap1_hi_GHz'], alpha=0.2, color='steelblue',
                                      label='gap extent')
                    ax_a.set_xlabel('a  (nm)', fontsize=11)
                    ax_a.set_ylabel('Frequency (GHz)', fontsize=11)
                    ax_a.set_title('Gap center vs lattice constant', fontsize=11)
                    ax_a.legend(fontsize=9)
                    ax_a.grid(alpha=0.3)
                    plt.tight_layout()
                    st.pyplot(fig_a)
                    plt.close(fig_a)

                # Full results table
                with st.expander('Full results table'):
                    show_cols = ['a_nm', 'da', 'ra', 'gap1_frac',
                                 'gap1_center_GHz', 'gap1_lo_GHz', 'gap1_hi_GHz', 'n_gaps']
                    show_cols = [c for c in show_cols if c in df.columns]
                    styled = (df[show_cols]
                              .sort_values('gap1_frac', ascending=False)
                              .reset_index(drop=True)
                              .rename(columns={'gap1_frac': 'gap/midgap',
                                               'gap1_center_GHz': 'center (GHz)',
                                               'gap1_lo_GHz': 'f_lo (GHz)',
                                               'gap1_hi_GHz': 'f_hi (GHz)'}))
                    st.dataframe(styled, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — STARTING POINT
# ════════════════════════════════════════════════════════════════════════════════

with tab_est:
    import pandas as pd

    col_in, col_out = st.columns([1, 2])

    # ── Inputs ────────────────────────────────────────────────────────────────

    with col_in:
        st.subheader('Target frequency')
        st.caption('Desired phononic bandgap center (GHz)')
        f_target = st.number_input('f_target (GHz)', min_value=0.1, max_value=1000.0,
                                    value=5.0, step=0.5, key='f_target_est')

        st.caption('Emitter wavelength for photonic check — SnV: 619 nm')
        lambda_nm = st.number_input('Emitter wavelength (nm)', min_value=100.0,
                                     max_value=3000.0, value=619.0, step=1.0,
                                     key='lambda_est')

        st.divider()
        st.subheader('Slab thickness d')
        sweep_d_est = st.checkbox('Sweep d?', value=False, key='sweep_d_est')
        if sweep_d_est:
            st.caption('50 – 500 nm  (diamond membranes typically 100–300 nm)')
            d_lo_est = st.number_input('d min (nm)', min_value=50.0, max_value=500.0,
                                        value=150.0, step=10.0, key='d_lo_est')
            d_hi_est = st.number_input('d max (nm)', min_value=50.0, max_value=500.0,
                                        value=300.0, step=10.0, key='d_hi_est')
            st.caption('2 – 10')
            d_n_est  = st.number_input('d points', min_value=2, max_value=10,
                                        value=4, step=1, key='d_n_est')
            d_arr_est = np.linspace(d_lo_est, d_hi_est, int(d_n_est)).tolist()
        else:
            st.caption('50 – 500 nm  (diamond membranes typically 100–300 nm)')
            d_fixed_est = st.number_input('d (nm)', min_value=50.0, max_value=500.0,
                                           value=200.0, step=10.0, key='d_fixed_est')
            d_arr_est = [float(d_fixed_est)]

    # ── Outputs ───────────────────────────────────────────────────────────────

    with col_out:

        # Acoustic velocities
        v_LA = np.sqrt(E_Pa * (1 - nu) / (rho * (1 + nu) * (1 - 2 * nu)))
        v_TA = np.sqrt(E_Pa / (2 * rho * (1 + nu)))

        # Estimated lattice constant.
        # Calibration: Safavi-Naeini & Painter Si snowflake a=500nm, v_LA≈9670 m/s,
        # f_gap≈9.5 GHz → α = f*a/v_LA ≈ 0.49.  Use α=0.5.
        # For circular holes the gap opens at a similar frequency but this is ±~30%.
        alpha = 0.5
        a_est_nm = alpha * v_LA / (f_target * 1e9) * 1e9

        # Natural frequency at current sidebar a (quick sanity metric)
        f_natural = alpha * v_LA / (a_nm * 1e-9) / 1e9

        # Photonic TE bandgap range for triangular lattice of holes, n≈2.4
        # Rough estimate: a/λ ≈ 0.25–0.38 (depends on r/a and d/a; needs full photonic sim)
        phot_lo, phot_hi = 0.25, 0.38
        phot_a_lo_nm = phot_lo * lambda_nm
        phot_a_hi_nm = phot_hi * lambda_nm
        phot_f_hi = alpha * v_LA / (phot_a_lo_nm * 1e-9) / 1e9
        phot_f_lo = alpha * v_LA / (phot_a_hi_nm * 1e-9) / 1e9

        # ── Top metrics ───────────────────────────────────────────────────────

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric('v_LA', f'{v_LA/1000:.1f} km/s')
        with m2:
            st.metric('v_TA', f'{v_TA/1000:.1f} km/s')
        with m3:
            st.metric('Estimated a', f'{a_est_nm:.0f} nm',
                      help='f ≈ 0.5 × v_LA / a  (±~30%; run COMSOL for the real number)')
        with m4:
            st.metric('Natural f at sidebar a', f'{f_natural:.1f} GHz',
                      help=f'Expected gap if a stays at {a_nm} nm')

        # ── Photonic compatibility check ───────────────────────────────────────

        a_over_lam = a_est_nm / lambda_nm
        in_phot_range = phot_a_lo_nm <= a_est_nm <= phot_a_hi_nm

        if in_phot_range:
            st.success(
                f'a/λ = {a_over_lam:.2f} — estimated a falls in the photonic TE bandgap '
                f'range (a/λ ≈ {phot_lo}–{phot_hi}) for {lambda_nm:.0f} nm. '
                f'Simultaneous photonic + phononic gap may be feasible.'
            )
        elif a_est_nm > phot_a_hi_nm:
            st.warning(
                f'a/λ = {a_over_lam:.2f} — too large for a photonic gap at {lambda_nm:.0f} nm '
                f'(need a/λ ≈ {phot_lo}–{phot_hi}, i.e. a ≈ {phot_a_lo_nm:.0f}–{phot_a_hi_nm:.0f} nm).'
            )
            st.info(
                f'**Photonically compatible phononic range: {phot_f_lo:.0f}–{phot_f_hi:.0f} GHz** '
                f'(for a ≈ {phot_a_hi_nm:.0f}–{phot_a_lo_nm:.0f} nm at {lambda_nm:.0f} nm).  \n'
                f'At {f_target:.0f} GHz you would need a ≈ {a_est_nm:.0f} nm, which puts the '
                f'photonic bandgap far from {lambda_nm:.0f} nm.  \n'
                f'**Recommended first test:** use a = {a_nm} nm (current sidebar value) — '
                f'expected gap around {f_natural:.0f} GHz. This exercises the full COMSOL '
                f'pipeline cheaply; rescale a once the gap is confirmed.'
            )
        else:
            st.warning(
                f'a/λ = {a_over_lam:.2f} — a is smaller than typical for a photonic gap at '
                f'{lambda_nm:.0f} nm (need a/λ ≈ {phot_lo}–{phot_hi}).'
            )

        # ── Parameter table ───────────────────────────────────────────────────

        rows = []
        for d_val in d_arr_est:
            rows.append({
                'd (nm)':          round(d_val),
                'a (nm)':          round(a_est_nm),
                'd/a':             round(d_val / a_est_nm, 3),
                'f_target (GHz)':  round(f_target, 1),
                'r/a to sweep':    '0.25 – 0.45',
            })
        st.markdown('**Suggested starting parameters:**')
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # ── Scaling plot ──────────────────────────────────────────────────────

        a_plot_max = max(3000.0, a_est_nm * 1.5)
        a_plot = np.linspace(50, a_plot_max, 500)
        f_plot = alpha * v_LA / (a_plot * 1e-9) / 1e9

        fig_est, ax_est = plt.subplots(figsize=(6.5, 3.5))
        ax_est.plot(a_plot, f_plot, color='steelblue', lw=2,
                    label=f'f ≈ 0.5·v_LA/a  (v_LA={v_LA/1000:.1f} km/s)')
        ax_est.axhline(f_target, color='tomato', lw=1.5, ls='--',
                       label=f'target: {f_target:.1f} GHz')
        if a_est_nm <= a_plot_max:
            ax_est.axvline(a_est_nm, color='tomato', lw=1.0, ls=':')
            ax_est.plot(a_est_nm, f_target, 'o', color='tomato', ms=8, zorder=5)
        ax_est.axvspan(phot_a_lo_nm, phot_a_hi_nm, alpha=0.15, color='#2ecc71',
                       label=f'photonic TE gap range ({lambda_nm:.0f} nm)')
        # Mark natural frequency at current sidebar a
        ax_est.plot(a_nm, f_natural, 's', color='#8e44ad', ms=8, zorder=5,
                    label=f'sidebar a={a_nm} nm → {f_natural:.0f} GHz')
        ax_est.set_xlabel('a  (nm)', fontsize=11)
        ax_est.set_ylabel('f_gap estimate  (GHz)', fontsize=11)
        ax_est.set_xlim(0, a_plot_max)
        ax_est.set_ylim(0, min(f_plot[0] * 1.05, 500))
        ax_est.legend(fontsize=9)
        ax_est.grid(alpha=0.3)
        ax_est.set_title(
            'Phononic gap estimate vs a  (f ≈ 0.5·v_LA/a, rough ±30%)\n'
            'Green band = photonic TE gap window for this emitter wavelength',
            fontsize=9,
        )
        plt.tight_layout()
        st.pyplot(fig_est)
        plt.close(fig_est)

        # ── Paste block ───────────────────────────────────────────────────────

        with st.expander('Copy to sidebar'):
            d_show = d_arr_est[0]
            st.code(
                f'a   = {a_est_nm:.0f} nm\n'
                f'd/a = {d_show/a_est_nm:.3f}   (d = {d_show:.0f} nm)\n'
                f'# recommended first sweep: r/a from 0.25 to 0.45',
                language='text',
            )
            if not in_phot_range:
                st.caption(
                    f'For a quick pipeline test, use the current sidebar a = {a_nm} nm instead '
                    f'(expected gap ~{f_natural:.0f} GHz). Rescale a once the gap is confirmed.'
                )
