#!/usr/bin/env python
"""
Quick Git Push Utility for VocalLocal

Usage:
    python git-push.py "Your commit message"
    
This script:
1. Stages all changes
2. Commits with your message
3. Pushes to the default remote branch

No need for separate git add, commit, and push commands!
"""

import sys
import subprocess

def git_push(commit_message):
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", commit_message],
        ["git", "push"]
    ]
    
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
            if "nothing to commit" in result.stderr:
                print("No changes to commit. Continuing...")
            elif "rejected" in result.stderr:
                print("Push rejected. Try pulling first with 'git pull'")
                return False
    
    print("Successfully pushed to GitHub!")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a commit message.")
        print("Usage: python git-push.py \"Your commit message\"")
        sys.exit(1)
    
    commit_message = sys.argv[1]
    git_push(commit_message)
