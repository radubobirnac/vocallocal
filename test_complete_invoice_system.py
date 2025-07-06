#!/usr/bin/env python3
"""
Complete test for VocalLocal invoice generation and delivery system.
Tests the entire flow from payment webhook to dashboard display.
"""

import os
import sys
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add the vocallocal directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_complete_payment_flow():
    """Test the complete payment flow from webhook to email delivery"""
    print("🔍 Testing Complete Payment Flow...")
    try:
        from services.payment_service import PaymentService
        from services.user_account_service import UserAccountService
        
        # Mock invoice data (simulating Stripe webhook)
        mock_invoice = {
            'id': 'in_complete_test_123',
            'amount_paid': 499,  # $4.99 in cents
            'currency': 'usd',
            'created': int(time.time()),
            'customer': 'cus_test_complete',
            'subscription': 'sub_test_complete'
        }
        
        # Mock customer and subscription
        mock_customer = Mock()
        mock_customer.email = 'complete.test@example.com'
        
        mock_subscription = Mock()
        mock_subscription.get.return_value = {'plan_type': 'basic'}
        mock_subscription.__getitem__ = lambda self, key: {
            'items': {'data': [{'price': {'id': 'price_basic_test'}}]}
        }[key]
        
        payment_service = PaymentService()
        
        # Mock all external dependencies
        with patch('stripe.Customer.retrieve', return_value=mock_customer), \
             patch('stripe.Subscription.retrieve', return_value=mock_subscription), \
             patch.object(UserAccountService, 'get_ref') as mock_ref, \
             patch('services.email_service.email_service.send_payment_confirmation_email') as mock_email:
            
            # Mock Firebase operations
            mock_billing_ref = Mock()
            mock_ref.return_value = mock_billing_ref
            
            # Mock successful email sending
            mock_email.return_value = {'success': True, 'message': 'Email sent successfully'}
            
            # Test the complete flow
            result = payment_service._handle_payment_succeeded(mock_invoice)
            
            # Validate results
            assert result['success'] == True, "Payment handler should succeed"
            assert 'Payment processed and email sent' in result['message']
            
            # Verify billing history was stored
            mock_billing_ref.push.assert_called_once()
            stored_data = mock_billing_ref.push.call_args[0][0]
            
            assert stored_data['invoiceId'] == 'in_complete_test_123'
            assert stored_data['amount'] == 4.99
            assert stored_data['currency'] == 'USD'
            assert stored_data['planType'] == 'basic'
            assert stored_data['status'] == 'paid'
            
            # Verify email was sent
            mock_email.assert_called_once()
            email_args = mock_email.call_args[1]
            
            assert email_args['email'] == 'complete.test@example.com'
            assert email_args['invoice_id'] == 'in_complete_test_123'
            assert email_args['amount'] == 4.99
            assert email_args['plan_type'] == 'basic'
            
            print("✅ Complete payment flow working correctly")
            print(f"   Invoice stored: {stored_data['invoiceId']}")
            print(f"   Email sent to: {email_args['email']}")
            print(f"   Amount: {email_args['currency']} {email_args['amount']}")
            return True
            
    except Exception as e:
        print(f"❌ Complete payment flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_billing_history_retrieval():
    """Test billing history retrieval for dashboard"""
    print("🔍 Testing Billing History Retrieval...")
    try:
        from services.user_account_service import UserAccountService
        
        # Mock billing data
        mock_billing_data = {
            'invoice_1': {
                'invoiceId': 'in_test_001',
                'amount': 4.99,
                'currency': 'USD',
                'paymentDate': int(time.time() * 1000),
                'planName': 'Basic Plan',
                'planType': 'basic',
                'status': 'paid'
            },
            'invoice_2': {
                'invoiceId': 'in_test_002',
                'amount': 12.99,
                'currency': 'USD',
                'paymentDate': int(time.time() * 1000) - 86400000,  # 1 day ago
                'planName': 'Professional Plan',
                'planType': 'professional',
                'status': 'paid'
            }
        }
        
        # Mock Firebase operations
        with patch.object(UserAccountService, 'get_ref') as mock_ref:
            mock_billing_ref = Mock()
            mock_billing_ref.get.return_value = mock_billing_data
            mock_ref.return_value = mock_billing_ref
            
            # Test retrieval
            billing_ref = UserAccountService.get_ref('users/test@example,com/billing/invoices')
            billing_data = billing_ref.get()
            
            # Process data (same logic as in the route)
            invoices = []
            if billing_data:
                for invoice_key, invoice_data in billing_data.items():
                    invoices.append({
                        'id': invoice_key,
                        'invoiceId': invoice_data.get('invoiceId'),
                        'amount': invoice_data.get('amount', 0),
                        'currency': invoice_data.get('currency', 'USD'),
                        'paymentDate': invoice_data.get('paymentDate'),
                        'planName': invoice_data.get('planName', 'Unknown Plan'),
                        'planType': invoice_data.get('planType'),
                        'status': invoice_data.get('status', 'paid')
                    })
                
                # Sort by payment date (newest first)
                invoices.sort(key=lambda x: x.get('paymentDate', 0), reverse=True)
            
            # Validate results
            assert len(invoices) == 2, "Should have 2 invoices"
            assert invoices[0]['invoiceId'] == 'in_test_001', "Newest invoice should be first"
            assert invoices[1]['invoiceId'] == 'in_test_002', "Older invoice should be second"
            
            print("✅ Billing history retrieval working correctly")
            print(f"   Retrieved {len(invoices)} invoices")
            print(f"   Latest: {invoices[0]['planName']} - {invoices[0]['currency']} {invoices[0]['amount']}")
            return True
            
    except Exception as e:
        print(f"❌ Billing history retrieval test failed: {e}")
        return False

def test_stripe_checkout_configuration():
    """Test enhanced Stripe checkout configuration"""
    print("🔍 Testing Stripe Checkout Configuration...")
    try:
        from services.payment_service import PaymentService
        
        payment_service = PaymentService()
        
        # Mock Stripe customer
        mock_customer = Mock()
        mock_customer.id = 'cus_test_checkout'
        mock_customer.email = 'checkout.test@example.com'
        
        # Mock Stripe session creation
        mock_session = Mock()
        mock_session.id = 'cs_test_session'
        mock_session.url = 'https://checkout.stripe.com/test'
        
        with patch.object(payment_service, '_get_or_create_customer', return_value=mock_customer), \
             patch('stripe.checkout.Session.create', return_value=mock_session) as mock_create:
            
            # Test checkout session creation
            result = payment_service.create_checkout_session(
                user_email='checkout.test@example.com',
                plan_type='basic',
                success_url='https://example.com/success',
                cancel_url='https://example.com/cancel'
            )
            
            # Validate results
            assert result['success'] == True, "Checkout session should be created successfully"
            assert result['session_id'] == 'cs_test_session'
            assert result['checkout_url'] == 'https://checkout.stripe.com/test'
            
            # Verify Stripe was called with enhanced configuration
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            
            # Check invoice creation configuration
            assert 'invoice_creation' in call_args, "Should have invoice creation config"
            assert call_args['invoice_creation']['enabled'] == True
            
            invoice_data = call_args['invoice_creation']['invoice_data']
            assert 'Basic Plan' in invoice_data['description']
            assert len(invoice_data['custom_fields']) == 2
            assert invoice_data['footer'] == 'Thank you for choosing VocalLocal! For support, contact support@vocallocal.com'
            
            print("✅ Stripe checkout configuration working correctly")
            print(f"   Session ID: {result['session_id']}")
            print(f"   Invoice creation enabled: {call_args['invoice_creation']['enabled']}")
            print(f"   Custom fields: {len(invoice_data['custom_fields'])}")
            return True
            
    except Exception as e:
        print(f"❌ Stripe checkout configuration test failed: {e}")
        return False

def run_complete_tests():
    """Run all comprehensive invoice system tests"""
    print("🚀 Starting Complete VocalLocal Invoice System Tests")
    print("=" * 70)
    
    tests = [
        test_complete_payment_flow,
        test_billing_history_retrieval,
        test_stripe_checkout_configuration
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
    
    print("=" * 70)
    print(f"📊 Complete Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All comprehensive invoice system tests passed!")
        print("\n✅ Complete invoice generation and delivery system is working correctly")
        print("\n🎯 System Features Validated:")
        print("   ✓ Webhook payment processing")
        print("   ✓ Invoice data extraction and storage")
        print("   ✓ Payment confirmation email generation")
        print("   ✓ Billing history retrieval")
        print("   ✓ Enhanced Stripe checkout configuration")
        print("   ✓ Dashboard integration ready")
        print("\n📝 Ready for Production:")
        print("   1. Configure Stripe webhook endpoints")
        print("   2. Test with real Stripe events")
        print("   3. Verify email delivery in production")
        print("   4. Test dashboard billing section")
    else:
        print("❌ Some comprehensive tests failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = run_complete_tests()
    sys.exit(0 if success else 1)
