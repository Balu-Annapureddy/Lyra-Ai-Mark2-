@echo off
REM Setup and run frontend development server

echo ========================================
echo Lyra AI Frontend - Development Server
echo ========================================
echo.

cd frontend

REM Check if node_modules exists
if not exist "node_modules\" (
    echo Installing dependencies...
    call npm install
    echo.
)

echo Starting development server...
echo Frontend will be available at: http://localhost:5173
echo.

call npm run dev
