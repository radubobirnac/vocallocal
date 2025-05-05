@echo off
echo Pushing changes to GitHub...

echo Checking git installation...
git --version
if %ERRORLEVEL% neq 0 (
    echo Git is not installed or not in PATH. Please install git and try again.
    exit /b 1
)

echo Checking if we're in a git repository...
git rev-parse --is-inside-work-tree
if %ERRORLEVEL% neq 0 (
    echo Not in a git repository. Initializing...
    git init
    git remote add origin https://github.com/radubobirnac/vocallocal.git
) else (
    echo Already in a git repository.
    
    echo Checking if remote exists...
    git remote -v | findstr "origin"
    if %ERRORLEVEL% neq 0 (
        echo Adding remote origin...
        git remote add origin https://github.com/radubobirnac/vocallocal.git
    )
)

echo Current git status:
git status

echo Adding modified files...
git add templates/index.html static/script.js

echo Committing changes...
git commit -m "Add model display in upload section"

echo Pulling latest changes...
git pull origin main --rebase

echo Pushing to GitHub...
git push origin main

echo Final git status:
git status

echo Done!
pause
