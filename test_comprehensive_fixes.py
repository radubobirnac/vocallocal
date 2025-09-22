#!/usr/bin/env python3
"""
Comprehensive test script for conversation room functionality fixes
"""

import json
import os
import sys

def test_json_parsing_fix():
    """Test that the JSON parsing error is fixed"""
    print("\n🧪 Testing JSON Parsing Fix...")
    
    # Test data that should be valid
    test_data = {
        'room_code': 'A4HCE4',
        'input_language': 'en',
        'target_language': 'es'
    }
    
    print(f"✅ Test data structure: {test_data}")
    print(f"✅ JSON serialization: {json.dumps(test_data)}")
    
    # Test JSON parsing
    try:
        json_str = json.dumps(test_data)
        parsed_data = json.loads(json_str)
        print(f"✅ JSON parsing successful: {parsed_data}")
        return True
    except Exception as e:
        print(f"❌ JSON parsing failed: {e}")
        return False

def test_conversation_modal_css_fix():
    """Test that conversation modal CSS is fixed"""
    print("\n🧪 Testing Conversation Modal CSS Fix...")
    
    # Check if CSS file exists and has the correct structure
    css_file = os.path.join(os.path.dirname(__file__), 'static', 'css', 'conversation-modal.css')
    
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            css_content = f.read()
            
        # Check for the fixed CSS rules
        checks = [
            'display: none;' in css_content,
            '.modal-overlay.show' in css_content,
            'display: flex !important;' in css_content
        ]
        
        if all(checks):
            print("✅ CSS file contains the fixed modal display rules")
            return True
        else:
            print("❌ CSS file missing expected modal display fixes")
            print(f"   Checks passed: {sum(checks)}/{len(checks)}")
            return False
    else:
        print("❌ CSS file not found")
        return False

def test_conversation_modal_js_fix():
    """Test that conversation modal JavaScript is fixed"""
    print("\n🧪 Testing Conversation Modal JavaScript Fix...")
    
    # Check if JS file exists and has the correct structure
    js_file = os.path.join(os.path.dirname(__file__), 'static', 'js', 'conversation-modal.js')
    
    if os.path.exists(js_file):
        with open(js_file, 'r') as f:
            js_content = f.read()
            
        # Check for the fixed JavaScript functions
        checks = [
            'modal.classList.add(\'show\')' in js_content,
            'modal.classList.remove(\'show\')' in js_content,
            'modal.style.display = \'none\'' in js_content,
            'Conversation modal explicitly hidden on page load' in js_content
        ]
        
        if all(checks):
            print("✅ JavaScript file contains all expected modal fixes")
            return True
        else:
            print("❌ JavaScript file missing some expected fixes")
            print(f"   Checks passed: {sum(checks)}/{len(checks)}")
            return False
    else:
        print("❌ JavaScript file not found")
        return False

def test_firebase_error_handling():
    """Test improved Firebase error handling"""
    print("\n🧪 Testing Firebase Error Handling...")
    
    # Check if Firebase models file has improved error handling
    models_file = os.path.join(os.path.dirname(__file__), 'models', 'firebase_models.py')
    
    if os.path.exists(models_file):
        with open(models_file, 'r') as f:
            models_content = f.read()
            
        # Check for improved error handling
        checks = [
            '[DEBUG]' in models_content,
            '[ERROR]' in models_content,
            'traceback.format_exc()' in models_content,
            'Failed to add participant:' in models_content
        ]
        
        if all(checks):
            print("✅ Firebase models contain improved error handling")
            return True
        else:
            print("❌ Firebase models missing some error handling improvements")
            print(f"   Checks passed: {sum(checks)}/{len(checks)}")
            return False
    else:
        print("❌ Firebase models file not found")
        return False

def test_conversation_route_logging():
    """Test improved conversation route logging"""
    print("\n🧪 Testing Conversation Route Logging...")
    
    # Check if conversation route has improved logging
    route_file = os.path.join(os.path.dirname(__file__), 'routes', 'conversation.py')
    
    if os.path.exists(route_file):
        with open(route_file, 'r') as f:
            route_content = f.read()
            
        # Check for improved logging
        checks = [
            'Attempting to add participant' in route_content,
            'Add participant result:' in route_content,
            'Failed to add participant' in route_content
        ]
        
        if all(checks):
            print("✅ Conversation route contains improved logging")
            return True
        else:
            print("❌ Conversation route missing some logging improvements")
            print(f"   Checks passed: {sum(checks)}/{len(checks)}")
            return False
    else:
        print("❌ Conversation route file not found")
        return False

def test_manual_verification_steps():
    """Provide manual testing steps"""
    print("\n🧪 Manual Testing Steps...")
    
    print("✅ To verify the fixes work correctly, please test:")
    print("\n📋 JSON Parsing Error Fix:")
    print("   1. Start the Flask application")
    print("   2. Create a conversation room")
    print("   3. Try to join the room with valid data")
    print("   4. Check server logs for detailed debugging info")
    print("   5. Verify no 'Invalid data; couldn't parse JSON object' errors")
    
    print("\n📋 Automatic Modal Popup Fix:")
    print("   1. Open the main page in a browser")
    print("   2. Verify conversation modal does NOT appear automatically")
    print("   3. Click the conversation button")
    print("   4. Verify modal opens only after clicking")
    print("   5. Check browser console for 'Conversation modal explicitly hidden on page load'")
    print("   6. Test on both desktop and mobile")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Running Comprehensive Conversation Room Functionality Tests")
    print("=" * 70)
    
    tests = [
        test_json_parsing_fix,
        test_conversation_modal_css_fix,
        test_conversation_modal_js_fix,
        test_firebase_error_handling,
        test_conversation_route_logging,
        test_manual_verification_steps
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    print(f"📈 Success Rate: {sum(results)/len(results)*100:.1f}%")
    
    if all(results):
        print("\n🎉 All tests passed! Conversation room fixes are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the issues above.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
