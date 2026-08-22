@echo off
setlocal
title RAG Asistent - INSTALL
cd /d "%~dp0"

rem -- all install output goes here, so we always have something to read --
set "LOGFILE=install_log.txt"
echo === RAG Asistent install %date% %time% ===> "%LOGFILE%"

echo.
echo === RAG Asistent: installation ===
echo (progress is written to install_log.txt)
echo.

rem ---- find a good Python (3.12 first, then 3.11) ----
rem Note: the py launcher might be missing, so we try several names.
set "PYCMD="

set "PYC=py -3.12"
%PYC% -c "import sys" >nul 2>&1
if not errorlevel 1 goto :pyfound
set "PYC=py -3.11"
%PYC% -c "import sys" >nul 2>&1
if not errorlevel 1 goto :pyfound
set "PYC=python"
%PYC% -c "import sys; v=sys.version_info; raise SystemExit(0 if (v>=(3,10) and v<(3,14)) else 1)" >nul 2>&1
if not errorlevel 1 goto :pyfound

echo.
echo [!] No suitable Python found.
echo     This needs Python 3.11 or 3.12 (3.14 is too new - no numpy wheels).
echo     Download Python 3.12 from:  https://www.python.org/downloads/
echo     Tick "Add python.exe to PATH" during install.
echo.
pause
exit /b 1

:pyfound
set "PYCMD=%PYC%"

echo Using: %PYCMD%
echo Using: %PYCMD%>> "%LOGFILE%"

rem ---- create venv if missing ----
if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment...
    %PYCMD% -m venv .venv 2>> "%LOGFILE%"
    if errorlevel 1 goto :fail
) else (
    echo [1/3] venv found, reusing.
)

rem ---- upgrade pip ----
echo [2/3] Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip >> "%LOGFILE%" 2>&1

rem ---- install deps: only prebuilt wheels, never compile ----
echo [3/3] Installing dependencies...
echo [3/3] Installing dependencies...>> "%LOGFILE%"
".venv\Scripts\python.exe" -m pip install --only-binary=:all: --prefer-binary -r requirements.txt >> "%LOGFILE%" 2>&1
set "RC=%ERRORLEVEL%"

echo.
echo Exit code: %RC%
echo.
if "%RC%"=="0" (
    echo DONE. Now double-click RUN.bat
) else (
    echo [!] Install failed. Open install_log.txt and read the ERROR line.
    echo     Send the last 20 lines to Hermes.
)
echo.

rem -- hard keep window open no matter what --
pause
exit /b %RC%

:fail
echo.
echo [!] Setup failed during venv creation.
echo     Details are in install_log.txt
echo.
pause
exit /b 1