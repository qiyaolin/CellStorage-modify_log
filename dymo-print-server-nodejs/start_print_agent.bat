@echo off
echo ========================================
echo DYMO Centralized Print System
echo Production Version 1.0.0 - Portable
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Checking configuration...
if not exist "%~dp0\src\print_agent_config.json" (
    echo ERROR: Configuration file not found
    echo Please copy print_agent_config.example.json to print_agent_config.json
    echo and edit it with your backend server settings
    pause
    exit /b 1
)

echo Starting DYMO Print Agent...
echo Print station ready - Press Ctrl+C to stop
echo Check print_agent.log for detailed information
echo.

cd /d "%~dp0\src"
python production_print_agent.py

echo.
echo Print agent stopped.
pause