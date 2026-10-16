"""
Shared utilities for COMSOL mph Python scripts.
Imported by all simulation scripts; remote_runner.py copies it alongside them.
"""
import sys
import time
import numpy as np
import matplotlib
matplotlib.use('Agg')


def start_client(model_file='unit_cell_3.mph'):
    """
    Start a headless COMSOL server (no GUI) and load model_file.
    Uses mph.start() which manages the server process internally.
    """
    import mph
    print('Starting COMSOL server (headless)...')
    sys.stdout.flush()
    client = mph.start()
    print(f'Loading {model_file}...')
    sys.stdout.flush()
    model = client.load(model_file)
    print('Model loaded.')
    sys.stdout.flush()
    return client, model


def mphglobal(m_java, expr, dataset):
    """
    Extract eigenvalue/eigenfrequency vector from a solved dataset.
    Equivalent to MATLAB mphglobal(model, expr, 'Dataset', dataset).
    Returns a complex numpy array, one entry per eigenvalue.

    solnum='all' is not supported by COMSOL Java API (only constant expressions
    allowed). Instead we iterate solnum=1,2,... until COMSOL raises out-of-range.
    """
    tag = '_tmp_gev'
    try:
        ev = m_java.result().numerical().create(tag, 'EvalGlobal')
        ev.set('data', dataset)
        ev.set('expr', expr)
        results = []
        for i in range(1, 201):  # 200 >> any realistic N_mode
            try:
                ev.set('solnum', str(i))
                re = ev.getReal()
                im = ev.getImag()
                results.append(complex(float(re[0][0]), float(im[0][0])))
            except Exception:
                break
        return np.array(results)
    finally:
        try:
            m_java.result().numerical().remove(tag)
        except Exception:
            pass


def make_bz_path(a, N_ks):
    """Return (2, n_kpts) array of k-vectors for Gamma->M->K->Gamma."""
    kxs_GM = np.pi/a * np.linspace(0,   1,   N_ks)
    kys_GM = np.pi/a * np.linspace(0,   1/np.sqrt(3), N_ks)
    kxs_MK = np.pi/a * np.linspace(1,   4/3, N_ks)
    kys_MK = np.pi/a * np.linspace(1/np.sqrt(3), 0,   N_ks)
    kxs_KG = np.pi/a * np.linspace(4/3, 0,   N_ks)
    kys_KG = np.pi/a * np.linspace(0,   0,   N_ks)
    kxs = np.concatenate([kxs_GM, kxs_MK[1:], kxs_KG[1:]])
    kys = np.concatenate([kys_GM, kys_MK[1:], kys_KG[1:]])
    return np.array([kxs, kys])


def bz_ticks(N_ks):
    return [1, N_ks, 2*N_ks-1, 3*N_ks-2]


BZ_LABELS = [r'$\Gamma$', 'M', 'K', r'$\Gamma$']
