#!/usr/bin/env python3
"""
Push Latest VocalLocal State to GitHub
This script commits and pushes all current changes to GitHub
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description, show_output=True):
    """Run a command and return success/failure"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} successful")
            if show_output and result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True, result.stdout
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False, str(e)

def check_git_status():
    """Check what files have changed"""
    print("\n📋 CHECKING CURRENT STATE")
    print("=" * 50)
    
    # Check if we're in a git repository
    success, output = run_command("git status", "Checking git repository", False)
    if not success:
        print("❌ Not in a git repository or git not available")
        return False
    
    # Show current branch
    success, branch = run_command("git branch --show-current", "Getting current branch", False)
    if success:
        print(f"📍 Current branch: {branch.strip()}")
    
    # Check for changes
    success, status_output = run_command("git status --porcelain", "Checking for changes", False)
    if success:
        if status_output.strip():
            print(f"📝 Found changes to commit:")
            for line in status_output.strip().split('\n'):
                status_code = line[:2]
                filename = line[3:]
                if status_code == "M ":
                    print(f"   📝 Modified: {filename}")
                elif status_code == "A ":
                    print(f"   ➕ Added: {filename}")
                elif status_code == "D ":
                    print(f"   ❌ Deleted: {filename}")
                elif status_code == "??":
                    print(f"   ❓ Untracked: {filename}")
                else:
                    print(f"   {status_code} {filename}")
            return True
        else:
            print("ℹ️  No changes detected")
            return False
    
    return False

def push_all_changes():
    """Add, commit, and push all changes"""
    print("\n📤 PUSHING ALL CHANGES TO GITHUB")
    print("=" * 50)
    
    # Add all changes
    success, _ = run_command("git add .", "Adding all changes")
    if not success:
        return False
    
    # Create a comprehensive commit message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"""Fix VocalLocal routes and Firebase authentication

- Fixed missing page routes (/login, /transcribe, /translate, /pricing)
- Added health check endpoints (/health, /api/health)
- Fixed Firebase credentials to use environment variable
- Fixed auth blueprint URL prefix issue
- Added missing route definitions in app.py
- Updated blueprint registration

Deployed: {timestamp}"""
    
    # Commit changes
    success, _ = run_command(f'git commit -m "{commit_message}"', "Committing changes")
    if not success:
        # Check if it's because there's nothing to commit
        success, status_output = run_command("git status --porcelain", "Checking status after add", False)
        if success and not status_output.strip():
            print("ℹ️  No changes to commit (everything up to date)")
            return True
        print("❌ Failed to commit changes")
        return False
    
    # Push to main branch
    success, _ = run_command("git push origin main", "Pushing to GitHub main branch")
    if not success:
        # Try pushing to master branch as fallback
        print("🔄 Trying master branch...")
        success, _ = run_command("git push origin master", "Pushing to GitHub master branch")
        if not success:
            return False
    
    return True

def show_summary():
    """Show a summary of what was pushed"""
    print("\n📊 PUSH SUMMARY")
    print("=" * 50)
    
    # Show recent commits
    success, log_output = run_command("git log --oneline -5", "Getting recent commits", False)
    if success:
        print("📝 Recent commits:")
        for line in log_output.strip().split('\n'):
            print(f"   {line}")
    
    # Show repository URL
    success, remote_url = run_command("git remote get-url origin", "Getting repository URL", False)
    if success:
        print(f"\n🔗 Repository: {remote_url.strip()}")
        
        # Extract GitHub URL for easy access
        if 'github.com' in remote_url:
            if remote_url.strip().endswith('.git'):
                web_url = remote_url.strip()[:-4]
            else:
                web_url = remote_url.strip()
            
            if web_url.startswith('git@github.com:'):
                web_url = web_url.replace('git@github.com:', 'https://github.com/')
            
            print(f"🌐 Web URL: {web_url}")

def main():
    print("📤 VOCALLOCAL - PUSH TO GITHUB")
    print("=" * 60)
    print("This script will push all current changes to GitHub")
    print("")
    
    try:
        # Step 1: Check current state
        has_changes = check_git_status()
        
        if not has_changes:
            print("\n✅ Repository is already up to date!")
            show_summary()
            return True
        
        # Step 2: Push all changes
        if not push_all_changes():
            print("\n❌ Failed to push changes to GitHub")
            return False
        
        # Step 3: Show summary
        show_summary()
        
        print("\n🎉 SUCCESS! All changes pushed to GitHub!")
        print("\n🎯 NEXT STEPS:")
        print("1. Go to DigitalOcean App Platform")
        print("2. Find your VocalLocal app")
        print("3. Click 'Deploy' or trigger a new deployment")
        print("4. DigitalOcean will pull the latest code from GitHub")
        print("5. Wait for deployment to complete")
        print("6. Test your app!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False
    
    finally:
        input("\n👆 Press ENTER to close this window...")

if __name__ == "__main__":
    main()
