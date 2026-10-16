"""
discover_op_study.py
====================
Prints the COMSOL model's study, solution, and dataset tags, plus the
f_op parameter value. Run this once to confirm the tags needed for
sweep_Si_mech_python.py before adding the optical sweep section.

Run via:
    python scripts/remote_runner.py --block scripts/discover_op_study.py
"""

import sys
from comsol_utils import start_client

client, model = start_client('unit_cell_3.mph')
m = model.java

print("=== Studies ===")
for tag in m.study().tags():
    try:
        label = str(m.study(tag).label())
    except Exception:
        label = '?'
    print(f"  {tag}  ({label})")

print("\n=== Solutions ===")
for tag in m.sol().tags():
    print(f"  {tag}")

print("\n=== Datasets ===")
for tag in m.result().dataset().tags():
    try:
        label = str(m.result().dataset(tag).label())
    except Exception:
        label = '?'
    print(f"  {tag}  ({label})")

print("\n=== Parameters ===")
for name in ['a', 'd', 'w', 'f_r', 't', 'N_mode', 'f_mech', 'f_op', 'scaling']:
    try:
        val = m.param().get(name)
        print(f"  {name} = {val}")
    except Exception:
        print(f"  {name} = (not found)")

print("\n=== ewfd feature tags ===")
try:
    ewfd = m.component('comp1').physics('ewfd')
    for tag in ewfd.feature().tags():
        try:
            label = str(ewfd.feature(tag).label())
        except Exception:
            label = '?'
        print(f"  {tag}  ({label})")
except Exception as e:
    print(f"  Error reading ewfd features: {e}")

client.clear()
print("\nDone.")
