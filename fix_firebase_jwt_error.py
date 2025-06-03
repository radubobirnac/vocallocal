#!/usr/bin/env python3
"""
Firebase JWT Signature Error Fix

This script helps diagnose and fix the "Invalid JWT Signature" error
that occurs with Firebase service account credentials.
"""

import json
import os
import sys
from datetime import datetime
import time

def check_firebase_credentials():
    """Check and validate Firebase credentials file."""
    print("🔍 Checking Firebase Credentials")
    print("=" * 40)
    
    credential_paths = [
        "firebase-credentials.json",
        "/etc/secrets/firebase-credentials.json",
        "/app/firebase-credentials.json"
    ]
    
    cred_file = None
    for path in credential_paths:
        if os.path.exists(path):
            cred_file = path
            print(f"✅ Found credentials at: {path}")
            break
    
    if not cred_file:
        print("❌ No Firebase credentials file found!")
        print("Please create firebase-credentials.json with your service account key")
        return False
    
    try:
        with open(cred_file, 'r') as f:
            creds = json.load(f)
        
        # Check required fields
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in creds:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            return False
        
        print("✅ All required fields present")
        
        # Check private key format
        private_key = creds.get('private_key', '')
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ Private key format is incorrect")
            print("   Private key should start with '-----BEGIN PRIVATE KEY-----'")
            return False
        
        if not private_key.endswith('-----END PRIVATE KEY-----\n'):
            print("⚠️  Private key might have formatting issues")
            print("   Private key should end with '-----END PRIVATE KEY-----\\n'")
        
        print("✅ Private key format looks correct")
        
        # Check project ID
        project_id = creds.get('project_id', '')
        if project_id:
            print(f"✅ Project ID: {project_id}")
        else:
            print("❌ Project ID is missing or empty")
            return False
        
        # Check client email
        client_email = creds.get('client_email', '')
        if client_email and '@' in client_email:
            print(f"✅ Client email: {client_email}")
        else:
            print("❌ Client email is missing or invalid")
            return False
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials: {e}")
        return False

def check_system_time():
    """Check if system time is synchronized."""
    print("\n🕐 Checking System Time")
    print("=" * 40)
    
    current_time = datetime.now()
    print(f"Current system time: {current_time}")
    
    # Check if time seems reasonable (not too far in past/future)
    import time
    current_timestamp = time.time()
    
    # Check if timestamp is reasonable (between 2020 and 2030)
    if current_timestamp < 1577836800:  # 2020-01-01
        print("❌ System time appears to be in the past")
        print("   Please synchronize your system clock")
        return False
    elif current_timestamp > 1893456000:  # 2030-01-01
        print("❌ System time appears to be in the future")
        print("   Please synchronize your system clock")
        return False
    else:
        print("✅ System time appears to be correct")
        return True

def fix_private_key_formatting():
    """Fix common private key formatting issues."""
    print("\n🔧 Fixing Private Key Formatting")
    print("=" * 40)
    
    cred_file = "firebase-credentials.json"
    if not os.path.exists(cred_file):
        print("❌ firebase-credentials.json not found")
        return False
    
    try:
        # Read current credentials
        with open(cred_file, 'r') as f:
            creds = json.load(f)
        
        private_key = creds.get('private_key', '')
        if not private_key:
            print("❌ No private key found in credentials")
            return False
        
        # Fix common formatting issues
        original_key = private_key
        
        # Ensure proper line endings
        if '\\n' in private_key:
            # Replace literal \n with actual newlines
            private_key = private_key.replace('\\n', '\n')
            print("✅ Fixed literal \\n characters")
        
        # Ensure proper start/end markers
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ Private key doesn't start with proper marker")
            return False
        
        if not private_key.endswith('\n'):
            private_key += '\n'
            print("✅ Added missing final newline")
        
        # Update credentials if changes were made
        if private_key != original_key:
            creds['private_key'] = private_key
            
            # Create backup
            backup_file = f"{cred_file}.backup"
            with open(backup_file, 'w') as f:
                json.dump(creds, f, indent=2)
            print(f"✅ Created backup: {backup_file}")
            
            # Write fixed credentials
            with open(cred_file, 'w') as f:
                json.dump(creds, f, indent=2)
            print("✅ Updated credentials with fixed private key")
        else:
            print("✅ Private key formatting is already correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing private key: {e}")
        return False

def test_firebase_connection():
    """Test Firebase connection with current credentials."""
    print("\n🔥 Testing Firebase Connection")
    print("=" * 40)
    
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        # Clear any existing apps
        for app in firebase_admin._apps.values():
            firebase_admin.delete_app(app)
        
        # Try to initialize with current credentials
        cred_file = "firebase-credentials.json"
        if os.path.exists(cred_file):
            cred = credentials.Certificate(cred_file)
            app = firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://vocal-local-e1e70-default-rtdb.firebaseio.com'
            })
            print("✅ Firebase initialization successful")
            
            # Test a simple database operation
            from firebase_admin import db
            ref = db.reference('test')
            ref.set({'timestamp': time.time(), 'test': True})
            print("✅ Database write test successful")
            
            # Clean up test data
            ref.delete()
            print("✅ Test cleanup successful")
            
            return True
        else:
            print("❌ No credentials file found")
            return False
            
    except Exception as e:
        print(f"❌ Firebase connection failed: {e}")
        return False

def main():
    """Main diagnostic and fix function."""
    print("Firebase JWT Signature Error Fix")
    print("=" * 50)
    print()
    
    checks = [
        ("Firebase Credentials", check_firebase_credentials),
        ("System Time", check_system_time),
        ("Private Key Formatting", fix_private_key_formatting),
        ("Firebase Connection", test_firebase_connection)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ Error in {check_name}: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if all_passed:
        print("🟢 ALL CHECKS PASSED")
        print("✅ Firebase JWT signature error should be resolved")
        print("✅ You can now test Google OAuth login again")
    else:
        print("🟡 SOME ISSUES FOUND")
        print("⚠️  Please fix the issues above and run this script again")
    
    print("\nCommon Solutions:")
    print("1. Regenerate Firebase service account key if issues persist")
    print("2. Ensure system time is synchronized")
    print("3. Check that the private key hasn't been corrupted")
    print("4. Verify the service account has proper permissions")

if __name__ == "__main__":
    main()
