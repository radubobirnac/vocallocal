#!/usr/bin/env python3
"""
Test script to promote a real user to Super User and verify the promotion worked.
"""

import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def list_all_users():
    """List all users in the system."""
    print("📋 Listing all users in the system...")
    
    try:
        from models.firebase_models import User
        
        # Get all users (this might not work if the method doesn't exist)
        try:
            users = User.get_all_users()
            if users:
                print(f"\nFound {len(users)} users:")
                print("-" * 80)
                print(f"{'Email':<35} {'Username':<20} {'Role':<15} {'Admin':<8}")
                print("-" * 80)
                
                for user in users:
                    email = user.get('email', 'Unknown')
                    username = user.get('username', 'Unknown')
                    role = user.get('role', 'Not set')
                    is_admin = user.get('is_admin', False)
                    
                    print(f"{email:<35} {username:<20} {role:<15} {is_admin:<8}")
                
                print("-" * 80)
                return users
            else:
                print("No users found or method not available")
                return []
        except AttributeError:
            print("get_all_users method not available, trying alternative approach...")
            
            # Try to get users from Firebase directly
            from services.firebase_service import FirebaseService
            firebase_service = FirebaseService()
            users_ref = firebase_service.get_ref('users')
            users_data = users_ref.get()
            
            if users_data:
                print(f"\nFound {len(users_data)} users:")
                print("-" * 80)
                print(f"{'User ID':<35} {'Email':<30} {'Role':<15}")
                print("-" * 80)
                
                for user_id, user_data in users_data.items():
                    email = user_data.get('email', 'Unknown')
                    role = user_data.get('role', 'Not set')
                    
                    print(f"{user_id:<35} {email:<30} {role:<15}")
                
                print("-" * 80)
                return list(users_data.values())
            else:
                print("No users found in Firebase")
                return []
                
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def promote_user_to_super_user(email):
    """Promote a specific user to Super User role."""
    print(f"🔄 Promoting user {email} to Super User role...")
    
    try:
        from models.firebase_models import User
        
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

def test_user_role_after_promotion(email):
    """Test user role functionality after promotion."""
    print(f"\n🧪 Testing role functionality for {email}...")
    
    try:
        from models.firebase_models import User
        from services.model_access_service import ModelAccessService
        from services.usage_validation_service import UsageValidationService
        
        # Test role methods
        role = User.get_user_role(email)
        is_super_user = User.is_super_user(email)
        has_premium_access = User.has_premium_access(email)
        
        print(f"Role: {role}")
        print(f"Is Super User: {is_super_user}")
        print(f"Has Premium Access: {has_premium_access}")
        
        if role != 'super_user':
            print(f"❌ Expected 'super_user', got '{role}'")
            return False
        
        # Test model access
        print(f"\n🤖 Testing model access...")
        premium_models = ['gpt-4o-mini-transcribe', 'gpt-4o', 'gemini-2.5-flash']
        
        for model in premium_models:
            access_info = ModelAccessService.can_access_model(model, email)
            status = "✅" if access_info['allowed'] else "❌"
            print(f"  {model}: {status} {access_info['reason']}")
        
        # Test usage validation
        print(f"\n📊 Testing usage validation...")
        
        # Test transcription
        result = UsageValidationService.validate_transcription_usage(email, 1000)
        status = "✅" if result['allowed'] else "❌"
        print(f"  Transcription (1000 min): {status} {result['message']}")
        
        # Test translation
        result = UsageValidationService.validate_translation_usage(email, 100000)
        status = "✅" if result['allowed'] else "❌"
        print(f"  Translation (100k words): {status} {result['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing role functionality: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to handle user promotion and testing."""
    print("🔧 Super User Promotion and Testing Tool")
    print("=" * 60)
    
    # List all users first
    users = list_all_users()
    
    if not users:
        print("\n❌ No users found. Please ensure:")
        print("   1. Firebase is properly configured")
        print("   2. Users have been created in the system")
        print("   3. Firebase credentials are correct")
        return False
    
    print(f"\n📝 Instructions:")
    print("   1. Choose a user email from the list above")
    print("   2. The script will promote them to Super User")
    print("   3. Test the role functionality")
    print("   4. You can then test in the browser with that user")
    
    # Get user input
    print(f"\n🎯 Enter the email of the user to promote to Super User:")
    print("   (or press Enter to skip promotion and just test an existing Super User)")
    
    email = input("Email: ").strip()
    
    if not email:
        print("No email provided. Exiting...")
        return False
    
    # Validate email format
    if '@' not in email:
        print("❌ Invalid email format")
        return False
    
    # Promote user
    success = promote_user_to_super_user(email)
    
    if not success:
        print("❌ Promotion failed")
        return False
    
    # Test functionality
    test_success = test_user_role_after_promotion(email)
    
    if test_success:
        print(f"\n🎉 Success! User {email} has been promoted to Super User")
        print(f"\n📝 Next Steps:")
        print(f"   1. Login to the VocalLocal app with: {email}")
        print(f"   2. Navigate to transcription/translation/TTS features")
        print(f"   3. Verify that all premium models are available")
        print(f"   4. Confirm no usage limits or subscription prompts appear")
        print(f"   5. Test actual API calls with premium models")
        
        return True
    else:
        print(f"❌ Role testing failed")
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
