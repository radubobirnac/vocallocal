@echo off
echo ========================================
echo VocalLocal Test Page Opener
echo ========================================
echo.
echo IMPORTANT: Make sure you run start_server.bat FIRST!
echo.

echo Checking if server is running...
netstat -an | findstr :5001 >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Server appears to be running on port 5001
) else (
    echo ✗ Server is NOT running on port 5001
    echo Please run start_server.bat first!
    echo.
    pause
    exit /b 1
)

echo.
echo Choose which test page to open:
echo.
echo 1. Test Sandbox (Enhanced with 200KB debug logs)
echo 2. Chunking Fix Test (Original test page)
echo 3. Main Application
echo 4. Open ALL test pages
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo Opening Test Sandbox...
    start http://localhost:5001/test-sandbox
    echo.
    echo ✓ Test Sandbox should open in your browser
    echo ✓ This page has enhanced console logging (200KB per log)
    echo ✓ Uses /api/test_transcribe_chunk endpoint (no usage limits)
) else if "%choice%"=="2" (
    echo Opening Chunking Fix Test...
    start http://localhost:5001/test-chunking-fix
    echo.
    echo ✓ Chunking Fix Test should open in your browser
    echo ✓ This page has enhanced console logging (200KB per log)
    echo ⚠ This page does LOCAL testing only (no server calls)
) else if "%choice%"=="3" (
    echo Opening Main Application...
    start http://localhost:5001/
    echo.
    echo ✓ Main application should open in your browser
) else if "%choice%"=="4" (
    echo Opening all test pages...
    start http://localhost:5001/test-sandbox
    timeout /t 1 /nobreak >nul
    start http://localhost:5001/test-chunking-fix
    timeout /t 1 /nobreak >nul
    start http://localhost:5001/
    echo.
    echo ✓ All pages should now be open in separate browser tabs
) else (
    echo Invalid choice. Opening Test Sandbox by default...
    start http://localhost:5001/test-sandbox
)

echo.
echo ========================================
echo CONSOLE LOGGING INSTRUCTIONS:
echo 1. Open browser Developer Tools (F12)
echo 2. Go to Console tab
echo 3. Start recording in the test page
echo 4. You should see MASSIVE debug logs (~200KB each)
echo 5. Copy the logs for debugging
echo ========================================
echo.
pause
