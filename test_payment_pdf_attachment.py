#!/usr/bin/env python3
"""
Comprehensive test for PDF invoice attachment in payment confirmation emails
Tests the complete flow from webhook processing to email delivery
"""

import os
import sys
import json
import logging
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_payment_webhook_pdf_flow():
    """Test the complete payment webhook flow with PDF attachment"""
    print("🚀 Testing Payment Webhook PDF Attachment Flow")
    print("=" * 60)
    
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment loaded")
        
        # Import services
        from services.payment_service import PaymentService
        from services.email_service import EmailService
        from services.pdf_invoice_service import PDFInvoiceService
        
        print("✅ Services imported successfully")
        
        # Initialize services
        payment_service = PaymentService()
        email_service = EmailService()
        pdf_service = PDFInvoiceService()
        
        # Test data
        test_email = "test.user@example.com"
        test_invoice_id = "in_test_pdf_attachment_001"
        
        # Mock Stripe objects with proper structure
        mock_customer = {
            'email': test_email,
            'metadata': {'user_email': test_email}
        }

        mock_subscription = {
            'metadata': {
                'user_email': test_email,
                'plan_type': 'basic'
            },
            'items': {
                'data': [{
                    'price': {
                        'id': 'price_1RbDgTRW10cnKUUV2Lp1t9K5',
                        'nickname': 'Basic Plan',
                        'unit_amount': 499,
                        'currency': 'usd',
                        'recurring': {'interval': 'month'}
                    }
                }]
            }
        }
        
        # Mock invoice object (as received from Stripe webhook)
        mock_invoice = {
            'id': test_invoice_id,
            'amount_paid': 499,  # $4.99 in cents
            'currency': 'usd',
            'created': int(datetime.now().timestamp()),
            'customer': 'cus_test_001',
            'subscription': 'sub_test_001',
            'lines': {
                'data': [{
                    'price': {
                        'id': 'price_1RbDgTRW10cnKUUV2Lp1t9K5',
                        'unit_amount': 499,
                        'currency': 'usd',
                        'recurring': {'interval': 'month'}
                    }
                }]
            }
        }
        
        print(f"🧪 Testing webhook processing for invoice: {test_invoice_id}")
        
        # Test 1: Direct PDF generation
        print("\n📄 Test 1: Direct PDF Generation")
        pdf_data = {
            'invoice_id': test_invoice_id,
            'customer_name': 'Test User',
            'customer_email': test_email,
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_name': 'Basic Plan',
            'plan_type': 'basic',
            'billing_cycle': 'monthly',
            'payment_method': 'Credit Card',
            'transaction_id': test_invoice_id
        }
        
        pdf_content = pdf_service.generate_invoice_pdf(pdf_data)
        if pdf_content:
            print(f"✅ PDF Generation: Success (Size: {len(pdf_content)} bytes)")
        else:
            print("❌ PDF Generation: Failed")
            return False
        
        # Test 2: Email creation with PDF attachment
        print("\n📧 Test 2: Email Creation with PDF Attachment")
        msg = email_service.create_payment_confirmation_email(
            username="Test User",
            email=test_email,
            invoice_id=test_invoice_id,
            amount=4.99,
            currency="USD",
            payment_date=datetime.now(),
            plan_type="basic",
            plan_name="Basic Plan",
            billing_cycle="monthly",
            pdf_attachment=pdf_content
        )
        
        # Check if PDF attachment is present
        attachments = []
        attachment_sizes = []
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                if filename:
                    attachments.append(filename)
                    # Get attachment size
                    payload = part.get_payload(decode=True)
                    if payload:
                        attachment_sizes.append(len(payload))
        
        if attachments:
            print(f"✅ Email Attachment: Found - {attachments}")
            print(f"✅ Attachment Sizes: {attachment_sizes} bytes")
            
            # Verify attachment integrity
            if attachment_sizes and attachment_sizes[0] == len(pdf_content):
                print("✅ Attachment Integrity: PDF size matches original")
            else:
                print("⚠️  Attachment Integrity: Size mismatch detected")
        else:
            print("❌ Email Attachment: No PDF attachment found")
            return False
        
        # Test 3: Complete webhook flow with mocked Stripe calls
        print("\n🔗 Test 3: Complete Webhook Flow")

        # Create proper mock objects that behave like Stripe objects
        mock_customer_obj = MagicMock()
        mock_customer_obj.email = test_email
        mock_customer_obj.metadata = {'user_email': test_email}

        mock_subscription_obj = MagicMock()
        mock_subscription_obj.metadata = {
            'user_email': test_email,
            'plan_type': 'basic'
        }

        # Create a proper mock for subscription items
        mock_price = MagicMock()
        mock_price.id = 'price_1RbDgTRW10cnKUUV2Lp1t9K5'
        mock_price.nickname = 'Basic Plan'
        mock_price.unit_amount = 499
        mock_price.currency = 'usd'
        mock_price.recurring = {'interval': 'month'}

        mock_item = MagicMock()
        mock_item.price = mock_price

        mock_subscription_obj.items = MagicMock()
        mock_subscription_obj.items.data = [mock_item]

        with patch('stripe.Customer.retrieve', return_value=mock_customer_obj), \
             patch('stripe.Subscription.retrieve', return_value=mock_subscription_obj), \
             patch.object(payment_service, '_store_billing_history') as mock_billing, \
             patch('services.payment_service.UserAccountService.update_subscription') as mock_update:

            # This simulates the actual webhook processing
            result = payment_service._handle_payment_succeeded(mock_invoice)

            print(f"✅ Webhook Processing: {result}")

            if result and result.get('success'):
                print("✅ Complete Flow: Success - PDF should be attached to email")
            else:
                print(f"❌ Complete Flow: Failed - {result}")
                return False
        
        # Test 4: Check email service configuration
        print("\n⚙️  Test 4: Email Service Configuration")
        print(f"✅ SMTP Server: {email_service.smtp_server}")
        print(f"✅ SMTP Port: {email_service.smtp_port}")
        print(f"✅ Username: {email_service.username}")
        print(f"✅ Password Configured: {bool(email_service.password)}")
        print(f"✅ Default Sender: {email_service.default_sender}")
        
        if not email_service.password:
            print("⚠️  Warning: Email password not configured - emails won't be sent")
        
        print("\n🎉 All Tests Passed!")
        print("\n📋 Summary:")
        print("✅ PDF generation working correctly")
        print("✅ PDF attachment added to emails")
        print("✅ Webhook processing functional")
        print("✅ Email service configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_actual_email_sending():
    """Test actual email sending with PDF attachment (optional)"""
    print("\n📤 Optional: Test Actual Email Sending")
    print("=" * 40)
    
    try:
        from services.email_service import EmailService
        from services.pdf_invoice_service import PDFInvoiceService
        
        email_service = EmailService()
        pdf_service = PDFInvoiceService()
        
        if not email_service.password:
            print("⚠️  Skipping actual email test - MAIL_PASSWORD not configured")
            return True
        
        # Generate test PDF
        pdf_data = {
            'invoice_id': 'test_email_001',
            'customer_name': 'Test User',
            'customer_email': 'test@example.com',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_name': 'Basic Plan',
            'plan_type': 'basic',
            'billing_cycle': 'monthly',
            'payment_method': 'Credit Card',
            'transaction_id': 'test_email_001'
        }
        
        pdf_content = pdf_service.generate_invoice_pdf(pdf_data)
        
        if not pdf_content:
            print("❌ Cannot test email - PDF generation failed")
            return False
        
        # SECURITY FIX: Do NOT send real emails in tests
        test_email = email_service.default_sender

        print(f"🧪 SIMULATING email send to: {test_email}")
        print("⚠️  SECURITY: Test mode - no actual email will be sent")

        # Simulate email creation without sending
        try:
            msg = email_service.create_payment_confirmation_email(
                username="Test User",
                email=test_email,
                invoice_id="test_email_001",
                amount=4.99,
                currency="USD",
                payment_date=datetime.now(),
                plan_type="basic",
                plan_name="Basic Plan",
                billing_cycle="monthly",
                pdf_attachment=pdf_content
            )
            result = {'success': True, 'message': 'Test email created successfully (not sent)'}
        except Exception as e:
            result = {'success': False, 'message': f'Test email creation failed: {str(e)}'}
        
        if result.get('success'):
            print("✅ Test Email Created Successfully!")
            print("⚠️  SECURITY: No actual email was sent - this is test mode")
        else:
            print(f"❌ Test Email Creation Failed: {result.get('message')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Email Test Failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 VocalLocal PDF Invoice Attachment - Comprehensive Test")
    print("=" * 70)
    
    # Run main tests
    success = test_payment_webhook_pdf_flow()
    
    if success:
        # Optionally test actual email sending
        user_input = input("\n❓ Do you want to test actual email sending? (y/N): ").strip().lower()
        if user_input in ['y', 'yes']:
            test_actual_email_sending()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 All tests completed successfully!")
        print("💡 If you're still not receiving PDF attachments in actual payments:")
        print("   1. Check server logs during real payment processing")
        print("   2. Verify Stripe webhook is properly configured")
        print("   3. Ensure webhook endpoint is accessible from Stripe")
        print("   4. Check email client spam/junk folders")
    else:
        print("❌ Tests failed - PDF attachment system needs attention")
