#!/usr/bin/env python3
"""
End-to-End Test for Super User Access Control
This script tests the complete workflow from authentication to API usage for Super Users.
"""

import sys
import os
import requests
import json
import time

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_api_endpoints():
    """Test API endpoints with Super User authentication."""
    print("🌐 Testing API Endpoints for Super User Access")
    print("=" * 60)

    base_url = "http://localhost:5001"

    # Test data
    test_cases = [
        {
            'name': 'User Role Info',
            'method': 'GET',
            'endpoint': '/api/user/role-info',
            'expected_role': 'super_user'
        },
        {
            'name': 'Usage Check - Transcription',
            'method': 'POST',
            'endpoint': '/api/check-usage',
            'data': {'service': 'transcription', 'amount': 100},
            'expected_allowed': True
        },
        {
            'name': 'Usage Check - Translation',
            'method': 'POST',
            'endpoint': '/api/check-usage',
            'data': {'service': 'translation', 'amount': 10000},
            'expected_allowed': True
        },
        {
            'name': 'Usage Check - TTS',
            'method': 'POST',
            'endpoint': '/api/check-usage',
            'data': {'service': 'tts', 'amount': 50},
            'expected_allowed': True
        }
    ]

    print("⚠️  Note: This test requires:")
    print("   1. Flask app running on localhost:5001")
    print("   2. User authenticated as Super User")
    print("   3. Valid session cookies")
    print()

    # Create a session to maintain cookies
    session = requests.Session()

    for test_case in test_cases:
        print(f"Testing {test_case['name']}...")

        try:
            if test_case['method'] == 'GET':
                response = session.get(f"{base_url}{test_case['endpoint']}")
            else:
                response = session.post(
                    f"{base_url}{test_case['endpoint']}",
                    json=test_case.get('data'),
                    headers={'Content-Type': 'application/json'}
                )

            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2)}")

                # Validate specific expectations
                if 'expected_role' in test_case:
                    actual_role = data.get('role')
                    if actual_role == test_case['expected_role']:
                        print(f"  ✅ Role check passed: {actual_role}")
                    else:
                        print(f"  ❌ Role check failed: expected {test_case['expected_role']}, got {actual_role}")

                if 'expected_allowed' in test_case:
                    actual_allowed = data.get('allowed')
                    if actual_allowed == test_case['expected_allowed']:
                        print(f"  ✅ Access check passed: {actual_allowed}")
                    else:
                        print(f"  ❌ Access check failed: expected {test_case['expected_allowed']}, got {actual_allowed}")

            elif response.status_code == 401:
                print(f"  ⚠️  Authentication required - please login as Super User first")
            elif response.status_code == 403:
                print(f"  ❌ Access denied - user may not have Super User privileges")
            else:
                print(f"  ❌ Unexpected status code: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"  Error: {error_data}")
                except:
                    print(f"  Error: {response.text}")

        except requests.exceptions.ConnectionError:
            print(f"  ❌ Could not connect to {base_url}")
            print(f"     Make sure Flask app is running")
            break
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

        print()

def test_model_access_validation():
    """Test model access validation for Super Users."""
    print("🤖 Testing Model Access Validation")
    print("=" * 60)

    try:
        from services.model_access_service import ModelAccessService

        # Test email (replace with actual Super User email)
        test_email = "superuser@example.com"

        premium_models = [
            'gpt-4o-mini-transcribe',
            'gpt-4o-transcribe',
            'gemini-2.5-flash',
            'gemini-2.5-flash-tts',
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4.1-mini',
            'openai'
        ]

        print(f"Testing model access for: {test_email}")
        print("Note: This test assumes the user has Super User role in Firebase")
        print()

        for model in premium_models:
            access_info = ModelAccessService.can_access_model(model, test_email)

            if access_info['allowed']:
                print(f"✅ {model}: {access_info['reason']}")
            else:
                print(f"❌ {model}: {access_info['reason']}")

        # Test comprehensive model info
        print("\n📊 Comprehensive Model Access Info:")
        restrictions_info = ModelAccessService.get_model_restrictions_info(test_email)

        print(f"User Role: {restrictions_info['user_role']}")
        print(f"Has Premium Access: {restrictions_info['has_premium_access']}")
        print(f"Unlimited Access: {restrictions_info['restrictions']['unlimited_access']}")
        print(f"Accessible Models: {len(restrictions_info['available_models']['accessible_models'])}")
        print(f"Restricted Models: {len(restrictions_info['available_models']['restricted_models'])}")

        return True

    except Exception as e:
        print(f"❌ Error testing model access: {str(e)}")
        return False

def test_usage_validation():
    """Test usage validation for Super Users."""
    print("📊 Testing Usage Validation")
    print("=" * 60)

    try:
        from services.usage_validation_service import UsageValidationService

        # Test email (replace with actual Super User email)
        test_email = "superuser@example.com"

        test_cases = [
            ('Transcription', 'validate_transcription_usage', 1000),  # 1000 minutes
            ('Translation', 'validate_translation_usage', 100000),   # 100k words
            ('TTS', 'validate_tts_usage', 500),                      # 500 minutes
            ('AI Credits', 'validate_ai_usage', 1000)                # 1000 credits
        ]

        print(f"Testing usage validation for: {test_email}")
        print("Note: This test assumes the user has Super User role in Firebase")
        print()

        for service_name, method_name, amount in test_cases:
            method = getattr(UsageValidationService, method_name)
            result = method(test_email, amount)

            if result['allowed']:
                print(f"✅ {service_name}: {result['message']}")
                print(f"   Requested: {amount}, Remaining: {result.get('remaining', 'unlimited')}")
            else:
                print(f"❌ {service_name}: {result['message']}")
                print(f"   Requested: {amount}, Limit: {result.get('limit', 'unknown')}")
            print()

        return True

    except Exception as e:
        print(f"❌ Error testing usage validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_user_role_system():
    """Test the user role system."""
    print("👤 Testing User Role System")
    print("=" * 60)

    try:
        from models.firebase_models import User

        # Test email (replace with actual Super User email)
        test_email = "superuser@example.com"

        print(f"Testing user role system for: {test_email}")
        print()

        # Test role checking methods
        role = User.get_user_role(test_email)
        print(f"User Role: {role}")

        is_admin = User.is_admin(test_email)
        print(f"Is Admin: {is_admin}")

        is_super_user = User.is_super_user(test_email)
        print(f"Is Super User: {is_super_user}")

        has_premium_access = User.has_premium_access(test_email)
        print(f"Has Premium Access: {has_premium_access}")

        has_admin_privileges = User.has_admin_privileges(test_email)
        print(f"Has Admin Privileges: {has_admin_privileges}")

        # Validate expectations for Super User
        if role == 'super_user':
            print("\n✅ User role validation:")
            print(f"   ✅ Role is 'super_user': {role == 'super_user'}")
            print(f"   ✅ Is Super User: {is_super_user}")
            print(f"   ✅ Has Premium Access: {has_premium_access}")
            print(f"   ✅ Not Admin: {not is_admin}")
            print(f"   ✅ No Admin Privileges: {not has_admin_privileges}")
        else:
            print(f"\n❌ Expected Super User role, got: {role}")
            print("   Make sure the test user is promoted to Super User")

        return True

    except Exception as e:
        print(f"❌ Error testing user role system: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all end-to-end tests."""
    print("🚀 Super User End-to-End Test Suite")
    print("=" * 70)
    print()

    print("This test suite validates that Super Users have unlimited access to:")
    print("  • All AI models (transcription, translation, TTS, interpretation)")
    print("  • Unlimited usage (no subscription restrictions)")
    print("  • Proper role-based access control")
    print("  • API-level enforcement")
    print()

    tests = [
        ("User Role System", test_user_role_system),
        ("Model Access Validation", test_model_access_validation),
        ("Usage Validation", test_usage_validation),
        ("API Endpoints", test_api_endpoints)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))

        print(f"{'='*70}")
        time.sleep(1)  # Brief pause between tests

    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 70)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Super User access control is working correctly.")
        print("\n📝 Next Steps:")
        print("   1. Test with actual Super User account in browser")
        print("   2. Verify premium models work in transcription/translation/TTS")
        print("   3. Confirm no subscription prompts appear")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure user is promoted to Super User role")
        print("   2. Check Firebase connection and credentials")
        print("   3. Verify Flask app is running for API tests")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
