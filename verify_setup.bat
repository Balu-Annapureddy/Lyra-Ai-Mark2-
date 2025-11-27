@echo off
REM Verification script to check if Lyra AI Mark2 is ready to run
REM This checks all prerequisites without starting servers

echo ========================================
echo Lyra AI Mark2 - Setup Verification
echo ========================================
echo.

set ERROR_COUNT=0

REM Check 1: Python
echo [1/8] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] Python not found
    set /a ERROR_COUNT+=1
) else (
    python --version
    echo   [OK] Python found
)
echo.

REM Check 2: Node.js
echo [2/8] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] Node.js not found
    set /a ERROR_COUNT+=1
) else (
    node --version
    echo   [OK] Node.js found
)
echo.

REM Check 3: Virtual environment
echo [3/8] Checking virtual environment...
if exist "venv\" (
    echo   [OK] Virtual environment exists
) else (
    echo   [FAIL] Virtual environment not found
    echo   Run: setup_venv.bat
    set /a ERROR_COUNT+=1
)
echo.

REM Check 4: Backend files
echo [4/8] Checking backend files...
if exist "ai-worker\app.py" (
    echo   [OK] app.py found
) else (
    echo   [FAIL] app.py not found
    set /a ERROR_COUNT+=1
)
echo.

REM Check 5: Core modules
echo [5/8] Checking core modules...
set MODULE_COUNT=0
for %%f in (ai-worker\core\*.py) do set /a MODULE_COUNT+=1
echo   [OK] Found %MODULE_COUNT% core modules
echo.

REM Check 6: Frontend directory
echo [6/8] Checking frontend...
if exist "frontend\package.json" (
    echo   [OK] Frontend package.json found
) else (
    echo   [FAIL] Frontend not set up
    set /a ERROR_COUNT+=1
)
echo.

REM Check 7: Frontend dependencies
echo [7/8] Checking frontend dependencies...
if exist "frontend\node_modules\" (
    echo   [OK] Frontend dependencies installed
) else (
    echo   [WARN] Frontend dependencies not installed
    echo   Run: cd frontend ^&^& npm install
)
echo.

REM Check 8: Start scripts
echo [8/8] Checking start scripts...
if exist "start.bat" (
    echo   [OK] Backend start script found
) else (
    echo   [FAIL] start.bat not found
    set /a ERROR_COUNT+=1
)
if exist "start-frontend.bat" (
    echo   [OK] Frontend start script found
) else (
    echo   [FAIL] start-frontend.bat not found
    set /a ERROR_COUNT+=1
)
echo.

REM Summary
echo ========================================
echo Verification Summary
echo ========================================
if %ERROR_COUNT%==0 (
    echo [SUCCESS] All checks passed!
    echo.
    echo Ready to start:
    echo   1. Run: start.bat ^(backend^)
    echo   2. Run: start-frontend.bat ^(frontend^)
    echo   3. Open: http://localhost:5173
) else (
    echo [FAILED] %ERROR_COUNT% check(s) failed
    echo.
    echo Please fix the issues above before starting.
)
echo ========================================

pause
