@echo off
setlocal EnableExtensions
cd /d "%~dp0"
rem The default `py -3` interpreter may be a separate Python installation
rem without the Windows Tcl/Tk component. Probe all supported Python versions
rem and use the first interpreter that can import Tkinter.
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
    echo.
    echo ERROR: Hastings Chess could not find Python 3.10 or later with Tkinter.
    echo This is a Python GUI installation issue, not a Fairy-Stockfish failure.
    echo.
    echo Installed Python interpreters, if the Python launcher is available:
    where py >nul 2>nul
    if not errorlevel 1 py -0p
    echo.
    echo Repair or modify your Python installation with the official Windows
    echo installer and enable "tcl/tk and IDLE" under Optional Features.
    echo Then reopen START_HASTINGS.bat.
    echo See WINDOWS_TKINTER_FIX.md for details.
    echo.
    pause
    exit /b 1
)
echo Using %HASTINGS_PY% with Tkinter.
%HASTINGS_PY% app.py
if errorlevel 1 (
    echo.
    echo Hastings Chess stopped with an error. The details are above.
    pause
    exit /b 1
)
endlocal
