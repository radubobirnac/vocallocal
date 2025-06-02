@echo off
echo ========================================
echo    VocalLocal Development Server
echo ========================================
echo.
echo Starting Flask server on port 5001...
echo.
echo Once started, you can access:
echo - Home Page: https://localhost:5001
echo - Try It Free: https://localhost:5001/try-it-free
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd /d "%~dp0"
python app.py --port 5001

echo.
echo Server stopped. Press any key to close this window...
pause > nul
