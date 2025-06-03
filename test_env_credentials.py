#!/usr/bin/env python3
"""
Test script to verify environment variable credential configuration.

This script tests both Firebase and OAuth credential loading from environment variables.
"""

import os
import json
import sys
from pathlib import Path

def test_firebase_env_vars():
    """Test Firebase environment variable configuration."""
    print("Testing Firebase Environment Variables")
    print("=" * 40)
    
    # Test FIREBASE_CREDENTIALS_JSON
    firebase_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
    if firebase_json:
        try:
            firebase_data = json.loads(firebase_json)
            print("✅ FIREBASE_CREDENTIALS_JSON: Valid JSON")
            print(f"   Project ID: {firebase_data.get('project_id', 'Not found')}")
            print(f"   Client Email: {firebase_data.get('client_email', 'Not found')}")
        except json.JSONDecodeError as e:
            print(f"❌ FIREBASE_CREDENTIALS_JSON: Invalid JSON - {e}")
            return False
    else:
        print("⚠️  FIREBASE_CREDENTIALS_JSON: Not set")
    
    # Test legacy FIREBASE_CREDENTIALS
    firebase_legacy = os.getenv('FIREBASE_CREDENTIALS')
    if firebase_legacy:
        try:
            firebase_data = json.loads(firebase_legacy)
            print("✅ FIREBASE_CREDENTIALS (legacy): Valid JSON")
        except json.JSONDecodeError as e:
            print(f"❌ FIREBASE_CREDENTIALS (legacy): Invalid JSON - {e}")
    else:
        print("⚠️  FIREBASE_CREDENTIALS (legacy): Not set")
    
    # Test file path
    firebase_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
    if os.path.exists(firebase_path):
        print(f"✅ Firebase file exists: {firebase_path}")
    else:
        print(f"⚠️  Firebase file not found: {firebase_path}")
    
    print()
    return True

def test_oauth_env_vars():
    """Test OAuth environment variable configuration."""
    print("Testing OAuth Environment Variables")
    print("=" * 40)
    
    # Test GOOGLE_OAUTH_CREDENTIALS_JSON
    oauth_json = os.getenv('GOOGLE_OAUTH_CREDENTIALS_JSON')
    if oauth_json:
        try:
            oauth_data = json.loads(oauth_json)
            print("✅ GOOGLE_OAUTH_CREDENTIALS_JSON: Valid JSON")
            if 'web' in oauth_data:
                web_config = oauth_data['web']
                client_id = web_config.get('client_id', '')
                print(f"   Client ID: {client_id[:10]}...{client_id[-10:] if len(client_id) > 20 else client_id}")
                print(f"   Project ID: {web_config.get('project_id', 'Not found')}")
            else:
                print("   Warning: 'web' key not found in OAuth data")
        except json.JSONDecodeError as e:
            print(f"❌ GOOGLE_OAUTH_CREDENTIALS_JSON: Invalid JSON - {e}")
            return False
    else:
        print("⚠️  GOOGLE_OAUTH_CREDENTIALS_JSON: Not set")
    
    # Test legacy OAUTH_CREDENTIALS
    oauth_legacy = os.getenv('OAUTH_CREDENTIALS')
    if oauth_legacy:
        try:
            oauth_data = json.loads(oauth_legacy)
            print("✅ OAUTH_CREDENTIALS (legacy): Valid JSON")
        except json.JSONDecodeError as e:
            print(f"❌ OAUTH_CREDENTIALS (legacy): Invalid JSON - {e}")
    else:
        print("⚠️  OAUTH_CREDENTIALS (legacy): Not set")
    
    # Test individual OAuth variables
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    if client_id and client_secret:
        print("✅ Individual OAuth variables: Set")
        print(f"   Client ID: {client_id[:10]}...{client_id[-10:] if len(client_id) > 20 else client_id}")
    else:
        print("⚠️  Individual OAuth variables: Not set")
    
    # Test OAuth file
    oauth_paths = ['Oauth.json', 'OAuth.json', 'oauth.json']
    oauth_file_found = False
    for oauth_path in oauth_paths:
        if os.path.exists(oauth_path):
            print(f"✅ OAuth file exists: {oauth_path}")
            oauth_file_found = True
            break
    
    if not oauth_file_found:
        print("⚠️  OAuth file not found")
    
    print()
    return True

def test_firebase_initialization():
    """Test Firebase initialization with current configuration."""
    print("Testing Firebase Initialization")
    print("=" * 40)
    
    try:
        import firebase_config
        firebase_config.initialize_firebase()
        print("✅ Firebase initialization: Success")
        return True
    except Exception as e:
        print(f"❌ Firebase initialization: Failed - {e}")
        return False

def main():
    """Main test function."""
    print("VocalLocal Environment Variable Test")
    print("=" * 50)
    print()
    
    # Run tests
    firebase_env_test = test_firebase_env_vars()
    oauth_env_test = test_oauth_env_vars()
    firebase_init_test = test_firebase_initialization()
    
    print()
    print("Test Summary")
    print("=" * 20)
    
    if firebase_env_test and oauth_env_test and firebase_init_test:
        print("✅ All tests passed!")
        print()
        print("Your environment variable configuration is working correctly.")
        print("You can safely deploy with environment variables.")
    else:
        print("⚠️  Some tests failed or showed warnings.")
        print()
        print("Recommendations:")
        print("1. Set environment variables using: python convert_json_to_env.py")
        print("2. Ensure JSON files exist for fallback during development")
        print("3. Check that environment variables contain valid JSON")
    
    print()
    print("Security Reminder:")
    print("- Keep environment variables secure")
    print("- Never commit credential files to version control")
    print("- Use deployment platform's secure environment variable storage")

if __name__ == "__main__":
    main()
