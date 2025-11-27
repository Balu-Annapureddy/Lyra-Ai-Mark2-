@echo off
echo ========================================
echo Lyra AI Mark2 - Virtual Environment Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check RAM (basic check)
echo Checking system RAM...
wmic computersystem get totalphysicalmemory >nul 2>&1
if errorlevel 1 (
    echo WARNING: Could not detect RAM. Proceeding anyway...
) else (
    echo RAM check passed.
)

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install lightweight dependencies
echo.
echo Installing lightweight dependencies...
if exist requirements-lightweight.txt (
    pip install -r requirements-lightweight.txt
) else (
    echo WARNING: requirements-lightweight.txt not found
    echo Installing from requirements.txt instead...
    if exist requirements.txt (
        pip install -r requirements.txt
    ) else (
        echo ERROR: No requirements file found
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Virtual environment is ready at: %cd%\venv
echo.
echo To activate the virtual environment:
echo   venv\Scripts\activate
echo.
echo To start the backend:
echo   python app.py
echo.
pause
