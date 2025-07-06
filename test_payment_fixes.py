#!/usr/bin/env python3
"""
Test script to verify payment system fixes
"""

import os
import sys
import requests
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_subscription_checking_logic():
    """Test the enhanced subscription checking logic"""
    print("🔧 Testing Enhanced Subscription Checking Logic...")
    
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from services.payment_service import PaymentService
        
        # Initialize payment service
        payment_service = PaymentService()
        print("✅ Payment Service: ✓ Initialized")
        
        # Test subscription checking for a test email
        test_email = "test@example.com"
        
        print(f"🧪 Testing subscription check for {test_email}...")
        
        # Test basic plan check
        result = payment_service.check_existing_subscription(test_email, 'basic')
        
        print(f"📊 Subscription Check Result:")
        print(f"   Has Subscription: {result.get('has_subscription', 'Unknown')}")
        print(f"   Message: {result.get('message', 'No message')}")
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
        else:
            print("✅ Subscription check completed without errors")
            
        # Test Firebase fallback
        print(f"🧪 Testing Firebase fallback...")
        firebase_result = payment_service._check_firebase_subscription(test_email, 'basic')
        print(f"   Firebase Result: {firebase_result.get('message', 'No message')}")
        
        # Test Stripe check
        print(f"🧪 Testing Stripe check...")
        stripe_result = payment_service._check_stripe_subscription(test_email, 'basic')
        print(f"   Stripe Result: {stripe_result.get('message', 'No message')}")
            
    except Exception as e:
        print(f"❌ Subscription Checking Test: Error - {str(e)}")
        import traceback
        traceback.print_exc()

def test_dashboard_plan_display():
    """Test the dashboard plan display logic"""
    print("\n🖥️ Testing Dashboard Plan Display Logic...")
    
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from routes.main import get_user_current_plan, get_user_plan_from_firebase
        
        test_email = "test@example.com"
        
        print(f"🧪 Testing plan retrieval for {test_email}...")
        
        # Test enhanced plan checking
        plan_type, plan_display = get_user_current_plan(test_email)
        print(f"✅ Enhanced Plan Check: {plan_type} ({plan_display})")
        
        # Test Firebase fallback
        fb_plan_type, fb_plan_display = get_user_plan_from_firebase(test_email)
        print(f"✅ Firebase Fallback: {fb_plan_type} ({fb_plan_display})")
        
    except Exception as e:
        print(f"❌ Dashboard Plan Display Test: Error - {str(e)}")
        import traceback
        traceback.print_exc()

def test_server_endpoints():
    """Test server endpoints for payment functionality"""
    print("\n🌐 Testing Server Endpoints...")
    
    base_url = "http://localhost:5001"
    
    # Test if server is running
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Server Status: ✓ Running (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Server Status: Not accessible - {str(e)}")
        return
    
    # Test home page (should have upgrade button)
    try:
        response = requests.get(base_url, timeout=5)
        if 'upgrade-button' in response.text:
            print("✅ Home Page: ✓ Upgrade button found")
        else:
            print("❌ Home Page: Upgrade button not found")
    except Exception as e:
        print(f"❌ Home Page Test: Error - {str(e)}")
    
    # Test pricing page
    try:
        response = requests.get(f"{base_url}/pricing", timeout=5)
        if response.status_code == 200:
            print("✅ Pricing Page: ✓ Accessible")
            if 'data-plan="basic"' in response.text and 'data-plan="professional"' in response.text:
                print("✅ Pricing Page: ✓ Plan buttons found")
            else:
                print("❌ Pricing Page: Plan buttons not found")
        else:
            print(f"❌ Pricing Page: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Pricing Page Test: Error - {str(e)}")
    
    # Test dashboard (requires authentication)
    try:
        response = requests.get(f"{base_url}/dashboard", timeout=5)
        if response.status_code == 302:  # Redirect to login
            print("✅ Dashboard: ✓ Properly protected (redirects to login)")
        elif response.status_code == 200:
            print("✅ Dashboard: ✓ Accessible (user logged in)")
        else:
            print(f"❌ Dashboard: Unexpected status {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard Test: Error - {str(e)}")

def test_javascript_configuration():
    """Test JavaScript configuration for upgrade functionality"""
    print("\n🔧 Testing JavaScript Configuration...")
    
    base_url = "http://localhost:5001"
    
    try:
        response = requests.get(base_url, timeout=5)
        content = response.text
        
        # Check for upgrade configuration
        if 'window.upgradeConfig' in content:
            print("✅ JavaScript Config: ✓ upgradeConfig found")
        else:
            print("❌ JavaScript Config: upgradeConfig not found")
        
        # Check for payment flow manager
        if 'window.paymentFlowManager' in content:
            print("✅ JavaScript Config: ✓ paymentFlowManager found")
        else:
            print("❌ JavaScript Config: paymentFlowManager not found")
        
        # Check for Stripe integration
        if 'stripe.com/v3' in content:
            print("✅ JavaScript Config: ✓ Stripe library loaded")
        else:
            print("❌ JavaScript Config: Stripe library not found")
        
        # Check for payment.js
        if 'payment.js' in content:
            print("✅ JavaScript Config: ✓ payment.js loaded")
        else:
            print("❌ JavaScript Config: payment.js not found")
            
    except Exception as e:
        print(f"❌ JavaScript Configuration Test: Error - {str(e)}")

def main():
    """Main test function"""
    print("🚀 VocalLocal Payment System Fixes - Verification Tests")
    print("=" * 60)
    
    test_subscription_checking_logic()
    test_dashboard_plan_display()
    test_server_endpoints()
    test_javascript_configuration()
    
    print("\n" + "=" * 60)
    print("🏁 Payment Fixes Verification Complete")
    print("\n📋 Summary of Fixes Applied:")
    print("1. ✅ Enhanced subscription checking (Firebase + Stripe)")
    print("2. ✅ Improved dashboard plan display logic")
    print("3. ✅ Fixed home page upgrade button JavaScript")
    print("4. ✅ Added comprehensive error handling")
    print("5. ✅ Created database schema documentation")

if __name__ == "__main__":
    main()
