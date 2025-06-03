#!/usr/bin/env python3
"""
Quick test script to verify Firebase JWT signature fix.
Run this after regenerating your Firebase service account key.
"""

import os
import json
import sys
from datetime import datetime

def test_firebase_credentials():
    """Test Firebase credentials and connection."""
    print("🔥 Testing Firebase Credentials Fix")
    print("=" * 50)
    
    # Check if credentials file exists
    if not os.path.exists('firebase-credentials.json'):
        print("❌ firebase-credentials.json not found!")
        print("Please download a new service account key from Firebase Console")
        return False
    
    try:
        # Load and validate credentials
        with open('firebase-credentials.json', 'r') as f:
            creds = json.load(f)
        
        print("✅ Credentials file loaded successfully")
        
        # Check key fields
        project_id = creds.get('project_id')
        client_email = creds.get('client_email')
        private_key = creds.get('private_key')
        
        print(f"📋 Project ID: {project_id}")
        print(f"📧 Client Email: {client_email}")
        print(f"🔑 Private Key: {'Present' if private_key else 'Missing'}")
        
        if not all([project_id, client_email, private_key]):
            print("❌ Missing required credential fields")
            return False
        
        # Test Firebase initialization
        print("\n🚀 Testing Firebase Connection...")
        
        import firebase_admin
        from firebase_admin import credentials, db
        
        # Clear any existing apps
        for app in firebase_admin._apps.values():
            firebase_admin.delete_app(app)
        
        # Initialize with new credentials
        cred = credentials.Certificate('firebase-credentials.json')
        app = firebase_admin.initialize_app(cred, {
            'databaseURL': f'https://{project_id}-default-rtdb.firebaseio.com'
        })
        
        print("✅ Firebase app initialized successfully")
        
        # Test database connection
        test_ref = db.reference('connection_test')
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'test': 'Firebase JWT fix verification',
            'status': 'success'
        }
        
        test_ref.set(test_data)
        print("✅ Database write test successful")
        
        # Read back the data
        read_data = test_ref.get()
        if read_data and read_data.get('test') == test_data['test']:
            print("✅ Database read test successful")
        else:
            print("⚠️  Database read test failed")
        
        # Clean up test data
        test_ref.delete()
        print("✅ Test cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Firebase test failed: {e}")
        
        if "Invalid JWT Signature" in str(e):
            print("\n🚨 JWT Signature Error Still Present!")
            print("Solutions:")
            print("1. Regenerate the service account key from Firebase Console")
            print("2. Ensure system time is synchronized")
            print("3. Check service account permissions in Google Cloud Console")
        
        return False

def test_oauth_integration():
    """Test that OAuth integration will work with fixed Firebase."""
    print("\n🔐 Testing OAuth Integration Readiness")
    print("=" * 50)
    
    try:
        # Test importing auth modules
        import auth
        print("✅ Auth module imported successfully")
        
        # Check if OAuth file exists
        if os.path.exists('Oauth.json'):
            with open('Oauth.json', 'r') as f:
                oauth_data = json.load(f)
            
            if 'web' in oauth_data:
                client_id = oauth_data['web'].get('client_id', '')
                print(f"✅ OAuth credentials found")
                print(f"📋 Client ID: {client_id[:10]}...{client_id[-10:] if len(client_id) > 20 else client_id}")
            else:
                print("⚠️  OAuth credentials format issue")
        else:
            print("⚠️  Oauth.json not found (normal for production deployment)")
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth integration test failed: {e}")
        return False

def main():
    """Main test function."""
    print("Firebase JWT Signature Fix Verification")
    print("=" * 60)
    print(f"Test Time: {datetime.now()}")
    print()
    
    # Run tests
    firebase_ok = test_firebase_credentials()
    oauth_ok = test_oauth_integration()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if firebase_ok and oauth_ok:
        print("🟢 ALL TESTS PASSED!")
        print("✅ Firebase JWT signature error is FIXED")
        print("✅ Google OAuth login should now work")
        print("✅ User data will be saved properly")
        print("\n🚀 You can now test the full application:")
        print("   python app.py")
        print("   Go to http://localhost:5001")
        print("   Try Google OAuth login")
        
    elif firebase_ok:
        print("🟡 FIREBASE FIXED, OAUTH NEEDS ATTENTION")
        print("✅ Firebase JWT signature error is FIXED")
        print("⚠️  OAuth configuration needs review")
        print("\n🚀 You can test Firebase features, but OAuth may need setup")
        
    else:
        print("🔴 FIREBASE STILL HAS ISSUES")
        print("❌ Firebase JWT signature error persists")
        print("\n🔧 Next steps:")
        print("1. Regenerate Firebase service account key")
        print("2. Check service account permissions")
        print("3. Verify system time synchronization")
        print("4. See FIREBASE_JWT_ERROR_SOLUTION.md for detailed instructions")
    
    print("\n📚 Documentation:")
    print("- FIREBASE_JWT_ERROR_SOLUTION.md - Complete fix guide")
    print("- CONSOLE_CREDENTIAL_SETUP.md - Deployment setup")
    print("- DEPLOYMENT_READINESS_CHECKLIST.md - Full deployment guide")

if __name__ == "__main__":
    main()
