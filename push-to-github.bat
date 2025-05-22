@echo off
echo ===== GitHub Push Tool =====
echo.

set /p commit_message=Enter commit message (leave blank for timestamp):
set /p target_branch=Enter target branch (leave blank for main):

if "%commit_message%"=="" (
    set commit_message=
) else (
    echo Using custom message: "%commit_message%"
)

if "%target_branch%"=="" (
    echo Using default branch: main
    set target_branch=main
) else (
    echo Using target branch: %target_branch%
)

if "%commit_message%"=="" (
    if "%target_branch%"=="main" (
        echo Using default timestamp message and main branch...
        python git-push.py
    ) else (
        echo Using default timestamp message and %target_branch% branch...
        python git-push.py "" "%target_branch%"
    )
) else (
    if "%target_branch%"=="main" (
        echo Using custom message and main branch...
        python git-push.py "%commit_message%"
    ) else (
        echo Using custom message and %target_branch% branch...
        python git-push.py "%commit_message%" "%target_branch%"
    )
)

echo.
echo Push operation completed.
echo Press any key to close this window...
pause > nul
