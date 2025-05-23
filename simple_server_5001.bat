@echo off
echo ===================================================
echo VocalLocal Simple Server - Port 5001
echo ===================================================
echo.

REM Create minimal .env file if it doesn't exist
if not exist ".env" (
    echo Creating minimal .env file...
    echo SECRET_KEY=development_key > .env
    echo DEBUG=True >> .env
)

REM Create uploads directory if it doesn't exist
if not exist "uploads" mkdir uploads

echo Starting Flask server on port 5001...
echo.
echo Server will be available at: http://localhost:5001
echo.
echo Press Ctrl+C to stop the server
echo ===================================================

REM Set environment variables
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Start the server with minimal configuration
python -m flask run --port=5001 --host=127.0.0.1

REM If there's an error, keep the window open
if %errorlevel% neq 0 (
    echo.
    echo Server failed to start (error code: %errorlevel%)
    echo.
    pause
)
