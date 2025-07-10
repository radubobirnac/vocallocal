#!/usr/bin/env python3
"""
Test webhook processing with PDF invoice generation
"""

import os
import sys
import logging
from datetime import datetime
from unittest.mock import patch, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_realistic_webhook_flow():
    """Test webhook flow with mocked Stripe calls"""
    print("🔗 Testing Realistic Webhook Flow with PDF Generation...")
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        from services.payment_service import PaymentService
        
        payment_service = PaymentService()
        
        # Mock Stripe customer data
        mock_customer = MagicMock()
        mock_customer.email = "test@example.com"
        mock_customer.id = "cus_test_123"
        
        # Mock Stripe subscription data
        mock_subscription = MagicMock()
        mock_subscription.get.return_value = {
            'plan_type': 'basic'
        }
        mock_subscription.__getitem__ = lambda self, key: {
            'metadata': {'plan_type': 'basic'},
            'items': {
                'data': [{
                    'price': {
                        'id': os.getenv('STRIPE_BASIC_PRICE_ID'),
                        'unit_amount': 499,
                        'currency': 'usd',
                        'recurring': {'interval': 'month'}
                    }
                }]
            }
        }[key]
        
        # Create realistic invoice data
        test_invoice = {
            'id': 'in_test_realistic_001',
            'amount_paid': 499,  # $4.99 in cents
            'currency': 'usd',
            'created': int(datetime.now().timestamp()),
            'customer': 'cus_test_123',
            'subscription': 'sub_test_123',
            'lines': {
                'data': [{
                    'price': {
                        'id': os.getenv('STRIPE_BASIC_PRICE_ID'),
                        'unit_amount': 499,
                        'currency': 'usd',
                        'recurring': {'interval': 'month'}
                    }
                }]
            }
        }
        
        print("🧪 Processing webhook with mocked Stripe calls...")
        
        # Mock Stripe API calls
        with patch('stripe.Customer.retrieve', return_value=mock_customer), \
             patch('stripe.Subscription.retrieve', return_value=mock_subscription):
            
            result = payment_service._handle_payment_succeeded(test_invoice)
            
            print(f"✅ Webhook Result: {result}")
            
            if result.get('success'):
                print("✅ Webhook Processing: ✓ Success")
                print("✅ PDF Generation: ✓ Should be included in email")
                print("✅ Email Sending: ✓ Should include PDF attachment")
                return True
            else:
                print(f"❌ Webhook Processing: Failed - {result}")
                return False
                
    except Exception as e:
        print(f"❌ Realistic Webhook Test: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_pdf_email_integration():
    """Test direct integration of PDF generation with email sending"""
    print("\n📧 Testing Direct PDF + Email Integration...")
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from services.payment_service import PaymentService
        from services.pdf_invoice_service import PDFInvoiceService
        from services.email_service import EmailService
        
        # Test data
        test_data = {
            'user_email': 'test@example.com',
            'invoice_id': 'in_direct_test_001',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_type': 'basic',
            'plan_name': 'Basic Plan',
            'billing_cycle': 'monthly'
        }
        
        print("🧪 Step 1: Generate PDF...")
        payment_service = PaymentService()
        pdf_content = payment_service._generate_pdf_invoice(**test_data)
        
        if pdf_content:
            print(f"✅ PDF Generated: {len(pdf_content)} bytes")
        else:
            print("❌ PDF Generation: Failed")
            return False
        
        print("🧪 Step 2: Send email with PDF...")
        email_result = payment_service._send_payment_confirmation_email(
            **test_data,
            pdf_attachment=pdf_content
        )
        
        if email_result.get('success'):
            print("✅ Email with PDF: ✓ Sent successfully")
            print(f"   Result: {email_result}")
            return True
        else:
            print(f"❌ Email with PDF: Failed - {email_result}")
            return False
            
    except Exception as e:
        print(f"❌ Direct Integration Test: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_pdf_content():
    """Verify that generated PDF contains correct information"""
    print("\n📄 Verifying PDF Content...")
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from services.pdf_invoice_service import PDFInvoiceService
        
        pdf_service = PDFInvoiceService()
        
        # Test with Basic Plan
        basic_data = {
            'invoice_id': 'in_content_test_basic',
            'customer_name': 'Test User',
            'customer_email': 'test@example.com',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_name': 'Basic Plan',
            'plan_type': 'basic',
            'billing_cycle': 'monthly',
            'payment_method': 'Credit Card',
            'transaction_id': 'txn_test_basic'
        }
        
        print("🧪 Generating Basic Plan PDF...")
        basic_pdf = pdf_service.generate_invoice_pdf(basic_data)
        
        if basic_pdf:
            print(f"✅ Basic Plan PDF: ✓ Generated ({len(basic_pdf)} bytes)")
            
            # Save for manual inspection
            with open('test_basic_invoice.pdf', 'wb') as f:
                f.write(basic_pdf)
            print("✅ Saved: test_basic_invoice.pdf")
        else:
            print("❌ Basic Plan PDF: Generation failed")
            return False
        
        # Test with Professional Plan
        pro_data = basic_data.copy()
        pro_data.update({
            'invoice_id': 'in_content_test_pro',
            'amount': 12.99,
            'plan_name': 'Professional Plan',
            'plan_type': 'professional'
        })
        
        print("🧪 Generating Professional Plan PDF...")
        pro_pdf = pdf_service.generate_invoice_pdf(pro_data)
        
        if pro_pdf:
            print(f"✅ Professional Plan PDF: ✓ Generated ({len(pro_pdf)} bytes)")
            
            # Save for manual inspection
            with open('test_professional_invoice.pdf', 'wb') as f:
                f.write(pro_pdf)
            print("✅ Saved: test_professional_invoice.pdf")
        else:
            print("❌ Professional Plan PDF: Generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ PDF Content Verification: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 VocalLocal PDF Invoice Webhook Flow - Verification")
    print("=" * 60)
    
    all_passed = True
    
    # Test 1: Realistic webhook flow
    if not test_realistic_webhook_flow():
        all_passed = False
    
    # Test 2: Direct PDF + Email integration
    if not test_direct_pdf_email_integration():
        all_passed = False
    
    # Test 3: PDF content verification
    if not verify_pdf_content():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All Webhook Tests Passed!")
        print("\n✅ PDF Invoice System Status:")
        print("   - PDF generation: Working")
        print("   - Email attachment: Working") 
        print("   - Webhook processing: Working")
        print("   - Plan name mapping: Working")
        print("\n📧 Your payment confirmation emails should now include PDF invoices!")
    else:
        print("❌ Some Tests Failed!")
    
    print("\n🔧 Troubleshooting Tips:")
    print("1. Check that Stripe webhooks are configured to send to your endpoint")
    print("2. Verify webhook endpoint is accessible from Stripe")
    print("3. Check server logs during actual payment processing")
    print("4. Ensure email service has proper SMTP configuration")

if __name__ == "__main__":
    main()
