@echo off
echo ===================================================
echo VocalLocal Development Server
echo ===================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Check if required directories exist
if not exist "static" (
    echo Warning: 'static' directory not found.
    echo This might indicate you're not running from the correct directory.
    echo Current directory: %CD%
    echo.
    set /p continue=Continue anyway? (y/n): 
    if /i not "%continue%"=="y" exit /b 1
    echo.
)

REM Create upload directory if it doesn't exist
if not exist "uploads" (
    echo Creating uploads directory...
    mkdir uploads
)

echo Starting VocalLocal server on port 5001...
echo.
echo Server will be available at: http://localhost:5001
echo.
echo Press Ctrl+C to stop the server
echo ===================================================
echo.

REM Start the Flask application with browser auto-open
python app.py --port 5001 --open-browser

REM If the server exits with an error, keep the window open
if %errorlevel% neq 0 (
    echo.
    echo Server stopped with an error (code: %errorlevel%).
    pause
)
