#!/usr/bin/env python3
"""
Create a test Super User account for immediate testing
"""

import sys
import os
from werkzeug.security import generate_password_hash

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def create_test_super_user():
    """Create a test Super User account."""
    print("🔧 Creating Test Super User Account")
    print("=" * 50)
    
    try:
        from models.firebase_models import User
        
        # Test Super User credentials
        email = "superuser@vocallocal.com"
        username = "SuperUser"
        password = "SuperUser123!"
        
        print(f"Creating Super User account:")
        print(f"  Email: {email}")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
        print(f"  Role: super_user")
        
        # Check if user already exists
        existing_user = User.get_by_email(email)
        if existing_user:
            print(f"✅ User already exists. Updating role to super_user...")
            
            # Update existing user to super_user role
            success = User.update_user_role(email, User.ROLE_SUPER_USER)
            if success:
                print(f"✅ Successfully updated {email} to Super User role")
            else:
                print(f"❌ Failed to update user role")
                return False
        else:
            print(f"Creating new user...")
            
            # Create new user with super_user role
            password_hash = generate_password_hash(password)
            
            try:
                User.create(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    is_admin=False,
                    role=User.ROLE_SUPER_USER  # Explicitly set super_user role
                )
                print(f"✅ Successfully created Super User account")
            except Exception as create_error:
                print(f"❌ Error creating user: {str(create_error)}")
                return False
        
        # Verify the user was created/updated correctly
        print(f"\n🧪 Verifying Super User account...")
        user_data = User.get_by_email(email)
        
        if user_data:
            role = user_data.get('role', 'Not set')
            is_admin = user_data.get('is_admin', False)
            
            print(f"  ✅ User found in Firebase")
            print(f"  Role: {role}")
            print(f"  Is Admin: {is_admin}")
            
            # Test role checking methods
            is_super_user = User.is_super_user(email)
            has_premium_access = User.has_premium_access(email)
            
            print(f"  Is Super User: {is_super_user}")
            print(f"  Has Premium Access: {has_premium_access}")
            
            if role == 'super_user' and is_super_user and has_premium_access:
                print(f"\n🎉 Super User account created successfully!")
                print(f"\n📝 Login Credentials:")
                print(f"   Email: {email}")
                print(f"   Password: {password}")
                print(f"\n🔗 Login URL: http://localhost:5001/auth/login")
                print(f"\n📋 Instructions:")
                print(f"   1. Go to http://localhost:5001/auth/login")
                print(f"   2. Enter the email and password above")
                print(f"   3. You should have unlimited access to all premium models")
                print(f"   4. No subscription prompts should appear")
                
                return True
            else:
                print(f"\n❌ User created but role verification failed")
                print(f"   Expected: role='super_user', is_super_user=True, has_premium_access=True")
                print(f"   Actual: role='{role}', is_super_user={is_super_user}, has_premium_access={has_premium_access}")
                return False
        else:
            print(f"❌ User not found after creation")
            return False
            
    except Exception as e:
        print(f"❌ Error creating Super User: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_super_user_functionality(email):
    """Test the Super User functionality."""
    print(f"\n🧪 Testing Super User Functionality")
    print("=" * 50)
    
    try:
        from services.model_access_service import ModelAccessService
        from services.usage_validation_service import UsageValidationService
        
        # Test model access
        print(f"🤖 Testing Model Access for {email}:")
        premium_models = ['gpt-4o', 'gpt-4o-mini-transcribe', 'gemini-2.5-flash', 'openai']
        
        for model in premium_models:
            access_info = ModelAccessService.can_access_model(model, email)
            status = "✅" if access_info['allowed'] else "❌"
            print(f"  {model}: {status}")
        
        # Test usage validation
        print(f"\n📊 Testing Usage Validation for {email}:")
        
        # Test transcription
        result = UsageValidationService.validate_transcription_usage(email, 1000)
        status = "✅" if result['allowed'] else "❌"
        print(f"  Transcription (1000 min): {status}")
        
        # Test translation
        result = UsageValidationService.validate_translation_usage(email, 100000)
        status = "✅" if result['allowed'] else "❌"
        print(f"  Translation (100k words): {status}")
        
        print(f"\n✅ Backend functionality test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing functionality: {str(e)}")
        return False

def main():
    """Main function."""
    print("🚀 Super User Account Creator")
    print("=" * 60)
    
    # Create the test Super User
    success = create_test_super_user()
    
    if success:
        # Test the functionality
        test_super_user_functionality("superuser@vocallocal.com")
        
        print(f"\n" + "="*60)
        print(f"🎯 READY TO TEST!")
        print(f"="*60)
        print(f"")
        print(f"Login with these credentials:")
        print(f"  📧 Email: superuser@vocallocal.com")
        print(f"  🔑 Password: SuperUser123!")
        print(f"")
        print(f"Expected behavior:")
        print(f"  ✅ All premium models available (no lock icons)")
        print(f"  ✅ No subscription prompts")
        print(f"  ✅ Unlimited usage for all services")
        print(f"  ✅ Can select GPT-4o, Claude, etc.")
        print(f"")
        print(f"If you still see restrictions:")
        print(f"  1. Clear browser cache and cookies")
        print(f"  2. Hard refresh (Ctrl+F5)")
        print(f"  3. Check browser console for errors")
        print(f"  4. Verify you're logged in with the correct account")
        print(f"")
        return True
    else:
        print(f"\n❌ Failed to create Super User account")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
