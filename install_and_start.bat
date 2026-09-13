@echo off

call setup_windows.bat

if errorlevel 1 (
    echo Setup failed.
    pause
    exit /b 1
)

call check_gpu.bat

call start_workbench.bat
