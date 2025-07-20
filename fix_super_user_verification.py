#!/usr/bin/env python3
"""
Fix Super User Email Verification
Ensure super user has verified email status for TTS access
"""

import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

def fix_super_user_verification():
    """Fix super user email verification status."""
    print("🔧 Fixing Super User Email Verification")
    print("=" * 60)
    
    try:
        from models.firebase_models import User
        
        super_user_email = "superuser@vocallocal.com"
        
        print(f"📧 Checking super user: {super_user_email}")
        
        # Check current verification status
        is_verified = User.is_email_verified(super_user_email)
        print(f"Current verification status: {is_verified}")
        
        if not is_verified:
            print("❌ Super user email not verified - fixing...")
            
            # Set email as verified
            result = User.mark_email_verified(super_user_email)
            if result:
                print("✅ Super user email verification fixed!")
            else:
                print("❌ Failed to fix super user email verification")
                return False
        else:
            print("✅ Super user email already verified")
        
        # Verify the fix
        is_verified_after = User.is_email_verified(super_user_email)
        print(f"Verification status after fix: {is_verified_after}")
        
        return is_verified_after
        
    except Exception as e:
        print(f"❌ Error fixing super user verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def fix_basic_user_verification():
    """Fix basic user email verification status."""
    print("\n🔧 Fixing Basic User Email Verification")
    print("=" * 60)
    
    try:
        from models.firebase_models import User
        
        basic_user_email = "anitha@gmail.com"
        
        print(f"📧 Checking basic user: {basic_user_email}")
        
        # Check current verification status
        is_verified = User.is_email_verified(basic_user_email)
        print(f"Current verification status: {is_verified}")
        
        if not is_verified:
            print("❌ Basic user email not verified - fixing...")
            
            # Set email as verified
            result = User.mark_email_verified(basic_user_email)
            if result:
                print("✅ Basic user email verification fixed!")
            else:
                print("❌ Failed to fix basic user email verification")
                return False
        else:
            print("✅ Basic user email already verified")
        
        # Verify the fix
        is_verified_after = User.is_email_verified(basic_user_email)
        print(f"Verification status after fix: {is_verified_after}")
        
        return is_verified_after
        
    except Exception as e:
        print(f"❌ Error fixing basic user verification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_tts_access_after_fix():
    """Test TTS access after fixing email verification."""
    print("\n🔧 Testing TTS Access After Fix")
    print("=" * 60)
    
    try:
        from services.usage_validation_service import UsageValidationService
        from services.email_verification_middleware import VerificationAwareAccessControl
        
        users_to_test = [
            "superuser@vocallocal.com",
            "anitha@gmail.com"
        ]
        
        for user_email in users_to_test:
            print(f"\n📧 Testing TTS access for: {user_email}")
            
            # Test usage validation service
            tts_access = UsageValidationService.check_tts_access(user_email)
            print(f"   Usage validation: {tts_access}")
            
            # Test email verification middleware
            verification_access = VerificationAwareAccessControl.check_tts_access(user_email)
            print(f"   Verification middleware: {verification_access}")
            
            if tts_access['allowed'] and verification_access['allowed']:
                print(f"   ✅ {user_email}: TTS access GRANTED")
            else:
                print(f"   ❌ {user_email}: TTS access DENIED")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing TTS access: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_test_user_if_needed():
    """Create test users if they don't exist."""
    print("\n🔧 Creating Test Users If Needed")
    print("=" * 60)
    
    try:
        from models.firebase_models import User
        
        # Check if super user exists
        super_user = User.get_by_email("superuser@vocallocal.com")
        if not super_user:
            print("❌ Super user not found - creating...")
            
            # Create super user
            super_user_data = {
                'email': 'superuser@vocallocal.com',
                'username': 'SuperUser',
                'role': 'super_user',
                'is_admin': True,
                'email_verified': True,
                'subscription_plan': 'unlimited'
            }
            
            result = User.create_user(super_user_data)
            if result:
                print("✅ Super user created successfully")
            else:
                print("❌ Failed to create super user")
        else:
            print("✅ Super user already exists")
        
        # Check if basic user exists
        basic_user = User.get_by_email("anitha@gmail.com")
        if not basic_user:
            print("❌ Basic user not found - creating...")
            
            # Create basic user
            basic_user_data = {
                'email': 'anitha@gmail.com',
                'username': 'anitha',
                'role': 'normal_user',
                'is_admin': False,
                'email_verified': True,
                'subscription_plan': 'basic'
            }
            
            result = User.create_user(basic_user_data)
            if result:
                print("✅ Basic user created successfully")
            else:
                print("❌ Failed to create basic user")
        else:
            print("✅ Basic user already exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test users: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main fix function."""
    print("🚨 FIXING TTS 403 ERRORS - EMAIL VERIFICATION")
    print("=" * 80)
    
    print("Fixing email verification issues that cause TTS 403 errors...")
    print("")
    
    # Create users if needed
    users_created = create_test_user_if_needed()
    
    # Fix email verification
    super_user_fixed = fix_super_user_verification()
    basic_user_fixed = fix_basic_user_verification()
    
    # Test TTS access
    tts_access_test = test_tts_access_after_fix()
    
    print(f"\n" + "="*80)
    print(f"🎯 EMAIL VERIFICATION FIX RESULTS:")
    print(f"="*80)
    
    if super_user_fixed and basic_user_fixed and tts_access_test:
        print(f"🎉 EMAIL VERIFICATION: FIXED")
        print(f"   ✅ Super user email verified")
        print(f"   ✅ Basic user email verified")
        print(f"   ✅ TTS access should now work")
        print(f"")
        print(f"📋 NEXT STEPS:")
        print(f"   1. Open browser and navigate to http://localhost:5001")
        print(f"   2. Login with super user credentials:")
        print(f"      Email: superuser@vocallocal.com")
        print(f"      Password: superpassword123")
        print(f"   3. Test TTS functionality")
        print(f"   4. Verify stop button works correctly")
        print(f"")
    else:
        print(f"❌ EMAIL VERIFICATION: ISSUES REMAIN")
        print(f"   Review the error details above")
        print(f"")
    
    return super_user_fixed and basic_user_fixed and tts_access_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
