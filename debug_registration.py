#!/usr/bin/env python3
"""
Debug script to test registration functionality.
"""

def test_registration_endpoint():
    """Test the registration endpoint directly."""
    try:
        from flask import Flask
        from auth import auth_bp
        import os
        
        print("=== Testing Registration Endpoint ===")
        
        # Create a test Flask app
        app = Flask(__name__)
        app.secret_key = 'test_secret_key'
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        with app.test_client() as client:
            # Test GET request
            response = client.get('/auth/register')
            print(f"GET /auth/register: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Registration page loads successfully")
            else:
                print(f"✗ Registration page failed: {response.status_code}")
                return False
            
            # Test POST request
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
                return True
            else:
                print(f"✗ Registration submission failed: {response.status_code}")
                print(f"Response data: {response.get_data(as_text=True)[:500]}")
                return False
        
    except Exception as e:
        print(f"Error testing registration endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_email_validation_service():
    """Test the email validation service."""
    try:
        from services.email_service import email_service
        
        print("\n=== Testing Email Validation Service ===")
        
        test_emails = [
            'test@gmail.com',
            'student@paruluniversity.ac.in',
            'invalid@email'
        ]
        
        for email in test_emails:
            result = email_service.validate_email(email)
            print(f"Email: {email}")
            print(f"  Valid: {result['valid']}")
            print(f"  Level: {result.get('validation_level', 'unknown')}")
            if result.get('errors'):
                print(f"  Errors: {result['errors']}")
            if result.get('warnings'):
                print(f"  Warnings: {result['warnings']}")
        
        return True
        
    except Exception as e:
        print(f"Error testing email validation service: {e}")
        return False

def test_email_verification_service():
    """Test the email verification service."""
    try:
        from services.email_verification_service import email_verification_service
        
        print("\n=== Testing Email Verification Service ===")
        
        # Test code generation
        code = email_verification_service.generate_verification_code()
        print(f"Generated code: {code} (length: {len(code)})")
        
        if len(code) == 6 and code.isdigit():
            print("✓ Code generation working")
        else:
            print("✗ Code generation failed")
            return False
        
        # Test rate limiting check
        can_resend, message = email_verification_service.can_resend_code('test@example.com')
        print(f"Can resend: {can_resend}, Message: {message}")
        
        return True
        
    except Exception as e:
        print(f"Error testing email verification service: {e}")
        return False

def check_environment():
    """Check environment configuration."""
    try:
        from config import Config
        
        print("\n=== Environment Configuration ===")
        
        print(f"MAIL_SERVER: {Config.MAIL_SERVER}")
        print(f"MAIL_PORT: {Config.MAIL_PORT}")
        print(f"MAIL_USERNAME: {Config.MAIL_USERNAME}")
        print(f"MAIL_PASSWORD configured: {bool(Config.MAIL_PASSWORD)}")
        print(f"MAIL_DEFAULT_SENDER: {Config.MAIL_DEFAULT_SENDER}")
        
        if Config.MAIL_PASSWORD:
            print("✓ Email configuration appears complete")
            return True
        else:
            print("⚠️  MAIL_PASSWORD not configured")
            return False
        
    except Exception as e:
        print(f"Error checking environment: {e}")
        return False

def main():
    """Run all debug tests."""
    print("Registration Debug Test")
    print("=" * 25)
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if check_environment():
        tests_passed += 1
    
    if test_email_validation_service():
        tests_passed += 1
    
    if test_email_verification_service():
        tests_passed += 1
    
    if test_registration_endpoint():
        tests_passed += 1
    
    print(f"\n=== Debug Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All debug tests passed!")
        print("\n✅ Registration system appears to be working")
        print("✅ Email validation is functional")
        print("✅ Email verification service is ready")
        print("✅ Environment is properly configured")
    else:
        print("⚠️  Some tests failed - check the output above")
    
    print("\n=== Next Steps ===")
    print("1. Start the Flask application: python app.py")
    print("2. Test registration in browser at: http://localhost:5000/auth/register")
    print("3. Check browser console for JavaScript errors")
    print("4. Monitor server logs for registration attempts")

if __name__ == "__main__":
    main()
