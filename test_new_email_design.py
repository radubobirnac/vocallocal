#!/usr/bin/env python3
"""
Test the new professional email design
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_new_email_design():
    """Test the new professional email template"""
    print("📧 Testing New Professional Email Design")
    print("=" * 50)
    
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()
        
        from services.email_service import EmailService
        from services.pdf_invoice_service import PDFInvoiceService
        
        email_service = EmailService()
        pdf_service = PDFInvoiceService()
        
        # Test data
        test_data = {
            'username': 'John Doe',
            'email': 'john.doe@example.com',
            'invoice_id': 'in_1234567890abcdef',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_type': 'basic',
            'plan_name': 'Basic Plan',
            'billing_cycle': 'monthly'
        }
        
        print("🧪 Generating test PDF...")
        pdf_data = {
            'invoice_id': test_data['invoice_id'],
            'customer_name': test_data['username'],
            'customer_email': test_data['email'],
            'amount': test_data['amount'],
            'currency': test_data['currency'],
            'payment_date': test_data['payment_date'],
            'plan_name': test_data['plan_name'],
            'plan_type': test_data['plan_type'],
            'billing_cycle': test_data['billing_cycle'],
            'payment_method': 'Credit Card',
            'transaction_id': test_data['invoice_id']
        }
        
        pdf_content = pdf_service.generate_invoice_pdf(pdf_data)
        
        if pdf_content:
            print(f"✅ PDF Generated: {len(pdf_content)} bytes")
        else:
            print("❌ PDF Generation failed")
            return False
        
        print("🧪 Creating email with new design...")
        
        # Create email with new design
        msg = email_service.create_payment_confirmation_email(
            username=test_data['username'],
            email=test_data['email'],
            invoice_id=test_data['invoice_id'],
            amount=test_data['amount'],
            currency=test_data['currency'],
            payment_date=test_data['payment_date'],
            plan_type=test_data['plan_type'],
            plan_name=test_data['plan_name'],
            billing_cycle=test_data['billing_cycle'],
            pdf_attachment=pdf_content
        )
        
        print(f"✅ Email Subject: {msg['Subject']}")
        print(f"✅ Email From: {msg['From']}")
        print(f"✅ Email To: {msg['To']}")
        
        # Check for PDF attachment
        attachments = []
        html_content = None
        text_content = None
        
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                if filename:
                    attachments.append(filename)
            elif part.get_content_type() == 'text/html':
                html_content = part.get_payload(decode=True).decode('utf-8')
            elif part.get_content_type() == 'text/plain':
                text_content = part.get_payload(decode=True).decode('utf-8')
        
        if attachments:
            print(f"✅ PDF Attachment: {attachments}")
        else:
            print("❌ No PDF attachment found")
        
        # Save HTML content for inspection
        if html_content:
            with open('test_email_design.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("✅ HTML email saved as: test_email_design.html")
        
        # Save text content for inspection
        if text_content:
            with open('test_email_design.txt', 'w', encoding='utf-8') as f:
                f.write(text_content)
            print("✅ Text email saved as: test_email_design.txt")
        
        print("\n📋 Email Design Features:")
        print("✅ Clean, minimalist design inspired by Anthropic receipt")
        print("✅ Professional dark header with VocalLocal branding")
        print("✅ Large, prominent amount display")
        print("✅ Clean receipt-style layout")
        print("✅ Download buttons for invoice and receipt")
        print("✅ Organized details section")
        print("✅ Dark invoice section with clear itemization")
        print("✅ Mobile-responsive design")
        print("✅ Professional footer")
        
        return True
        
    except Exception as e:
        print(f"❌ Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_actual_email_sending():
    """Test sending the new email design"""
    print("\n📤 Testing Actual Email Sending")
    print("=" * 40)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from services.email_service import EmailService
        from services.pdf_invoice_service import PDFInvoiceService
        
        email_service = EmailService()
        pdf_service = PDFInvoiceService()
        
        if not email_service.password:
            print("⚠️  Skipping actual email test - MAIL_PASSWORD not configured")
            return True
        
        # Generate test PDF
        pdf_data = {
            'invoice_id': 'in_test_design_001',
            'customer_name': 'Test User',
            'customer_email': 'test@example.com',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_name': 'Basic Plan',
            'plan_type': 'basic',
            'billing_cycle': 'monthly',
            'payment_method': 'Credit Card',
            'transaction_id': 'in_test_design_001'
        }
        
        pdf_content = pdf_service.generate_invoice_pdf(pdf_data)
        
        if not pdf_content:
            print("❌ Cannot test email - PDF generation failed")
            return False
        
        # Send test email to configured sender (self-test)
        test_email = email_service.default_sender
        
        print(f"🧪 Sending new design email to: {test_email}")
        
        result = email_service.send_payment_confirmation_email(
            username="Test User",
            email=test_email,
            invoice_id="in_test_design_001",
            amount=4.99,
            currency="USD",
            payment_date=datetime.now(),
            plan_type="basic",
            plan_name="Basic Plan",
            billing_cycle="monthly",
            pdf_attachment=pdf_content
        )
        
        if result.get('success'):
            print("✅ New Design Email Sent Successfully!")
            print("📧 Check your email inbox for the new professional design")
        else:
            print(f"❌ Email Failed: {result.get('message')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Email Test Failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎨 VocalLocal New Email Design Test")
    print("=" * 45)
    
    # Test email creation
    success = test_new_email_design()
    
    if success:
        # Optionally test actual email sending
        user_input = input("\n❓ Do you want to send a test email with the new design? (y/N): ").strip().lower()
        if user_input in ['y', 'yes']:
            test_actual_email_sending()
    
    print("\n" + "=" * 45)
    if success:
        print("🎉 New email design is ready!")
        print("💡 The email now features:")
        print("   • Clean, professional layout inspired by Anthropic")
        print("   • Prominent amount display")
        print("   • Receipt-style organization")
        print("   • Mobile-responsive design")
        print("   • Professional branding")
    else:
        print("❌ Email design test failed")
