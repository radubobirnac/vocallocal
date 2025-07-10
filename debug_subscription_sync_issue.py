#!/usr/bin/env python3
"""
Comprehensive diagnostic script to debug subscription synchronization issues
between Firebase and Stripe
"""

import os
import sys
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_firebase_subscription_data(user_email):
    """Check Firebase subscription data for a specific user"""
    print(f"🔍 Checking Firebase Subscription Data for {user_email}...")
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from services.user_account_service import UserAccountService
        
        # Convert email to Firebase key format
        user_id = user_email.replace('.', ',')
        print(f"   Firebase User ID: {user_id}")
        
        # Get complete user account data
        user_account = UserAccountService.get_user_account(user_id)
        
        if user_account:
            print("✅ Firebase User Account: ✓ Found")
            
            # Check subscription data specifically
            if 'subscription' in user_account:
                subscription_data = user_account['subscription']
                print("✅ Firebase Subscription Data: ✓ Found")
                print(f"   Plan Type: {subscription_data.get('planType', 'Not set')}")
                print(f"   Status: {subscription_data.get('status', 'Not set')}")
                print(f"   Start Date: {subscription_data.get('startDate', 'Not set')}")
                print(f"   End Date: {subscription_data.get('endDate', 'Not set')}")
                print(f"   Payment Method: {subscription_data.get('paymentMethod', 'Not set')}")
                print(f"   Billing Cycle: {subscription_data.get('billingCycle', 'Not set')}")
                
                # Check if subscription appears active
                status = subscription_data.get('status', 'inactive')
                plan_type = subscription_data.get('planType', 'free')
                
                if status == 'active' and plan_type in ['basic', 'professional']:
                    print(f"⚠️  Firebase shows ACTIVE {plan_type} subscription!")
                    return True, subscription_data
                else:
                    print(f"✅ Firebase shows {status} {plan_type} subscription (not blocking)")
                    return False, subscription_data
            else:
                print("✅ Firebase Subscription Data: ✓ Not found (clean state)")
                return False, None
        else:
            print("❌ Firebase User Account: Not found")
            return False, None
            
    except Exception as e:
        print(f"❌ Firebase Check Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def test_stripe_subscription_data(user_email):
    """Check Stripe subscription data for a specific user"""
    print(f"\n💳 Checking Stripe Subscription Data for {user_email}...")
    
    try:
        from services.payment_service import PaymentService
        import stripe
        
        payment_service = PaymentService()
        
        # Get Stripe customer
        customer = payment_service.get_customer_by_email(user_email)
        
        if customer:
            print(f"✅ Stripe Customer: ✓ Found (ID: {customer.id})")
            
            # Get all subscriptions for this customer
            subscriptions = stripe.Subscription.list(
                customer=customer.id,
                limit=10
            )
            
            print(f"   Total Subscriptions: {len(subscriptions.data)}")
            
            active_subscriptions = []
            for i, subscription in enumerate(subscriptions.data):
                print(f"\n   Subscription {i+1}:")
                print(f"     ID: {subscription.id}")
                print(f"     Status: {subscription.status}")
                print(f"     Created: {datetime.fromtimestamp(subscription.created)}")
                
                # Check metadata
                metadata = subscription.get('metadata', {})
                plan_type = metadata.get('plan_type', 'unknown')
                print(f"     Plan Type (metadata): {plan_type}")
                
                # Check subscription items for price info
                if subscription.items and subscription.items.data:
                    price = subscription.items.data[0].price
                    print(f"     Price ID: {price.id}")
                    print(f"     Amount: ${price.unit_amount/100:.2f}")
                    
                    # Map price to plan name
                    plan_name = payment_service._get_plan_name_from_price(price)
                    print(f"     Plan Name: {plan_name}")
                
                if subscription.status == 'active':
                    active_subscriptions.append({
                        'id': subscription.id,
                        'status': subscription.status,
                        'plan_type': plan_type,
                        'created': subscription.created
                    })
            
            if active_subscriptions:
                print(f"\n⚠️  Found {len(active_subscriptions)} ACTIVE Stripe subscriptions!")
                return True, active_subscriptions
            else:
                print("\n✅ No active Stripe subscriptions found")
                return False, []
                
        else:
            print("✅ Stripe Customer: ✓ Not found (clean state)")
            return False, []
            
    except Exception as e:
        print(f"❌ Stripe Check Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, []

def test_subscription_checking_logic(user_email):
    """Test the actual subscription checking logic"""
    print(f"\n🔧 Testing Subscription Checking Logic for {user_email}...")
    
    try:
        from services.payment_service import PaymentService
        
        payment_service = PaymentService()
        
        # Test the enhanced subscription checking
        print("🧪 Testing check_existing_subscription() for 'basic' plan...")
        basic_result = payment_service.check_existing_subscription(user_email, 'basic')
        
        print(f"   Basic Plan Check Result:")
        print(f"     Has Subscription: {basic_result.get('has_subscription', 'Unknown')}")
        print(f"     Message: {basic_result.get('message', 'No message')}")
        print(f"     Source: {basic_result.get('source', 'Unknown')}")
        print(f"     Plan Type: {basic_result.get('plan_type', 'Unknown')}")
        print(f"     Current Plan: {basic_result.get('current_plan', 'Unknown')}")
        print(f"     Sync Issue: {basic_result.get('sync_issue', False)}")
        
        print("\n🧪 Testing check_existing_subscription() for 'professional' plan...")
        pro_result = payment_service.check_existing_subscription(user_email, 'professional')
        
        print(f"   Professional Plan Check Result:")
        print(f"     Has Subscription: {pro_result.get('has_subscription', 'Unknown')}")
        print(f"     Message: {pro_result.get('message', 'No message')}")
        print(f"     Source: {pro_result.get('source', 'Unknown')}")
        print(f"     Plan Type: {pro_result.get('plan_type', 'Unknown')}")
        print(f"     Current Plan: {pro_result.get('current_plan', 'Unknown')}")
        print(f"     Sync Issue: {pro_result.get('sync_issue', False)}")
        
        # Determine if either check would block a new subscription
        basic_blocks = basic_result.get('has_subscription', False)
        pro_blocks = pro_result.get('has_subscription', False)
        
        if basic_blocks or pro_blocks:
            print(f"\n⚠️  SUBSCRIPTION BLOCKING DETECTED!")
            print(f"     Basic blocks: {basic_blocks}")
            print(f"     Professional blocks: {pro_blocks}")
            return True, {'basic': basic_result, 'professional': pro_result}
        else:
            print(f"\n✅ No subscription blocking detected")
            return False, {'basic': basic_result, 'professional': pro_result}
            
    except Exception as e:
        print(f"❌ Subscription Logic Test Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, {}

def test_individual_checking_methods(user_email):
    """Test individual Firebase and Stripe checking methods"""
    print(f"\n🔬 Testing Individual Checking Methods for {user_email}...")
    
    try:
        from services.payment_service import PaymentService
        
        payment_service = PaymentService()
        
        # Test Firebase checking
        print("🧪 Testing _check_firebase_subscription()...")
        firebase_result = payment_service._check_firebase_subscription(user_email, 'professional')
        print(f"   Firebase Result: {firebase_result}")
        
        # Test Stripe checking
        print("\n🧪 Testing _check_stripe_subscription()...")
        stripe_result = payment_service._check_stripe_subscription(user_email, 'professional')
        print(f"   Stripe Result: {stripe_result}")
        
        # Test reconciliation
        print("\n🧪 Testing _reconcile_subscription_status()...")
        reconciled_result = payment_service._reconcile_subscription_status(
            firebase_result, stripe_result, user_email, 'professional'
        )
        print(f"   Reconciled Result: {reconciled_result}")
        
        return {
            'firebase': firebase_result,
            'stripe': stripe_result,
            'reconciled': reconciled_result
        }
        
    except Exception as e:
        print(f"❌ Individual Methods Test Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def simulate_payment_attempt(user_email, plan_type):
    """Simulate what happens when user tries to make a payment"""
    print(f"\n💰 Simulating Payment Attempt for {user_email} - {plan_type} plan...")
    
    try:
        from services.payment_service import PaymentService
        
        payment_service = PaymentService()
        
        # This is what the payment route does
        subscription_check = payment_service.check_existing_subscription(user_email, plan_type)
        
        if subscription_check.get('has_subscription'):
            current_plan = subscription_check.get('current_plan') or subscription_check.get('plan_type')
            
            if current_plan == plan_type:
                error_msg = f"You already have an active {plan_type.title()} Plan subscription. Please manage your existing subscription instead."
            else:
                error_msg = f"You already have an active {current_plan.title()} Plan subscription. To change plans, please manage your subscription through the customer portal."
            
            print(f"❌ Payment would be BLOCKED with error:")
            print(f"   '{error_msg}'")
            return False, error_msg
        else:
            print(f"✅ Payment would be ALLOWED")
            return True, "Payment allowed"
            
    except Exception as e:
        print(f"❌ Payment Simulation Error: {str(e)}")
        return False, str(e)

def main():
    """Main diagnostic function"""
    print("🚀 VocalLocal Subscription Synchronization Issue - Diagnostic Tool")
    print("=" * 75)
    
    # Get user email to test
    test_email = input("Enter the user email to debug (or press Enter for default test): ").strip()
    if not test_email:
        test_email = "test@example.com"  # Default test email
    
    print(f"\n🎯 Debugging subscription sync for: {test_email}")
    print("=" * 75)
    
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment: ✓ Loaded from .env file")
    except:
        print("⚠️ Environment: .env file not loaded")
    
    # Run comprehensive tests
    firebase_has_active, firebase_data = test_firebase_subscription_data(test_email)
    stripe_has_active, stripe_data = test_stripe_subscription_data(test_email)
    
    logic_blocks, logic_results = test_subscription_checking_logic(test_email)
    individual_results = test_individual_checking_methods(test_email)
    
    # Test payment simulation
    basic_allowed, basic_msg = simulate_payment_attempt(test_email, 'basic')
    pro_allowed, pro_msg = simulate_payment_attempt(test_email, 'professional')
    
    # Summary
    print("\n" + "=" * 75)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 75)
    
    print(f"Firebase Active Subscription: {firebase_has_active}")
    print(f"Stripe Active Subscription: {stripe_has_active}")
    print(f"Logic Blocks New Subscription: {logic_blocks}")
    print(f"Basic Plan Payment Allowed: {basic_allowed}")
    print(f"Professional Plan Payment Allowed: {pro_allowed}")
    
    if logic_blocks and not (firebase_has_active or stripe_has_active):
        print("\n🚨 SYNC ISSUE DETECTED!")
        print("   Logic is blocking payments but no active subscriptions found in raw data")
        print("   This indicates a synchronization problem in the checking logic")
    elif logic_blocks:
        print("\n⚠️  LEGITIMATE BLOCKING")
        print("   Active subscriptions found - blocking is correct")
    else:
        print("\n✅ NO ISSUES DETECTED")
        print("   System is working correctly")
    
    print("\n🔧 RECOMMENDED ACTIONS:")
    if firebase_has_active and not stripe_has_active:
        print("1. Clear Firebase subscription data completely")
        print("2. Verify Firebase deletion was successful")
    elif stripe_has_active and not firebase_has_active:
        print("1. Cancel Stripe subscription through Stripe dashboard")
        print("2. Or sync Firebase data with Stripe status")
    elif firebase_has_active and stripe_has_active:
        print("1. Cancel subscription through proper channels")
        print("2. Ensure both systems are updated")
    else:
        print("1. Check for caching issues")
        print("2. Verify subscription checking logic")

if __name__ == "__main__":
    main()
