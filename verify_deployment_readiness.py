#!/usr/bin/env python3
"""
VocalLocal Deployment Readiness Verification Script

This script verifies that the VocalLocal application is properly configured
for console-based credential deployment.
"""

import os
import json
import sys
from pathlib import Path

def check_gitignore_protection():
    """Check that credential files are properly excluded from version control."""
    print("🔒 Checking .gitignore Protection")
    print("=" * 40)
    
    gitignore_files = [
        ".gitignore",
        "../.gitignore"
    ]
    
    required_entries = [
        "Oauth.json",
        "OAuth.json", 
        "oauth.json",
        "firebase_credentials.json",
        "firebase-credentials.json"
    ]
    
    protected_files = set()
    
    for gitignore_path in gitignore_files:
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r') as f:
                    content = f.read()
                    for entry in required_entries:
                        if entry in content:
                            protected_files.add(entry)
                            print(f"✅ {entry} - Protected in {gitignore_path}")
            except Exception as e:
                print(f"⚠️  Error reading {gitignore_path}: {e}")
    
    missing_protection = set(required_entries) - protected_files
    if missing_protection:
        print(f"❌ Missing protection for: {', '.join(missing_protection)}")
        return False
    else:
        print("✅ All credential files properly protected from version control")
        return True

def check_credential_loading_system():
    """Check that the credential loading system is properly configured."""
    print("\n🔧 Checking Credential Loading System")
    print("=" * 40)
    
    try:
        # Test Firebase configuration
        import firebase_config
        print("✅ Firebase config module imported successfully")
        
        # Test credential file paths
        firebase_paths = [
            "firebase-credentials.json",
            "/etc/secrets/firebase-credentials.json",
            "/app/firebase-credentials.json"
        ]
        
        oauth_paths = [
            "Oauth.json",
            "/etc/secrets/Oauth.json", 
            "/app/Oauth.json"
        ]
        
        print("\n📁 Firebase credential search paths:")
        for path in firebase_paths:
            exists = os.path.exists(path)
            status = "✅ EXISTS" if exists else "⚠️  Not found"
            print(f"   {path} - {status}")
        
        print("\n📁 OAuth credential search paths:")
        for path in oauth_paths:
            exists = os.path.exists(path)
            status = "✅ EXISTS" if exists else "⚠️  Not found"
            print(f"   {path} - {status}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error importing firebase_config: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking credential loading: {e}")
        return False

def check_firebase_initialization():
    """Test Firebase initialization with current configuration."""
    print("\n🔥 Testing Firebase Initialization")
    print("=" * 40)
    
    try:
        import firebase_config
        firebase_config.initialize_firebase()
        print("✅ Firebase initialization successful")
        return True
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False

def check_oauth_configuration():
    """Check OAuth configuration."""
    print("\n🔐 Checking OAuth Configuration")
    print("=" * 40)
    
    oauth_file_paths = [
        "Oauth.json",
        "/etc/secrets/Oauth.json",
        "/app/Oauth.json"
    ]
    
    oauth_found = False
    for path in oauth_file_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    oauth_data = json.load(f)
                    if 'web' in oauth_data:
                        web_config = oauth_data['web']
                        client_id = web_config.get('client_id', '')
                        if client_id:
                            print(f"✅ Valid OAuth configuration found at: {path}")
                            print(f"   Client ID: {client_id[:10]}...{client_id[-10:] if len(client_id) > 20 else client_id}")
                            oauth_found = True
                            break
            except Exception as e:
                print(f"⚠️  Error reading OAuth file {path}: {e}")
    
    if not oauth_found:
        print("⚠️  No valid OAuth configuration found")
        print("   This is normal for initial setup - create Oauth.json on deployment server")
    
    return True

def check_environment_variables():
    """Check environment variable configuration."""
    print("\n🌍 Checking Environment Variables")
    print("=" * 40)
    
    required_vars = [
        "OPENAI_API_KEY",
        "SECRET_KEY"
    ]
    
    optional_vars = [
        "GEMINI_API_KEY",
        "FIREBASE_DATABASE_URL",
        "FIREBASE_STORAGE_BUCKET",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET"
    ]
    
    all_good = True
    
    print("Required environment variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} - Set")
        else:
            print(f"❌ {var} - Not set")
            all_good = False
    
    print("\nOptional environment variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} - Set")
        else:
            print(f"⚠️  {var} - Not set (will use defaults or credential files)")
    
    return all_good

def main():
    """Main verification function."""
    print("VocalLocal Deployment Readiness Verification")
    print("=" * 50)
    print()
    
    checks = [
        ("GitIgnore Protection", check_gitignore_protection),
        ("Credential Loading System", check_credential_loading_system),
        ("Firebase Initialization", check_firebase_initialization),
        ("OAuth Configuration", check_oauth_configuration),
        ("Environment Variables", check_environment_variables)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error in {check_name}: {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🟢 DEPLOYMENT READY")
        print("✅ All checks passed!")
        print("✅ VocalLocal is ready for console-based credential deployment")
        print("\nNext steps:")
        print("1. Deploy your application to your chosen platform")
        print("2. Use console commands to create credential files on the server")
        print("3. See CONSOLE_CREDENTIAL_SETUP.md for platform-specific instructions")
    else:
        print("🟡 NEEDS ATTENTION")
        print("⚠️  Some checks failed - review the issues above")
        print("⚠️  Fix the failing checks before deployment")
    
    print("\nDocumentation:")
    print("- DEPLOYMENT_READINESS_CHECKLIST.md - Complete deployment guide")
    print("- CONSOLE_CREDENTIAL_SETUP.md - Platform-specific setup instructions")
    print("- README.md - General setup and configuration")

if __name__ == "__main__":
    main()
