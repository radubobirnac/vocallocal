#!/usr/bin/env python3
"""
Test script for forgot password functionality.
Tests the password reset service and email sending.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_password_reset_service():
    """Test the password reset service functionality."""
    print("🔐 Testing Password Reset Service")
    print("=" * 50)
    
    try:
        from services.password_reset_service import password_reset_service
        
        # Test 1: Token Generation
        print("\n1. Testing token generation...")
        test_email = "test@example.com"
        token = password_reset_service.generate_reset_token(test_email)
        
        print(f"✓ Token generated successfully")
        print(f"  Email: {test_email}")
        print(f"  Token: {token[:20]}... (truncated)")
        print(f"  Token length: {len(token)} characters")
        
        # Test 2: Token Storage
        print("\n2. Testing token storage...")
        stored = password_reset_service.store_reset_token(test_email, token)
        
        if stored:
            print("✓ Token stored successfully")
        else:
            print("✗ Failed to store token")
            return False
        
        # Test 3: Token Validation
        print("\n3. Testing token validation...")
        is_valid, message = password_reset_service.validate_reset_token(test_email, token)
        
        if is_valid:
            print(f"✓ Token validation successful: {message}")
        else:
            print(f"✗ Token validation failed: {message}")
            return False
        
        # Test 4: Rate Limiting
        print("\n4. Testing rate limiting...")
        rate_ok, rate_msg = password_reset_service.check_rate_limit(test_email)
        
        if rate_ok:
            print(f"✓ Rate limit check passed: {rate_msg}")
        else:
            print(f"⚠️ Rate limit exceeded: {rate_msg}")
        
        # Test 5: Email Creation
        print("\n5. Testing email creation...")
        msg = password_reset_service.create_reset_email(test_email, token, "TestUser")

        print("✓ Reset email created successfully")
        print(f"  Subject: {msg['Subject']}")
        print(f"  From: {msg['From']}")
        print(f"  To: {msg['To']}")
        print(f"  Parts: {len(msg.get_payload())} (text + html)")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing password reset service: {e}")
        return False

def test_email_service_integration():
    """Test integration with email service."""
    print("\n📧 Testing Email Service Integration")
    print("=" * 50)
    
    try:
        from services.email_service import email_service
        
        # Test email configuration
        print("\n1. Testing email configuration...")
        config_ok = bool(email_service.password)
        
        if config_ok:
            print("✓ Email service is configured")
            print(f"  SMTP Server: {email_service.smtp_server}")
            print(f"  SMTP Port: {email_service.smtp_port}")
            print(f"  Use TLS: {email_service.use_tls}")
            print(f"  Username: {email_service.username}")
            print(f"  Default Sender: {email_service.default_sender}")
        else:
            print("⚠️ Email service not configured (missing MAIL_PASSWORD)")
            print("  This is normal for development without email setup")
        
        return config_ok
        
    except Exception as e:
        print(f"✗ Error testing email service: {e}")
        return False

def test_user_model_integration():
    """Test integration with user model."""
    print("\n👤 Testing User Model Integration")
    print("=" * 50)
    
    try:
        from models.firebase_models import User
        
        # Test user lookup
        print("\n1. Testing user lookup...")
        test_emails = [
            "anitha@gmail.com",  # Known test user
            "nonexistent@example.com"  # Non-existent user
        ]
        
        for email in test_emails:
            user_data = User.get_by_email(email)
            if user_data:
                print(f"✓ User found: {email}")
                print(f"  Username: {user_data.get('username')}")
                print(f"  Role: {user_data.get('role', 'normal_user')}")
            else:
                print(f"ℹ️ User not found: {email}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing user model: {e}")
        return False

def test_complete_flow():
    """Test the complete forgot password flow."""
    print("\n🔄 Testing Complete Forgot Password Flow")
    print("=" * 50)
    
    try:
        from services.password_reset_service import password_reset_service
        
        # Use a test email
        test_email = "anitha@gmail.com"  # Known test user
        
        print(f"\n1. Testing complete flow for: {test_email}")
        
        # Send reset email
        result = password_reset_service.send_reset_email(test_email)
        
        if result['success']:
            print(f"✓ Reset email process completed: {result['message']}")
        else:
            print(f"✗ Reset email process failed: {result['message']}")
            return False
        
        print("\n2. Testing token validation flow...")
        
        # Note: In a real test, you'd extract the token from the email
        # For this test, we'll generate a new token to test the validation flow
        token = password_reset_service.generate_reset_token(test_email)
        password_reset_service.store_reset_token(test_email, token)
        
        # Validate token
        is_valid, message = password_reset_service.validate_reset_token(test_email, token)
        
        if is_valid:
            print(f"✓ Token validation successful: {message}")
            
            # Mark token as used
            marked = password_reset_service.mark_token_used(test_email, token)
            if marked:
                print("✓ Token marked as used successfully")
                
                # Try to validate used token
                is_valid_after, message_after = password_reset_service.validate_reset_token(test_email, token)
                if not is_valid_after:
                    print(f"✓ Used token correctly rejected: {message_after}")
                else:
                    print("✗ Used token was not rejected")
                    return False
            else:
                print("✗ Failed to mark token as used")
                return False
        else:
            print(f"✗ Token validation failed: {message}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing complete flow: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 VocalLocal Forgot Password Functionality Test")
    print("=" * 60)
    
    tests = [
        ("Password Reset Service", test_password_reset_service),
        ("Email Service Integration", test_email_service_integration),
        ("User Model Integration", test_user_model_integration),
        ("Complete Flow", test_complete_flow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Forgot password functionality is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    print("\n📋 Next Steps:")
    print("1. Test the web interface at http://localhost:5001/auth/forgot-password")
    print("2. Verify email sending works with your SMTP configuration")
    print("3. Test the complete user flow from forgot password to login")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
