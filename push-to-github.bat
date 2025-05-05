@echo off
echo ===== GitHub Push Tool =====
echo.

set /p commit_message=Enter commit message (leave blank for timestamp):

if "%commit_message%"=="" (
    echo Using default timestamp message...
    python git-push.py
) else (
    echo Using custom message: "%commit_message%"
    python git-push.py "%commit_message%"
)

echo.
echo Push operation completed.
echo Press any key to close this window...
pause > nul
