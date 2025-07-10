#!/usr/bin/env python3
"""
Pre-deployment readiness check for PDF invoice attachments
Verifies all components are ready for production deployment
"""

import os
import sys
from dotenv import load_dotenv

def check_dependencies():
    """Check if all required dependencies are available"""
    print("📦 Checking Dependencies...")
    
    try:
        import reportlab
        print(f"✅ ReportLab: {reportlab.Version}")
    except ImportError:
        print("❌ ReportLab: Not installed")
        return False
    
    try:
        from email.mime.application import MIMEApplication
        print("✅ Email MIME: Available")
    except ImportError:
        print("❌ Email MIME: Not available")
        return False
    
    try:
        import stripe
        print(f"✅ Stripe: Available")
    except ImportError:
        print("❌ Stripe: Not installed")
        return False
    
    return True

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("\n⚙️  Checking Environment Variables...")
    
    load_dotenv()
    
    required_vars = [
        'MAIL_SERVER',
        'MAIL_PORT', 
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER',
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'OPENAI_API_KEY',
        'GEMINI_API_KEY',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var or 'PASSWORD' in var or 'SECRET' in var:
                print(f"✅ {var}: Set (hidden)")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Missing")
            missing_vars.append(var)
    
    return len(missing_vars) == 0, missing_vars

def check_files():
    """Check if required files exist"""
    print("\n📁 Checking Required Files...")
    
    required_files = [
        'requirements.txt',
        'Procfile',
        'app.py',
        'services/pdf_invoice_service.py',
        'services/email_service.py',
        'services/payment_service.py',
        'firebase-credentials.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}: Exists")
        else:
            print(f"❌ {file_path}: Missing")
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files

def check_pdf_generation():
    """Test PDF generation functionality"""
    print("\n📄 Testing PDF Generation...")
    
    try:
        from services.pdf_invoice_service import PDFInvoiceService
        from datetime import datetime
        
        pdf_service = PDFInvoiceService()
        
        test_data = {
            'invoice_id': 'test_deployment_001',
            'customer_name': 'Test User',
            'customer_email': 'test@example.com',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_name': 'Basic Plan',
            'plan_type': 'basic',
            'billing_cycle': 'monthly',
            'payment_method': 'Credit Card',
            'transaction_id': 'test_deployment_001'
        }
        
        pdf_content = pdf_service.generate_invoice_pdf(test_data)
        
        if pdf_content:
            print(f"✅ PDF Generation: Success ({len(pdf_content)} bytes)")
            return True
        else:
            print("❌ PDF Generation: Failed")
            return False
            
    except Exception as e:
        print(f"❌ PDF Generation: Error - {str(e)}")
        return False

def check_email_attachment():
    """Test email attachment functionality"""
    print("\n📧 Testing Email Attachment...")
    
    try:
        from services.email_service import EmailService
        from services.pdf_invoice_service import PDFInvoiceService
        from datetime import datetime
        
        email_service = EmailService()
        pdf_service = PDFInvoiceService()
        
        # Generate test PDF
        test_data = {
            'invoice_id': 'test_attachment_001',
            'customer_name': 'Test User',
            'customer_email': 'test@example.com',
            'amount': 4.99,
            'currency': 'USD',
            'payment_date': datetime.now(),
            'plan_name': 'Basic Plan',
            'plan_type': 'basic',
            'billing_cycle': 'monthly',
            'payment_method': 'Credit Card',
            'transaction_id': 'test_attachment_001'
        }
        
        pdf_content = pdf_service.generate_invoice_pdf(test_data)
        
        if not pdf_content:
            print("❌ Email Attachment: PDF generation failed")
            return False
        
        # Create email with attachment
        msg = email_service.create_payment_confirmation_email(
            username="Test User",
            email="test@example.com",
            invoice_id="test_attachment_001",
            amount=4.99,
            currency="USD",
            payment_date=datetime.now(),
            plan_type="basic",
            plan_name="Basic Plan",
            billing_cycle="monthly",
            pdf_attachment=pdf_content
        )
        
        # Check for attachment
        attachments = []
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                if filename:
                    attachments.append(filename)
        
        if attachments:
            print(f"✅ Email Attachment: Success - {attachments}")
            return True
        else:
            print("❌ Email Attachment: No PDF attachment found")
            return False
            
    except Exception as e:
        print(f"❌ Email Attachment: Error - {str(e)}")
        return False

def main():
    """Run all deployment readiness checks"""
    print("🚀 VocalLocal PDF Invoice - Deployment Readiness Check")
    print("=" * 60)
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Environment Variables", check_environment_variables),
        ("Required Files", check_files),
        ("PDF Generation", check_pdf_generation),
        ("Email Attachment", check_email_attachment)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            if check_name == "Environment Variables":
                result, missing = check_func()
                results.append((check_name, result, missing if not result else None))
            elif check_name == "Required Files":
                result, missing = check_func()
                results.append((check_name, result, missing if not result else None))
            else:
                result = check_func()
                results.append((check_name, result, None))
        except Exception as e:
            print(f"❌ {check_name}: Error - {str(e)}")
            results.append((check_name, False, str(e)))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 DEPLOYMENT READINESS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed, details in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check_name}")
        if not passed and details:
            if isinstance(details, list):
                for item in details:
                    print(f"     - Missing: {item}")
            else:
                print(f"     - Error: {details}")
        all_passed = all_passed and passed
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 READY FOR DEPLOYMENT!")
        print("✅ All PDF invoice attachment components are working")
        print("✅ Environment is properly configured")
        print("✅ Dependencies are available")
        print("\n📋 Next Steps:")
        print("1. Push code to your repository")
        print("2. Configure environment variables in DigitalOcean")
        print("3. Update Stripe webhook URL to production domain")
        print("4. Test with a real payment after deployment")
    else:
        print("❌ NOT READY FOR DEPLOYMENT")
        print("🔧 Fix the issues above before deploying")
    
    return all_passed

if __name__ == "__main__":
    main()
