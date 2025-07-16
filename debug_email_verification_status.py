#!/usr/bin/env python3
"""
Debug script to check email verification status for users.
This will help diagnose why transcription is returning 403 errors.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.firebase_models import User
from services.email_verification_middleware import EmailVerificationMiddleware

def check_user_verification_status(email):
    """Check verification status for a specific user."""
    print(f"\n=== Checking Email Verification Status for: {email} ===")
    
    try:
        # Get user data
        user_data = User.get_by_email(email)
        if not user_data:
            print(f"❌ User not found: {email}")
            return
        
        print(f"✅ User found: {email}")
        print(f"   - OAuth Provider: {user_data.get('oauth_provider', 'None')}")
        print(f"   - Created: {user_data.get('created_at', 'Unknown')}")
        
        # Check if OAuth user (automatically verified)
        if user_data.get('oauth_provider'):
            print(f"✅ OAuth user - automatically verified")
            return
        
        # Check email verification status
        is_verified = User.is_email_verified(email)
        requires_verification = User.requires_email_verification(email)
        
        print(f"   - Email Verified: {is_verified}")
        print(f"   - Requires Verification: {requires_verification}")
        
        # Check verification middleware status
        verification_status = EmailVerificationMiddleware.check_verification_status(email)
        print(f"   - Middleware Status: {verification_status}")
        
        # Check transcription access
        transcription_access = EmailVerificationMiddleware.check_transcription_access(email)
        print(f"   - Transcription Access: {transcription_access}")
        
        if not transcription_access.get('allowed', False):
            print(f"❌ TRANSCRIPTION BLOCKED: {transcription_access.get('reason', 'Unknown reason')}")
            if transcription_access.get('verification_required'):
                print(f"   📧 Email verification required!")
        else:
            print(f"✅ Transcription access granted")
            
    except Exception as e:
        print(f"❌ Error checking verification status: {str(e)}")
        import traceback
        traceback.print_exc()

def list_recent_users():
    """List recent users and their verification status."""
    print("\n=== Recent Users and Verification Status ===")
    
    try:
        # Get recent users from Firebase
        users_ref = User.get_ref('users')
        users_data = users_ref.order_by_child('created_at').limit_to_last(10).get()
        
        if not users_data:
            print("No users found")
            return
        
        for user_id, user_data in users_data.items():
            email = user_data.get('email', 'No email')
            oauth_provider = user_data.get('oauth_provider', None)
            created_at = user_data.get('created_at', 'Unknown')
            
            print(f"\n📧 {email}")
            print(f"   - User ID: {user_id}")
            print(f"   - Created: {created_at}")
            print(f"   - OAuth: {oauth_provider or 'Manual registration'}")
            
            if oauth_provider:
                print(f"   - Status: ✅ OAuth user (auto-verified)")
            else:
                is_verified = User.is_email_verified(email)
                print(f"   - Status: {'✅ Verified' if is_verified else '❌ Not verified'}")
                
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run diagnostics."""
    print("🔍 Email Verification Status Diagnostic Tool")
    print("=" * 50)
    
    # List recent users first
    list_recent_users()
    
    # Check specific user if provided
    if len(sys.argv) > 1:
        email = sys.argv[1]
        check_user_verification_status(email)
    else:
        print("\n💡 Usage: python debug_email_verification_status.py <email>")
        print("   Example: python debug_email_verification_status.py user@example.com")

if __name__ == "__main__":
    main()
