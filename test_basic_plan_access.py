#!/usr/bin/env python3
"""
Test script to verify Basic plan users can access their models without upgrade prompts.
This script tests the model access control fix for Basic plan users.
"""

import os
import sys
from datetime import datetime

def test_basic_plan_access():
    """Test that Basic plan users have proper model access."""
    
    print("=" * 70)
    print("BASIC PLAN MODEL ACCESS TEST")
    print("=" * 70)
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Test 1: Check JavaScript files for proper plan-based access control
    print("1. Checking JavaScript files for Basic plan access logic...")
    print()
    
    js_files_to_check = [
        ('static/js/plan-access-control.js', [
            'isModelAccessible',
            'planModelAccess',
            'basic',
            'userPlan'
        ]),
        ('templates/index.html', [
            'plan-access-control.js',
            'rbac-access-control.js'  # Should NOT be present
        ])
    ]
    
    for file_path, required_content in js_files_to_check:
        print(f"  Checking {file_path}...")
        
        if not os.path.exists(file_path):
            print(f"    ❌ File not found: {file_path}")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for item in required_content:
                if item == 'rbac-access-control.js':
                    # This should NOT be present in index.html
                    if item in content:
                        print(f"    ❌ CONFLICT: {item} found in {file_path} (should be removed)")
                    else:
                        print(f"    ✅ GOOD: {item} not found in {file_path} (conflict resolved)")
                else:
                    # These should be present
                    if item in content:
                        print(f"    ✅ Found: {item}")
                    else:
                        print(f"    ❌ Missing: {item}")
                        
        except Exception as e:
            print(f"    ❌ Error reading {file_path}: {e}")
        
        print()
    
    # Test 2: Check plan model access configuration
    print("2. Checking Basic plan model access configuration...")
    print()
    
    try:
        # Import the plan access control service
        from services.plan_access_control import PlanAccessControl
        
        # Test Basic plan model access
        basic_models = {
            'transcription': ['gemini-2.0-flash-lite', 'gpt-4o-mini-transcribe', 'gemini-2.5-flash-preview-04-17'],
            'translation': ['gemini-2.0-flash-lite', 'gemini-2.5-flash', 'gpt-4.1-mini'],
            'tts': ['gemini-2.5-flash-tts', 'gpt4o-mini', 'openai'],
            'interpretation': ['gemini-2.0-flash-lite', 'gemini-2.5-flash']
        }
        
        for service_type, expected_models in basic_models.items():
            print(f"  Testing {service_type} models for Basic plan...")
            accessible_models = PlanAccessControl.get_accessible_models(service_type, 'basic')
            
            for model in expected_models:
                if model in accessible_models:
                    print(f"    ✅ {model} - accessible")
                else:
                    print(f"    ❌ {model} - NOT accessible")
            
            # Check if any extra models are accessible
            extra_models = set(accessible_models) - set(expected_models)
            if extra_models:
                print(f"    ℹ️  Extra models: {', '.join(extra_models)}")
            
            print()
            
    except ImportError as e:
        print(f"  ❌ Could not import PlanAccessControl: {e}")
        print("  Make sure you're running this from the correct directory")
    except Exception as e:
        print(f"  ❌ Error testing plan access: {e}")
    
    # Test 3: Check for conflicting access control systems
    print("3. Checking for conflicting access control systems...")
    print()
    
    template_files = [
        'templates/index.html',
        'templates/dashboard.html'
    ]
    
    for template_file in template_files:
        if os.path.exists(template_file):
            print(f"  Checking {template_file}...")
            
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count access control systems
                plan_access = 'plan-access-control.js' in content
                rbac_access = 'rbac-access-control.js' in content
                model_access = 'model-access-control.js' in content
                
                print(f"    Plan Access Control: {'✅ Present' if plan_access else '❌ Missing'}")
                print(f"    RBAC Access Control: {'⚠️  Present' if rbac_access else '✅ Not present'}")
                print(f"    Model Access Control: {'ℹ️  Present' if model_access else 'ℹ️  Not present'}")
                
                if template_file == 'templates/index.html' and rbac_access:
                    print(f"    ❌ CONFLICT: RBAC system should be removed from index.html")
                elif template_file == 'templates/index.html' and not rbac_access:
                    print(f"    ✅ GOOD: RBAC conflict resolved in index.html")
                    
            except Exception as e:
                print(f"    ❌ Error reading {template_file}: {e}")
        else:
            print(f"  ❌ Template not found: {template_file}")
        
        print()
    
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("If all checks pass, Basic plan users should now be able to:")
    print("• Select Basic tier models without seeing upgrade prompts")
    print("• Access transcription models: gemini-2.0-flash-lite, gpt-4o-mini-transcribe, gemini-2.5-flash-preview-04-17")
    print("• Access translation models: gemini-2.0-flash-lite, gemini-2.5-flash, gpt-4.1-mini")
    print("• Access TTS models: gemini-2.5-flash-tts, gpt4o-mini, openai")
    print("• Access interpretation models: gemini-2.0-flash-lite, gemini-2.5-flash")
    print()
    print("The fix involved:")
    print("1. Removing conflicting RBAC access control from index.html")
    print("2. Updating plan-access-control.js to use proper plan-based checking")
    print("3. Ensuring model selection logic respects user plan types")
    print()

if __name__ == "__main__":
    test_basic_plan_access()
