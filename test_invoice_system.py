#!/usr/bin/env python3
"""
Comprehensive test for VocalLocal invoice generation and delivery system.
Tests payment webhook handling, email delivery, and billing history storage.
"""

import os
import sys
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch

# Add the vocallocal directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_payment_service_import():
    """Test that payment service can be imported successfully"""
    print("🔍 Testing Payment Service Import...")
    try:
        from services.payment_service import PaymentService
        print("✅ PaymentService imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import PaymentService: {e}")
        return False

def test_email_service_import():
    """Test that email service can be imported successfully"""
    print("🔍 Testing Email Service Import...")
    try:
        from services.email_service import email_service
        print("✅ EmailService imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import EmailService: {e}")
        return False

def test_payment_confirmation_email_creation():
    """Test payment confirmation email creation"""
    print("🔍 Testing Payment Confirmation Email Creation...")
    try:
        from services.email_service import email_service
        
        # Test data
        test_data = {
            'username': 'John Doe',
            'email': 'john.doe@example.com',
            'invoice_id': 'in_test123456789',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_type': 'basic',
            'plan_name': 'Basic Plan',
            'billing_cycle': 'monthly'
        }
        
        # Create email
        msg = email_service.create_payment_confirmation_email(**test_data)
        
        # Validate email structure
        assert msg['Subject'] == 'Payment Confirmation - VocalLocal Basic Plan'
        assert msg['To'] == 'john.doe@example.com'
        assert msg['From'] == email_service.default_sender
        
        # Check that email has both HTML and text parts
        parts = msg.get_payload()
        assert len(parts) == 2, "Email should have both text and HTML parts"
        
        # Validate content contains key information
        # The content might be base64 encoded, so we need to decode it
        html_content = parts[1].get_payload()
        if parts[1].get('Content-Transfer-Encoding') == 'base64':
            import base64
            html_content = base64.b64decode(html_content).decode('utf-8')

        assert 'in_test123456789' in html_content, "Invoice ID should be in email"
        assert 'USD 4.99' in html_content, "Amount should be in email"
        assert 'Basic Plan' in html_content, "Plan name should be in email"
        
        print("✅ Payment confirmation email created successfully")
        print(f"   Subject: {msg['Subject']}")
        print(f"   To: {msg['To']}")
        print(f"   Parts: {len(parts)} (text + HTML)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create payment confirmation email: {e}")
        return False

def test_webhook_payment_succeeded_handler():
    """Test the webhook payment succeeded handler"""
    print("🔍 Testing Webhook Payment Succeeded Handler...")
    try:
        from services.payment_service import PaymentService
        
        # Mock Stripe objects
        mock_invoice = {
            'id': 'in_test123456789',
            'amount_paid': 499,  # $4.99 in cents
            'currency': 'usd',
            'created': int(time.time()),
            'customer': 'cus_test123',
            'subscription': 'sub_test123'
        }
        
        mock_customer = Mock()
        mock_customer.email = 'test@example.com'
        
        mock_subscription = Mock()
        mock_subscription.get.return_value = {'plan_type': 'basic'}
        mock_subscription.__getitem__ = lambda self, key: {'items': {'data': [{'price': {'id': 'price_basic'}}]}}[key]
        
        # Create payment service instance
        payment_service = PaymentService()
        
        # Mock Stripe API calls
        with patch('stripe.Customer.retrieve', return_value=mock_customer), \
             patch('stripe.Subscription.retrieve', return_value=mock_subscription), \
             patch.object(payment_service, '_store_billing_history') as mock_store, \
             patch.object(payment_service, '_send_payment_confirmation_email') as mock_email:
            
            # Mock successful email sending
            mock_email.return_value = {'success': True, 'message': 'Email sent'}
            
            # Test the handler
            result = payment_service._handle_payment_succeeded(mock_invoice)
            
            # Validate results
            assert result['success'] == True, "Handler should return success"
            assert 'Payment processed and email sent' in result['message']
            
            # Verify billing history was stored
            mock_store.assert_called_once()
            
            # Verify email was sent
            mock_email.assert_called_once()
            
            print("✅ Webhook payment succeeded handler working correctly")
            print(f"   Result: {result}")
            return True
            
    except Exception as e:
        print(f"❌ Failed webhook payment succeeded test: {e}")
        return False

def test_billing_history_storage():
    """Test billing history storage functionality"""
    print("🔍 Testing Billing History Storage...")
    try:
        from services.payment_service import PaymentService
        from services.user_account_service import UserAccountService
        
        payment_service = PaymentService()
        
        # Test billing data
        test_billing_data = {
            'invoiceId': 'in_test123456789',
            'amount': 4.99,
            'currency': 'USD',
            'paymentDate': int(time.time() * 1000),
            'planType': 'basic',
            'planName': 'Basic Plan',
            'billingCycle': 'monthly',
            'status': 'paid'
        }
        
        # Mock Firebase operations
        with patch.object(UserAccountService, 'get_ref') as mock_ref:
            mock_billing_ref = Mock()
            mock_ref.return_value = mock_billing_ref
            
            # Test storage
            payment_service._store_billing_history('test@example.com', test_billing_data)
            
            # Verify Firebase was called correctly
            mock_ref.assert_called_with('users/test@example,com/billing/invoices')
            mock_billing_ref.push.assert_called_once_with(test_billing_data)
            
            print("✅ Billing history storage working correctly")
            return True
            
    except Exception as e:
        print(f"❌ Failed billing history storage test: {e}")
        return False

def test_plan_name_mapping():
    """Test plan name mapping from Stripe price IDs"""
    print("🔍 Testing Plan Name Mapping...")
    try:
        from services.payment_service import PaymentService
        
        payment_service = PaymentService()
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'STRIPE_BASIC_PRICE_ID': 'price_basic_test',
            'STRIPE_PROFESSIONAL_PRICE_ID': 'price_pro_test'
        }):
            # Test basic plan mapping
            basic_price = {'id': 'price_basic_test'}
            basic_name = payment_service._get_plan_name_from_price(basic_price)
            assert basic_name == 'Basic Plan', f"Expected 'Basic Plan', got '{basic_name}'"
            
            # Test professional plan mapping
            pro_price = {'id': 'price_pro_test'}
            pro_name = payment_service._get_plan_name_from_price(pro_price)
            assert pro_name == 'Professional Plan', f"Expected 'Professional Plan', got '{pro_name}'"
            
            # Test fallback for unknown price
            unknown_price = {'id': 'price_unknown', 'unit_amount': 999, 'currency': 'usd'}
            unknown_name = payment_service._get_plan_name_from_price(unknown_price)
            assert 'USD 9.99 Plan' in unknown_name, f"Expected fallback name, got '{unknown_name}'"
            
            print("✅ Plan name mapping working correctly")
            print(f"   Basic: {basic_name}")
            print(f"   Professional: {pro_name}")
            print(f"   Fallback: {unknown_name}")
            return True
            
    except Exception as e:
        print(f"❌ Failed plan name mapping test: {e}")
        return False

def run_all_tests():
    """Run all invoice system tests"""
    print("🚀 Starting VocalLocal Invoice System Tests")
    print("=" * 60)
    
    tests = [
        test_payment_service_import,
        test_email_service_import,
        test_payment_confirmation_email_creation,
        test_webhook_payment_succeeded_handler,
        test_billing_history_storage,
        test_plan_name_mapping
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All invoice system tests passed!")
        print("\n✅ Invoice generation and delivery system is working correctly")
        print("\n📝 Next Steps:")
        print("   1. Test with actual Stripe webhook events")
        print("   2. Verify email delivery in production")
        print("   3. Test billing history in user dashboard")
    else:
        print("❌ Some tests failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
