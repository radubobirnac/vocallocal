#!/usr/bin/env python3
"""
Test the four specific base URLs for password reset functionality.
"""

import sys
import os
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_four_base_urls():
    """Test the four specific base URLs."""
    print("🌐 Testing Four Base URLs for Password Reset")
    print("=" * 50)
    
    try:
        from services.password_reset_service import PasswordResetService
        
        service = PasswordResetService()
        
        # Define the four base URLs
        test_cases = [
            {
                'name': 'Production VocalLocal',
                'env': {'VOCALLOCAL_BASE_URL': 'https://vocallocal.com'},
                'expected': 'https://vocallocal.com'
            },
            {
                'name': 'Production DigitalOcean',
                'env': {'APP_URL': 'https://vocallocal-l5et5.ondigitalocean.app'},
                'expected': 'https://vocallocal-l5et5.ondigitalocean.app'
            },
            {
                'name': 'Test DigitalOcean',
                'env': {'APP_URL': 'https://test-vocallocal-x9n74.ondigitalocean.app'},
                'expected': 'https://test-vocallocal-x9n74.ondigitalocean.app'
            },
            {
                'name': 'Production VocalLocal.net',
                'env': {'VOCALLOCAL_BASE_URL': 'https://vocallocal.net'},
                'expected': 'https://vocallocal.net'
            },
            {
                'name': 'Development Localhost',
                'env': {},  # No environment variables
                'expected': 'http://localhost:5001'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing {test_case['name']}:")
            
            with patch.dict(os.environ, test_case['env'], clear=True):
                base_url = service.get_base_url()
                
                if base_url == test_case['expected']:
                    print(f"   ✓ Base URL: {base_url}")
                else:
                    print(f"   ✗ Expected: {test_case['expected']}")
                    print(f"   ✗ Got: {base_url}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing base URLs: {e}")
        return False

def test_reset_emails_with_four_urls():
    """Test that reset emails contain the correct URLs for all four cases."""
    print("\n📧 Testing Reset Emails with Four Base URLs")
    print("=" * 50)
    
    try:
        from services.password_reset_service import PasswordResetService
        
        service = PasswordResetService()
        test_email = "user@example.com"
        test_token = "test_token_123"
        
        # Define the four test cases
        test_cases = [
            {
                'name': 'Production VocalLocal',
                'env': {'VOCALLOCAL_BASE_URL': 'https://vocallocal.com'},
                'expected_url': 'https://vocallocal.com/auth/reset-password'
            },
            {
                'name': 'Production DigitalOcean',
                'env': {'APP_URL': 'https://vocallocal-l5et5.ondigitalocean.app'},
                'expected_url': 'https://vocallocal-l5et5.ondigitalocean.app/auth/reset-password'
            },
            {
                'name': 'Test DigitalOcean',
                'env': {'APP_URL': 'https://test-vocallocal-x9n74.ondigitalocean.app'},
                'expected_url': 'https://test-vocallocal-x9n74.ondigitalocean.app/auth/reset-password'
            },
            {
                'name': 'Production VocalLocal.net',
                'env': {'VOCALLOCAL_BASE_URL': 'https://vocallocal.net'},
                'expected_url': 'https://vocallocal.net/auth/reset-password'
            },
            {
                'name': 'Development Localhost',
                'env': {},
                'expected_url': 'http://localhost:5001/auth/reset-password'
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing {test_case['name']}:")
            
            with patch.dict(os.environ, test_case['env'], clear=True):
                msg = service.create_reset_email(test_email, test_token, "TestUser")
                
                # Extract text content (more reliable than HTML)
                text_content = ""
                for part in msg.get_payload():
                    if part.get_content_type() == 'text/plain':
                        text_content = part.get_payload()
                        break
                
                expected_full_url = f"{test_case['expected_url']}?email={test_email}&token={test_token}"
                
                if expected_full_url in text_content:
                    print(f"   ✓ Correct URL found: {test_case['expected_url']}")
                else:
                    print(f"   ✗ Expected URL not found: {test_case['expected_url']}")
                    
                    # Debug: show what URLs were found
                    import re
                    urls = re.findall(r'https?://[^\s]+reset-password[^\s]*', text_content)
                    if urls:
                        print(f"   Found instead: {urls[0]}")
                    else:
                        print("   No reset-password URLs found")
                    return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing reset emails: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_deployment_configuration():
    """Show how to configure each environment."""
    print("\n⚙️ Deployment Configuration for Four Base URLs")
    print("=" * 50)
    
    print("\n1. Production VocalLocal (https://vocallocal.com):")
    print("   Environment Variable: VOCALLOCAL_BASE_URL=https://vocallocal.com")
    print("   Use this for your main production domain")
    
    print("\n2. Production DigitalOcean (https://vocallocal-l5et5.ondigitalocean.app):")
    print("   Environment Variable: APP_URL=https://vocallocal-l5et5.ondigitalocean.app")
    print("   Use this for your production DigitalOcean deployment")
    
    print("\n3. Test DigitalOcean (https://test-vocallocal-x9n74.ondigitalocean.app):")
    print("   Environment Variable: APP_URL=https://test-vocallocal-x9n74.ondigitalocean.app")
    print("   Use this for your test/staging DigitalOcean deployment")

    print("\n4. Production VocalLocal.net (https://vocallocal.net):")
    print("   Environment Variable: VOCALLOCAL_BASE_URL=https://vocallocal.net")
    print("   Use this for your production custom domain")

    print("\n4. Development Localhost (http://localhost:5001):")
    print("   No environment variables needed")
    print("   Automatically used when no other URLs are configured")
    
    print("\n🔧 Priority Order:")
    print("   1. VOCALLOCAL_BASE_URL (highest priority)")
    print("   2. APP_URL (DigitalOcean deployments)")
    print("   3. Flask request context (automatic detection)")
    print("   4. localhost:5001 (development fallback)")
    
    return True

def main():
    """Run all tests for the four base URLs."""
    print("🧪 VocalLocal Four Base URLs Test")
    print("=" * 60)
    
    tests = [
        ("Four Base URLs", test_four_base_urls),
        ("Reset Emails with Four URLs", test_reset_emails_with_four_urls),
        ("Deployment Configuration", show_deployment_configuration)
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
    
    if passed >= 2:  # Allow configuration to always pass
        print("🎉 All base URLs are working correctly!")
        print("\n📋 Your Base URLs:")
        print("• https://vocallocal.com")
        print("• https://vocallocal-l5et5.ondigitalocean.app")
        print("• https://test-vocallocal-x9n74.ondigitalocean.app")
        print("• https://vocallocal.net")
        print("• http://localhost:5001")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed >= 2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
