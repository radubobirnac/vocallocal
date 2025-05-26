#!/usr/bin/env python3
"""
Firebase Functions Deployment Script for VocalLocal

This script helps deploy Firebase Cloud Functions including the new
monthly usage reset functions.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_firebase_cli():
    """Check if Firebase CLI is installed."""
    try:
        result = subprocess.run(['firebase', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Firebase CLI found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Firebase CLI not found. Please install it first:")
        print("   npm install -g firebase-tools")
        return False

def check_firebase_login():
    """Check if user is logged into Firebase."""
    try:
        result = subprocess.run(['firebase', 'projects:list'], 
                              capture_output=True, text=True, check=True)
        print("✅ Firebase authentication verified")
        return True
    except subprocess.CalledProcessError:
        print("❌ Not logged into Firebase. Please run:")
        print("   firebase login")
        return False

def check_firebase_project():
    """Check if Firebase project is configured."""
    firebase_json_path = Path('firebase.json')
    if not firebase_json_path.exists():
        print("❌ firebase.json not found. Please run:")
        print("   firebase init functions")
        return False
    
    try:
        with open(firebase_json_path, 'r') as f:
            config = json.load(f)
        
        if 'functions' not in config:
            print("❌ Functions not configured in firebase.json")
            return False
        
        print("✅ Firebase project configuration found")
        return True
    except json.JSONDecodeError:
        print("❌ Invalid firebase.json file")
        return False

def check_functions_directory():
    """Check if functions directory exists and has required files."""
    functions_dir = Path('firebase-functions')
    if not functions_dir.exists():
        print("❌ firebase-functions directory not found")
        return False
    
    required_files = [
        'index.js',
        'package.json',
        'usage-validation-functions.js',
        'monthly-reset-functions.js'
    ]
    
    missing_files = []
    for file in required_files:
        if not (functions_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files in firebase-functions/: {', '.join(missing_files)}")
        return False
    
    print("✅ All required function files found")
    return True

def install_dependencies():
    """Install npm dependencies for Firebase functions."""
    functions_dir = Path('firebase-functions')
    
    print("📦 Installing npm dependencies...")
    try:
        result = subprocess.run(['npm', 'install'], 
                              cwd=functions_dir, 
                              capture_output=True, text=True, check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e.stderr}")
        return False

def deploy_functions():
    """Deploy Firebase functions."""
    print("🚀 Deploying Firebase functions...")
    try:
        result = subprocess.run(['firebase', 'deploy', '--only', 'functions'], 
                              capture_output=True, text=True, check=True)
        print("✅ Functions deployed successfully!")
        print("\nDeployment output:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e.stderr}")
        return False

def show_function_urls():
    """Show the deployed function URLs."""
    print("\n📋 Deployed Functions:")
    print("=" * 50)
    
    functions = [
        "validateTranscriptionUsage",
        "validateTranslationUsage", 
        "validateTTSUsage",
        "validateAICredits",
        "trackUsage",
        "deductUsage",
        "deductTranscriptionUsage",
        "deductTranslationUsage",
        "deductTTSUsage",
        "deductAICredits",
        "resetMonthlyUsage",
        "resetMonthlyUsageHTTP",
        "getUsageStatistics",
        "checkAndResetUsage"
    ]
    
    try:
        # Get project ID
        result = subprocess.run(['firebase', 'use'], 
                              capture_output=True, text=True, check=True)
        project_id = result.stdout.strip().split()[-1]
        
        print(f"Project ID: {project_id}")
        print(f"Region: us-central1 (default)")
        print("\nFunction URLs:")
        
        for func in functions:
            if func == "resetMonthlyUsageHTTP":
                print(f"  🌐 {func}: https://us-central1-{project_id}.cloudfunctions.net/{func}")
            else:
                print(f"  📞 {func}: Callable function (use Firebase SDK)")
        
        print("\n💡 Usage Examples:")
        print(f"  External cron trigger:")
        print(f"    curl -X POST https://us-central1-{project_id}.cloudfunctions.net/resetMonthlyUsageHTTP \\")
        print(f"      -H 'x-reset-token: vocallocal-reset-2024' \\")
        print(f"      -d '{\"forceReset\": false}'")
        
    except subprocess.CalledProcessError:
        print("Could not determine project ID")

def main():
    """Main deployment process."""
    print("🔥 VocalLocal Firebase Functions Deployment")
    print("=" * 50)
    
    # Pre-deployment checks
    checks = [
        ("Firebase CLI", check_firebase_cli),
        ("Firebase Login", check_firebase_login),
        ("Firebase Project", check_firebase_project),
        ("Functions Directory", check_functions_directory),
    ]
    
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        if not check_func():
            print(f"\n❌ {check_name} check failed. Please fix the issues above and try again.")
            sys.exit(1)
    
    # Install dependencies
    print(f"\n📦 Installing Dependencies...")
    if not install_dependencies():
        print("\n❌ Dependency installation failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    # Deploy functions
    print(f"\n🚀 Deploying Functions...")
    if not deploy_functions():
        print("\n❌ Deployment failed. Please check the errors above.")
        sys.exit(1)
    
    # Show function URLs
    show_function_urls()
    
    print("\n🎉 Deployment completed successfully!")
    print("\n📚 Next Steps:")
    print("1. Test the functions using the Firebase Console")
    print("2. Set up external cron jobs if needed (see MONTHLY_USAGE_RESET_GUIDE.md)")
    print("3. Configure Firebase security rules if not already done")
    print("4. Test the admin interface at /admin/usage-reset")

if __name__ == "__main__":
    main()
