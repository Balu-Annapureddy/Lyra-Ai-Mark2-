@echo off
REM Run E2E Smoke Tests
REM Requires server to be running on localhost:8000

echo ========================================
echo Lyra AI Mark2 - E2E Smoke Tests
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
call venv\Scripts\activate.bat

REM Install test dependencies
echo Installing test dependencies...
pip install -q -r requirements-test.txt

echo.
echo Running smoke tests...
echo Make sure the server is running on http://localhost:8000
echo.

REM Run tests
pytest tests/e2e/test_smoke.py -v --asyncio-mode=auto

REM Deactivate
deactivate

echo.
echo Tests complete!
pause
