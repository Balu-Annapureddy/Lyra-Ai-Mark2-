@echo off
REM Quick Start Script for Lyra AI Mark2
REM Activates virtual environment and starts the application

echo ========================================
echo Lyra AI Mark2 - Quick Start
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_venv.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if activation succeeded
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo Starting Lyra AI Mark2...
echo Server will be available at: http://localhost:8000
echo Health check: http://localhost:8000/health/
echo.

REM Start the application
cd ai-worker
python app.py

REM Deactivate on exit
deactivate
