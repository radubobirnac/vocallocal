#!/usr/bin/env python3
"""
Test script to verify Gmail SMTP fix and password field UI changes.
"""

import os
import re
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
            return False
        elif email_service.password == "your_gmail_app_password_here":
            print("⚠️  MAIL_PASSWORD still has placeholder value")
            print("   Please replace with your actual Gmail app password")
            print("   See GMAIL_APP_PASSWORD_SETUP.md for instructions")
            return False
        else:
            print("✅ Email service configured with password")
            
            # Check if it looks like a regular password vs app password
            if len(email_service.password) == 16 and ' ' not in email_service.password:
                print("✅ Password format looks like Gmail app password")
                return True
            elif len(email_service.password) == 19 and email_service.password.count(' ') == 3:
                print("✅ Password format looks like Gmail app password (with spaces)")
                return True
            else:
                print("⚠️  Password doesn't look like Gmail app password format")
                print("   Gmail app passwords are 16 characters (may include spaces)")
                print("   Regular passwords won't work for SMTP authentication")
                return False
            
    except ImportError as e:
        print(f"❌ Failed to import email service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing email configuration: {e}")
        return False

def test_password_field_removal():
    """Test that password toggle buttons have been removed."""
    print("\n=== Testing Password Field Changes ===")
    
    templates_dir = Path("templates")
    templates_to_check = [
        "login.html",
        "register.html", 
        "admin_login.html",
        "profile.html"
    ]
    
    all_clean = True
    
    for template_name in templates_to_check:
        template_path = templates_dir / template_name
        if template_path.exists():
            content = template_path.read_text()
            
            # Check for password toggle buttons
            toggle_buttons = content.count('password-toggle-btn')
            eye_icons = content.count('fa-eye')
            password_containers = content.count('password-input-container')
            
            print(f"\n✓ {template_name}:")
            print(f"   - Password toggle buttons: {toggle_buttons}")
            print(f"   - Eye icons: {eye_icons}")
            print(f"   - Password containers: {password_containers}")
            
            if toggle_buttons == 0 and eye_icons == 0 and password_containers == 0:
                print(f"   ✅ Clean - no toggle buttons or containers")
            elif toggle_buttons > 0 or eye_icons > 0:
                print(f"   ❌ Still contains toggle buttons or eye icons")
                all_clean = False
            else:
                print(f"   ✅ Toggle buttons removed successfully")
        else:
            print(f"❌ {template_name} not found")
            all_clean = False
    
    return all_clean

def test_javascript_cleanup():
    """Test that JavaScript password toggle code has been removed."""
    print("\n=== Testing JavaScript Changes ===")
    
    auth_js = Path("static/auth.js")
    if auth_js.exists():
        content = auth_js.read_text()
        
        # Check for removed functions
        has_toggle_function = 'togglePasswordVisibility' in content
        has_init_function = 'initializePasswordToggles' in content
        has_password_logic = 'password-toggle-btn' in content
        
        print(f"✓ auth.js found")
        print(f"   - Toggle function present: {has_toggle_function}")
        print(f"   - Init function present: {has_init_function}")
        print(f"   - Password toggle logic: {has_password_logic}")
        
        if not has_toggle_function and not has_init_function and not has_password_logic:
            print("   ✅ Password toggle code successfully removed")
            return True
        else:
            print("   ⚠️  Some password toggle code may still be present")
            return False
    else:
        print("❌ auth.js not found")
        return False

def test_css_cleanup():
    """Test that CSS password toggle styles have been removed."""
    print("\n=== Testing CSS Changes ===")
    
    auth_css = Path("static/auth.css")
    if auth_css.exists():
        content = auth_css.read_text()
        
        # Check for removed styles
        has_toggle_btn_styles = '.password-toggle-btn' in content
        has_container_styles = '.password-input-container' in content
        has_icon_styles = 'fa-eye' in content
        
        print(f"✓ auth.css found")
        print(f"   - Toggle button styles: {has_toggle_btn_styles}")
        print(f"   - Container styles: {has_container_styles}")
        print(f"   - Icon styles: {has_icon_styles}")
        
        if not has_toggle_btn_styles and not has_container_styles:
            print("   ✅ Password toggle styles successfully removed")
            return True
        else:
            print("   ⚠️  Some password toggle styles may still be present")
            return False
    else:
        print("❌ auth.css not found")
        return False

def test_env_file():
    """Test .env file configuration."""
    print("\n=== Testing .env File ===")
    
    env_file = Path(".env")
    if env_file.exists():
        content = env_file.read_text()
        
        # Check email configuration
        if "MAIL_PASSWORD=" in content:
            print("✅ MAIL_PASSWORD variable found")
            
            # Extract the password value
            match = re.search(r'MAIL_PASSWORD=(.+)', content)
            if match:
                password = match.group(1).strip()
                if password == "your_gmail_app_password_here":
                    print("⚠️  Still has placeholder value - needs Gmail app password")
                    return False
                else:
                    print("✅ MAIL_PASSWORD has been set")
                    return True
            else:
                print("❌ Could not extract MAIL_PASSWORD value")
                return False
        else:
            print("❌ MAIL_PASSWORD not found in .env")
            return False
    else:
        print("❌ .env file not found")
        return False

def main():
    """Run all tests."""
    print("Gmail SMTP and Password Field UI Test")
    print("=" * 50)
    
    # Change to the correct directory if needed
    if not Path("services").exists():
        print("Changing to vocallocal directory...")
        os.chdir("vocallocal")
    
    tests_passed = 0
    total_tests = 5
    
    # Run tests
    if test_email_configuration():
        tests_passed += 1
    
    if test_password_field_removal():
        tests_passed += 1
    
    if test_javascript_cleanup():
        tests_passed += 1
    
    if test_css_cleanup():
        tests_passed += 1
    
    if test_env_file():
        tests_passed += 1
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All tests passed!")
    else:
        print("⚠️  Some issues found - please review the output above")
    
    print("\n=== Next Steps ===")
    if tests_passed < total_tests:
        print("1. Follow the Gmail App Password setup guide")
        print("2. Replace placeholder password in .env file")
        print("3. Restart your Flask application")
    else:
        print("1. Restart your Flask application")
        print("2. Test user registration to verify email sending")
        print("3. Check login/register forms for clean password fields")

if __name__ == "__main__":
    main()
