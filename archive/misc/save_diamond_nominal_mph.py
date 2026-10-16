"""
save_diamond_nominal_mph.py

Loads unit_cell_3.mph, sets diamond center-point parameters, and saves as
diamond_nominal.mph.  No simulation is run -- open in COMSOL GUI to inspect
the geometry and check the snowflake looks right before trusting sweep results.

Center of diamond sweep: a=190nm, d=72nm, w=43nm, t=140nm, f_r=10nm

Run via:
    python scripts/remote_runner.py --block scripts/save_diamond_nominal_mph.py
"""

import mph
from pathlib import Path

print('Starting COMSOL...')
client = mph.start()
model  = client.load('unit_cell_3.mph')
m      = model.java

# Diamond material overrides
mat = m.material('mat1').propertyGroup('def')
mat.set('density',       '3500[kg/m^3]')
mat.set('youngsmodulus', '1050e9[Pa]')
mat.set('poissonsratio', '0.07')

# Center of 5x5 sweep: d=72nm, w=43nm (midpoints of linspace ranges)
a   = 190e-9
d   = 72e-9
w   = 43e-9
t   = 140e-9
f_r = 10e-9

for name, val in [('a', a), ('d', d), ('w', w), ('f_r', f_r), ('t', t)]:
    m.param().set(name, str(val))

out = 'diamond_nominal.mph'
model.save(out)
print(f'Saved: {out}')
client.clear()
