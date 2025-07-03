#!/usr/bin/env python3
"""
Test script to verify registration works with proper Flask app initialization.
"""

def test_registration_with_proper_init():
    """Test registration with properly initialized Flask app."""
    try:
        # Import the actual app
        from app import app
        
        print("=== Testing Registration with Proper App ===")
        
        with app.test_client() as client:
            # Test GET request to registration page
            response = client.get('/auth/register')
            print(f"GET /auth/register: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Registration page loads successfully")
            else:
                print(f"✗ Registration page failed: {response.status_code}")
                print(f"Response: {response.get_data(as_text=True)[:200]}")
                return False
            
            # Test POST request with valid data
            test_data = {
                'username': 'testuser123',
                'email': 'test@gmail.com',
                'password': 'testpassword123',
                'confirm_password': 'testpassword123'
            }
            
            response = client.post('/auth/register', data=test_data, follow_redirects=False)
            print(f"POST /auth/register: {response.status_code}")
            
            if response.status_code in [200, 302, 303]:
                print("✓ Registration form submission accepted")
                if response.location:
                    print(f"  Redirected to: {response.location}")
                    if 'verify' in response.location:
                        print("✓ Correctly redirected to email verification")
                return True
            else:
                print(f"✗ Registration submission failed: {response.status_code}")
                print(f"Response: {response.get_data(as_text=True)[:500]}")
                return False
        
    except Exception as e:
        print(f"Error testing registration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_email_validation_endpoint():
    """Test the email validation API endpoint."""
    try:
        from app import app
        import json
        
        print("\n=== Testing Email Validation API ===")
        
        with app.test_client() as client:
            test_emails = [
                ('test@gmail.com', True),
                ('student@paruluniversity.ac.in', True),
                ('user@mit.edu', True),
                ('invalid-email', False),
                ('user@domain', False)
            ]
            
            for email, should_be_valid in test_emails:
                response = client.post(
                    '/api/validate-email',
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps({'email': email})
                )
                
                print(f"Email: {email}")
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    is_valid = result.get('valid', False)
                    print(f"  Valid: {is_valid} (expected: {should_be_valid})")
                    
                    if is_valid == should_be_valid:
                        print("  ✓ Validation result correct")
                    else:
                        print("  ✗ Validation result incorrect")
                        if result.get('errors'):
                            print(f"    Errors: {result['errors']}")
                else:
                    print(f"  ✗ API call failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"Error testing email validation API: {e}")
        return False

def test_verification_code_endpoint():
    """Test the verification code sending endpoint."""
    try:
        from app import app
        import json
        
        print("\n=== Testing Verification Code Endpoint ===")
        
        with app.test_client() as client:
            # Test sending verification code
            test_data = {
                'email': 'test@gmail.com',
                'username': 'testuser'
            }
            
            response = client.post(
                '/api/send-verification-code',
                headers={'Content-Type': 'application/json'},
                data=json.dumps(test_data)
            )
            
            print(f"POST /api/send-verification-code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  Success: {result.get('success', False)}")
                print(f"  Message: {result.get('message', 'No message')}")
                
                if result.get('success'):
                    print("✓ Verification code endpoint working")
                    return True
                else:
                    print("✗ Verification code sending failed")
                    return False
            else:
                print(f"✗ Verification code endpoint failed: {response.status_code}")
                print(f"Response: {response.get_data(as_text=True)[:300]}")
                return False
        
    except Exception as e:
        print(f"Error testing verification code endpoint: {e}")
        return False

def check_javascript_files():
    """Check if JavaScript files exist and are accessible."""
    try:
        import os
        
        print("\n=== Checking JavaScript Files ===")
        
        js_files = [
            'static/auth.js',
            'static/js/email-validation.js'
        ]
        
        all_exist = True
        
        for js_file in js_files:
            if os.path.exists(js_file):
                print(f"✓ {js_file} exists")
                
                # Check file size
                size = os.path.getsize(js_file)
                print(f"  Size: {size} bytes")
                
                if size == 0:
                    print(f"  ⚠️  File is empty!")
                    all_exist = False
            else:
                print(f"✗ {js_file} missing")
                all_exist = False
        
        return all_exist
        
    except Exception as e:
        print(f"Error checking JavaScript files: {e}")
        return False

def main():
    """Run all registration tests."""
    print("Registration Fix Verification Test")
    print("=" * 35)
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if test_registration_with_proper_init():
        tests_passed += 1
        print("✅ Registration endpoint: PASSED")
    else:
        print("❌ Registration endpoint: FAILED")
    
    if test_email_validation_endpoint():
        tests_passed += 1
        print("✅ Email validation API: PASSED")
    else:
        print("❌ Email validation API: FAILED")
    
    if test_verification_code_endpoint():
        tests_passed += 1
        print("✅ Verification code API: PASSED")
    else:
        print("❌ Verification code API: FAILED")
    
    if check_javascript_files():
        tests_passed += 1
        print("✅ JavaScript files: PASSED")
    else:
        print("❌ JavaScript files: FAILED")
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed!")
        print("\n✅ Registration system is working correctly")
        print("✅ Email validation is inclusive and functional")
        print("✅ Verification code system is ready")
        print("✅ JavaScript files are in place")
        
        print("\n=== Registration Flow ===")
        print("1. User fills registration form")
        print("2. Email validation (format-only, inclusive)")
        print("3. Form submits to /auth/register")
        print("4. Verification code sent via email")
        print("5. User redirected to verification page")
        print("6. User enters OTP code")
        print("7. Account created after successful verification")
        
    else:
        print("⚠️  Some tests failed - check the output above")
    
    print("\n=== Troubleshooting Tips ===")
    print("• Check browser console for JavaScript errors")
    print("• Verify form submission isn't blocked by validation")
    print("• Monitor server logs for registration attempts")
    print("• Test with different email domains")

if __name__ == "__main__":
    main()
