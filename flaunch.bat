@echo off
setlocal
rem Launch utility for Flux
set PYTHONPATH=%PYTHONPATH%;%~dp0/py/flaunch_packages.zip
python %~dp0/src/launch/start.py %*
