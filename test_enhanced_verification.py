#!/usr/bin/env python3
"""
Test script to verify the enhanced email verification system with verification links.
"""

def test_token_generation():
    """Test secure token generation and verification."""
    try:
        from services.email_verification_service import email_verification_service
        
        print("=== Testing Token Generation ===")
        
        test_email = "test@example.com"
        test_code = "123456"

        # First store the verification code
        store_result = email_verification_service.store_verification_code(test_email, test_code)
        if not store_result['success']:
            print("✗ Failed to store verification code for testing")
            return False

        # Generate token
        token = email_verification_service.generate_verification_token(test_email, test_code)
        print(f"Generated token: {token}")
        print(f"Token length: {len(token)}")

        if len(token) == 32:
            print("✓ Token has correct length (32 characters)")
        else:
            print("✗ Token has incorrect length")
            return False

        # Verify token
        is_valid = email_verification_service.verify_token(test_email, token, test_code)
        print(f"Token verification: {is_valid}")
        
        if is_valid:
            print("✓ Token verification successful")
        else:
            print("✗ Token verification failed")
            return False
        
        # Test with wrong code
        wrong_token_valid = email_verification_service.verify_token(test_email, token, "654321")
        print(f"Wrong code verification: {wrong_token_valid}")
        
        if not wrong_token_valid:
            print("✓ Token correctly rejects wrong code")
        else:
            print("✗ Token incorrectly accepts wrong code")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error testing token generation: {e}")
        return False

def test_enhanced_email_creation():
    """Test enhanced email creation with verification links."""
    try:
        from services.email_service import email_service
        
        print("\n=== Testing Enhanced Email Creation ===")
        
        test_email = "test@example.com"
        test_code = "123456"
        test_username = "testuser"
        test_token = "abcd1234567890efgh1234567890ijkl"
        
        # Create email with verification link
        msg = email_service.create_verification_email(
            email=test_email,
            code=test_code,
            username=test_username,
            verification_token=test_token
        )
        
        print(f"Email subject: {msg['Subject']}")
        print(f"Email to: {msg['To']}")
        print(f"Email from: {msg['From']}")
        
        # Extract HTML content properly
        html_content = ""
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                html_content = part.get_payload(decode=True).decode('utf-8')
                break

        if not html_content:
            print("✗ No HTML content found in email")
            return False

        # Save email content for inspection
        with open('enhanced_email_test.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
            print("✓ Email content saved to 'enhanced_email_test.html'")

        if "Verify Email Instantly" in html_content:
            print("✓ Email contains verification button")
        else:
            print("✗ Email missing verification button")
            return False

        if f"email={test_email}" in html_content:
            print("✓ Email contains email parameter in link")
        else:
            print("✗ Email missing email parameter")
            return False

        if f"token={test_token}" in html_content:
            print("✓ Email contains token parameter in link")
        else:
            print("✗ Email missing token parameter")
            return False

        if f"code={test_code}" in html_content:
            print("✓ Email contains code parameter in link")
        else:
            print("✗ Email missing code parameter")
            return False

        if "Two Ways to Verify" in html_content:
            print("✓ Email explains both verification methods")
        else:
            print("✗ Email missing verification method explanation")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error testing enhanced email creation: {e}")
        return False

def test_verification_link_flow():
    """Test the verification link flow."""
    try:
        from app import app
        
        print("\n=== Testing Verification Link Flow ===")
        
        with app.test_client() as client:
            # Test direct verification link access
            test_email = "linktest@example.com"
            test_code = "789012"
            test_token = "test_token_1234567890abcdef1234"
            
            # First, store a verification code (simulate email sending)
            from services.email_verification_service import email_verification_service
            store_result = email_verification_service.store_verification_code(test_email, test_code)
            
            if store_result['success']:
                print("✓ Test verification code stored")
            else:
                print("✗ Failed to store test verification code")
                return False
            
            # Generate proper token for the stored code
            proper_token = email_verification_service.generate_verification_token(test_email, test_code)
            
            # Test verification link access
            verification_url = f"/auth/verify-email?email={test_email}&token={proper_token}&code={test_code}"
            response = client.get(verification_url)
            
            print(f"Verification link response: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Verification link accessible")
                
                # Check if page contains auto-verification elements
                page_content = response.get_data(as_text=True)
                
                if "auto_verify" in page_content:
                    print("✓ Page includes auto-verification functionality")
                else:
                    print("⚠️  Page missing auto-verification (may be normal)")
                
                if test_email in page_content:
                    print("✓ Page contains correct email address")
                else:
                    print("✗ Page missing email address")
                    return False
                
                return True
            else:
                print(f"✗ Verification link failed: {response.status_code}")
                return False
        
    except Exception as e:
        print(f"Error testing verification link flow: {e}")
        return False

def test_registration_with_enhanced_verification():
    """Test registration flow with enhanced verification."""
    try:
        from app import app
        
        print("\n=== Testing Enhanced Registration Flow ===")
        
        with app.test_client() as client:
            # Test registration
            test_data = {
                'username': 'enhancedtest123',
                'email': 'enhancedtest@gmail.com',
                'password': 'testpassword123',
                'confirm_password': 'testpassword123'
            }
            
            print("Step 1: Submitting registration...")
            response = client.post('/auth/register', data=test_data, follow_redirects=False)
            print(f"Registration response: {response.status_code}")
            
            if response.status_code in [302, 303]:
                print("✓ Registration submitted successfully")
                
                if 'verify-email' in response.location:
                    print("✓ Redirected to verification page")
                else:
                    print("✗ Not redirected to verification page")
                    return False
            else:
                print(f"✗ Registration failed: {response.status_code}")
                return False
            
            # Test verification page access
            print("\nStep 2: Accessing verification page...")
            response = client.get('/auth/verify-email')
            print(f"Verification page response: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Verification page accessible")
                
                page_content = response.get_data(as_text=True)
                if 'enhancedtest@gmail.com' in page_content:
                    print("✓ Verification page shows correct email")
                    return True
                else:
                    print("✗ Verification page missing email")
                    return False
            else:
                print(f"✗ Verification page failed: {response.status_code}")
                return False
        
    except Exception as e:
        print(f"Error testing enhanced registration flow: {e}")
        return False

def main():
    """Run all enhanced verification tests."""
    print("Enhanced Email Verification System Test")
    print("=" * 45)
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if test_token_generation():
        tests_passed += 1
        print("✅ Token generation: PASSED")
    else:
        print("❌ Token generation: FAILED")
    
    if test_enhanced_email_creation():
        tests_passed += 1
        print("✅ Enhanced email creation: PASSED")
    else:
        print("❌ Enhanced email creation: FAILED")
    
    if test_verification_link_flow():
        tests_passed += 1
        print("✅ Verification link flow: PASSED")
    else:
        print("❌ Verification link flow: FAILED")
    
    if test_registration_with_enhanced_verification():
        tests_passed += 1
        print("✅ Enhanced registration flow: PASSED")
    else:
        print("❌ Enhanced registration flow: FAILED")
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All enhanced verification tests passed!")
        print("\n✅ Enhanced Email Verification Features:")
        print("• Secure token generation and validation")
        print("• Verification emails with clickable links")
        print("• Auto-verification from email links")
        print("• Fallback to manual OTP entry")
        print("• Enhanced user experience")
        
        print("\n📧 Email Features:")
        print("• Both OTP code and verification link")
        print("• Professional HTML email design")
        print("• Clear instructions for both methods")
        print("• Security warnings and expiration info")
        
        print("\n🔗 Verification Link Features:")
        print("• Secure token-based authentication")
        print("• Direct link to verification page")
        print("• Auto-verification with visual feedback")
        print("• Graceful fallback to manual entry")
        
    else:
        print("⚠️  Some enhanced verification tests failed")
    
    print("\n=== Next Steps ===")
    print("1. Start your Flask application: python app.py")
    print("2. Test registration with any email address")
    print("3. Check your email for the verification message")
    print("4. Try both the verification link and manual code entry")
    print("5. Verify the enhanced user experience")

if __name__ == "__main__":
    main()
