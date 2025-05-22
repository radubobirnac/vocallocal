#!/usr/bin/env python
"""
Quick Git Push Utility for VocalLocal

This script automates git operations to make pushing changes to GitHub fast and simple.
When the AI assistant is asked to "push to git", it will recommend using this script.

Usage:
    python git-push.py ["Optional commit message"] ["Optional target branch"]

If no commit message is provided, it will use a default message with the current date/time.
If no target branch is provided, it will push to the 'main' branch.
"""

import sys
import subprocess
import datetime

def git_push(commit_message=None, target_branch="main"):
    # Use default commit message if none provided
    if not commit_message:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_message = f"Update VocalLocal - {now}"

    # Get current branch
    current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()

    print(f"Current branch: {current_branch}")
    print(f"Target branch for push: {target_branch}")
    print(f"Pushing changes to GitHub with message: '{commit_message}'")

    # Check if we're in detached HEAD state
    head_check = subprocess.run(["git", "symbolic-ref", "-q", "HEAD"],
                               capture_output=True, text=True)

    if head_check.returncode != 0:
        print("Detected detached HEAD state. Creating a new branch...")
        branch_name = f"changes-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        create_branch = subprocess.run(["git", "checkout", "-b", branch_name],
                                     capture_output=True, text=True)

        if create_branch.returncode != 0:
            print(f"Error creating branch: {create_branch.stderr}")
            print("Please create a new branch manually before pushing.")
            return False

        print(f"Created new branch: {branch_name}")
        current_branch = branch_name

    # If we're not on the target branch, switch to it
    if current_branch != target_branch:
        print(f"Switching from '{current_branch}' to '{target_branch}' branch...")

        # First, stash any changes
        stash_result = subprocess.run(["git", "stash", "push", "-m", f"Auto-stash before switching to {target_branch}"],
                                    capture_output=True, text=True)

        # Check if target branch exists locally
        branch_check = subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{target_branch}"],
                                    capture_output=True, text=True)

        if branch_check.returncode != 0:
            # Branch doesn't exist locally, try to fetch it
            print(f"Branch '{target_branch}' not found locally. Fetching from remote...")
            fetch_result = subprocess.run(["git", "fetch", "origin", target_branch],
                                        capture_output=True, text=True)

            if fetch_result.returncode != 0:
                print(f"Error fetching branch: {fetch_result.stderr}")
                print(f"Creating new branch '{target_branch}'...")
                create_branch = subprocess.run(["git", "checkout", "-b", target_branch],
                                            capture_output=True, text=True)
                if create_branch.returncode != 0:
                    print(f"Error creating branch: {create_branch.stderr}")
                    return False
            else:
                # Checkout the branch
                checkout_result = subprocess.run(["git", "checkout", target_branch],
                                              capture_output=True, text=True)
                if checkout_result.returncode != 0:
                    print(f"Error checking out branch: {checkout_result.stderr}")
                    return False
        else:
            # Branch exists locally, just checkout
            checkout_result = subprocess.run(["git", "checkout", target_branch],
                                          capture_output=True, text=True)
            if checkout_result.returncode != 0:
                print(f"Error checking out branch: {checkout_result.stderr}")
                return False

        # Apply stashed changes if there were any
        if "No local changes to save" not in stash_result.stdout and "No local changes to save" not in stash_result.stderr:
            print("Applying stashed changes...")
            apply_result = subprocess.run(["git", "stash", "apply"],
                                        capture_output=True, text=True)
            if apply_result.returncode != 0:
                print(f"Warning: Could not apply stashed changes: {apply_result.stderr}")
                print("You may need to manually resolve conflicts.")
    # Commands to execute
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", commit_message],
        ["git", "push", "--set-upstream", "origin", target_branch]
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

                # Get current branch name
                current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()

                pull_result = subprocess.run(["git", "pull", "--rebase", "origin", current_branch],
                                           capture_output=True, text=True)
                if pull_result.returncode == 0:
                    print("Pull successful, trying to push again...")
                    push_again = subprocess.run(["git", "push", "--set-upstream", "origin", current_branch],
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
    # Get commit message and target branch from command line args or use defaults
    commit_message = sys.argv[1] if len(sys.argv) > 1 else None
    target_branch = sys.argv[2] if len(sys.argv) > 2 else "main"
    git_push(commit_message, target_branch)
