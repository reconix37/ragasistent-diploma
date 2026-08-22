@echo off
setlocal
title RAG Asistent
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo No venv found. Run INSTALL.bat first.
    echo.
    pause
    exit /b 1
)

echo Starting RAG Asistent...
echo Browser will open at  http://localhost:8501
echo Close this window to stop the app.
echo.

rem open browser a few seconds after launch
start "" /b cmd /c "timeout /t 5 >nul & start http://localhost:8501"

".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true --browser.gatherUsageStats false

pause