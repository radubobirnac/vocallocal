#!/usr/bin/env python3
"""
Test script to debug payment flow issues
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

def test_stripe_configuration():
    """Test if Stripe is properly configured"""
    print("🔧 Testing Stripe Configuration...")
    
    try:
        import stripe
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        stripe_secret = os.getenv('STRIPE_SECRET_KEY')
        stripe_publishable = os.getenv('STRIPE_PUBLISHABLE_KEY')
        basic_price_id = os.getenv('STRIPE_BASIC_PRICE_ID')
        professional_price_id = os.getenv('STRIPE_PROFESSIONAL_PRICE_ID')
        
        print(f"✅ Stripe Secret Key: {'✓ Found' if stripe_secret else '❌ Missing'}")
        print(f"✅ Stripe Publishable Key: {'✓ Found' if stripe_publishable else '❌ Missing'}")
        print(f"✅ Basic Price ID: {'✓ Found' if basic_price_id else '❌ Missing'}")
        print(f"✅ Professional Price ID: {'✓ Found' if professional_price_id else '❌ Missing'}")
        
        if stripe_secret:
            stripe.api_key = stripe_secret
            
            # Test API connection
            try:
                account = stripe.Account.retrieve()
                print(f"✅ Stripe API Connection: ✓ Connected (Account: {account.id})")
                
                # Test price IDs
                if basic_price_id:
                    try:
                        basic_price = stripe.Price.retrieve(basic_price_id)
                        print(f"✅ Basic Price: ✓ Valid (${basic_price.unit_amount/100:.2f})")
                    except Exception as e:
                        print(f"❌ Basic Price: Invalid - {str(e)}")
                
                if professional_price_id:
                    try:
                        professional_price = stripe.Price.retrieve(professional_price_id)
                        print(f"✅ Professional Price: ✓ Valid (${professional_price.unit_amount/100:.2f})")
                    except Exception as e:
                        print(f"❌ Professional Price: Invalid - {str(e)}")
                        
            except Exception as e:
                print(f"❌ Stripe API Connection: Failed - {str(e)}")
                
    except ImportError:
        print("❌ Stripe module not installed")
    except Exception as e:
        print(f"❌ Stripe configuration error: {str(e)}")

def test_payment_endpoint():
    """Test the payment endpoint directly"""
    print("\n🌐 Testing Payment Endpoint...")
    
    base_url = "http://localhost:5001"
    
    # Test if server is running
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ Server Status: ✓ Running (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Server Status: Not accessible - {str(e)}")
        return
    
    # Test payment endpoint (this will fail without authentication, but we can see the error)
    try:
        payment_data = {
            "plan_type": "basic"
        }
        
        response = requests.post(
            f"{base_url}/payment/create-checkout-session",
            json=payment_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"✅ Payment Endpoint Response: Status {response.status_code}")
        
        if response.status_code == 401:
            print("✅ Authentication Required: ✓ Expected (need to login first)")
        elif response.status_code == 400:
            try:
                error_data = response.json()
                print(f"❌ Payment Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Payment Error: Status 400 - {response.text}")
        else:
            try:
                data = response.json()
                print(f"✅ Payment Response: {json.dumps(data, indent=2)}")
            except:
                print(f"✅ Payment Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Payment Endpoint: Error - {str(e)}")

def test_payment_service_directly():
    """Test the payment service directly"""
    print("\n🔧 Testing Payment Service Directly...")
    
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from services.payment_service import PaymentService
        
        # Initialize payment service
        payment_service = PaymentService()
        print("✅ Payment Service: ✓ Initialized")
        
        # Test checkout session creation
        test_email = "test@example.com"
        test_plan = "basic"
        success_url = "http://localhost:5001/success"
        cancel_url = "http://localhost:5001/cancel"
        
        print(f"🧪 Testing checkout session creation for {test_email}...")
        
        result = payment_service.create_checkout_session(
            user_email=test_email,
            plan_type=test_plan,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        if 'error' in result:
            print(f"❌ Checkout Session: Error - {result['error']}")
        else:
            print(f"✅ Checkout Session: ✓ Created successfully")
            print(f"   Session ID: {result.get('session_id', 'N/A')}")
            print(f"   Checkout URL: {result.get('checkout_url', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Payment Service: Error - {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("🚀 VocalLocal Payment System Diagnostic")
    print("=" * 50)
    
    test_stripe_configuration()
    test_payment_endpoint()
    test_payment_service_directly()
    
    print("\n" + "=" * 50)
    print("🏁 Diagnostic Complete")

if __name__ == "__main__":
    main()
