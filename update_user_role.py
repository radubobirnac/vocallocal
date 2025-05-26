#!/usr/bin/env python3
"""
Script to update user role to super_user
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

def update_user_role():
    """Update user role to super_user"""
    try:
        # Initialize Firebase
        from firebase_config import initialize_firebase
        initialize_firebase()
        print("Firebase initialized successfully")

        from models.firebase_models import User

        # The user email you want to update to Super User
        user_email = "addankianitha28@gmail.com"

        print(f"Updating role for user: {user_email}")

        # Check if user exists
        user_data = User.get_by_email(user_email)
        if not user_data:
            print(f"User not found: {user_email}")
            return False

        print(f"Current user data: {user_data}")
        print(f"Current role: {user_data.get('role', 'normal_user')}")

        # Update role to super_user
        success = User.update_user_role(user_email, User.ROLE_SUPER_USER)

        if success:
            print(f"✅ Successfully updated {user_email} to super_user role")

            # Verify the update
            updated_user_data = User.get_by_email(user_email)
            print(f"Updated role: {updated_user_data.get('role', 'normal_user')}")

            return True
        else:
            print(f"❌ Failed to update user role")
            return False

    except Exception as e:
        print(f"Error updating user role: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Update User Role to Super User ===\n")

    success = update_user_role()

    if success:
        print("\n✅ User role update completed successfully!")
    else:
        print("\n❌ User role update failed!")
        sys.exit(1)
