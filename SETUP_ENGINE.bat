@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 setup_engine.py
) else (
  python setup_engine.py
)
pause
