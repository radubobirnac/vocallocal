@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo VocalLocal Development Server - Debug Mode
echo ===================================================
echo.

REM Display current directory
echo Current directory: %CD%
echo.

REM Check if Python is installed and get version
echo Checking Python installation...
python --version > temp_version.txt 2>&1
set /p PYTHON_VERSION=<temp_version.txt
del temp_version.txt

echo Python version: %PYTHON_VERSION%
if "%PYTHON_VERSION%"=="" (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM List key files to verify environment
echo.
echo Checking for key application files...
if exist "app.py" (
    echo FOUND: app.py
) else (
    echo MISSING: app.py - This is the main application file
    echo This might indicate you're not running from the correct directory.
)

if exist "static" (
    echo FOUND: static directory
) else (
    echo MISSING: static directory - Contains CSS, JavaScript, and images
)

if exist "templates" (
    echo FOUND: templates directory
) else (
    echo MISSING: templates directory - Contains HTML templates
)

REM Create upload directory if it doesn't exist
if not exist "uploads" (
    echo Creating uploads directory...
    mkdir uploads
    echo CREATED: uploads directory
) else (
    echo FOUND: uploads directory
)

echo.
echo ===================================================
echo Starting VocalLocal server on port 5001...
echo ===================================================
echo.
echo Server will be available at: http://localhost:5001
echo.
echo If the browser doesn't open automatically, please
echo manually navigate to: http://localhost:5001
echo.
echo Press Ctrl+C to stop the server
echo ===================================================
echo.

REM Start the Flask application with verbose output
echo Starting Flask application...
python app.py --port 5001 --debug

REM If the server exits with an error, keep the window open
if %errorlevel% neq 0 (
    echo.
    echo Server stopped with an error (code: %errorlevel%).
    echo.
    echo Possible issues:
    echo 1. Port 5001 might be in use by another application
    echo 2. Required Python packages might be missing
    echo 3. There might be syntax errors in the application code
    echo.
    echo Try running: pip install -r requirements.txt
    echo to ensure all dependencies are installed.
    echo.
    pause
)
