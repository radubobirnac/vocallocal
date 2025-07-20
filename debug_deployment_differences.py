#!/usr/bin/env python3
"""
Debug Deployment Differences
Compare local and remote environment configurations that could affect TTS functionality
"""

import sys
import os
import json

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

def check_environment_variables():
    """Check critical environment variables for TTS functionality."""
    print("🔧 Checking Environment Variables")
    print("=" * 60)
    
    # Critical environment variables for TTS
    critical_vars = [
        'OPENAI_API_KEY',
        'GOOGLE_API_KEY',
        'GEMINI_API_KEY',
        'FIREBASE_PROJECT_ID',
        'FLASK_SECRET_KEY',
        'FLASK_ENV',
        'DEBUG'
    ]
    
    print("📋 Environment Variables Status:")
    missing_vars = []
    
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            # Show first 10 characters for security
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"   ✅ {var}: {masked_value}")
        else:
            print(f"   ❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Missing environment variables: {missing_vars}")
        print("   These may be required for TTS functionality in remote deployment")
    else:
        print(f"\n✅ All critical environment variables are set")
    
    return len(missing_vars) == 0

def check_api_keys():
    """Check API key configuration files."""
    print("\n🔧 Checking API Key Files")
    print("=" * 60)
    
    api_files = [
        'firebase-credentials.json',
        'Oauth.json',
        '.env'
    ]
    
    print("📋 API Key Files Status:")
    all_files_exist = True
    
    for file_path in api_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"   ✅ {file_path}: EXISTS ({file_size} bytes)")
            
            # Check if file has content
            if file_size == 0:
                print(f"      ⚠️ File is empty!")
                all_files_exist = False
        else:
            print(f"   ❌ {file_path}: NOT FOUND")
            all_files_exist = False
    
    return all_files_exist

def check_firebase_configuration():
    """Check Firebase configuration."""
    print("\n🔧 Checking Firebase Configuration")
    print("=" * 60)
    
    try:
        # Check if Firebase credentials file exists and is valid
        firebase_file = 'firebase-credentials.json'
        if os.path.exists(firebase_file):
            with open(firebase_file, 'r') as f:
                firebase_config = json.load(f)
            
            required_fields = ['project_id', 'private_key_id', 'client_email']
            missing_fields = []
            
            for field in required_fields:
                if field in firebase_config:
                    print(f"   ✅ {field}: PRESENT")
                else:
                    print(f"   ❌ {field}: MISSING")
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"\n⚠️ Missing Firebase fields: {missing_fields}")
                return False
            else:
                print(f"\n✅ Firebase configuration appears valid")
                return True
        else:
            print("❌ Firebase credentials file not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Firebase configuration: {str(e)}")
        return False

def check_tts_service_dependencies():
    """Check TTS service dependencies."""
    print("\n🔧 Checking TTS Service Dependencies")
    print("=" * 60)
    
    try:
        # Test imports
        print("📋 Testing Python Module Imports:")
        
        modules_to_test = [
            ('google.generativeai', 'Google Generative AI'),
            ('openai', 'OpenAI'),
            ('flask', 'Flask'),
            ('firebase_admin', 'Firebase Admin'),
            ('requests', 'Requests')
        ]
        
        all_imports_ok = True
        
        for module_name, display_name in modules_to_test:
            try:
                __import__(module_name)
                print(f"   ✅ {display_name}: AVAILABLE")
            except ImportError as e:
                print(f"   ❌ {display_name}: MISSING ({str(e)})")
                all_imports_ok = False
        
        return all_imports_ok
        
    except Exception as e:
        print(f"❌ Error checking dependencies: {str(e)}")
        return False

def check_tts_service_initialization():
    """Check if TTS service can be initialized."""
    print("\n🔧 Checking TTS Service Initialization")
    print("=" * 60)
    
    try:
        from services.tts import TTSService
        
        print("📋 Testing TTS Service Initialization:")
        
        # Try to initialize TTS service
        tts_service = TTSService()
        print("   ✅ TTSService: INITIALIZED")
        
        # Check available models
        if hasattr(tts_service, 'available_models'):
            print(f"   ✅ Available models: {tts_service.available_models}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ TTSService initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_deployment_specific_issues():
    """Check for deployment-specific configuration issues."""
    print("\n🔧 Checking Deployment-Specific Issues")
    print("=" * 60)
    
    issues_found = []
    
    # Check if running in production mode
    flask_env = os.environ.get('FLASK_ENV', 'development')
    debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"📋 Deployment Configuration:")
    print(f"   Flask Environment: {flask_env}")
    print(f"   Debug Mode: {debug_mode}")
    
    # Check for common deployment issues
    if flask_env == 'production' and debug_mode:
        issues_found.append("Debug mode enabled in production")
        print("   ⚠️ Debug mode should be disabled in production")
    
    # Check file permissions (basic check)
    critical_files = ['firebase-credentials.json', 'Oauth.json']
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    f.read(1)  # Try to read first character
                print(f"   ✅ {file_path}: READABLE")
            except PermissionError:
                issues_found.append(f"Permission denied reading {file_path}")
                print(f"   ❌ {file_path}: PERMISSION DENIED")
    
    # Check for port conflicts
    default_port = 5001
    print(f"   Default Port: {default_port}")
    
    if issues_found:
        print(f"\n⚠️ Deployment issues found: {issues_found}")
        return False
    else:
        print(f"\n✅ No obvious deployment issues detected")
        return True

def generate_deployment_checklist():
    """Generate a checklist for remote deployment."""
    print("\n📋 Remote Deployment Checklist")
    print("=" * 60)
    
    checklist = [
        "✅ Set OPENAI_API_KEY environment variable",
        "✅ Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable", 
        "✅ Upload firebase-credentials.json file",
        "✅ Upload Oauth.json file",
        "✅ Set FLASK_SECRET_KEY environment variable",
        "✅ Set FLASK_ENV=production",
        "✅ Set DEBUG=False",
        "✅ Ensure all Python dependencies are installed",
        "✅ Verify Firebase project configuration",
        "✅ Test API key validity",
        "✅ Check file permissions for credential files",
        "✅ Verify network access to external APIs"
    ]
    
    print("For successful remote deployment, ensure:")
    for item in checklist:
        print(f"   {item}")

def main():
    """Main diagnostic function."""
    print("🚀 Deployment Differences Diagnosis")
    print("=" * 80)
    
    print("Comparing local and remote deployment configurations...")
    print("This will help identify why TTS works locally but fails remotely.")
    print("")
    
    # Run all diagnostic checks
    env_vars_ok = check_environment_variables()
    api_files_ok = check_api_keys()
    firebase_ok = check_firebase_configuration()
    deps_ok = check_tts_service_dependencies()
    tts_init_ok = check_tts_service_initialization()
    deployment_ok = check_deployment_specific_issues()
    
    # Generate checklist
    generate_deployment_checklist()
    
    print(f"\n" + "="*80)
    
    all_checks_passed = all([env_vars_ok, api_files_ok, firebase_ok, deps_ok, tts_init_ok, deployment_ok])
    
    if all_checks_passed:
        print(f"🎉 LOCAL ENVIRONMENT: All checks passed")
        print(f"="*80)
        print(f"")
        print(f"Your local environment appears to be configured correctly.")
        print(f"If TTS fails in remote deployment, check:")
        print(f"  1. Environment variables are set in remote environment")
        print(f"  2. Credential files are uploaded to remote server")
        print(f"  3. API keys are valid and have proper permissions")
        print(f"  4. Network access to external APIs is allowed")
        print(f"")
    else:
        print(f"❌ LOCAL ENVIRONMENT: Issues detected")
        print(f"="*80)
        print(f"")
        print(f"Issues found in local environment that may also affect remote:")
        print(f"Review the error details above and fix before deploying.")
        print(f"")
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
