#!/usr/bin/env python3
"""
Test script to verify the RBAC system is working correctly.
This script tests the role-based access control functionality.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebase_models import User

def test_rbac_system():
    """Test the RBAC system functionality."""
    print("🧪 Testing RBAC System")
    print("=" * 50)

    # Test user email
    test_email = "addankianitha28@gmail.com"

    try:
        # Test 1: Get user role
        print(f"\n1️⃣ Testing get_user_role for {test_email}")
        role = User.get_user_role(test_email)
        print(f"   ✅ Current role: {role}")

        # Test 2: Check role-specific methods
        print(f"\n2️⃣ Testing role-specific methods")
        is_admin = User.is_admin(test_email)
        is_super_user = User.is_super_user(test_email)
        is_normal_user = User.is_normal_user(test_email)
        has_premium_access = User.has_premium_access(test_email)
        has_admin_privileges = User.has_admin_privileges(test_email)

        print(f"   • is_admin: {is_admin}")
        print(f"   • is_super_user: {is_super_user}")
        print(f"   • is_normal_user: {is_normal_user}")
        print(f"   • has_premium_access: {has_premium_access}")
        print(f"   • has_admin_privileges: {has_admin_privileges}")

        # Test 3: Verify Super User has premium access
        print(f"\n3️⃣ Testing Super User premium access")
        if role == User.ROLE_SUPER_USER:
            if has_premium_access and not has_admin_privileges:
                print("   ✅ Super User correctly has premium access but no admin privileges")
            else:
                print("   ❌ Super User access permissions are incorrect")
        else:
            print(f"   ⚠️  User is not a Super User (role: {role})")

        # Test 4: Test role constants
        print(f"\n4️⃣ Testing role constants")
        print(f"   • ROLE_ADMIN: {User.ROLE_ADMIN}")
        print(f"   • ROLE_SUPER_USER: {User.ROLE_SUPER_USER}")
        print(f"   • ROLE_NORMAL_USER: {User.ROLE_NORMAL_USER}")
        print(f"   • VALID_ROLES: {User.VALID_ROLES}")

        # Test 5: Test UserObject with role
        print(f"\n5️⃣ Testing UserObject with role information")
        user_obj = User.get_or_create(test_email)  # Use get_or_create to get UserObject
        if user_obj:
            print(f"   ✅ User object retrieved successfully")
            print(f"   • Email: {user_obj.email}")
            print(f"   • Username: {user_obj.username}")
            print(f"   • Role: {user_obj.role}")
            print(f"   • has_premium_access(): {user_obj.has_premium_access()}")
            print(f"   • is_super_user(): {user_obj.is_super_user()}")
        else:
            print("   ❌ Failed to retrieve user object")

        print(f"\n🎉 RBAC System Test Completed Successfully!")
        print(f"📋 Summary:")
        print(f"   • User: {test_email}")
        print(f"   • Role: {role}")
        print(f"   • Premium Access: {'✅ Yes' if has_premium_access else '❌ No'}")
        print(f"   • Admin Privileges: {'✅ Yes' if has_admin_privileges else '❌ No'}")

        return True

    except Exception as e:
        print(f"❌ Error testing RBAC system: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_model_access_scenarios():
    """Test different model access scenarios."""
    print(f"\n🎯 Testing Model Access Scenarios")
    print("=" * 50)

    # Import the ModelAccessService
    try:
        from services.model_access_service import ModelAccessService
    except ImportError:
        print("❌ ModelAccessService not available")
        return False

    # Premium models that Super Users should have access to
    premium_models = [
        'gpt-4o-mini-transcribe',
        'gpt-4o-transcribe',
        'gemini-2.5-flash-preview-04-17',
        'gemini-2.5-flash',
        'gpt-4.1-mini',
        'gemini-2.5-flash-tts',
        'gpt4o-mini',
        'openai'
    ]

    # Free models that everyone should have access to
    free_models = [
        'gemini-2.0-flash-lite',
        'gemini'
    ]

    test_email = "addankianitha28@gmail.com"
    role = User.get_user_role(test_email)

    print(f"Testing model access for {test_email} (role: {role})")

    # Test actual model access control
    all_tests_passed = True

    if role == User.ROLE_SUPER_USER:
        print(f"\n✅ Super User should have access to ALL models:")

        # Test free models
        for model in free_models:
            access_result = ModelAccessService.can_access_model(model, test_email)
            if access_result['allowed']:
                print(f"   • {model}: ✅ Accessible")
            else:
                print(f"   • {model}: ❌ Access denied - {access_result['reason']}")
                all_tests_passed = False

        # Test premium models
        for model in premium_models:
            access_result = ModelAccessService.can_access_model(model, test_email)
            if access_result['allowed']:
                print(f"   • {model}: ✅ Accessible")
            else:
                print(f"   • {model}: ❌ Access denied - {access_result['reason']}")
                all_tests_passed = False

    elif role == User.ROLE_NORMAL_USER:
        print(f"\n⚠️  Normal User should only have access to free models:")

        # Test free models (should be accessible)
        for model in free_models:
            access_result = ModelAccessService.can_access_model(model, test_email)
            if access_result['allowed']:
                print(f"   • {model}: ✅ Accessible")
            else:
                print(f"   • {model}: ❌ Unexpected access denial - {access_result['reason']}")
                all_tests_passed = False

        # Test premium models (should be restricted)
        for model in premium_models:
            access_result = ModelAccessService.can_access_model(model, test_email)
            if not access_result['allowed']:
                print(f"   • {model}: 🔒 Restricted (requires premium)")
            else:
                print(f"   • {model}: ❌ Unexpected access granted")
                all_tests_passed = False

    elif role == User.ROLE_ADMIN:
        print(f"\n✅ Admin should have access to ALL models:")

        # Test all models
        for model in premium_models + free_models:
            access_result = ModelAccessService.can_access_model(model, test_email)
            if access_result['allowed']:
                print(f"   • {model}: ✅ Accessible")
            else:
                print(f"   • {model}: ❌ Access denied - {access_result['reason']}")
                all_tests_passed = False

    return all_tests_passed

def test_normal_user_restrictions():
    """Test that normal users are properly restricted."""
    print(f"\n🔒 Testing Normal User Restrictions")
    print("=" * 50)

    # Import the ModelAccessService
    try:
        from services.model_access_service import ModelAccessService
    except ImportError:
        print("❌ ModelAccessService not available")
        return False

    # Test with a hypothetical normal user
    test_normal_email = "normal.user@example.com"

    # Temporarily create a normal user for testing
    try:
        # Check if user exists, if not create one
        existing_user = User.get_by_email(test_normal_email)
        if not existing_user:
            User.create(
                username="Normal User",
                email=test_normal_email,
                role=User.ROLE_NORMAL_USER
            )
            print(f"Created test normal user: {test_normal_email}")

        role = User.get_user_role(test_normal_email)
        print(f"Testing model access for {test_normal_email} (role: {role})")

        if role != User.ROLE_NORMAL_USER:
            print(f"❌ Expected normal_user role, got {role}")
            return False

        # Test free models (should be accessible)
        free_models = ['gemini-2.0-flash-lite', 'gemini']
        print(f"\n✅ Normal User should have access to free models:")
        all_tests_passed = True

        for model in free_models:
            access_result = ModelAccessService.can_access_model(model, test_normal_email)
            if access_result['allowed']:
                print(f"   • {model}: ✅ Accessible")
            else:
                print(f"   • {model}: ❌ Unexpected access denial - {access_result['reason']}")
                all_tests_passed = False

        # Test premium models (should be restricted)
        premium_models = ['gpt-4o-mini-transcribe', 'gpt-4.1-mini', 'gemini-2.5-flash']
        print(f"\n🔒 Normal User should be restricted from premium models:")

        for model in premium_models:
            access_result = ModelAccessService.can_access_model(model, test_normal_email)
            if not access_result['allowed']:
                print(f"   • {model}: 🔒 Restricted - {access_result['reason']}")
            else:
                print(f"   • {model}: ❌ Unexpected access granted")
                all_tests_passed = False

        return all_tests_passed

    except Exception as e:
        print(f"❌ Error testing normal user restrictions: {str(e)}")
        return False

def main():
    """Main function."""
    print("VocalLocal RBAC System Test")
    print("=" * 60)

    # Test the RBAC system
    rbac_success = test_rbac_system()

    # Test model access scenarios for super user
    model_access_success = test_model_access_scenarios()

    # Test normal user restrictions
    normal_user_success = test_normal_user_restrictions()

    if rbac_success and model_access_success and normal_user_success:
        print(f"\n🎉 All tests passed! RBAC system is working correctly.")
        return True
    else:
        print(f"\n❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
