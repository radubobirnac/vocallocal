#!/usr/bin/env python3
"""
Clean Push Essential Files Only
This script removes problematic files and pushes only essential code
"""

import os
import subprocess
from datetime import datetime

def run_command(command, description, ignore_errors=False):
    """Run a command and return success/failure"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0 or ignore_errors:
            print(f"✅ {description} successful")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def remove_problematic_files():
    """Remove files that contain secrets"""
    print("\n🗑️  REMOVING PROBLEMATIC FILES")
    print("=" * 50)
    
    files_to_remove = [
        'deploy_final_fix.py',
        'deploy_firebase_fix.py', 
        'deploy_simple_test.py',
        'fix_digitalocean_auto.py',
        'push_and_deploy.py',
        'deploy_to_digitalocean.py',
        'git_push.py',
        'remove_secrets_and_push.py'
    ]
    
    removed_files = []
    
    for filepath in files_to_remove:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"✅ Removed {filepath}")
                removed_files.append(filepath)
            except Exception as e:
                print(f"❌ Failed to remove {filepath}: {e}")
        else:
            print(f"ℹ️  {filepath} not found (already removed)")
    
    return removed_files

def create_simple_deploy_script():
    """Create a simple deployment script without secrets"""
    print("\n📝 CREATING CLEAN DEPLOYMENT SCRIPT")
    print("=" * 50)
    
    script_content = '''#!/usr/bin/env python3
"""
Simple VocalLocal Deployment Script
This script helps deploy VocalLocal without hardcoded secrets
"""

import os
import subprocess

def main():
    print("🚀 VOCALLOCAL DEPLOYMENT HELPER")
    print("=" * 50)
    print("This script helps you deploy VocalLocal safely.")
    print("")
    
    print("🎯 DEPLOYMENT STEPS:")
    print("1. Make sure your code is pushed to GitHub")
    print("2. Go to DigitalOcean App Platform")
    print("3. Find your VocalLocal app")
    print("4. Click 'Deploy' or 'Create Deployment'")
    print("5. Wait for deployment to complete")
    print("6. Test your app!")
    print("")
    
    print("🔗 Quick Links:")
    print("   GitHub: https://github.com/radubobirnac/vocallocal")
    print("   DigitalOcean: https://cloud.digitalocean.com/apps")
    print("   Your App: https://vocallocal-l5et5.ondigitalocean.app")
    print("")
    
    print("✅ All environment variables should already be set in DigitalOcean:")
    print("   - FIREBASE_CREDENTIALS")
    print("   - FIREBASE_DATABASE_URL") 
    print("   - OPENAI_API_KEY")
    print("   - GEMINI_API_KEY")
    print("   - SECRET_KEY")
    
    input("\\nPress ENTER to close...")

if __name__ == "__main__":
    main()
'''
    
    try:
        with open('deploy_helper.py', 'w') as f:
            f.write(script_content)
        print("✅ Created deploy_helper.py (clean deployment helper)")
        return True
    except Exception as e:
        print(f"❌ Failed to create deploy_helper.py: {e}")
        return False

def push_essential_code():
    """Push only the essential application code"""
    print("\n📤 PUSHING ESSENTIAL CODE TO GITHUB")
    print("=" * 50)
    
    # Add all changes (including removals)
    if not run_command("git add .", "Adding all changes"):
        return False
    
    # Create commit message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"""Clean deployment - remove files with secrets

Security cleanup:
- Removed deployment scripts containing hardcoded secrets
- Kept only essential application code
- Added clean deployment helper script

Application fixes included:
- Fixed missing page routes (/login, /transcribe, /translate, /pricing)
- Added health check endpoints (/health, /api/health)
- Fixed Firebase credentials to use environment variable
- Fixed auth blueprint URL prefix issue

Clean deployment: {timestamp}"""
    
    # Commit changes
    if not run_command(f'git commit -m "{commit_message}"', "Committing essential code"):
        return False
    
    # Push to main branch
    if not run_command("git push origin main", "Pushing essential code to GitHub"):
        return False
    
    return True

def verify_essential_files():
    """Verify that essential application files are present"""
    print("\n✅ VERIFYING ESSENTIAL FILES")
    print("=" * 50)
    
    essential_files = [
        'app.py',
        'config.py',
        'auth.py',
        'firebase_config.py',
        'requirements.txt',
        'Procfile',
        'gunicorn_config.py'
    ]
    
    missing_files = []
    
    for filepath in essential_files:
        if os.path.exists(filepath):
            print(f"✅ {filepath} present")
        else:
            print(f"❌ {filepath} missing")
            missing_files.append(filepath)
    
    if missing_files:
        print(f"\n⚠️  Missing essential files: {missing_files}")
        return False
    else:
        print("\n✅ All essential files present")
        return True

def main():
    print("🧹 VOCALLOCAL - CLEAN PUSH ESSENTIAL CODE")
    print("=" * 60)
    print("This script will:")
    print("1. Remove files containing secrets")
    print("2. Create a clean deployment helper")
    print("3. Push only essential application code")
    print("4. Verify all essential files are present")
    print("")
    
    try:
        # Step 1: Verify essential files
        if not verify_essential_files():
            print("❌ Missing essential files. Cannot proceed.")
            return False
        
        # Step 2: Remove problematic files
        removed_files = remove_problematic_files()
        
        if removed_files:
            print(f"\n✅ Removed {len(removed_files)} problematic files")
        
        # Step 3: Create clean deployment script
        create_simple_deploy_script()
        
        # Step 4: Push essential code
        if not push_essential_code():
            print("\n❌ Failed to push essential code")
            return False
        
        print("\n🎉 SUCCESS! Essential code pushed to GitHub!")
        print("\n🎯 NEXT STEPS:")
        print("1. Go to DigitalOcean App Platform")
        print("2. Find your VocalLocal app")
        print("3. Click 'Deploy' or 'Create Deployment'")
        print("4. DigitalOcean will pull the latest clean code")
        print("5. Wait for deployment to complete")
        print("6. Test your app at: https://vocallocal-l5et5.ondigitalocean.app")
        print("")
        print("🔗 Quick Links:")
        print("   DigitalOcean Apps: https://cloud.digitalocean.com/apps")
        print("   Your GitHub Repo: https://github.com/radubobirnac/vocallocal")
        
        return True
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False
    
    finally:
        input("\n👆 Press ENTER to close this window...")

if __name__ == "__main__":
    main()
