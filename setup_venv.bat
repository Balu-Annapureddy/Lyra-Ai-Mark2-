@echo off
REM Virtual Environment Setup Script for Windows
REM Creates venv and installs all dependencies

echo ========================================
echo Lyra AI Mark2 - Virtual Environment Setup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.10 or higher from python.org
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo Virtual environment created successfully!
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
echo.

REM Upgrade pip
echo [1/4] Upgrading pip...
python -m pip install --upgrade pip

REM Install core dependencies
echo.
echo [2/4] Installing core dependencies...
cd ai-worker
pip install -r requirements-lightweight.txt

REM Install optional dependencies
echo.
echo [3/4] Installing optional dependencies...
pip install -r requirements-optional.txt

REM Install security dependencies
echo.
echo [4/4] Installing security dependencies...
pip install -r requirements-security.txt

cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Virtual environment created at: venv\
echo.
echo To activate manually:
echo   venv\Scripts\activate.bat
echo.
echo To start the application:
echo   start.bat
echo.
echo ========================================

deactivate
pause
