@echo off
rem Launch utility for Flux
setlocal
set PYTHONPATH=%PYTHONPATH%;%~dp0/py/flaunch_packages.zip
python %~dp0/src/build/start.py %*
