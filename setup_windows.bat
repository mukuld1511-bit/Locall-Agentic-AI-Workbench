@echo off
setlocal

title Local Agentic AI Workbench - Windows Setup

echo.
echo ============================================================
echo LOCAL AGENTIC AI WORKBENCH - WINDOWS SETUP
echo RTX 5060
echo ============================================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python launcher not found.
    echo Install Python 3.12 from python.org and rerun this file.
    pause
    exit /b 1
)

echo [1/6] Checking Python...
py -3.12 --version
if errorlevel 1 (
    echo [ERROR] Python 3.12 not found.
    echo.
    echo Install Python 3.12 first.
    pause
    exit /b 1
)

echo.
echo [2/6] Creating Windows virtual environment...

if exist ".venv" (
    echo [INFO] Existing .venv found.
) else (
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create virtual environment.
        pause
        exit /b 1
    )
)

echo.
echo [3/6] Upgrading pip...

".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

echo.
echo [4/6] Installing project dependencies...

if exist "requirements-windows.txt" (
    ".venv\Scripts\python.exe" -m pip install -r requirements-windows.txt
) else if exist "requirements.txt" (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
) else (
    echo [WARNING] No requirements file found.
)

echo.
echo [5/6] Checking PySide6...

".venv\Scripts\python.exe" -c "import PySide6; print('PySide6 OK')"

if errorlevel 1 (
    echo [WARNING] PySide6 is missing.
    ".venv\Scripts\python.exe" -m pip install PySide6
)

echo.
echo [6/6] Creating local directories...

if not exist "models" mkdir models
if not exist "vision-media" mkdir vision-media
if not exist "logs" mkdir logs
if not exist "workspace" mkdir workspace

echo.
echo ============================================================
echo SETUP COMPLETE
echo ============================================================
echo.
echo Run:
echo     start_workbench.bat
echo.
pause
endlocal
