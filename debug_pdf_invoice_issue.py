#!/usr/bin/env python3
"""
Comprehensive diagnostic script to debug PDF invoice attachment issues
"""

import os
import sys
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test all required imports"""
    print("🔍 Testing Imports...")
    
    try:
        import reportlab
        print(f"✅ ReportLab: ✓ Version {reportlab.Version}")
    except ImportError as e:
        print(f"❌ ReportLab: Import failed - {e}")
        return False
    
    try:
        from services.pdf_invoice_service import PDFInvoiceService
        print("✅ PDFInvoiceService: ✓ Import successful")
    except ImportError as e:
        print(f"❌ PDFInvoiceService: Import failed - {e}")
        return False
    
    try:
        from services.email_service import EmailService
        print("✅ EmailService: ✓ Import successful")
    except ImportError as e:
        print(f"❌ EmailService: Import failed - {e}")
        return False
    
    try:
        from services.payment_service import PaymentService
        print("✅ PaymentService: ✓ Import successful")
    except ImportError as e:
        print(f"❌ PaymentService: Import failed - {e}")
        return False
    
    return True

def test_pdf_generation():
    """Test PDF generation in isolation"""
    print("\n📄 Testing PDF Generation...")
    
    try:
        from services.pdf_invoice_service import PDFInvoiceService
        
        pdf_service = PDFInvoiceService()
        
        # Test invoice data
        test_data = {
            'invoice_id': 'in_debug_test_001',
            'customer_name': 'Debug Test User',
            'customer_email': 'debug@test.com',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_name': 'Basic Plan',
            'plan_type': 'basic',
            'billing_cycle': 'monthly',
            'payment_method': 'Credit Card',
            'transaction_id': 'txn_debug_001'
        }
        
        print("🧪 Generating test PDF...")
        pdf_content = pdf_service.generate_invoice_pdf(test_data)
        
        if pdf_content:
            print(f"✅ PDF Generation: ✓ Success (Size: {len(pdf_content)} bytes)")
            
            # Save test PDF for inspection
            test_filename = f"debug_invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            with open(test_filename, 'wb') as f:
                f.write(pdf_content)
            print(f"✅ Test PDF saved: {test_filename}")
            
            return pdf_content
        else:
            print("❌ PDF Generation: Failed - No content returned")
            return None
            
    except Exception as e:
        print(f"❌ PDF Generation: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_email_attachment(pdf_content):
    """Test email attachment functionality"""
    print("\n📧 Testing Email Attachment...")
    
    try:
        from services.email_service import EmailService
        
        email_service = EmailService()
        
        # Test email data
        test_data = {
            'username': 'Debug Test User',
            'email': 'debug@test.com',
            'invoice_id': 'in_debug_test_001',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_type': 'basic',
            'plan_name': 'Basic Plan',
            'billing_cycle': 'monthly',
            'pdf_attachment': pdf_content
        }
        
        print("🧪 Creating email with PDF attachment...")
        msg = email_service.create_payment_confirmation_email(**test_data)
        
        if msg:
            print("✅ Email Creation: ✓ Success")
            
            # Check if PDF attachment is present
            attachments = []
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    attachments.append(part.get_filename())
            
            if attachments:
                print(f"✅ PDF Attachment: ✓ Found - {attachments}")
                
                # Check attachment size
                for part in msg.walk():
                    if part.get_content_disposition() == 'attachment' and 'pdf' in part.get_content_type():
                        attachment_size = len(part.get_payload(decode=True))
                        print(f"✅ Attachment Size: {attachment_size} bytes")
                        
                        if attachment_size == len(pdf_content):
                            print("✅ Attachment Integrity: ✓ Size matches original PDF")
                        else:
                            print(f"❌ Attachment Integrity: Size mismatch (original: {len(pdf_content)}, attached: {attachment_size})")
                
                return True
            else:
                print("❌ PDF Attachment: Not found in email")
                return False
        else:
            print("❌ Email Creation: Failed")
            return False
            
    except Exception as e:
        print(f"❌ Email Attachment Test: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_payment_service_integration():
    """Test payment service PDF generation integration"""
    print("\n💳 Testing Payment Service Integration...")
    
    try:
        from services.payment_service import PaymentService
        
        payment_service = PaymentService()
        
        # Test data
        test_email = "debug@test.com"
        test_invoice_id = "in_debug_integration_001"
        
        print("🧪 Testing payment service PDF generation...")
        
        pdf_content = payment_service._generate_pdf_invoice(
            user_email=test_email,
            invoice_id=test_invoice_id,
            amount=4.99,
            currency='USD',
            payment_date=datetime.now(),
            plan_type='basic',
            plan_name='Basic Plan',
            billing_cycle='monthly'
        )
        
        if pdf_content:
            print(f"✅ Payment Service PDF: ✓ Generated (Size: {len(pdf_content)} bytes)")
            
            # Test email sending with PDF
            print("🧪 Testing payment service email sending...")
            
            # Note: This won't actually send email, just test the method
            try:
                email_result = payment_service._send_payment_confirmation_email(
                    user_email=test_email,
                    invoice_id=test_invoice_id,
                    amount=4.99,
                    currency='USD',
                    payment_date=datetime.now(),
                    plan_type='basic',
                    plan_name='Basic Plan',
                    billing_cycle='monthly',
                    pdf_attachment=pdf_content
                )
                
                print(f"✅ Payment Service Email: ✓ Method executed")
                print(f"   Result: {email_result}")
                
                return True
                
            except Exception as e:
                print(f"❌ Payment Service Email: Error - {str(e)}")
                return False
        else:
            print("❌ Payment Service PDF: Generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Payment Service Integration: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def simulate_webhook_event():
    """Simulate a Stripe webhook event to test the full flow"""
    print("\n🔗 Simulating Webhook Event...")
    
    try:
        from services.payment_service import PaymentService
        
        payment_service = PaymentService()
        
        # Mock invoice data (similar to what Stripe would send)
        mock_invoice = {
            'id': 'in_debug_webhook_001',
            'amount_paid': 499,  # $4.99 in cents
            'currency': 'usd',
            'created': int(datetime.now().timestamp()),
            'customer': 'cus_debug_001',
            'subscription': 'sub_debug_001',
            'lines': {
                'data': [{
                    'price': {
                        'id': 'price_debug_basic',
                        'unit_amount': 499,
                        'currency': 'usd',
                        'recurring': {'interval': 'month'}
                    }
                }]
            }
        }
        
        print("🧪 Processing mock webhook event...")
        
        # This would normally be called by the webhook handler
        result = payment_service._handle_payment_succeeded(mock_invoice)
        
        print(f"✅ Webhook Processing: ✓ Completed")
        print(f"   Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook Simulation: Error - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_environment_config():
    """Check environment configuration"""
    print("\n⚙️ Checking Environment Configuration...")
    
    # Check email configuration
    email_vars = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
    for var in email_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print(f"✅ {var}: ✓ Set (hidden)")
            else:
                print(f"✅ {var}: ✓ {value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Check Stripe configuration
    stripe_vars = ['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'STRIPE_BASIC_PRICE_ID', 'STRIPE_PROFESSIONAL_PRICE_ID']
    for var in stripe_vars:
        value = os.getenv(var)
        if value:
            if 'SECRET' in var or 'KEY' in var:
                print(f"✅ {var}: ✓ Set (hidden)")
            else:
                print(f"✅ {var}: ✓ {value}")
        else:
            print(f"❌ {var}: Not set")

def main():
    """Main diagnostic function"""
    print("🚀 VocalLocal PDF Invoice Attachment - Diagnostic Tool")
    print("=" * 65)
    
    # Add current directory to Python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment: ✓ Loaded from .env file")
    except:
        print("⚠️ Environment: .env file not loaded")
    
    # Run all tests
    all_passed = True
    
    # Test 1: Imports
    if not test_imports():
        all_passed = False
    
    # Test 2: PDF Generation
    pdf_content = test_pdf_generation()
    if not pdf_content:
        all_passed = False
    
    # Test 3: Email Attachment (only if PDF generation worked)
    if pdf_content:
        if not test_email_attachment(pdf_content):
            all_passed = False
    
    # Test 4: Payment Service Integration
    if not test_payment_service_integration():
        all_passed = False
    
    # Test 5: Environment Configuration
    check_environment_config()
    
    # Test 6: Webhook Simulation
    if not simulate_webhook_event():
        all_passed = False
    
    print("\n" + "=" * 65)
    if all_passed:
        print("🎉 All Tests Passed! PDF invoice system should be working.")
    else:
        print("❌ Some Tests Failed! Check the errors above.")
    
    print("\n📋 Next Steps:")
    print("1. Check server logs during actual payment processing")
    print("2. Verify Stripe webhook is properly configured")
    print("3. Test with real payment to confirm end-to-end flow")

if __name__ == "__main__":
    main()
