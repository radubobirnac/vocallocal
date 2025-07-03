#!/usr/bin/env python3
"""
Test script for email functionality in VocalLocal application.
Tests email validation, configuration, and sending capabilities.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_email_service_import():
    """Test if email service can be imported."""
    try:
        from services.email_service import email_service
        print("✓ Email service imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import email service: {e}")
        return False

def test_email_configuration():
    """Test email service configuration."""
    try:
        from services.email_service import email_service
        
        print("\n=== Email Configuration ===")
        print(f"SMTP Server: {email_service.smtp_server}")
        print(f"SMTP Port: {email_service.smtp_port}")
        print(f"Use TLS: {email_service.use_tls}")
        print(f"Use SSL: {email_service.use_ssl}")
        print(f"Username: {email_service.username}")
        print(f"Password configured: {bool(email_service.password)}")
        print(f"Default sender: {email_service.default_sender}")
        
        if not email_service.password:
            print("⚠️  Warning: MAIL_PASSWORD not configured. Email sending will fail.")
            print("   Set MAIL_PASSWORD environment variable with Gmail app password.")
        else:
            print("✓ Email service appears to be configured")
            
        return True
    except Exception as e:
        print(f"✗ Error checking email configuration: {e}")
        return False

def test_email_format_validation():
    """Test email format validation."""
    try:
        from services.email_service import email_service
        
        print("\n=== Email Format Validation Tests ===")
        
        test_emails = [
            ("test@example.com", True),
            ("user.name@domain.co.uk", True),
            ("invalid-email", False),
            ("@domain.com", False),
            ("user@", False),
            ("", False),
            ("user@domain", True),  # Basic format is valid, DNS will catch invalid domains
        ]
        
        all_passed = True
        for email, expected in test_emails:
            result = email_service.validate_email_format(email)
            status = "✓" if result == expected else "✗"
            print(f"{status} {email}: {result} (expected: {expected})")
            if result != expected:
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"✗ Error in email format validation: {e}")
        return False

def test_email_domain_validation():
    """Test email domain validation (DNS check)."""
    try:
        from services.email_service import email_service
        
        print("\n=== Email Domain Validation Tests ===")
        
        test_domains = [
            "gmail.com",
            "outlook.com", 
            "yahoo.com",
            "nonexistentdomain12345.com"
        ]
        
        for domain in test_domains:
            email = f"test@{domain}"
            is_valid, error_msg = email_service.validate_email_domain(email)
            status = "✓" if is_valid else "✗"
            print(f"{status} {domain}: {is_valid} {f'({error_msg})' if error_msg else ''}")
        
        return True
    except Exception as e:
        print(f"✗ Error in domain validation: {e}")
        return False

def test_comprehensive_email_validation():
    """Test comprehensive email validation."""
    try:
        from services.email_service import email_service
        
        print("\n=== Comprehensive Email Validation Tests ===")
        
        test_emails = [
            "test@gmail.com",
            "invalid@nonexistentdomain12345.com",
            "invalid-format",
        ]
        
        for email in test_emails:
            result = email_service.validate_email(email)
            status = "✓" if result['valid'] else "✗"
            errors = ", ".join(result.get('errors', [])) if result.get('errors') else "None"
            print(f"{status} {email}: Valid={result['valid']}, Errors: {errors}")
        
        return True
    except Exception as e:
        print(f"✗ Error in comprehensive validation: {e}")
        return False

def test_welcome_email_creation():
    """Test welcome email template creation."""
    try:
        from services.email_service import email_service
        
        print("\n=== Welcome Email Template Test ===")
        
        msg = email_service.create_welcome_email(
            username="TestUser",
            email="test@example.com",
            user_tier="free"
        )
        
        print(f"✓ Email created successfully")
        print(f"  Subject: {msg['Subject']}")
        print(f"  From: {msg['From']}")
        print(f"  To: {msg['To']}")
        print(f"  Parts: {len(msg.get_payload())} (text + html)")
        
        return True
    except Exception as e:
        print(f"✗ Error creating welcome email: {e}")
        return False

def test_email_sending_dry_run():
    """Test email sending configuration (without actually sending)."""
    try:
        from services.email_service import email_service
        
        print("\n=== Email Sending Configuration Test ===")
        
        if not email_service.password:
            print("⚠️  Cannot test email sending: MAIL_PASSWORD not configured")
            print("   To test email sending, set MAIL_PASSWORD environment variable")
            return True
        
        # Create a test email
        msg = email_service.create_welcome_email(
            username="TestUser",
            email="test@example.com",
            user_tier="free"
        )
        
        print("✓ Email message created for sending test")
        print("  Note: Actual sending test requires valid MAIL_PASSWORD")
        print("  Use /api/test-email-config endpoint to test live configuration")
        
        return True
    except Exception as e:
        print(f"✗ Error in email sending test: {e}")
        return False

def main():
    """Run all email functionality tests."""
    print("VocalLocal Email Functionality Test")
    print("=" * 40)
    
    tests = [
        test_email_service_import,
        test_email_configuration,
        test_email_format_validation,
        test_email_domain_validation,
        test_comprehensive_email_validation,
        test_welcome_email_creation,
        test_email_sending_dry_run,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check configuration and dependencies.")
    
    print("\n=== Next Steps ===")
    print("1. Set MAIL_PASSWORD environment variable with Gmail app password")
    print("2. Test email sending via /api/test-email-config endpoint")
    print("3. Test registration with email validation")
    print("4. Verify welcome emails are sent successfully")

if __name__ == "__main__":
    main()
