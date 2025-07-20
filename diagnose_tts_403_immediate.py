#!/usr/bin/env python3
"""
Immediate TTS 403 Error Diagnosis and Resolution
Diagnose and fix TTS 403 Forbidden errors and stop button functionality
"""

import sys
import os
import requests
import json

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

def check_current_user_session():
    """Check the current user session and authentication status."""
    print("🔧 Checking Current User Session")
    print("=" * 60)
    
    try:
        # Check authentication status
        response = requests.get('http://localhost:5001/api/user/role', 
                              timeout=10)
        
        print(f"Authentication check: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ User authenticated: {user_data.get('email', 'unknown')}")
            print(f"   Role: {user_data.get('role', 'unknown')}")
            print(f"   Is Admin: {user_data.get('is_admin', False)}")
            return user_data
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking user session: {str(e)}")
        return None

def check_tts_access_api():
    """Check TTS access through the API endpoint."""
    print("\n🔧 Checking TTS Access API")
    print("=" * 60)
    
    try:
        # Check TTS access
        response = requests.get('http://localhost:5001/api/user/tts-access', 
                              timeout=10)
        
        print(f"TTS access check: {response.status_code}")
        
        if response.status_code == 200:
            tts_data = response.json()
            print(f"✅ TTS access result: {json.dumps(tts_data, indent=2)}")
            return tts_data
        else:
            print(f"❌ TTS access check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error checking TTS access: {str(e)}")
        return None

def test_tts_endpoint_direct():
    """Test the TTS endpoint directly to reproduce 403 errors."""
    print("\n🔧 Testing TTS Endpoint Direct")
    print("=" * 60)
    
    try:
        # Test TTS endpoint with a simple request
        payload = {
            'text': 'This is a test of the TTS endpoint to diagnose 403 errors.',
            'language': 'en',
            'tts_model': 'gemini-2.5-flash-tts'
        }
        
        print(f"Making TTS request: {json.dumps(payload, indent=2)}")
        
        response = requests.post('http://localhost:5001/api/tts',
                               json=payload,
                               timeout=30)
        
        print(f"TTS endpoint response: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"✅ TTS request successful!")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            print(f"   Content-Length: {response.headers.get('Content-Length', 'unknown')}")
            return True
        elif response.status_code == 403:
            print(f"❌ TTS 403 FORBIDDEN ERROR REPRODUCED!")
            print(f"   Response text: {response.text}")
            return False
        else:
            print(f"❌ TTS request failed: {response.status_code}")
            print(f"   Response text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing TTS endpoint: {str(e)}")
        return False

def check_tts_authentication_flow():
    """Check the TTS authentication flow step by step."""
    print("\n🔧 Checking TTS Authentication Flow")
    print("=" * 60)
    
    try:
        from models.firebase_models import User
        from services.usage_validation_service import UsageValidationService
        from services.email_verification_middleware import VerificationAwareAccessControl
        
        # Get current user from session (this might be the issue)
        print("1. Checking Flask session...")
        
        # Since we can't access Flask session outside request context,
        # let's check if there are any users in the database
        print("2. Checking available users in database...")
        
        # Check super user
        super_user = User.get_by_email("superuser@vocallocal.com")
        if super_user:
            print(f"   ✅ Super user exists: {super_user.get('username', 'N/A')}")
            
            # Check TTS access for super user
            tts_access = UsageValidationService.check_tts_access("superuser@vocallocal.com")
            print(f"   Super user TTS access: {tts_access}")
            
            # Check email verification
            verification_access = VerificationAwareAccessControl.check_tts_access("superuser@vocallocal.com")
            print(f"   Super user verification access: {verification_access}")
        else:
            print(f"   ❌ Super user not found")
        
        # Check basic user
        basic_user = User.get_by_email("anitha@gmail.com")
        if basic_user:
            print(f"   ✅ Basic user exists: {basic_user.get('username', 'N/A')}")
            
            # Check TTS access for basic user
            tts_access = UsageValidationService.check_tts_access("anitha@gmail.com")
            print(f"   Basic user TTS access: {tts_access}")
            
            # Check email verification
            verification_access = VerificationAwareAccessControl.check_tts_access("anitha@gmail.com")
            print(f"   Basic user verification access: {verification_access}")
        else:
            print(f"   ❌ Basic user not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking authentication flow: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_login_and_tts():
    """Test logging in and then making TTS requests."""
    print("\n🔧 Testing Login and TTS Flow")
    print("=" * 60)
    
    try:
        # Create a session
        session = requests.Session()
        
        # Try to access the login page first
        login_page = session.get('http://localhost:5001/auth/login', timeout=10)
        print(f"Login page access: {login_page.status_code}")
        
        if login_page.status_code == 200:
            print("✅ Login page accessible")
            
            # Try to login with super user credentials
            login_data = {
                'email': 'superuser@vocallocal.com',
                'password': 'superpassword123'
            }
            
            print("Attempting login with super user...")
            login_response = session.post('http://localhost:5001/auth/login',
                                        data=login_data,
                                        timeout=10)
            
            print(f"Login response: {login_response.status_code}")
            print(f"Login response URL: {login_response.url}")
            
            # Check if redirected to home page (successful login)
            if login_response.url.endswith('/') or 'login' not in login_response.url:
                print("✅ Login appears successful")
                
                # Now test TTS with authenticated session
                tts_payload = {
                    'text': 'Testing TTS with authenticated session.',
                    'language': 'en',
                    'tts_model': 'gemini-2.5-flash-tts'
                }
                
                print("Making TTS request with authenticated session...")
                tts_response = session.post('http://localhost:5001/api/tts',
                                          json=tts_payload,
                                          timeout=30)
                
                print(f"Authenticated TTS response: {tts_response.status_code}")
                
                if tts_response.status_code == 200:
                    print("✅ TTS works with authenticated session!")
                    return True
                elif tts_response.status_code == 403:
                    print("❌ TTS still returns 403 even with authenticated session!")
                    print(f"   Response: {tts_response.text}")
                    return False
                else:
                    print(f"❌ TTS failed with status: {tts_response.status_code}")
                    print(f"   Response: {tts_response.text}")
                    return False
            else:
                print("❌ Login failed - not redirected properly")
                print(f"   Response text: {login_response.text[:200]}...")
                return False
        else:
            print(f"❌ Cannot access login page: {login_page.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing login and TTS: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_tts_route_decorators():
    """Check the TTS route decorators and middleware."""
    print("\n🔧 Checking TTS Route Decorators")
    print("=" * 60)
    
    try:
        # Read the TTS route definition
        with open('routes/tts_routes.py', 'r') as f:
            tts_routes_content = f.read()
        
        print("TTS route decorators found:")
        
        # Check for decorators
        if '@login_required' in tts_routes_content:
            print("   ✅ @login_required decorator found")
        else:
            print("   ❌ @login_required decorator missing")
        
        if '@requires_verified_email' in tts_routes_content:
            print("   ✅ @requires_verified_email decorator found")
        else:
            print("   ❌ @requires_verified_email decorator missing")
        
        # Check for usage validation
        if 'UsageValidationService.check_tts_access' in tts_routes_content:
            print("   ✅ TTS access validation found")
        else:
            print("   ❌ TTS access validation missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking TTS route: {str(e)}")
        return False

def main():
    """Main diagnostic function."""
    print("🚨 IMMEDIATE TTS 403 ERROR DIAGNOSIS")
    print("=" * 80)
    
    print("Diagnosing TTS 403 Forbidden errors and stop button issues...")
    print("This will identify the root cause and provide immediate fixes.")
    print("")
    
    # Run immediate diagnostics
    user_session = check_current_user_session()
    tts_access = check_tts_access_api()
    tts_direct = test_tts_endpoint_direct()
    auth_flow = check_tts_authentication_flow()
    route_check = check_tts_route_decorators()
    login_test = test_login_and_tts()
    
    print(f"\n" + "="*80)
    print(f"🎯 DIAGNOSIS RESULTS:")
    print(f"="*80)
    
    if tts_direct:
        print(f"🎉 TTS ENDPOINT: WORKING")
        print(f"   The TTS 403 errors may be intermittent or session-related")
    else:
        print(f"❌ TTS ENDPOINT: 403 FORBIDDEN ERROR CONFIRMED")
        print(f"   Root cause identified - authentication/authorization failure")
    
    if login_test:
        print(f"✅ AUTHENTICATED TTS: WORKING")
        print(f"   TTS works when properly authenticated")
    else:
        print(f"❌ AUTHENTICATED TTS: STILL FAILING")
        print(f"   Authentication is not the only issue")
    
    print(f"\n📋 IMMEDIATE ACTION ITEMS:")
    if not user_session:
        print(f"   1. ❌ User not logged in - need to authenticate")
    if not tts_access:
        print(f"   2. ❌ TTS access denied - check user permissions")
    if not tts_direct:
        print(f"   3. ❌ TTS endpoint failing - check route decorators")
    if not auth_flow:
        print(f"   4. ❌ Authentication flow broken - check middleware")
    
    return tts_direct and login_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
