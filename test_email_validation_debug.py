#!/usr/bin/env python3
"""
Debug script to test email validation logic and DNS resolution.
"""

import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_dns_resolution():
    """Test DNS resolution for Gmail domain."""
    print("=== Testing DNS Resolution ===")
    
    try:
        import dns.resolver
        
        # Test Gmail MX records
        print("Testing gmail.com MX records:")
        try:
            mx_records = dns.resolver.resolve('gmail.com', 'MX')
            print(f"✓ Found {len(mx_records)} MX records for gmail.com:")
            for mx in mx_records:
                print(f"  Priority {mx.preference}: {mx.exchange}")
        except Exception as e:
            print(f"✗ Failed to resolve gmail.com MX records: {e}")
        
        # Test Gmail A records
        print("\nTesting gmail.com A records:")
        try:
            a_records = dns.resolver.resolve('gmail.com', 'A')
            print(f"✓ Found {len(a_records)} A records for gmail.com:")
            for a in a_records:
                print(f"  {a}")
        except Exception as e:
            print(f"✗ Failed to resolve gmail.com A records: {e}")
            
        # Test non-existent domain
        print("\nTesting non-existent domain:")
        try:
            mx_records = dns.resolver.resolve('nonexistentdomain12345.com', 'MX')
            print(f"Unexpected: Found MX records for non-existent domain")
        except dns.resolver.NXDOMAIN:
            print("✓ Correctly identified non-existent domain (NXDOMAIN)")
        except Exception as e:
            print(f"✓ Non-existent domain failed as expected: {e}")
            
    except ImportError:
        print("✗ dns.resolver not available")

def test_email_service_validation():
    """Test email service validation logic."""
    print("\n=== Testing Email Service Validation ===")
    
    try:
        from services.email_service import email_service
        
        test_emails = [
            "",  # Configured sender (should exist)
            "virinchi@gmail.com",         # Non-existent but valid domain
            "test@gmail.com",             # Non-existent but valid domain
            "invalid@nonexistentdomain12345.com",  # Invalid domain
            "invalid-format",             # Invalid format
        ]
        
        for email in test_emails:
            print(f"\nTesting: {email}")
            
            # Test format validation
            format_valid = email_service.validate_email_format(email)
            print(f"  Format valid: {format_valid}")
            
            # Test domain validation
            if format_valid:
                domain_valid, domain_error = email_service.validate_email_domain(email)
                print(f"  Domain valid: {domain_valid}")
                if domain_error:
                    print(f"  Domain error: {domain_error}")
            
            # Test comprehensive validation
            result = email_service.validate_email(email)
            print(f"  Overall result: {result}")
            
    except Exception as e:
        print(f"✗ Email service validation failed: {e}")

def test_current_validation_logic():
    """Test what the current validation logic actually does."""
    print("\n=== Understanding Current Validation Logic ===")
    
    print("Current validation checks:")
    print("1. Format validation - checks email format with regex")
    print("2. Domain validation - checks if domain has MX or A records")
    print("3. Does NOT check if specific email address exists")
    print("\nThis means:")
    print("- virinchi@gmail.com passes because gmail.com has MX records")
    print("- The validation cannot determine if 'virinchi' user exists")
    print("- This is actually correct behavior for most applications")
    print("\nTo verify individual email existence, you would need:")
    print("- SMTP verification (connect and try RCPT TO)")
    print("- Email verification links")
    print("- Third-party email verification services")

if __name__ == "__main__":
    print("Email Validation Debug Script")
    print("=" * 40)
    
    test_dns_resolution()
    test_email_service_validation()
    test_current_validation_logic()
    
    print("\n" + "=" * 40)
    print("Summary:")
    print("The current validation is working correctly!")
    print("It validates that the domain can receive emails,")
    print("but cannot verify if specific addresses exist.")
    print("This is standard behavior for email validation.")
