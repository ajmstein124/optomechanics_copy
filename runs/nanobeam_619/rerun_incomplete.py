"""rerun_incomplete.py (remote): rerun optical_screen combos that found < 2 guided bands, with N_op = 40."""
import os
import runpy
os.environ['N_OP'] = '40'
os.environ['RERUN_INCOMPLETE'] = '1'
runpy.run_path('nanobeam_619__optical_screen.py', run_name='__main__')
