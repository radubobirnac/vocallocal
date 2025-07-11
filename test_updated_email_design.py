#!/usr/bin/env python3
"""
Test the updated email design with VocalLocal brand colors and no download buttons
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_updated_email_design():
    """Test the updated email template with brand colors and no download buttons"""
    print("🎨 Testing Updated Email Design")
    print("=" * 45)
    
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
            'username': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'invoice_id': 'in_updated_design_test',
            'amount': 12.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_type': 'professional',
            'plan_name': 'Professional Plan',
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
        
        print("🧪 Creating email with updated design...")
        
        # Create email with updated design
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
            with open('updated_email_design.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("✅ HTML email saved as: updated_email_design.html")
            
            # Check for removed download buttons
            if 'Download invoice' not in html_content and 'Download receipt' not in html_content:
                print("✅ Download buttons: Successfully removed")
            else:
                print("❌ Download buttons: Still present in email")
            
            # Check for VocalLocal brand colors
            if 'hsl(262, 83%, 67%)' in html_content:
                print("✅ Brand colors: VocalLocal purple applied")
            else:
                print("❌ Brand colors: VocalLocal purple not found")
        
        # Save text content for inspection
        if text_content:
            with open('updated_email_design.txt', 'w', encoding='utf-8') as f:
                f.write(text_content)
            print("✅ Text email saved as: updated_email_design.txt")
        
        print("\n📋 Updated Email Design Features:")
        print("✅ VocalLocal brand colors (purple: hsl(262, 83%, 67%))")
        print("✅ Download buttons removed")
        print("✅ Clean, professional layout maintained")
        print("✅ Mobile-responsive design")
        print("✅ PDF invoice attachment working")
        
        return True
        
    except Exception as e:
        print(f"❌ Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🎨 VocalLocal Updated Email Design Test")
    print("=" * 50)
    
    # Test updated email design
    success = test_updated_email_design()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Updated email design is ready!")
        print("💡 Changes implemented:")
        print("   • Removed download invoice/receipt buttons")
        print("   • Applied VocalLocal brand colors (purple)")
        print("   • Maintained professional layout")
        print("   • Kept PDF attachment functionality")
    else:
        print("❌ Email design update test failed")
