@echo off
setlocal

title Local Agentic AI Workbench

cd /d "%~dp0"

echo.
echo ============================================================
echo STARTING LOCAL AGENTIC AI WORKBENCH
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Windows environment not found.
    echo Running setup first...
    call setup_windows.bat

    if errorlevel 1 (
        echo [ERROR] Setup failed.
        pause
        exit /b 1
    )
)

echo [INFO] Starting Workbench...
echo.

".venv\Scripts\python.exe" -m desktop_gui.main

if errorlevel 1 (
    echo.
    echo ========================================================
    echo WORKBENCH EXITED WITH ERROR
    echo ========================================================
    echo.
    pause
)

endlocal
