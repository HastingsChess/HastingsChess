@echo off
setlocal EnableExtensions
cd /d "%~dp0"
rem Use a Python interpreter that supports the Tk desktop GUI tests.
set "HASTINGS_PY="
where py >nul 2>nul
if not errorlevel 1 (
    for %%V in (3.15 3.14 3.13 3.12 3.11 3.10) do (
        if not defined HASTINGS_PY (
            py -%%V -c "import sys, tkinter; assert sys.version_info >= (3, 10)" >nul 2>nul
            if not errorlevel 1 set "HASTINGS_PY=py -%%V"
        )
    )
)
if not defined HASTINGS_PY (
    python -c "import sys, tkinter; assert sys.version_info >= (3, 10)" >nul 2>nul
    if not errorlevel 1 set "HASTINGS_PY=python"
)
if not defined HASTINGS_PY (
    echo ERROR: Python 3.10+ with Tkinter is required for the GUI tests.
    echo See WINDOWS_TKINTER_FIX.md.
    where py >nul 2>nul
    if not errorlevel 1 py -0p
    pause
    exit /b 1
)
echo Running tests using %HASTINGS_PY%.
%HASTINGS_PY% -m unittest -v tests test_engine test_features test_resources test_gui
pause
endlocal
