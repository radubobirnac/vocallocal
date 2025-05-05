import subprocess
import sys

def run_command(command):
    """Run a command and print its output."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(e.stderr)
        return False

def main():
    """Main function to push changes to GitHub."""
    print("Pushing changes to GitHub...")
    
    # Check if git is installed
    if not run_command("git --version"):
        print("Git is not installed or not in PATH. Please install git and try again.")
        return False
    
    # Check if we're in a git repository
    if not run_command("git rev-parse --is-inside-work-tree"):
        print("Not in a git repository. Initializing...")
        run_command("git init")
        run_command("git remote add origin https://github.com/radubobirnac/vocallocal.git")
    else:
        print("Already in a git repository.")
        
        # Check if remote exists
        result = subprocess.run("git remote -v", shell=True, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               universal_newlines=True)
        if "origin" not in result.stdout:
            print("Adding remote origin...")
            run_command("git remote add origin https://github.com/radubobirnac/vocallocal.git")
    
    # Check current status
    run_command("git status")
    
    # Add the modified files
    print("Adding modified files...")
    run_command("git add templates/index.html static/script.js")
    
    # Commit the changes
    print("Committing changes...")
    run_command("git commit -m \"Add model display in upload section\"")
    
    # Pull latest changes to avoid conflicts
    print("Pulling latest changes...")
    run_command("git pull origin main --rebase")
    
    # Push to GitHub
    print("Pushing to GitHub...")
    run_command("git push origin main")
    
    # Show final status
    run_command("git status")
    
    print("Done!")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
