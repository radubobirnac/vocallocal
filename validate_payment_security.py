#!/usr/bin/env python3
"""
Payment Security Validation Script
Ensures that payment confirmation emails are only sent for legitimate Stripe payments
"""

import os
import sys
import re
from pathlib import Path

def scan_for_email_sending_tests():
    """Scan for test files that might send real payment emails"""
    
    print("🔍 Payment Security Validation")
    print("=" * 50)
    
    # Patterns that indicate real email sending in tests
    dangerous_patterns = [
        r'send_payment_confirmation_email\(',
        r'_send_payment_confirmation_email\(',
        r'email_service\.send_email\(',
        r'\.send\(msg\)'
    ]
    
    # Safe patterns that indicate proper mocking/simulation
    safe_patterns = [
        r'patch.*send_payment_confirmation_email',
        r'Mock.*send_payment_confirmation_email',
        r'create_payment_confirmation_email\(',
        r'SIMULATING.*email',
        r'Test mode.*no actual email'
    ]
    
    test_files = []
    current_dir = Path(__file__).parent
    
    # Find all test files
    for pattern in ['test_*.py', '*test*.py']:
        test_files.extend(current_dir.glob(pattern))
    
    issues_found = []
    secure_files = []
    
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for dangerous patterns
            dangerous_found = []
            for pattern in dangerous_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    dangerous_found.extend(matches)
            
            # Check for safe patterns
            safe_found = []
            for pattern in safe_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    safe_found.extend(matches)
            
            if dangerous_found:
                if safe_found or 'SECURITY' in content:
                    secure_files.append({
                        'file': test_file.name,
                        'status': 'SECURED',
                        'dangerous': dangerous_found,
                        'safe': safe_found
                    })
                else:
                    issues_found.append({
                        'file': test_file.name,
                        'status': 'VULNERABLE',
                        'dangerous': dangerous_found,
                        'safe': safe_found
                    })
            
        except Exception as e:
            print(f"⚠️  Error scanning {test_file.name}: {e}")
    
    # Report results
    print(f"\n📊 Scan Results:")
    print(f"   Total test files scanned: {len(test_files)}")
    print(f"   Secure files: {len(secure_files)}")
    print(f"   Vulnerable files: {len(issues_found)}")
    
    if issues_found:
        print(f"\n🚨 SECURITY ISSUES FOUND:")
        for issue in issues_found:
            print(f"   ❌ {issue['file']}")
            print(f"      Dangerous patterns: {issue['dangerous']}")
            print(f"      Safe patterns: {issue['safe']}")
    
    if secure_files:
        print(f"\n✅ SECURED FILES:")
        for secure in secure_files:
            print(f"   ✅ {secure['file']} - {secure['status']}")
    
    return len(issues_found) == 0

def validate_webhook_security():
    """Validate that webhook endpoints require proper Stripe signatures"""
    
    print(f"\n🔐 Webhook Security Validation")
    print("-" * 30)
    
    webhook_file = Path(__file__).parent / 'routes' / 'payment.py'
    
    if not webhook_file.exists():
        print("❌ Payment routes file not found")
        return False
    
    try:
        with open(webhook_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required security measures
        security_checks = [
            ('Stripe signature verification', r'stripe\.Webhook\.construct_event'),
            ('Signature header check', r'Stripe-Signature'),
            ('Missing signature error', r'Missing.*signature'),
            ('Signature verification error', r'SignatureVerificationError')
        ]
        
        all_secure = True
        
        for check_name, pattern in security_checks:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_secure = False
        
        return all_secure
        
    except Exception as e:
        print(f"❌ Error validating webhook security: {e}")
        return False

def validate_email_service_security():
    """Validate that email service has proper validation"""
    
    print(f"\n📧 Email Service Security Validation")
    print("-" * 35)
    
    email_service_file = Path(__file__).parent / 'services' / 'email_service.py'
    
    if not email_service_file.exists():
        print("❌ Email service file not found")
        return False
    
    try:
        with open(email_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for security measures
        security_checks = [
            ('Email validation', r'validate_email'),
            ('SMTP authentication', r'smtp_server.*password'),
            ('Error handling', r'except.*Exception'),
            ('Logging', r'logger\.')
        ]
        
        all_secure = True
        
        for check_name, pattern in security_checks:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"   ✅ {check_name}: Found")
            else:
                print(f"   ❌ {check_name}: Missing")
                all_secure = False
        
        return all_secure
        
    except Exception as e:
        print(f"❌ Error validating email service security: {e}")
        return False

def main():
    """Run comprehensive payment security validation"""
    
    print("🛡️  VocalLocal Payment Security Validation")
    print("=" * 60)
    
    # Run all security checks
    test_security = scan_for_email_sending_tests()
    webhook_security = validate_webhook_security()
    email_security = validate_email_service_security()
    
    # Overall security status
    print(f"\n🏁 OVERALL SECURITY STATUS")
    print("=" * 30)
    
    if test_security and webhook_security and email_security:
        print("✅ SECURE: All payment security checks passed")
        print("✅ Test files are properly secured")
        print("✅ Webhook endpoints require Stripe signatures")
        print("✅ Email service has proper validation")
        return True
    else:
        print("❌ SECURITY ISSUES DETECTED")
        if not test_security:
            print("❌ Test files may send real emails")
        if not webhook_security:
            print("❌ Webhook security insufficient")
        if not email_security:
            print("❌ Email service security insufficient")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
