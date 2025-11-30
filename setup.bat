@echo off
REM Lyra AI Mark2 - Windows Setup Script
REM Automates initial setup and environment configuration

echo ========================================
echo Lyra AI Mark2 - Setup Script
echo ========================================
echo.

REM Check Python version
echo [1/6] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from python.org
    pause
    exit /b 1
)

python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10 or higher is required
    python --version
    pause
    exit /b 1
)

echo Python version OK
python --version
echo.

REM Create virtual environment
echo [2/6] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment
echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

REM Upgrade pip
echo [4/6] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo pip upgraded successfully
echo.

REM Install requirements
echo [5/6] Installing dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully
) else (
    echo WARNING: requirements.txt not found
    echo Skipping dependency installation
)
echo.

REM Check GPU availability
echo [6/6] Checking GPU availability...
python -c "try: import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}'); print(f'GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}') except ImportError: print('PyTorch not installed - GPU check skipped')" 2>nul
echo.

REM Create necessary directories
echo Creating necessary directories...
if not exist "ai-worker\cache" mkdir "ai-worker\cache"
if not exist "ai-worker\state" mkdir "ai-worker\state"
if not exist "ai-worker\logs" mkdir "ai-worker\logs"
if not exist "ai-worker\config" mkdir "ai-worker\config"
echo Directories created
echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    (
        echo # Lyra AI Mark2 - Environment Configuration
        echo LYRA_ENV=development
        echo LYRA_HOST=0.0.0.0
        echo LYRA_PORT=8000
        echo.
        echo # Logging
        echo LOG_LEVEL=INFO
        echo LOG_FILE=logs/lyra.log
        echo.
        echo # Cache Settings
        echo CACHE_DIR=ai-worker/cache
        echo CACHE_MAX_SIZE_GB=50
        echo.
        echo # Performance
        echo MAX_WORKERS=4
        echo MEMORY_LIMIT_PERCENT=85
    ) > .env
    echo .env file created with default settings
    echo Please review and update .env as needed
) else (
    echo .env file already exists
)
echo.

REM Setup complete
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Review and update .env file if needed
echo 2. Navigate to ai-worker directory: cd ai-worker
echo 3. Run the application: python app.py
echo.
echo For production deployment, see DEPLOYMENT.md
echo.
pause
