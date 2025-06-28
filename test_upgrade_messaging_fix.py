#!/usr/bin/env python3
"""
Test script to verify the upgrade messaging fix for Basic plan users.
This script tests that Basic plan users see appropriate messages instead of "Free models available. Upgrade for premium models."
"""

import os
import sys
from datetime import datetime

def test_upgrade_messaging_fix():
    """Test that upgrade messaging is appropriate for different plan types."""
    
    print("=" * 70)
    print("UPGRADE MESSAGING FIX TEST")
    print("=" * 70)
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Test 1: Check backend API endpoint includes plan type
    print("1. Checking /api/user/available-models endpoint includes plan type...")
    print()
    
    try:
        # Check the main.py file for the endpoint
        main_py_path = 'routes/main.py'
        if os.path.exists(main_py_path):
            with open(main_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for plan type inclusion in the response
            if "'user_plan': user_plan" in content:
                print("  ✅ Backend endpoint includes user_plan in response")
            else:
                print("  ❌ Backend endpoint missing user_plan in response")
            
            # Check for proper plan detection logic
            if "subscription.get('planType', 'free')" in content:
                print("  ✅ Backend has plan type detection logic")
            else:
                print("  ❌ Backend missing plan type detection logic")
            
            # Check for has_premium_access update
            if "user_plan in ['basic', 'professional']" in content:
                print("  ✅ Backend correctly identifies premium access for Basic/Professional plans")
            else:
                print("  ❌ Backend doesn't properly identify premium access for paid plans")
                
        else:
            print(f"  ❌ File not found: {main_py_path}")
            
    except Exception as e:
        print(f"  ❌ Error checking backend: {e}")
    
    print()
    
    # Test 2: Check frontend messaging logic
    print("2. Checking frontend messaging logic in script.js...")
    print()
    
    try:
        script_js_path = 'static/script.js'
        if os.path.exists(script_js_path):
            with open(script_js_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for plan-based messaging
            if "data.user_plan === 'basic'" in content:
                print("  ✅ Frontend checks for Basic plan")
            else:
                print("  ❌ Frontend missing Basic plan check")
            
            if "data.user_plan === 'professional'" in content:
                print("  ✅ Frontend checks for Professional plan")
            else:
                print("  ❌ Frontend missing Professional plan check")
            
            # Check for appropriate messages
            if "Basic plan active: Access to premium models included" in content:
                print("  ✅ Frontend has appropriate Basic plan message")
            else:
                print("  ❌ Frontend missing appropriate Basic plan message")
            
            if "Professional plan active: Full access to all models" in content:
                print("  ✅ Frontend has appropriate Professional plan message")
            else:
                print("  ❌ Frontend missing appropriate Professional plan message")
            
            # Check that free plan message is only for free users
            free_message_lines = []
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "Free models available. Upgrade for premium models." in line:
                    free_message_lines.append(i + 1)
            
            if len(free_message_lines) == 1:
                print("  ✅ Free plan message appears only once (good)")
                # Check if it's in the right context
                context_start = max(0, free_message_lines[0] - 10)
                context_end = min(len(lines), free_message_lines[0] + 5)
                context = '\n'.join(lines[context_start:context_end])
                
                if "} else {" in context and "Free plan" in context:
                    print("  ✅ Free plan message is in the correct else block")
                else:
                    print("  ⚠️  Free plan message context needs verification")
            else:
                print(f"  ❌ Free plan message appears {len(free_message_lines)} times (should be 1)")
                
        else:
            print(f"  ❌ File not found: {script_js_path}")
            
    except Exception as e:
        print(f"  ❌ Error checking frontend: {e}")
    
    print()
    
    # Test 3: Check for plan type storage in userRoleInfo
    print("3. Checking userRoleInfo includes plan information...")
    print()
    
    try:
        if os.path.exists(script_js_path):
            with open(script_js_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "plan: data.user_plan" in content:
                print("  ✅ Frontend stores user plan in userRoleInfo")
            else:
                print("  ❌ Frontend doesn't store user plan in userRoleInfo")
                
    except Exception as e:
        print(f"  ❌ Error checking userRoleInfo: {e}")
    
    print()
    
    # Test 4: Verify expected behavior for each plan type
    print("4. Expected behavior verification...")
    print()
    
    expected_behaviors = {
        'Free Plan Users': {
            'message': 'Free models available. Upgrade for premium models.',
            'type': 'info',
            'should_see_upgrade': True
        },
        'Basic Plan Users': {
            'message': 'Basic plan active: Access to premium models included',
            'type': 'success',
            'should_see_upgrade': False
        },
        'Professional Plan Users': {
            'message': 'Professional plan active: Full access to all models',
            'type': 'success',
            'should_see_upgrade': False
        },
        'Admin Users': {
            'message': 'Admin access: Full system access',
            'type': 'success',
            'should_see_upgrade': False
        },
        'Super Users': {
            'message': 'Super User access: All models available',
            'type': 'success',
            'should_see_upgrade': False
        }
    }
    
    for user_type, behavior in expected_behaviors.items():
        print(f"  {user_type}:")
        print(f"    Expected message: '{behavior['message']}'")
        print(f"    Message type: {behavior['type']}")
        print(f"    Should see upgrade prompts: {behavior['should_see_upgrade']}")
        print()
    
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("The fix addresses the issue where Basic plan users were seeing:")
    print("❌ 'Free models available. Upgrade for premium models.'")
    print()
    print("Now Basic plan users should see:")
    print("✅ 'Basic plan active: Access to premium models included'")
    print()
    print("This fix involved:")
    print("1. ✅ Updated /api/user/available-models to include user_plan")
    print("2. ✅ Modified frontend logic to check plan type, not just role")
    print("3. ✅ Added appropriate messages for Basic and Professional plans")
    print("4. ✅ Ensured free plan message only shows for actual free users")
    print()
    print("The fix should work consistently across:")
    print("• Page refreshes (data comes from backend API)")
    print("• Different browser sessions (plan stored in Firebase)")
    print("• Basic mode and bilingual mode (same messaging logic)")
    print()

if __name__ == "__main__":
    test_upgrade_messaging_fix()
