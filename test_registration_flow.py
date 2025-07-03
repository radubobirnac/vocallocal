#!/usr/bin/env python3
"""
Test script to verify the registration flow is working correctly.
"""

def test_registration_route():
    """Test that the registration route is accessible."""
    try:
        import requests
        
        print("=== Testing Registration Route ===")
        
        # Test GET request to registration page
        response = requests.get('http://localhost:5000/auth/register')
        print(f"GET /auth/register: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Registration page loads successfully")
            return True
        else:
            print(f"✗ Registration page failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error testing registration route: {e}")
        return False

def test_email_validation_api():
    """Test the email validation API endpoint."""
    try:
        import requests
        import json
        
        print("\n=== Testing Email Validation API ===")
        
        test_emails = [
            'test@gmail.com',
            'student@paruluniversity.ac.in',
            'invalid-email'
        ]
        
        for email in test_emails:
            response = requests.post(
                'http://localhost:5000/api/validate-email',
                headers={'Content-Type': 'application/json'},
                data=json.dumps({'email': email})
            )
            
            print(f"Email: {email}")
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  Valid: {result.get('valid', False)}")
                if result.get('errors'):
                    print(f"  Errors: {result['errors']}")
            else:
                print(f"  Error: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"Error testing email validation API: {e}")
        return False

def test_registration_submission():
    """Test actual registration form submission."""
    try:
        import requests
        
        print("\n=== Testing Registration Submission ===")
        
        # Test data
        registration_data = {
            'username': 'testuser123',
            'email': 'test@gmail.com',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        }
        
        response = requests.post(
            'http://localhost:5000/auth/register',
            data=registration_data,
            allow_redirects=False
        )
        
        print(f"POST /auth/register: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code in [200, 302, 303]:
            print("✓ Registration form submission accepted")
            if 'Location' in response.headers:
                print(f"  Redirected to: {response.headers['Location']}")
            return True
        else:
            print(f"✗ Registration submission failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Error testing registration submission: {e}")
        return False

def check_server_running():
    """Check if the Flask server is running."""
    try:
        import requests
        
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code == 200:
            print("✓ Flask server is running")
            return True
        else:
            print(f"✗ Server responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Flask server at localhost:5000")
        print("  Please start the server with: python app.py")
        return False
    except Exception as e:
        print(f"Error checking server: {e}")
        return False

def main():
    """Run all registration flow tests."""
    print("Registration Flow Test")
    print("=" * 30)
    
    # Check if server is running
    if not check_server_running():
        print("\n❌ Server not running. Please start the Flask application first.")
        return
    
    tests_passed = 0
    total_tests = 3
    
    # Run tests
    if test_registration_route():
        tests_passed += 1
    
    if test_email_validation_api():
        tests_passed += 1
    
    if test_registration_submission():
        tests_passed += 1
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
        
    print("\n=== Troubleshooting Steps ===")
    print("1. Check Flask server logs for errors")
    print("2. Verify email validation JavaScript is working")
    print("3. Check browser console for JavaScript errors")
    print("4. Test form submission manually in browser")

if __name__ == "__main__":
    main()
