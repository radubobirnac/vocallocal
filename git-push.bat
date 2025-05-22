@echo off
echo ===== GitHub Push Tool =====
echo.

set /p commit_message=Enter commit message (leave blank for timestamp):
set /p target_branch=Enter target branch (leave blank for main):

if "%commit_message%"=="" (
    echo Using default timestamp message...
    if "%target_branch%"=="" (
        echo Using default branch: main
        python git-push.py
    ) else (
        echo Using default message and branch: %target_branch%
        python git-push.py "" "%target_branch%"
    )
) else (
    if "%target_branch%"=="" (
        echo Using custom message: "%commit_message%"
        echo Using default branch: main
        echo Using custom message and main branch...
        python git-push.py "%commit_message%"
    ) else (
        echo Using custom message: "%commit_message%"
        echo Using custom branch: %target_branch%
        echo Using custom message and branch...
        python git-push.py "%commit_message%" "%target_branch%"
    )
)

echo.
echo Push operation completed.
echo Press any key to close this window...
pause > nul
