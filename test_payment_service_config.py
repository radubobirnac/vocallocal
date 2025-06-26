#!/usr/bin/env python3
"""
Test Payment Service Configuration
Verifies that all premium models have proper payment route configuration
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔧 Testing Environment Variables...")
    
    required_vars = [
        'STRIPE_PUBLISHABLE_KEY',
        'STRIPE_SECRET_KEY',
        'STRIPE_BASIC_PRICE_ID',
        'STRIPE_PROFESSIONAL_PRICE_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: NOT SET")
        else:
            # Show partial value for security
            if 'KEY' in var:
                display_value = value[:20] + '...' if len(value) > 20 else value
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"\n⚠️  Missing {len(missing_vars)} environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    
    print("✅ All environment variables are set")
    return True

def test_plan_access_control():
    """Test plan access control configuration"""
    print("\n📋 Testing Plan Access Control...")
    
    try:
        from services.plan_access_control import PlanAccessControl
        
        # Test model access matrix
        plan_access = PlanAccessControl.PLAN_MODEL_ACCESS
        
        print("Plan configurations:")
        for plan, services in plan_access.items():
            print(f"  {plan.upper()} Plan:")
            for service, models in services.items():
                print(f"    {service}: {len(models)} models")
                if service == 'tts':
                    print(f"      Models: {models}")
        
        # Test specific models
        test_models = [
            ('gemini-2.5-flash-tts', 'tts'),
            ('gpt4o-mini', 'tts'),
            ('openai', 'tts'),
            ('gpt-4o-mini-transcribe', 'transcription'),
            ('gpt-4o-transcribe', 'transcription')
        ]
        
        print("\nModel access tests:")
        for model, service in test_models:
            restriction_info = PlanAccessControl.get_model_restriction_info(model, service, 'free')
            required_plan = restriction_info.get('required_plan', 'free')
            print(f"  {model} ({service}): requires {required_plan} plan")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import PlanAccessControl: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing plan access control: {e}")
        return False

def test_payment_service():
    """Test payment service configuration"""
    print("\n💳 Testing Payment Service...")
    
    try:
        from services.payment_service import PaymentService
        
        payment_service = PaymentService()
        
        # Test price IDs
        print("Price ID configuration:")
        for plan, price_id in payment_service.price_ids.items():
            if price_id:
                print(f"  ✅ {plan}: {price_id}")
            else:
                print(f"  ❌ {plan}: NOT SET")
        
        # Test if all required price IDs are set
        missing_prices = [plan for plan, price_id in payment_service.price_ids.items() if not price_id]
        
        if missing_prices:
            print(f"\n⚠️  Missing price IDs for: {', '.join(missing_prices)}")
            return False
        
        print("✅ All price IDs are configured")
        return True
        
    except Exception as e:
        print(f"❌ Error testing payment service: {e}")
        return False

def test_stripe_connectivity():
    """Test Stripe API connectivity"""
    print("\n🌐 Testing Stripe API Connectivity...")
    
    try:
        import stripe
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        if not stripe.api_key:
            print("❌ STRIPE_SECRET_KEY not set")
            return False
        
        # Test API call
        account = stripe.Account.retrieve()
        print(f"✅ Connected to Stripe successfully")
        print(f"   Account ID: {account.id}")
        print(f"   Charges enabled: {account.charges_enabled}")
        print(f"   Payouts enabled: {account.payouts_enabled}")
        
        return True
        
    except stripe.error.AuthenticationError:
        print("❌ Stripe authentication failed - check your secret key")
        return False
    except Exception as e:
        print(f"❌ Stripe API connection failed: {str(e)}")
        return False

def test_model_to_payment_mapping():
    """Test that all premium models map to correct payment plans"""
    print("\n🔗 Testing Model-to-Payment Mapping...")
    
    try:
        from services.plan_access_control import PlanAccessControl
        
        # Get all premium models
        all_models = {}
        for plan, services in PlanAccessControl.PLAN_MODEL_ACCESS.items():
            if plan != 'free':  # Skip free models
                for service, models in services.items():
                    for model in models:
                        if model not in all_models:
                            all_models[model] = []
                        all_models[model].append((plan, service))
        
        print("Premium model payment mapping:")
        payment_issues = []
        
        for model, plan_services in all_models.items():
            # Find the minimum required plan
            plans = [ps[0] for ps in plan_services]
            if 'basic' in plans:
                required_plan = 'basic'
            elif 'professional' in plans:
                required_plan = 'professional'
            else:
                required_plan = 'unknown'
            
            # Check if payment route exists
            if required_plan in ['basic', 'professional']:
                print(f"  ✅ {model}: {required_plan} plan → payment route available")
            else:
                print(f"  ❌ {model}: {required_plan} plan → NO payment route")
                payment_issues.append(model)
        
        if payment_issues:
            print(f"\n⚠️  Models without payment routes: {', '.join(payment_issues)}")
            return False
        
        print("✅ All premium models have payment routes")
        return True
        
    except Exception as e:
        print(f"❌ Error testing model mapping: {e}")
        return False

def main():
    """Run all payment configuration tests"""
    print("🚀 VocalLocal Payment Service Configuration Test")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Plan Access Control", test_plan_access_control),
        ("Payment Service", test_payment_service),
        ("Stripe Connectivity", test_stripe_connectivity),
        ("Model-to-Payment Mapping", test_model_to_payment_mapping)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
    
    # Summary
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All payment routes are properly configured!")
    elif passed >= total * 0.8:
        print("⚠️  Most tests passed. Address the issues above.")
    else:
        print("❌ Multiple configuration issues found. Please fix before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
