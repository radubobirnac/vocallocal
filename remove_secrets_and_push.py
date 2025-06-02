#!/usr/bin/env python3
"""
Remove Secrets from Code and Push to GitHub
This script removes hardcoded API keys and pushes safely
"""

import os
import re
import subprocess
from datetime import datetime

def remove_secrets_from_file(filepath):
    """Remove hardcoded secrets from a file"""
    if not os.path.exists(filepath):
        return False
    
    print(f"🔍 Checking {filepath}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove DigitalOcean API tokens
        do_token_pattern = r'dop_v1_[a-f0-9]{64}'
        if re.search(do_token_pattern, content):
            print(f"   🔒 Found DigitalOcean token in {filepath}")
            content = re.sub(do_token_pattern, 'os.environ.get("DIGITALOCEAN_API_TOKEN")', content)
            
            # Add import if not present
            if 'import os' not in content and 'from os import' not in content:
                content = 'import os\n' + content
        
        # Remove Google Cloud credentials (JSON strings)
        gc_cred_pattern = r'"type":\s*"service_account"[^}]+}'
        if re.search(gc_cred_pattern, content):
            print(f"   🔒 Found Google Cloud credentials in {filepath}")
            content = re.sub(gc_cred_pattern, 'os.environ.get("GOOGLE_CLOUD_CREDENTIALS")', content)
        
        # If content changed, write it back
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ Cleaned secrets from {filepath}")
            return True
        else:
            print(f"   ✅ No secrets found in {filepath}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error processing {filepath}: {e}")
        return False

def find_and_clean_files():
    """Find and clean all files with potential secrets"""
    print("🧹 CLEANING SECRETS FROM FILES")
    print("=" * 50)
    
    # Files that might contain secrets
    files_to_check = [
        'deploy_final_fix.py',
        'deploy_firebase_fix.py', 
        'deploy_simple_test.py',
        'fix_digitalocean_auto.py',
        'push_and_deploy.py',
        'deploy_to_digitalocean.py'
    ]
    
    cleaned_files = []
    
    for filepath in files_to_check:
        if remove_secrets_from_file(filepath):
            cleaned_files.append(filepath)
    
    return cleaned_files

def run_command(command, description):
    """Run a command and return success/failure"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
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

def push_clean_code():
    """Push the cleaned code to GitHub"""
    print("\n📤 PUSHING CLEAN CODE TO GITHUB")
    print("=" * 50)
    
    # Add all changes
    if not run_command("git add .", "Adding cleaned files"):
        return False
    
    # Create commit message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"""Remove hardcoded secrets and fix VocalLocal routes

Security fixes:
- Removed hardcoded DigitalOcean API tokens
- Removed hardcoded Google Cloud credentials
- Updated scripts to use environment variables

Route fixes:
- Fixed missing page routes (/login, /transcribe, /translate, /pricing)
- Added health check endpoints (/health, /api/health)
- Fixed Firebase credentials to use environment variable
- Fixed auth blueprint URL prefix issue

Deployed: {timestamp}"""
    
    # Commit changes
    if not run_command(f'git commit -m "{commit_message}"', "Committing cleaned code"):
        return False
    
    # Push to main branch
    if not run_command("git push origin main", "Pushing to GitHub"):
        return False
    
    return True

def create_env_template():
    """Create a template for environment variables"""
    print("\n📝 CREATING ENVIRONMENT TEMPLATE")
    print("=" * 50)
    
    env_template = """# VocalLocal Environment Variables Template
# Copy this to .env and fill in your actual values

# DigitalOcean API Token (for deployment scripts)
DIGITALOCEAN_API_TOKEN=your_digitalocean_token_here

# Google Cloud Credentials (JSON string)
GOOGLE_CLOUD_CREDENTIALS={"type":"service_account","project_id":"your_project"}

# Firebase Configuration
FIREBASE_CREDENTIALS={"type":"service_account","project_id":"vocal-local-e1e70"}
FIREBASE_DATABASE_URL=https://vocal-local-e1e70-default-rtdb.firebaseio.com
FIREBASE_STORAGE_BUCKET=vocal-local-e1e70.appspot.com

# API Keys
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here

# Flask Configuration
SECRET_KEY=your_secret_key_here
DEBUG=False
"""
    
    try:
        with open('.env.template', 'w') as f:
            f.write(env_template)
        print("✅ Created .env.template file")
        print("   Copy this to .env and fill in your actual values")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env.template: {e}")
        return False

def main():
    print("🔒 VOCALLOCAL - REMOVE SECRETS AND PUSH")
    print("=" * 60)
    print("This script will:")
    print("1. Remove hardcoded API keys and secrets")
    print("2. Update code to use environment variables")
    print("3. Push clean code to GitHub")
    print("")
    
    try:
        # Step 1: Clean files
        cleaned_files = find_and_clean_files()
        
        if cleaned_files:
            print(f"\n✅ Cleaned {len(cleaned_files)} files:")
            for file in cleaned_files:
                print(f"   - {file}")
        else:
            print("\n✅ No files needed cleaning")
        
        # Step 2: Create environment template
        create_env_template()
        
        # Step 3: Push clean code
        if not push_clean_code():
            print("\n❌ Failed to push clean code")
            return False
        
        print("\n🎉 SUCCESS! Clean code pushed to GitHub!")
        print("\n🎯 NEXT STEPS:")
        print("1. Go to DigitalOcean App Platform")
        print("2. Set environment variables in your app settings:")
        print("   - DIGITALOCEAN_API_TOKEN (for future deployments)")
        print("   - FIREBASE_CREDENTIALS (already set)")
        print("   - Other API keys as needed")
        print("3. Deploy your app from GitHub")
        print("4. Test your routes!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False
    
    finally:
        input("\n👆 Press ENTER to close this window...")

if __name__ == "__main__":
    main()
