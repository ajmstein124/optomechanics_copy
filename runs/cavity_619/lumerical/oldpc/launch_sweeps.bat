cd /d C:\Users\JVadmin\Documents\optomechanics\lumerical
del lum_w650_mf60_shape_summary.txt 2>nul
py -3.8 -u run_sweeps.py lum_w650_mf60_shape lum_ad_mf60 lum_shape_mf60 > run_sweeps_log.txt 2>&1
