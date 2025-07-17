#!/usr/bin/env python3
"""
Fix Unknown Plan Names in Firebase Database

This script identifies and fixes billing records that have "Unknown Plan" 
as the plan name by using enhanced plan name resolution logic.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.user_account_service import UserAccountService
from services.payment_service import PaymentService

def fix_unknown_plan_names():
    """Fix all billing records with 'Unknown Plan' names"""
    print("🔧 Starting Unknown Plan Names Fix...")
    print("=" * 60)
    
    try:
        # Initialize payment service for plan name resolution
        payment_service = PaymentService()
        
        # Get all users from Firebase
        users_ref = UserAccountService.get_ref('users')
        all_users = users_ref.get()
        
        if not all_users:
            print("❌ No users found in database")
            return
        
        total_users = len(all_users)
        users_with_billing = 0
        fixed_records = 0
        
        print(f"📊 Found {total_users} users in database")
        print("\n🔍 Scanning for billing records with 'Unknown Plan'...")
        
        for user_id, user_data in all_users.items():
            billing_data = user_data.get('billing', {})
            invoices = billing_data.get('invoices', {})
            
            if not invoices:
                continue
                
            users_with_billing += 1
            user_email = user_data.get('email', 'unknown@example.com')
            
            print(f"\n👤 Checking user: {user_email}")
            
            for invoice_id, invoice_data in invoices.items():
                plan_name = invoice_data.get('planName', '')
                plan_type = invoice_data.get('planType', 'unknown')
                amount = invoice_data.get('amount', 0)
                
                if plan_name == 'Unknown Plan' or not plan_name:
                    print(f"   🔧 Fixing invoice {invoice_id}: '{plan_name}' -> ", end="")
                    
                    # Use enhanced plan name resolution
                    new_plan_name = resolve_plan_name(plan_type, amount, payment_service)
                    
                    # Update the record in Firebase
                    invoice_ref = UserAccountService.get_ref(f'users/{user_id}/billing/invoices/{invoice_id}')
                    invoice_ref.update({'planName': new_plan_name})
                    
                    print(f"'{new_plan_name}' ✅")
                    fixed_records += 1
                else:
                    print(f"   ✅ Invoice {invoice_id}: '{plan_name}' (already correct)")
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY:")
        print(f"   Total users: {total_users}")
        print(f"   Users with billing: {users_with_billing}")
        print(f"   Records fixed: {fixed_records}")
        
        if fixed_records > 0:
            print(f"✅ Successfully fixed {fixed_records} billing records!")
        else:
            print("✅ No records needed fixing - all plan names are correct!")
            
    except Exception as e:
        print(f"❌ Error during fix process: {str(e)}")
        import traceback
        traceback.print_exc()

def resolve_plan_name(plan_type, amount, payment_service):
    """Resolve plan name using enhanced logic"""
    try:
        # Try plan type mapping first
        if plan_type and plan_type != 'unknown':
            plan_name = payment_service._get_plan_name_from_type(plan_type)
            if plan_name != 'Subscription Plan':
                return plan_name
        
        # Try amount-based mapping
        if amount == 4.99:
            return 'Basic Plan'
        elif amount == 12.99:
            return 'Professional Plan'
        
        # Fallback based on plan type
        if plan_type == 'basic':
            return 'Basic Plan'
        elif plan_type == 'professional':
            return 'Professional Plan'
        elif plan_type == 'payg':
            return 'Pay-As-You-Go Plan'
        
        # Final fallback
        if amount > 0:
            return f'Subscription Plan (${amount:.2f})'
        else:
            return 'VocalLocal Subscription'
            
    except Exception as e:
        print(f"   ⚠️ Error resolving plan name: {e}")
        return 'VocalLocal Subscription'

def preview_changes():
    """Preview what changes would be made without actually updating"""
    print("👀 PREVIEW MODE - No changes will be made")
    print("=" * 60)
    
    try:
        # Get all users from Firebase
        users_ref = UserAccountService.get_ref('users')
        all_users = users_ref.get()
        
        if not all_users:
            print("❌ No users found in database")
            return
        
        payment_service = PaymentService()
        preview_count = 0
        
        for user_id, user_data in all_users.items():
            billing_data = user_data.get('billing', {})
            invoices = billing_data.get('invoices', {})
            
            if not invoices:
                continue
                
            user_email = user_data.get('email', 'unknown@example.com')
            
            for invoice_id, invoice_data in invoices.items():
                plan_name = invoice_data.get('planName', '')
                plan_type = invoice_data.get('planType', 'unknown')
                amount = invoice_data.get('amount', 0)
                
                if plan_name == 'Unknown Plan' or not plan_name:
                    new_plan_name = resolve_plan_name(plan_type, amount, payment_service)
                    print(f"📧 {user_email}")
                    print(f"   Invoice: {invoice_id}")
                    print(f"   Current: '{plan_name}' -> Proposed: '{new_plan_name}'")
                    print(f"   Type: {plan_type}, Amount: ${amount:.2f}")
                    print()
                    preview_count += 1
        
        print(f"📊 Found {preview_count} records that would be updated")
        
    except Exception as e:
        print(f"❌ Error during preview: {str(e)}")

def main():
    """Main function"""
    print("🔧 VocalLocal Plan Name Fix Utility")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--preview':
        preview_changes()
    else:
        print("💡 Usage:")
        print("   python fix_unknown_plan_names.py --preview  (preview changes)")
        print("   python fix_unknown_plan_names.py           (apply fixes)")
        print()
        
        if len(sys.argv) == 1:
            response = input("🤔 Apply fixes to database? (y/N): ")
            if response.lower() == 'y':
                fix_unknown_plan_names()
            else:
                print("❌ Operation cancelled")
        else:
            fix_unknown_plan_names()

if __name__ == "__main__":
    main()
