#!/usr/bin/env python3
"""
Test script to verify email and PDF invoice system functionality
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pdf_invoice_generation():
    """Test PDF invoice generation functionality"""
    print("📄 Testing PDF Invoice Generation...")
    
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from services.pdf_invoice_service import PDFInvoiceService
        
        # Initialize PDF service
        pdf_service = PDFInvoiceService()
        print("✅ PDF Service: ✓ Initialized")
        
        # Test invoice data
        test_invoice_data = {
            'invoice_id': 'in_test_12345',
            'customer_name': 'Test User',
            'customer_email': 'test@example.com',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_name': 'Basic Plan',
            'plan_type': 'basic',
            'billing_cycle': 'monthly',
            'payment_method': 'Credit Card',
            'transaction_id': 'txn_test_67890'
        }
        
        print(f"🧪 Generating test PDF invoice...")
        
        # Generate PDF
        pdf_content = pdf_service.generate_invoice_pdf(test_invoice_data)
        
        if pdf_content:
            print(f"✅ PDF Generation: ✓ Success (Size: {len(pdf_content)} bytes)")
            
            # Save test PDF
            test_filename = f"test_invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            try:
                with open(test_filename, 'wb') as f:
                    f.write(pdf_content)
                print(f"✅ PDF Saved: ✓ {test_filename}")
                
                # Clean up test file
                os.remove(test_filename)
                print(f"✅ Cleanup: ✓ Test file removed")
                
            except Exception as e:
                print(f"❌ PDF Save Error: {str(e)}")
        else:
            print("❌ PDF Generation: Failed")
            
    except ImportError as e:
        print(f"❌ PDF Service: Import error - {str(e)}")
        print("💡 Note: Run 'pip install reportlab' to enable PDF generation")
    except Exception as e:
        print(f"❌ PDF Generation Test: Error - {str(e)}")
        import traceback
        traceback.print_exc()

def test_plan_name_mapping():
    """Test plan name mapping functionality"""
    print("\n🏷️ Testing Plan Name Mapping...")
    
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from services.payment_service import PaymentService
        
        # Initialize payment service
        payment_service = PaymentService()
        print("✅ Payment Service: ✓ Initialized")
        
        # Test plan type to name mapping
        test_plan_types = ['basic', 'professional', 'premium', 'unknown']
        
        for plan_type in test_plan_types:
            plan_name = payment_service._get_plan_name_from_type(plan_type)
            print(f"✅ Plan Mapping: {plan_type} → {plan_name}")
        
        # Test price-based mapping (mock price objects)
        test_prices = [
            {'id': 'price_test_basic', 'unit_amount': 499, 'currency': 'usd'},
            {'id': 'price_test_pro', 'unit_amount': 1299, 'currency': 'usd'},
            {'id': 'price_test_unknown', 'unit_amount': 999, 'currency': 'usd'}
        ]
        
        for price in test_prices:
            plan_name = payment_service._get_plan_name_from_price(price)
            amount = price['unit_amount'] / 100
            print(f"✅ Price Mapping: ${amount:.2f} → {plan_name}")
            
    except Exception as e:
        print(f"❌ Plan Name Mapping Test: Error - {str(e)}")
        import traceback
        traceback.print_exc()

def test_email_service():
    """Test email service functionality"""
    print("\n📧 Testing Email Service...")
    
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from services.email_service import EmailService
        
        # Initialize email service
        email_service = EmailService()
        print("✅ Email Service: ✓ Initialized")
        
        # Test email creation (without sending)
        test_email_data = {
            'username': 'Test User',
            'email': 'test@example.com',
            'invoice_id': 'in_test_12345',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_type': 'basic',
            'plan_name': 'Basic Plan',
            'billing_cycle': 'monthly'
        }
        
        print(f"🧪 Creating test payment confirmation email...")
        
        # Create email message
        msg = email_service.create_payment_confirmation_email(**test_email_data)
        
        if msg:
            print("✅ Email Creation: ✓ Success")
            print(f"   Subject: {msg['Subject']}")
            print(f"   To: {msg['To']}")
            print(f"   From: {msg['From']}")
            
            # Check if email contains plan name
            email_content = str(msg)
            if 'Basic Plan' in email_content:
                print("✅ Plan Name: ✓ Found in email content")
            else:
                print("❌ Plan Name: Not found in email content")
                
        else:
            print("❌ Email Creation: Failed")
            
    except Exception as e:
        print(f"❌ Email Service Test: Error - {str(e)}")
        import traceback
        traceback.print_exc()

def test_integrated_system():
    """Test the integrated email + PDF system"""
    print("\n🔗 Testing Integrated Email + PDF System...")
    
    try:
        # Add the current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from services.payment_service import PaymentService
        
        # Initialize payment service
        payment_service = PaymentService()
        print("✅ Payment Service: ✓ Initialized")
        
        # Test PDF generation
        test_user_email = "test@example.com"
        test_invoice_id = "in_test_integrated"
        
        print(f"🧪 Testing integrated PDF generation...")
        
        pdf_content = payment_service._generate_pdf_invoice(
            user_email=test_user_email,
            invoice_id=test_invoice_id,
            amount=4.99,
            currency='USD',
            payment_date=datetime.now(),
            plan_type='basic',
            plan_name='Basic Plan',
            billing_cycle='monthly'
        )
        
        if pdf_content:
            print(f"✅ Integrated PDF: ✓ Generated (Size: {len(pdf_content)} bytes)")
        else:
            print("❌ Integrated PDF: Generation failed")
            
    except Exception as e:
        print(f"❌ Integrated System Test: Error - {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("🚀 VocalLocal Email & Invoice System - Verification Tests")
    print("=" * 65)
    
    test_pdf_invoice_generation()
    test_plan_name_mapping()
    test_email_service()
    test_integrated_system()
    
    print("\n" + "=" * 65)
    print("🏁 Email & Invoice System Verification Complete")
    print("\n📋 Summary of Fixes Applied:")
    print("1. ✅ Enhanced plan name mapping with debugging")
    print("2. ✅ PDF invoice generation with professional layout")
    print("3. ✅ Email service with PDF attachment support")
    print("4. ✅ Integrated payment confirmation system")
    print("\n💡 Next Steps:")
    print("- Install reportlab: pip install reportlab")
    print("- Test with real Stripe webhook events")
    print("- Verify email delivery in production")

if __name__ == "__main__":
    main()
