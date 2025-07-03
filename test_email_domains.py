#!/usr/bin/env python3
"""
Test script to check email domain validation for educational and other domains.
"""

def test_email_validation():
    """Test email validation for various domains."""
    try:
        from services.email_service import email_service
        
        print("=== Email Domain Validation Test ===")
        
        test_emails = [
            'test@paruluniversity.ac.in',
            'student@mit.edu', 
            'user@gmail.com',
            'test@university.edu',
            'student@stanford.edu',
            'user@outlook.com',
            'test@yahoo.com',
            'student@iit.ac.in',
            'user@example.org'
        ]
        
        for email in test_emails:
            print(f"\nTesting: {email}")
            
            # Test format validation
            format_valid = email_service.validate_email_format(email)
            print(f"  Format valid: {format_valid}")
            
            # Test domain validation
            domain_valid, domain_msg = email_service.validate_email_domain(email)
            print(f"  Domain valid: {domain_valid}")
            if domain_msg:
                print(f"  Domain message: {domain_msg}")
            
            # Test comprehensive validation
            result = email_service.validate_email(email)
            print(f"  Overall valid: {result['valid']}")
            if result.get('errors'):
                print(f"  Errors: {result['errors']}")
            if result.get('warnings'):
                print(f"  Warnings: {result['warnings']}")
        
        return True
        
    except Exception as e:
        print(f"Error testing email validation: {e}")
        return False

def test_basic_validation():
    """Test basic email format validation."""
    try:
        from services.email_service import email_service
        
        print("\n=== Basic Email Format Test ===")
        
        test_cases = [
            ('valid@domain.com', True),
            ('user.name@domain.co.uk', True),
            ('test@paruluniversity.ac.in', True),
            ('student@mit.edu', True),
            ('invalid-email', False),
            ('@domain.com', False),
            ('user@', False),
            ('', False)
        ]
        
        for email, expected in test_cases:
            result = email_service.validate_email_format(email)
            status = "✓" if result == expected else "✗"
            print(f"{status} {email}: {result} (expected: {expected})")
        
        return True
        
    except Exception as e:
        print(f"Error testing basic validation: {e}")
        return False

if __name__ == "__main__":
    print("Email Domain Validation Test")
    print("=" * 40)
    
    test_basic_validation()
    test_email_validation()
