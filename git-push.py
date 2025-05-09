#!/usr/bin/env python
"""
Quick Git Push Utility for VocalLocal

This script automates git operations to make pushing changes to GitHub fast and simple.
When the AI assistant is asked to "push to git", it will recommend using this script.

Usage:
    python git-push.py ["Optional commit message"]

If no commit message is provided, it will use a default message with the current date/time.
"""

import sys
import subprocess
import datetime

def git_push(commit_message=None):
    # Use default commit message if none provided
    if not commit_message:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_message = f"Update VocalLocal - {now}"

    print(f"Pushing changes to GitHub with message: '{commit_message}'")

    # Commands to execute
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", commit_message],
        ["git", "push"]
    ]

    # Execute each command
    for cmd in commands:
        print(f"\nRunning: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Print stdout if there is any
        if result.stdout:
            print(result.stdout)

        # Handle errors
        if result.returncode != 0:
            print(f"Error: {result.stderr}")

            # Handle common errors with helpful messages
            if "nothing to commit" in result.stderr:
                print("No changes to commit. Continuing...")
            elif "rejected" in result.stderr:
                print("Push rejected. Trying to pull changes first...")
                pull_result = subprocess.run(["git", "pull", "--rebase"],
                                           capture_output=True, text=True)
                if pull_result.returncode == 0:
                    print("Push successful, trying to push again...")
                    push_again = subprocess.run(["git", "push"],
                                              capture_output=True, text=True)
                    if push_again.returncode == 0:
                        print("Successfully pushed to GitHub after pulling!")
                        return True
                print("Failed to push changes. Please resolve conflicts manually.")
                return False
            elif "Authentication failed" in result.stderr:
                print("GitHub authentication failed. Please check your credentials.")
                return False

    print("\nSuccessfully pushed to GitHub!")
    return True

if __name__ == "__main__":
    # Get commit message from command line args or use default
    commit_message = sys.argv[1] if len(sys.argv) > 1 else None
    git_push(commit_message)
