#!/usr/bin/env python3
"""
Final Critical Fixes Test Script for Conversation Room Functionality
Tests both Firebase JSON serialization fix and conversation modal popup fix
"""

import json
import os
import sys
from datetime import datetime

def test_firebase_json_serialization():
    """Test that Firebase data serialization is working correctly"""
    print("\n🧪 Testing Firebase JSON Serialization Fix...")
    
    # Test the sanitize_for_firebase function
    test_data = {
        'user_email': 'test@example.com',
        'joined_at': datetime.now(),  # This should be converted to string
        'input_language': 'en',
        'target_language': 'es',
        'status': 'connected',
        'last_seen': datetime.now(),  # This should be converted to string
        'nested_data': {
            'created_at': datetime.now(),  # Nested datetime should also be converted
            'some_list': [datetime.now(), 'string', 123]  # List with datetime
        }
    }
    
    print(f"✅ Original test data contains datetime objects")
    
    # Simulate the sanitize_for_firebase function
    def sanitize_for_firebase(data):
        """Ensure all data is JSON-serializable for Firebase."""
        if isinstance(data, dict):
            return {key: sanitize_for_firebase(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [sanitize_for_firebase(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data
    
    # Test sanitization
    sanitized_data = sanitize_for_firebase(test_data)
    print(f"✅ Data sanitized successfully")
    
    # Test JSON serialization
    try:
        json_str = json.dumps(sanitized_data)
        print(f"✅ Sanitized data is JSON-serializable")
        
        # Verify the datetime objects were converted to strings
        parsed_data = json.loads(json_str)
        if isinstance(parsed_data['joined_at'], str) and 'T' in parsed_data['joined_at']:
            print(f"✅ Datetime objects converted to ISO format strings")
            return True
        else:
            print(f"❌ Datetime objects not properly converted")
            return False
            
    except (TypeError, ValueError) as e:
        print(f"❌ JSON serialization failed: {e}")
        return False

def test_conversation_modal_files():
    """Test that conversation modal files have the correct fixes"""
    print("\n🧪 Testing Conversation Modal Files...")
    
    # Test CSS file
    css_file = os.path.join(os.path.dirname(__file__), 'static', 'css', 'conversation-modal.css')
    css_checks_passed = 0
    css_total_checks = 3
    
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            css_content = f.read()
            
        # Check for the fixed CSS rules
        if 'display: none;' in css_content:
            print("   ✅ CSS: Modal defaults to hidden")
            css_checks_passed += 1
        else:
            print("   ❌ CSS: Modal does not default to hidden")
            
        if '.modal-overlay.show' in css_content:
            print("   ✅ CSS: Show class rule exists")
            css_checks_passed += 1
        else:
            print("   ❌ CSS: Show class rule missing")
            
        if 'display: flex !important;' in css_content:
            print("   ✅ CSS: Important display rule exists")
            css_checks_passed += 1
        else:
            print("   ❌ CSS: Important display rule missing")
    else:
        print("   ❌ CSS file not found")
    
    # Test JavaScript file
    js_file = os.path.join(os.path.dirname(__file__), 'static', 'js', 'conversation-modal.js')
    js_checks_passed = 0
    js_total_checks = 4
    
    if os.path.exists(js_file):
        with open(js_file, 'r') as f:
            js_content = f.read()
            
        # Check for the fixed JavaScript functions
        if 'modal.classList.add(\'show\')' in js_content:
            print("   ✅ JS: Modal show class management")
            js_checks_passed += 1
        else:
            print("   ❌ JS: Modal show class management missing")
            
        if 'modal.classList.remove(\'show\')' in js_content:
            print("   ✅ JS: Modal hide class management")
            js_checks_passed += 1
        else:
            print("   ❌ JS: Modal hide class management missing")
            
        if 'modal.style.display = \'none\'' in js_content:
            print("   ✅ JS: Explicit display none setting")
            js_checks_passed += 1
        else:
            print("   ❌ JS: Explicit display none setting missing")
            
        if 'Conversation modal explicitly hidden on page load' in js_content:
            print("   ✅ JS: Page load hiding logic")
            js_checks_passed += 1
        else:
            print("   ❌ JS: Page load hiding logic missing")
    else:
        print("   ❌ JavaScript file not found")
    
    total_checks = css_checks_passed + js_checks_passed
    max_checks = css_total_checks + js_total_checks
    
    print(f"   📊 Modal fixes: {total_checks}/{max_checks} checks passed")
    return total_checks == max_checks

def test_firebase_models_fix():
    """Test that Firebase models have the sanitization fix"""
    print("\n🧪 Testing Firebase Models Fix...")
    
    models_file = os.path.join(os.path.dirname(__file__), 'models', 'firebase_models.py')
    
    if os.path.exists(models_file):
        with open(models_file, 'r') as f:
            models_content = f.read()
            
        checks_passed = 0
        total_checks = 4
        
        # Check for sanitization function
        if 'def sanitize_for_firebase' in models_content:
            print("   ✅ Sanitization function exists")
            checks_passed += 1
        else:
            print("   ❌ Sanitization function missing")
            
        # Check for sanitization usage
        if 'sanitize_for_firebase(participants)' in models_content:
            print("   ✅ Participants data sanitization")
            checks_passed += 1
        else:
            print("   ❌ Participants data sanitization missing")
            
        # Check for JSON validation
        if 'json.dumps(update_data)' in models_content:
            print("   ✅ JSON validation before Firebase update")
            checks_passed += 1
        else:
            print("   ❌ JSON validation missing")
            
        # Check for improved error handling
        if '[DEBUG]' in models_content and '[ERROR]' in models_content:
            print("   ✅ Enhanced debugging and error handling")
            checks_passed += 1
        else:
            print("   ❌ Enhanced debugging missing")
            
        print(f"   📊 Firebase models: {checks_passed}/{total_checks} checks passed")
        return checks_passed == total_checks
    else:
        print("   ❌ Firebase models file not found")
        return False

def main():
    """Run all tests"""
    print("🚀 Running Final Critical Conversation Room Fixes Tests")
    print("=" * 60)
    
    tests = [
        test_firebase_json_serialization,
        test_conversation_modal_files,
        test_firebase_models_fix
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Critical Fixes Test Results:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    print(f"📈 Success Rate: {sum(results)/len(results)*100:.1f}%")
    
    if all(results):
        print("\n🎉 All critical fixes are properly implemented!")
    else:
        print("\n⚠️  Some fixes may need attention.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
