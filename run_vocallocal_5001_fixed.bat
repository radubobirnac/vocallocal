@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo VocalLocal Development Server - Fixed Version
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

REM Check for key files
echo.
echo Checking for key application files...
if exist "app.py" (
    echo FOUND: app.py
) else (
    echo MISSING: app.py - This is the main application file
    echo This might indicate you're not running from the correct directory.
    pause
    exit /b 1
)

REM Check for .env file and create if needed
if not exist ".env" (
    echo .env file not found. Creating a minimal .env file...
    echo # Minimal configuration for VocalLocal > .env
    echo SECRET_KEY=development_secret_key >> .env
    echo DEBUG=True >> .env
    echo # You can add API keys later if needed >> .env
    echo # OPENAI_API_KEY=your_key_here >> .env
    echo # GEMINI_API_KEY=your_key_here >> .env
    echo .env file created with minimal configuration.
) else (
    echo FOUND: .env file
)

REM Create required directories
if not exist "uploads" (
    echo Creating uploads directory...
    mkdir uploads
    echo CREATED: uploads directory
) else (
    echo FOUND: uploads directory
)

if not exist "static" (
    echo WARNING: static directory not found. This may cause issues with CSS and JavaScript.
)

if not exist "templates" (
    echo WARNING: templates directory not found. This may cause issues with HTML templates.
)

REM Install required packages
echo.
echo Checking for required packages...
pip show flask > nul 2>&1
if %errorlevel% neq 0 (
    echo Flask not found. Installing required packages...
    pip install flask python-dotenv
    if %errorlevel% neq 0 (
        echo Failed to install required packages.
        pause
        exit /b 1
    )
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

REM Set environment variables for this session
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Start the Flask application with minimal configuration
python app.py --port 5001 --debug --host 127.0.0.1

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
