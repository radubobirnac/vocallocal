#!/usr/bin/env python3
"""
Script to promote a user to Super User role for testing the AI model access control system.
This script allows you to set a user's role to 'super_user' in Firebase.
"""

import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def promote_user_to_super_user(email):
    """Promote a user to Super User role."""
    try:
        from models.firebase_models import User
        
        print(f"🔄 Promoting user {email} to Super User role...")
        
        # Check if user exists
        user_data = User.get_by_email(email)
        if not user_data:
            print(f"❌ User {email} not found in Firebase")
            return False
        
        print(f"✅ User found: {user_data.get('username', 'Unknown')}")
        print(f"Current role: {user_data.get('role', 'Not set')}")
        print(f"Current is_admin: {user_data.get('is_admin', False)}")
        
        # Update user role to super_user
        success = User.update_user_role(email, User.ROLE_SUPER_USER)
        
        if success:
            print(f"✅ Successfully promoted {email} to Super User role")
            
            # Verify the change
            updated_user_data = User.get_by_email(email)
            print(f"New role: {updated_user_data.get('role', 'Not set')}")
            print(f"New is_admin: {updated_user_data.get('is_admin', False)}")
            
            # Test role checking methods
            print(f"\nRole verification:")
            print(f"  is_super_user(): {User.is_super_user(email)}")
            print(f"  has_premium_access(): {User.has_premium_access(email)}")
            print(f"  has_admin_privileges(): {User.has_admin_privileges(email)}")
            
            return True
        else:
            print(f"❌ Failed to promote {email} to Super User role")
            return False
            
    except Exception as e:
        print(f"❌ Error promoting user: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def demote_user_to_normal(email):
    """Demote a user back to Normal User role."""
    try:
        from models.firebase_models import User
        
        print(f"🔄 Demoting user {email} to Normal User role...")
        
        # Check if user exists
        user_data = User.get_by_email(email)
        if not user_data:
            print(f"❌ User {email} not found in Firebase")
            return False
        
        print(f"✅ User found: {user_data.get('username', 'Unknown')}")
        print(f"Current role: {user_data.get('role', 'Not set')}")
        
        # Update user role to normal_user
        success = User.update_user_role(email, User.ROLE_NORMAL_USER)
        
        if success:
            print(f"✅ Successfully demoted {email} to Normal User role")
            
            # Verify the change
            updated_user_data = User.get_by_email(email)
            print(f"New role: {updated_user_data.get('role', 'Not set')}")
            print(f"New is_admin: {updated_user_data.get('is_admin', False)}")
            
            return True
        else:
            print(f"❌ Failed to demote {email} to Normal User role")
            return False
            
    except Exception as e:
        print(f"❌ Error demoting user: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def list_users():
    """List all users and their roles."""
    try:
        from models.firebase_models import User
        
        print("📋 Listing all users and their roles...")
        
        users = User.get_all_users()
        if not users:
            print("No users found in Firebase")
            return
        
        print(f"\nFound {len(users)} users:")
        print("-" * 80)
        print(f"{'Email':<30} {'Username':<20} {'Role':<15} {'Admin':<8}")
        print("-" * 80)
        
        for user in users:
            email = user.get('email', 'Unknown')
            username = user.get('username', 'Unknown')
            role = user.get('role', 'Not set')
            is_admin = user.get('is_admin', False)
            
            print(f"{email:<30} {username:<20} {role:<15} {is_admin:<8}")
        
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to handle user input and execute commands."""
    print("🔧 VocalLocal User Role Management Tool")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python promote_user_to_super_user.py <command> [email]")
        print("")
        print("Commands:")
        print("  list                    - List all users and their roles")
        print("  promote <email>         - Promote user to Super User role")
        print("  demote <email>          - Demote user to Normal User role")
        print("")
        print("Examples:")
        print("  python promote_user_to_super_user.py list")
        print("  python promote_user_to_super_user.py promote user@example.com")
        print("  python promote_user_to_super_user.py demote user@example.com")
        return False
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_users()
        return True
    
    elif command == "promote":
        if len(sys.argv) < 3:
            print("❌ Email address required for promote command")
            return False
        
        email = sys.argv[2]
        return promote_user_to_super_user(email)
    
    elif command == "demote":
        if len(sys.argv) < 3:
            print("❌ Email address required for demote command")
            return False
        
        email = sys.argv[2]
        return demote_user_to_normal(email)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: list, promote, demote")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
