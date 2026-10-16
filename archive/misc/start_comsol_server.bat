@echo off
echo Starting COMSOL 6.4 server on port 2036...
echo Working directory: C:\Users\abby\comsol
echo Keep this window open while simulations are running.
echo Press Ctrl+C to stop the server.
"C:\Program Files\COMSOL\COMSOL64\Multiphysics_copy1\bin\win64\comsol.exe" mphserver -port 2036 -login off
