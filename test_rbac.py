#!/usr/bin/env python3
"""
Test script for RBAC functionality
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_model_access_service():
    """Test the ModelAccessService functionality"""
    print("Testing ModelAccessService...")

    try:
        from services.model_access_service import ModelAccessService

        # Test with a super user email (from the database)
        test_email = "addankianitha28@gmail.com"

        print(f"Testing access for user: {test_email}")

        # Get available models
        result = ModelAccessService.get_available_models(test_email)

        print("Available models result:")
        print(f"  Accessible models: {result['accessible_models']}")
        print(f"  Restricted models: {result['restricted_models']}")
        print(f"  Restrictions: {result.get('restrictions', 'None')}")

        # Test model validation
        print("\nTesting model validation:")

        # Test free model (should work for everyone)
        validation = ModelAccessService.validate_model_request('gemini-2.0-flash-lite', test_email)
        print(f"  gemini-2.0-flash-lite: {validation}")

        # Test premium model (should work for super users)
        validation = ModelAccessService.validate_model_request('gpt-4o', test_email)
        print(f"  gpt-4o: {validation}")

        return True

    except Exception as e:
        print(f"Error testing ModelAccessService: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_user_role():
    """Test user role functionality"""
    print("\nTesting User role functionality...")

    try:
        from models.firebase_models import User

        # First, list all users to see what's available
        print("Listing all users in database:")
        all_users = User.get_all_users()
        if all_users:
            for user_data in all_users:
                email = user_data.get('email', 'Unknown')
                role = user_data.get('role', 'normal_user')
                print(f"  - {email} (role: {role})")
        else:
            print("  No users found in database")

        # Test getting user by email
        test_email = "addankianitha28@gmail.com"
        user_data = User.get_by_email(test_email)

        if user_data:
            print(f"\nUser found: {user_data.get('email', test_email)}")
            print(f"User role: {user_data.get('role', 'normal_user')}")
            print(f"User name: {user_data.get('username', 'Unknown')}")
        else:
            print(f"\nUser not found: {test_email}")
            # Try with a user that exists
            if all_users:
                test_user_data = all_users[0]
                test_email = test_user_data.get('email', 'Unknown')
                print(f"Testing with existing user: {test_email}")
                print(f"User role: {test_user_data.get('role', 'normal_user')}")

        return True

    except Exception as e:
        print(f"Error testing User role: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_rbac_decorators():
    """Test RBAC decorators"""
    print("\nTesting RBAC decorators...")

    try:
        from models.firebase_models import User

        # Test role checking functions
        test_email = "addankianitha28@gmail.com"

        # Test admin permission
        has_admin = User.is_admin(test_email)
        print(f"  Is admin: {has_admin}")

        # Test super_user permission
        has_super = User.is_super_user(test_email)
        print(f"  Is super_user: {has_super}")

        # Test normal_user permission
        has_normal = User.is_normal_user(test_email)
        print(f"  Is normal_user: {has_normal}")

        # Test premium access
        has_premium = User.has_premium_access(test_email)
        print(f"  Has premium access: {has_premium}")

        return True

    except Exception as e:
        print(f"Error testing RBAC decorators: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== RBAC System Test ===\n")

    # Initialize Firebase first
    try:
        from firebase_config import initialize_firebase
        initialize_firebase()
        print("Firebase initialized successfully\n")
    except Exception as e:
        print(f"Firebase initialization failed: {str(e)}\n")

    # Run tests
    tests = [
        test_user_role,
        test_rbac_decorators,
        test_model_access_service
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with exception: {str(e)}")
            results.append(False)
        print("-" * 50)

    # Summary
    print(f"\nTest Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("✅ All RBAC tests passed!")
    else:
        print("❌ Some RBAC tests failed!")
        sys.exit(1)
