# PowerShell script to push changes to GitHub

# Check if git is installed
Write-Host "Checking git installation..."
try {
    $gitVersion = git --version
    Write-Host "Git is installed: $gitVersion"
} catch {
    Write-Host "Git is not installed or not in PATH. Please install git and try again."
    exit 1
}

# Check if we're in a git repository
Write-Host "Checking if we're in a git repository..."
try {
    $isGitRepo = git rev-parse --is-inside-work-tree
    if ($isGitRepo -ne "true") {
        Write-Host "Not in a git repository. Initializing..."
        git init
        git remote add origin https://github.com/radubobirnac/vocallocal.git
    } else {
        Write-Host "Already in a git repository."

        # Check if remote exists
        $remotes = git remote -v
        if ($remotes -notcontains "origin") {
            Write-Host "Adding remote origin..."
            git remote add origin https://github.com/radubobirnac/vocallocal.git
        }
    }
} catch {
    Write-Host "Error checking git repository: $_"
    Write-Host "Initializing new repository..."
    git init
    git remote add origin https://github.com/radubobirnac/vocallocal.git
}

# Check current status
Write-Host "Current git status:"
git status

# Add the modified files
Write-Host "Adding modified files..."
git add templates/index.html static/script.js

# Commit the changes
Write-Host "Committing changes..."
git commit -m "Add model display in upload section"

# Pull latest changes to avoid conflicts
Write-Host "Pulling latest changes..."
git pull origin main --rebase

# Push to GitHub
Write-Host "Pushing to GitHub..."
git push origin main

# Show final status
Write-Host "Final git status:"
git status
