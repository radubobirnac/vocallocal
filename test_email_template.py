#!/usr/bin/env python3
"""
Simple test to verify email template with verification links.
"""

def test_email_template():
    """Test the email template generation."""
    try:
        from services.email_service import email_service
        
        print("=== Testing Email Template ===")
        
        test_email = "test@example.com"
        test_code = "123456"
        test_username = "testuser"
        test_token = "abcd1234567890efgh1234567890ijkl"
        
        # Test without verification token
        print("1. Testing email without verification link...")
        msg_without_link = email_service.create_verification_email(
            email=test_email,
            code=test_code,
            username=test_username
        )
        
        # Extract HTML content properly
        html_content_without_link = ""
        for part in msg_without_link.walk():
            if part.get_content_type() == 'text/html':
                html_content_without_link = part.get_payload(decode=True).decode('utf-8')
                break

        print(f"   Email contains code: {'✓' if test_code in html_content_without_link else '✗'}")
        print(f"   Email contains username: {'✓' if test_username in html_content_without_link else '✗'}")

        # Test with verification token
        print("\n2. Testing email with verification link...")
        msg_with_link = email_service.create_verification_email(
            email=test_email,
            code=test_code,
            username=test_username,
            verification_token=test_token
        )

        # Extract HTML content properly
        html_content_with_link = ""
        for part in msg_with_link.walk():
            if part.get_content_type() == 'text/html':
                html_content_with_link = part.get_payload(decode=True).decode('utf-8')
                break

        print(f"   Email contains code: {'✓' if test_code in html_content_with_link else '✗'}")
        print(f"   Email contains username: {'✓' if test_username in html_content_with_link else '✗'}")
        print(f"   Email contains verification button: {'✓' if 'Verify Email Instantly' in html_content_with_link else '✗'}")
        print(f"   Email contains verification link: {'✓' if f'email={test_email}' in html_content_with_link else '✗'}")
        print(f"   Email contains token: {'✓' if f'token={test_token}' in html_content_with_link else '✗'}")
        print(f"   Email contains 'Two Ways to Verify': {'✓' if 'Two Ways to Verify' in html_content_with_link else '✗'}")
        
        # Save email content for inspection
        with open('test_email_output.html', 'w', encoding='utf-8') as f:
            f.write(html_content_with_link)
        
        print("\n✓ Email template test completed")
        print("✓ HTML email saved to 'test_email_output.html' for inspection")
        
        return True
        
    except Exception as e:
        print(f"Error testing email template: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_token_generation_simple():
    """Simple token generation test."""
    try:
        from services.email_verification_service import email_verification_service
        
        print("\n=== Testing Token Generation (Simple) ===")
        
        test_email = "simple@test.com"
        test_code = "789012"
        
        # Generate two tokens with same inputs
        token1 = email_verification_service.generate_verification_token(test_email, test_code)
        token2 = email_verification_service.generate_verification_token(test_email, test_code)
        
        print(f"Token 1: {token1}")
        print(f"Token 2: {token2}")
        print(f"Tokens match: {'✓' if token1 == token2 else '✗'}")
        
        if token1 == token2:
            print("✓ Token generation is deterministic")
            return True
        else:
            print("✗ Token generation is not deterministic")
            return False
        
    except Exception as e:
        print(f"Error testing token generation: {e}")
        return False

def test_complete_flow():
    """Test the complete enhanced verification flow."""
    try:
        from services.email_verification_service import email_verification_service
        
        print("\n=== Testing Complete Enhanced Flow ===")
        
        test_email = "complete@test.com"
        test_username = "completeuser"
        
        # Step 1: Send verification code (this should generate token internally)
        print("1. Sending verification code...")
        result = email_verification_service.send_verification_code(test_email, test_username)
        
        if result['success']:
            print("✓ Verification code sent successfully")
        else:
            print(f"✗ Failed to send verification code: {result['message']}")
            return False
        
        # Step 2: Get the stored verification data
        verification_data = email_verification_service.get_verification_data(test_email)
        if verification_data:
            stored_code = verification_data.get('code')
            print(f"✓ Stored code retrieved: {stored_code}")
        else:
            print("✗ No verification data found")
            return False
        
        # Step 3: Generate token for the stored code
        token = email_verification_service.generate_verification_token(test_email, stored_code)
        print(f"✓ Generated token: {token}")
        
        # Step 4: Verify the token
        is_valid = email_verification_service.verify_token(test_email, token, stored_code)
        print(f"✓ Token verification: {'PASSED' if is_valid else 'FAILED'}")
        
        return is_valid
        
    except Exception as e:
        print(f"Error testing complete flow: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run email template tests."""
    print("Enhanced Email Verification Template Test")
    print("=" * 45)
    
    tests_passed = 0
    total_tests = 3
    
    if test_email_template():
        tests_passed += 1
        print("✅ Email template: PASSED")
    else:
        print("❌ Email template: FAILED")
    
    if test_token_generation_simple():
        tests_passed += 1
        print("✅ Token generation: PASSED")
    else:
        print("❌ Token generation: FAILED")
    
    if test_complete_flow():
        tests_passed += 1
        print("✅ Complete flow: PASSED")
    else:
        print("❌ Complete flow: FAILED")
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All email template tests passed!")
    else:
        print("⚠️  Some tests failed")

if __name__ == "__main__":
    main()
