#!/usr/bin/env python3
"""
Debug TTS 403 Forbidden Issues
Comprehensive diagnosis of authentication and access control problems
"""

import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_super_user_status():
    """Check the super user's authentication and verification status."""
    print("🔧 Checking Super User Status")
    print("=" * 60)
    
    try:
        from models.firebase_models import User
        
        super_user_email = "superuser@vocallocal.com"
        
        print(f"📧 Checking user: {super_user_email}")
        
        # Check if user exists
        user_data = User.get_by_email(super_user_email)
        if not user_data:
            print("❌ Super user not found in database!")
            return False
        
        print(f"✅ User found in database")
        print(f"   Username: {user_data.get('username', 'N/A')}")
        print(f"   Role: {user_data.get('role', 'N/A')}")
        print(f"   Is Admin: {user_data.get('is_admin', False)}")
        
        # Check email verification status
        is_verified = User.is_email_verified(super_user_email)
        print(f"   Email Verified: {is_verified}")
        
        # Check if verification is required
        requires_verification = User.requires_email_verification(super_user_email)
        print(f"   Requires Verification: {requires_verification}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking super user: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_tts_access_control():
    """Check TTS access control configuration."""
    print("\n🔧 Checking TTS Access Control")
    print("=" * 60)
    
    try:
        from services.usage_validation_service import UsageValidationService
        
        super_user_email = "superuser@vocallocal.com"
        
        print(f"📧 Testing TTS access for: {super_user_email}")
        
        # Check TTS access
        tts_access = UsageValidationService.check_tts_access(super_user_email)
        print(f"TTS Access Result: {tts_access}")
        
        if tts_access['allowed']:
            print("✅ TTS access is ALLOWED")
            print(f"   Plan Type: {tts_access.get('plan_type', 'N/A')}")
            print(f"   Reason: {tts_access.get('reason', 'N/A')}")
        else:
            print("❌ TTS access is DENIED")
            print(f"   Reason: {tts_access.get('reason', 'N/A')}")
            print(f"   Upgrade Required: {tts_access.get('upgrade_required', False)}")
            print(f"   Message: {tts_access.get('message', 'N/A')}")
        
        return tts_access['allowed']
        
    except Exception as e:
        print(f"❌ Error checking TTS access: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_email_verification_middleware():
    """Check email verification middleware."""
    print("\n🔧 Checking Email Verification Middleware")
    print("=" * 60)
    
    try:
        from services.email_verification_middleware import VerificationAwareAccessControl
        
        super_user_email = "superuser@vocallocal.com"
        
        print(f"📧 Testing email verification for: {super_user_email}")
        
        # Check TTS access through verification middleware
        tts_access = VerificationAwareAccessControl.check_tts_access(super_user_email)
        print(f"Verification Middleware TTS Access: {tts_access}")
        
        if tts_access['allowed']:
            print("✅ Email verification middleware allows TTS access")
        else:
            print("❌ Email verification middleware denies TTS access")
            if tts_access.get('verification_required'):
                print("   Issue: Email verification required")
            
        return tts_access['allowed']
        
    except Exception as e:
        print(f"❌ Error checking email verification middleware: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_plan_access_control():
    """Check plan access control for TTS."""
    print("\n🔧 Checking Plan Access Control")
    print("=" * 60)
    
    try:
        from services.plan_access_control import PlanAccessControl
        
        # Check user plan
        user_plan = PlanAccessControl.get_user_plan()
        print(f"Current User Plan: {user_plan}")
        
        # Check TTS models accessible to different plans
        for plan in ['free', 'basic', 'professional']:
            tts_models = PlanAccessControl.get_accessible_models('tts', plan)
            print(f"{plan.title()} Plan TTS Models: {tts_models}")
        
        # Test TTS model validation
        test_models = ['gemini-2.5-flash-tts', 'gpt4o-mini', 'openai']
        for model in test_models:
            is_allowed, result = PlanAccessControl.validate_model_access(model, 'tts', 'basic')
            status = "✅ ALLOWED" if is_allowed else "❌ DENIED"
            print(f"Basic Plan - {model}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking plan access control: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_tts_endpoint_locally():
    """Test TTS endpoint with authentication simulation."""
    print("\n🔧 Testing TTS Endpoint Authentication Flow")
    print("=" * 60)
    
    try:
        # This would require Flask app context, so we'll just check the logic
        print("📋 TTS Endpoint Authentication Requirements:")
        print("   1. @login_required - User must be logged in")
        print("   2. @requires_verified_email - Email must be verified")
        print("   3. UsageValidationService.check_tts_access() - Plan-based access")
        print("")
        
        # Check each requirement
        user_status = check_super_user_status()
        tts_access = check_tts_access_control()
        email_verification = check_email_verification_middleware()
        
        print(f"\n📊 Authentication Flow Summary:")
        print(f"   User Exists & Authenticated: {'✅' if user_status else '❌'}")
        print(f"   TTS Access Allowed: {'✅' if tts_access else '❌'}")
        print(f"   Email Verification Passed: {'✅' if email_verification else '❌'}")
        
        all_passed = user_status and tts_access and email_verification
        
        if all_passed:
            print(f"\n🎉 All authentication checks PASSED")
            print(f"   TTS requests should work for super user")
        else:
            print(f"\n❌ Authentication checks FAILED")
            print(f"   TTS requests will return 403 Forbidden")
            
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing TTS endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main diagnostic function."""
    print("🚀 TTS 403 Forbidden Issue Diagnosis")
    print("=" * 80)
    
    print("Diagnosing why TTS requests return 403 Forbidden errors...")
    print("")
    
    # Run all diagnostic checks
    user_status = check_super_user_status()
    plan_access = check_plan_access_control()
    endpoint_test = test_tts_endpoint_locally()
    
    print(f"\n" + "="*80)
    if endpoint_test:
        print(f"🎉 DIAGNOSIS COMPLETE: TTS should work")
        print(f"="*80)
        print(f"")
        print(f"All authentication and access control checks passed.")
        print(f"If TTS is still returning 403 errors, the issue may be:")
        print(f"  1. Session/cookie problems in the browser")
        print(f"  2. Different user logged in than expected")
        print(f"  3. Remote deployment configuration differences")
        print(f"")
    else:
        print(f"❌ DIAGNOSIS COMPLETE: TTS access issues found")
        print(f"="*80)
        print(f"")
        print(f"Authentication or access control checks failed.")
        print(f"Review the error details above to identify the specific issue.")
        print(f"")
    
    return endpoint_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
