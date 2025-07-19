#!/usr/bin/env python3
"""
Verify the super user's email to enable TTS functionality
"""

import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def verify_super_user_email():
    """Mark the super user's email as verified."""
    print("🔧 Verifying Super User Email")
    print("=" * 50)
    
    try:
        from models.firebase_models import User
        
        # Super User email
        email = "superuser@vocallocal.com"
        
        print(f"Checking email verification status for: {email}")
        
        # Check current status
        is_verified = User.is_email_verified(email)
        print(f"Current verification status: {is_verified}")
        
        if is_verified:
            print("✅ Email is already verified!")
            return True
        
        # Mark email as verified
        print("📧 Marking email as verified...")
        success = User.mark_email_verified(email)
        
        if success:
            print("✅ Successfully marked email as verified!")
            
            # Verify the change
            is_verified_now = User.is_email_verified(email)
            print(f"New verification status: {is_verified_now}")
            
            if is_verified_now:
                print("\n🎉 Super User email verification complete!")
                print("\n📋 You can now:")
                print("  ✅ Use TTS functionality")
                print("  ✅ Access all premium features")
                print("  ✅ No email verification prompts")
                return True
            else:
                print("❌ Verification failed - status not updated")
                return False
        else:
            print("❌ Failed to mark email as verified")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    print("🚀 Super User Email Verification")
    print("=" * 60)
    
    success = verify_super_user_email()
    
    if success:
        print(f"\n" + "="*60)
        print(f"🎯 EMAIL VERIFIED!")
        print(f"="*60)
        print(f"")
        print(f"The super user account is now fully ready:")
        print(f"  📧 Email: superuser@vocallocal.com")
        print(f"  🔑 Password: SuperUser123!")
        print(f"  ✅ Email verified: YES")
        print(f"  ✅ TTS access: ENABLED")
        print(f"")
        print(f"You can now test the interpretation TTS button!")
        print(f"")
        return True
    else:
        print(f"\n❌ Failed to verify super user email")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
