@echo off
echo ========================================
echo VocalLocal Server Diagnostics
echo ========================================
echo.

echo Checking if Flask server is running...
netstat -an | findstr :5001
if %errorlevel% == 0 (
    echo ✓ Something is listening on port 5001
) else (
    echo ✗ Nothing is listening on port 5001
    echo You need to run start_server.bat first!
    pause
    exit /b 1
)

echo.
echo Testing server response...
curl -s -o nul -w "HTTP Status: %%{http_code}\n" http://localhost:5001/
if %errorlevel% == 0 (
    echo ✓ Server responded successfully
) else (
    echo ✗ Server did not respond
)

echo.
echo Testing specific endpoints...
echo Testing /test-sandbox:
curl -s -o nul -w "HTTP Status: %%{http_code}\n" http://localhost:5001/test-sandbox

echo Testing /static/test_sandbox.html:
curl -s -o nul -w "HTTP Status: %%{http_code}\n" http://localhost:5001/static/test_sandbox.html

echo Testing /test_chunking_fix.html:
curl -s -o nul -w "HTTP Status: %%{http_code}\n" http://localhost:5001/test_chunking_fix.html

echo.
echo ========================================
echo If all tests pass, try opening:
echo http://localhost:5001/static/test_sandbox.html
echo ========================================
pause
