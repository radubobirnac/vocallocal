#!/usr/bin/env python3
"""
Debug email content generation for payment confirmation emails.
"""

import os
import sys
from datetime import datetime

# Add the vocallocal directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_email_content():
    """Debug the email content generation"""
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
        
        print("🔍 Creating payment confirmation email...")
        print(f"Test data: {test_data}")
        
        # Create email
        msg = email_service.create_payment_confirmation_email(**test_data)
        
        print(f"\n📧 Email created successfully!")
        print(f"Subject: {msg['Subject']}")
        print(f"To: {msg['To']}")
        print(f"From: {msg['From']}")
        
        # Get email parts
        parts = msg.get_payload()
        print(f"Number of parts: {len(parts)}")
        
        if len(parts) >= 2:
            # Check HTML content
            html_content = parts[1].get_payload()
            print(f"\n📄 HTML Content Length: {len(html_content)} characters")
            
            # Check for key elements
            checks = [
                ('Invoice ID', 'in_test123456789'),
                ('Amount', 'USD 4.99'),
                ('Plan Name', 'Basic Plan'),
                ('Username', 'John Doe')
            ]
            
            print("\n🔍 Content Checks:")
            for check_name, check_value in checks:
                if check_value in html_content:
                    print(f"✅ {check_name}: Found '{check_value}'")
                else:
                    print(f"❌ {check_name}: Missing '{check_value}'")
                    # Show context around where it should be
                    if 'Invoice ID' in check_name:
                        lines = html_content.split('\n')
                        for i, line in enumerate(lines):
                            if 'Invoice ID' in line and i < len(lines) - 1:
                                print(f"   Found line: {line.strip()}")
                                print(f"   Next line: {lines[i+1].strip()}")
                                break
            
            # Save HTML content for inspection
            with open('debug_email_output.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"\n💾 HTML content saved to debug_email_output.html")
            
            # Check text content too
            text_content = parts[0].get_payload()
            print(f"\n📝 Text Content Length: {len(text_content)} characters")
            
            if 'in_test123456789' in text_content:
                print("✅ Invoice ID found in text content")
            else:
                print("❌ Invoice ID missing from text content")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_email_content()
