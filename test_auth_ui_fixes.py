#!/usr/bin/env python3
"""
Test script to verify authentication UI fixes and email configuration.
"""

import os
import sys
from pathlib import Path

def test_email_configuration():
    """Test email service configuration."""
    print("=== Testing Email Configuration ===")
    
    try:
        from services.email_service import email_service
        
        print(f"✓ SMTP Server: {email_service.smtp_server}")
        print(f"✓ SMTP Port: {email_service.smtp_port}")
        print(f"✓ Use TLS: {email_service.use_tls}")
        print(f"✓ Username: {email_service.username}")
        print(f"✓ Password configured: {bool(email_service.password)}")
        print(f"✓ Default sender: {email_service.default_sender}")
        
        if not email_service.password:
            print("❌ MAIL_PASSWORD not configured!")
            print("   Please set MAIL_PASSWORD in your .env file with Gmail app password.")
            return False
        else:
            print("✅ Email service appears to be properly configured")
            return True
            
    except ImportError as e:
        print(f"❌ Failed to import email service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing email configuration: {e}")
        return False

def test_static_files():
    """Test that static files exist and have been updated."""
    print("\n=== Testing Static Files ===")
    
    static_dir = Path("static")
    
    # Check auth.js
    auth_js = static_dir / "auth.js"
    if auth_js.exists():
        content = auth_js.read_text()
        if "passwordTogglesInitialized" in content:
            print("✅ auth.js has been updated with duplicate prevention")
        else:
            print("❌ auth.js may not have the latest fixes")
    else:
        print("❌ auth.js not found")
    
    # Check auth.css
    auth_css = static_dir / "auth.css"
    if auth_css.exists():
        content = auth_css.read_text()
        if "pointer-events: none" in content:
            print("✅ auth.css has been updated with icon fixes")
        else:
            print("❌ auth.css may not have the latest fixes")
    else:
        print("❌ auth.css not found")

def test_env_file():
    """Test .env file configuration."""
    print("\n=== Testing .env File ===")
    
    env_file = Path(".env")
    if env_file.exists():
        content = env_file.read_text()
        
        # Check for email configuration
        if "MAIL_PASSWORD=" in content:
            print("✅ MAIL_PASSWORD variable found in .env")
            if "your_gmail_app_password_here" in content:
                print("⚠️  MAIL_PASSWORD still has placeholder value")
                print("   Please replace with your actual Gmail app password")
            else:
                print("✅ MAIL_PASSWORD appears to be configured")
        else:
            print("❌ MAIL_PASSWORD not found in .env file")
        
        # Check other email settings
        email_vars = ["MAIL_SERVER", "MAIL_PORT", "MAIL_USE_TLS", "MAIL_USERNAME"]
        for var in email_vars:
            if f"{var}=" in content:
                print(f"✅ {var} configured")
            else:
                print(f"❌ {var} missing")
    else:
        print("❌ .env file not found")

def test_template_files():
    """Test template files for proper structure."""
    print("\n=== Testing Template Files ===")
    
    templates_dir = Path("templates")
    
    # Check login.html
    login_html = templates_dir / "login.html"
    if login_html.exists():
        content = login_html.read_text()
        password_containers = content.count('password-input-container')
        password_toggles = content.count('password-toggle-btn')
        
        print(f"✅ login.html found")
        print(f"   - Password containers: {password_containers}")
        print(f"   - Password toggle buttons: {password_toggles}")
        
        if password_containers == password_toggles == 1:
            print("✅ Login form has correct password field structure")
        else:
            print("⚠️  Login form structure may need review")
    else:
        print("❌ login.html not found")
    
    # Check register.html
    register_html = templates_dir / "register.html"
    if register_html.exists():
        content = register_html.read_text()
        password_containers = content.count('password-input-container')
        password_toggles = content.count('password-toggle-btn')
        
        print(f"✅ register.html found")
        print(f"   - Password containers: {password_containers}")
        print(f"   - Password toggle buttons: {password_toggles}")
        
        if password_containers == password_toggles == 2:
            print("✅ Register form has correct password field structure")
        else:
            print("⚠️  Register form structure may need review")
    else:
        print("❌ register.html not found")

def main():
    """Run all tests."""
    print("Authentication UI and Email Configuration Test")
    print("=" * 50)
    
    # Change to the correct directory if needed
    if not Path("services").exists():
        print("Changing to vocallocal directory...")
        os.chdir("vocallocal")
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if test_email_configuration():
        tests_passed += 1
    
    test_static_files()
    tests_passed += 1
    
    test_env_file()
    tests_passed += 1
    
    test_template_files()
    tests_passed += 1
    
    print(f"\n=== Test Summary ===")
    print(f"Tests completed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All tests passed!")
    else:
        print("⚠️  Some issues found - please review the output above")
    
    print("\n=== Next Steps ===")
    print("1. Set your Gmail app password in the .env file")
    print("2. Restart your Flask application")
    print("3. Test the login/register forms in your browser")
    print("4. Try registering a new user to test email verification")

if __name__ == "__main__":
    main()
