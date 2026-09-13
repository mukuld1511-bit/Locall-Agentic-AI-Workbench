@echo off

title RTX 5060 Check

echo.
echo ============================================================
echo NVIDIA GPU CHECK
echo ============================================================
echo.

where nvidia-smi >nul 2>nul

if errorlevel 1 (
    echo [ERROR] nvidia-smi not found.
    echo Install the current NVIDIA Windows driver.
    pause
    exit /b 1
)

nvidia-smi

echo.
echo ============================================================
echo PYTORCH CUDA CHECK
echo ============================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import torch; print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')"
) else (
    echo [INFO] .venv not created yet.
    echo Run setup_windows.bat first.
)

echo.
pause
