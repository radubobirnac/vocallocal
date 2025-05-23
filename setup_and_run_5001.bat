@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo VocalLocal Setup and Run - Port 5001
echo ===================================================
echo.

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM Install required packages
echo Installing required packages...
pip install flask python-dotenv werkzeug jinja2

REM Check if requirements.txt exists and install dependencies
if exist "requirements.txt" (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo WARNING: Some dependencies failed to install.
        echo The application may still work with limited functionality.
        echo.
    )
) else (
    echo requirements.txt not found. Installed minimal dependencies only.
)

REM Create minimal .env file if it doesn't exist
if not exist ".env" (
    echo Creating minimal .env file...
    echo SECRET_KEY=development_key > .env
    echo DEBUG=True >> .env
)

REM Create uploads directory if it doesn't exist
if not exist "uploads" mkdir uploads

echo.
echo ===================================================
echo Starting VocalLocal server on port 5001...
echo ===================================================
echo.
echo Server will be available at: http://localhost:5001
echo.
echo Press Ctrl+C to stop the server
echo ===================================================
echo.

REM Start the Flask application
python app.py --port 5001 --host 127.0.0.1

REM If the server exits with an error, keep the window open
if %errorlevel% neq 0 (
    echo.
    echo Server stopped with an error (code: %errorlevel%).
    pause
)
