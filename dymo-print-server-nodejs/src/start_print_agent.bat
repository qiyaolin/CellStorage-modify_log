@echo off
echo Starting DYMO Print Agent...
echo.
echo Checking configuration...
if not exist "print_agent_config.json" (
    echo ERROR: print_agent_config.json not found!
    echo Please copy print_agent_config.example.json to print_agent_config.json and configure it.
    pause
    exit /b 1
)

echo Configuration found.
echo.
echo Starting print agent service...
echo Press Ctrl+C to stop the service.
echo.

python production_print_agent.py

pause