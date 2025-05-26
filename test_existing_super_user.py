#!/usr/bin/env python3
"""
Test existing Super User functionality
"""

import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_existing_super_user(email):
    """Test an existing Super User's functionality."""
    print(f"🧪 Testing Super User functionality for: {email}")
    print("=" * 60)

    try:
        from models.firebase_models import User
        from services.model_access_service import ModelAccessService
        from services.usage_validation_service import UsageValidationService

        # Test role methods
        print("👤 Testing User Role Methods:")
        role = User.get_user_role(email)
        is_super_user = User.is_super_user(email)
        has_premium_access = User.has_premium_access(email)
        is_admin = User.is_admin(email)

        print(f"  Role: {role}")
        print(f"  Is Super User: {is_super_user}")
        print(f"  Has Premium Access: {has_premium_access}")
        print(f"  Is Admin: {is_admin}")

        if role != 'super_user':
            print(f"❌ Expected 'super_user', got '{role}'")
            return False

        # Test model access
        print(f"\n🤖 Testing Model Access:")
        premium_models = [
            'gpt-4o-mini-transcribe',
            'gpt-4o-transcribe',
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4.1-mini',
            'gemini-2.5-flash',
            'gemini-2.5-flash-tts',
            'openai'
        ]

        all_accessible = True
        for model in premium_models:
            access_info = ModelAccessService.can_access_model(model, email)
            status = "✅" if access_info['allowed'] else "❌"
            print(f"  {model}: {status} {access_info['reason']}")
            if not access_info['allowed']:
                all_accessible = False

        # Test usage validation
        print(f"\n📊 Testing Usage Validation:")

        test_cases = [
            ('Transcription', UsageValidationService.validate_transcription_usage, 1000),
            ('Translation', UsageValidationService.validate_translation_usage, 100000),
            ('TTS', UsageValidationService.validate_tts_usage, 500),
            ('AI Credits', UsageValidationService.validate_ai_usage, 1000)
        ]

        all_unlimited = True
        for service_name, method, amount in test_cases:
            result = method(email, amount)
            status = "✅" if result['allowed'] else "❌"
            plan_type = result.get('plan_type', 'unknown')
            message = result.get('message', 'No message')

            print(f"  {service_name} ({amount}): {status}")
            print(f"    Plan Type: {plan_type}")
            print(f"    Message: {message}")

            if not result['allowed'] or plan_type != 'unlimited':
                all_unlimited = False

        # Summary
        print(f"\n📋 Test Summary:")
        print(f"  ✅ Role is Super User: {role == 'super_user'}")
        print(f"  ✅ All premium models accessible: {all_accessible}")
        print(f"  ✅ All services have unlimited access: {all_unlimited}")

        success = (role == 'super_user') and all_accessible and all_unlimited

        if success:
            print(f"\n🎉 All tests passed! {email} has full Super User privileges")
        else:
            print(f"\n❌ Some tests failed. Super User access may not be working correctly")

        return success

    except Exception as e:
        print(f"❌ Error testing Super User functionality: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test existing Super Users."""
    print("🔍 Testing Existing Super Users")
    print("=" * 60)

    # Known Super Users from the previous output
    super_users = [
        'addankianitha28@gmail.com',
        'bobirnacr@gmail.com'
    ]

    results = []

    for email in super_users:
        print(f"\n{'='*60}")
        success = test_existing_super_user(email)
        results.append((email, success))
        print(f"{'='*60}")

    # Summary
    print(f"\n📊 Overall Test Results:")
    print("=" * 60)

    passed = 0
    total = len(results)

    for email, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{email}: {status}")
        if success:
            passed += 1

    print(f"\nOverall: {passed}/{total} Super Users working correctly")

    if passed == total:
        print("\n🎉 All Super Users have correct backend functionality!")
        print("\n📝 Next Steps:")
        print("   1. Login to VocalLocal with one of these Super User accounts")
        print("   2. Test premium model selection in the UI")
        print("   3. Verify no subscription prompts appear")
        print("   4. Test actual transcription/translation/TTS with premium models")
        print("\n🔧 If frontend issues persist, check:")
        print("   - Browser console for JavaScript errors")
        print("   - Network tab for failed API calls")
        print("   - Authentication cookies/session")
    else:
        print("\n❌ Some Super Users don't have correct backend functionality")
        print("   Check Firebase role data and backend implementation")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
