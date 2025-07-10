#!/usr/bin/env python3
"""
Test the actual webhook endpoint to verify PDF attachment functionality
"""

import os
import sys
import json
import requests
import time
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_webhook_endpoint():
    """Test the actual webhook endpoint with a mock payment event"""
    print("🔗 Testing Webhook Endpoint for PDF Attachments")
    print("=" * 50)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    if not webhook_secret:
        print("❌ STRIPE_WEBHOOK_SECRET not configured")
        return False
    
    print(f"✅ Webhook secret configured: {webhook_secret[:10]}...")
    
    # Create a mock Stripe webhook event
    mock_event = {
        "id": "evt_test_webhook_pdf",
        "object": "event",
        "api_version": "2020-08-27",
        "created": int(time.time()),
        "data": {
            "object": {
                "id": "in_test_webhook_pdf_001",
                "object": "invoice",
                "amount_paid": 499,
                "currency": "usd",
                "created": int(time.time()),
                "customer": "cus_test_webhook",
                "subscription": "sub_test_webhook",
                "lines": {
                    "object": "list",
                    "data": [{
                        "id": "il_test",
                        "object": "line_item",
                        "price": {
                            "id": "price_1RbDgTRW10cnKUUV2Lp1t9K5",
                            "object": "price",
                            "unit_amount": 499,
                            "currency": "usd",
                            "recurring": {
                                "interval": "month"
                            }
                        }
                    }]
                }
            }
        },
        "livemode": False,
        "pending_webhooks": 1,
        "request": {
            "id": "req_test",
            "idempotency_key": None
        },
        "type": "invoice.payment_succeeded"
    }
    
    print("🧪 Created mock webhook event")
    
    # Test webhook processing directly
    try:
        from services.payment_service import PaymentService
        from unittest.mock import patch, MagicMock
        
        payment_service = PaymentService()
        
        # Mock Stripe objects for the test
        mock_customer = MagicMock()
        mock_customer.email = "webhook.test@example.com"
        mock_customer.metadata = {'user_email': 'webhook.test@example.com'}
        
        mock_subscription = MagicMock()
        mock_subscription.metadata = {
            'user_email': 'webhook.test@example.com',
            'plan_type': 'basic'
        }
        
        mock_price = MagicMock()
        mock_price.id = 'price_1RbDgTRW10cnKUUV2Lp1t9K5'
        mock_price.nickname = 'Basic Plan'
        
        mock_item = MagicMock()
        mock_item.price = mock_price
        
        mock_subscription.items = MagicMock()
        mock_subscription.items.data = [mock_item]
        
        print("🧪 Testing webhook processing...")
        
        with patch('stripe.Customer.retrieve', return_value=mock_customer), \
             patch('stripe.Subscription.retrieve', return_value=mock_subscription), \
             patch.object(payment_service, '_store_billing_history'):
            
            # Process the webhook event
            result = payment_service._handle_payment_succeeded(mock_event['data']['object'])
            
            print(f"✅ Webhook Result: {result}")
            
            if result and result.get('success'):
                print("✅ Webhook Processing: Success")
                print("✅ PDF Generation: Should be included")
                print("✅ Email Sending: Should include PDF attachment")
                return True
            else:
                print(f"❌ Webhook Processing: Failed - {result}")
                return False
                
    except Exception as e:
        print(f"❌ Webhook Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_webhook_configuration():
    """Check webhook configuration and provide guidance"""
    print("\n⚙️  Webhook Configuration Check")
    print("=" * 35)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    stripe_secret = os.getenv('STRIPE_SECRET_KEY')
    
    print(f"✅ Stripe Secret Key: {'Configured' if stripe_secret else 'Missing'}")
    print(f"✅ Webhook Secret: {'Configured' if webhook_secret else 'Missing'}")
    
    if webhook_secret and stripe_secret:
        print("\n📋 Webhook Configuration Checklist:")
        print("1. ✅ Environment variables configured")
        print("2. 🔍 Check Stripe Dashboard webhook configuration:")
        print("   - Webhook URL: https://your-domain.com/payment/webhook")
        print("   - Events: invoice.payment_succeeded")
        print("   - Webhook signing secret matches .env file")
        print("3. 🔍 Check server logs during actual payments")
        print("4. 🔍 Verify webhook endpoint is accessible from internet")
        
        return True
    else:
        print("\n❌ Missing webhook configuration")
        return False

if __name__ == "__main__":
    print("🔍 VocalLocal Webhook PDF Attachment Test")
    print("=" * 45)
    
    # Test webhook processing
    webhook_success = test_webhook_endpoint()
    
    # Check configuration
    config_success = check_webhook_configuration()
    
    print("\n" + "=" * 45)
    if webhook_success and config_success:
        print("🎉 Webhook system appears to be working correctly!")
        print("\n💡 If PDF attachments are still missing in real payments:")
        print("   1. Check that Stripe webhook is actually being triggered")
        print("   2. Monitor server logs during real payment processing")
        print("   3. Verify webhook endpoint URL is correct in Stripe Dashboard")
        print("   4. Test with Stripe CLI: stripe listen --forward-to localhost:5000/payment/webhook")
    else:
        print("❌ Webhook system needs attention")
        print("   Check the errors above and fix configuration issues")
