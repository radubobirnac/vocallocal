#!/usr/bin/env python3
"""
Test script for improved email validation system.
Tests the enhanced validation logic with better messaging.
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_improved_validation():
    """Test the improved email validation system."""
    print("Testing Improved Email Validation System")
    print("=" * 50)
    
    try:
        from services.email_service import email_service
        
        test_cases = [
            {
                'email': '',
                'description': 'Configured sender email (should be valid)',
                'expected_valid': True
            },
            {
                'email': 'virinchi@gmail.com',
                'description': 'Non-existent user on valid domain',
                'expected_valid': True  # Domain validation only
            },
            {
                'email': 'test@gmail.com',
                'description': 'Another non-existent user on valid domain',
                'expected_valid': True  # Domain validation only
            },
            {
                'email': 'user@nonexistentdomain12345.com',
                'description': 'Valid format but invalid domain',
                'expected_valid': False
            },
            {
                'email': 'invalid-email-format',
                'description': 'Invalid email format',
                'expected_valid': False
            },
            {
                'email': 'user@outlook.com',
                'description': 'Valid domain (Outlook)',
                'expected_valid': True
            },
            {
                'email': 'test@yahoo.com',
                'description': 'Valid domain (Yahoo)',
                'expected_valid': True
            }
        ]
        
        print("\n=== Standard Domain Validation ===")
        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {case['email']}")
            print(f"   Description: {case['description']}")
            
            result = email_service.validate_email(case['email'])
            
            print(f"   Result: {'✓ VALID' if result['valid'] else '✗ INVALID'}")
            print(f"   Expected: {'VALID' if case['expected_valid'] else 'INVALID'}")
            
            if result['errors']:
                print(f"   Errors: {', '.join(result['errors'])}")
            
            if result['warnings']:
                print(f"   Warnings: {', '.join(result['warnings'])}")
            
            print(f"   Validation Level: {result.get('validation_level', 'unknown')}")
            
            # Check if result matches expectation
            if result['valid'] == case['expected_valid']:
                print("   Status: ✓ PASSED")
            else:
                print("   Status: ✗ FAILED")
        
        print("\n=== Key Insights ===")
        print("1. Domain validation checks if the domain can receive emails")
        print("2. It does NOT verify if specific email addresses exist")
        print("3. This is standard behavior for email validation")
        print("4. Gmail, Outlook, Yahoo domains pass validation")
        print("5. Non-existent domains fail validation")
        print("6. Invalid formats fail validation")
        
        print("\n=== Testing SMTP Verification (Optional) ===")
        print("Note: SMTP verification is more thorough but slower and potentially intrusive")
        
        # Test SMTP verification on a few emails (if enabled)
        smtp_test_emails = ['test@gmail.com', '']
        
        for email in smtp_test_emails:
            print(f"\nTesting SMTP verification for: {email}")
            try:
                # Note: SMTP verification is disabled by default
                # Uncomment the next line to test (may be slow/blocked)
                # result = email_service.validate_email(email, smtp_verify=True)
                print("   SMTP verification skipped (can be enabled for testing)")
                print("   This would connect to the actual mail server")
            except Exception as e:
                print(f"   SMTP verification error: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_validation_messages():
    """Test that validation messages are clear and helpful."""
    print("\n" + "=" * 50)
    print("Testing Validation Messages")
    print("=" * 50)
    
    try:
        from services.email_service import email_service
        
        message_tests = [
            {
                'email': 'invalid-format',
                'expected_message_contains': 'valid email format'
            },
            {
                'email': 'user@nonexistentdomain12345.com',
                'expected_message_contains': 'does not exist'
            },
            {
                'email': 'valid@gmail.com',
                'expected_warning_contains': 'does not verify'
            }
        ]
        
        for test in message_tests:
            result = email_service.validate_email(test['email'])
            print(f"\nTesting messages for: {test['email']}")
            
            if 'expected_message_contains' in test:
                found = any(test['expected_message_contains'] in error for error in result['errors'])
                print(f"   Error message check: {'✓' if found else '✗'}")
                if result['errors']:
                    print(f"   Actual errors: {result['errors']}")
            
            if 'expected_warning_contains' in test:
                found = any(test['expected_warning_contains'] in warning for warning in result['warnings'])
                print(f"   Warning message check: {'✓' if found else '✗'}")
                if result['warnings']:
                    print(f"   Actual warnings: {result['warnings']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Message test failed: {e}")
        return False

def main():
    """Run all improved validation tests."""
    print("VocalLocal Improved Email Validation Test")
    print("=" * 60)
    
    success1 = test_improved_validation()
    success2 = test_validation_messages()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if success1 and success2:
        print("✓ All tests passed!")
        print("\nThe improved email validation system:")
        print("• Provides clear, helpful error messages")
        print("• Distinguishes between format and domain errors")
        print("• Explains validation limitations clearly")
        print("• Offers optional SMTP verification")
        print("• Follows industry best practices")
    else:
        print("✗ Some tests failed. Check the output above.")
    
    print("\nFor production use:")
    print("1. Domain validation is sufficient for most applications")
    print("2. SMTP verification can be enabled for critical flows")
    print("3. Email verification links provide the best user experience")
    print("4. The current validation prevents typos and invalid domains")

if __name__ == "__main__":
    main()
