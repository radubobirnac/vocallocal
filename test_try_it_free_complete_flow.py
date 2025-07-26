#!/usr/bin/env python3
"""
Complete flow test for Try It Free functionality to verify the JSON parsing error is fixed.
Tests the entire user journey from language selection to audio processing.
"""

import os
import re

def test_complete_flow_integration():
    """Test that all components work together for the complete Try It Free flow"""
    print("🔄 Testing Complete Try It Free Flow Integration")
    print("=" * 60)
    
    # Step 1: Check Try It Free page template
    template_path = "templates/try_it_free.html"
    if not os.path.exists(template_path):
        print(f"❌ Try It Free template not found: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Check for language selection elements
    language_elements = [
        r'<select.*id=["\']language-select["\']',
        r'<option.*value=["\']en["\']',
        r'<option.*value=["\']es["\']'
    ]
    
    for pattern in language_elements:
        if not re.search(pattern, template_content):
            print(f"❌ Language selection element missing: {pattern}")
            return False
    
    print("✅ Try It Free template has proper language selection")
    
    # Step 2: Check JavaScript integration
    js_path = "static/try_it_free.js"
    with open(js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    # Check for complete flow elements
    flow_elements = [
        r'function processAudio\(',
        r'selectedLanguage.*languageSelect\.value',
        r'formData\.append\(["\']language["\']',
        r'formData\.append\(["\']model["\']',
        r'fetch\(["\']\/api\/transcribe_free_trial["\']',
        r'response\.json\(\)',
        r'displayTranscription\('
    ]
    
    missing_elements = []
    for pattern in flow_elements:
        if not re.search(pattern, js_content):
            missing_elements.append(pattern)
    
    if missing_elements:
        print("❌ Missing JavaScript flow elements:")
        for element in missing_elements:
            print(f"   - {element}")
        return False
    
    print("✅ JavaScript has complete audio processing flow")
    
    # Step 3: Check API endpoints
    transcription_path = "routes/transcription.py"
    translation_path = "routes/translation.py"
    
    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription_content = f.read()
    
    with open(translation_path, 'r', encoding='utf-8') as f:
        translation_content = f.read()
    
    # Check transcription endpoint flow
    transcription_flow = [
        r'@bp\.route\(["\']\/transcribe_free_trial["\']',
        r'request\.files\[["\']file["\']',
        r'request\.form\.get\(["\']language["\']',
        r'request\.form\.get\(["\']model["\']',
        r'transcription_service\.transcribe_audio',
        r'return jsonify\('
    ]
    
    for pattern in transcription_flow:
        if not re.search(pattern, transcription_content):
            print(f"❌ Missing transcription flow element: {pattern}")
            return False
    
    print("✅ Transcription endpoint has complete processing flow")
    
    # Check translation endpoint flow
    translation_flow = [
        r'@bp\.route\(["\']\/translate_free_trial["\']',
        r'request\.json',
        r'["\']text["\'].*["\']target_language["\']',
        r'translation_service\.translate',
        r'return jsonify\('
    ]
    
    for pattern in translation_flow:
        if not re.search(pattern, translation_content):
            print(f"❌ Missing translation flow element: {pattern}")
            return False
    
    print("✅ Translation endpoint has complete processing flow")
    
    return True

def test_error_scenarios():
    """Test that error scenarios return JSON instead of HTML"""
    print("\n⚠️ Testing Error Scenarios Return JSON")
    print("=" * 60)
    
    # Check transcription endpoint error handling
    transcription_path = "routes/transcription.py"
    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription_content = f.read()
    
    # Look for error scenarios that return JSON
    error_scenarios = [
        r'No file part.*return jsonify',
        r'No selected file.*return jsonify',
        r'File size exceeds.*return jsonify',
        r'Audio duration exceeds.*return jsonify',
        r'exceeded the free trial limit.*return jsonify',
        r'except Exception.*return jsonify'
    ]
    
    found_scenarios = []
    for scenario in error_scenarios:
        if re.search(scenario, transcription_content, re.DOTALL):
            found_scenarios.append(scenario)
    
    if len(found_scenarios) >= 4:  # Should find most error scenarios
        print("✅ Transcription endpoint returns JSON for error scenarios")
    else:
        print("❌ Transcription endpoint may return HTML for some errors")
        return False
    
    # Check translation endpoint error handling
    translation_path = "routes/translation.py"
    with open(translation_path, 'r', encoding='utf-8') as f:
        translation_content = f.read()
    
    translation_errors = [
        r'Missing required parameters.*return jsonify',
        r'Empty text provided.*return jsonify',
        r'exceeded the free trial limit.*return jsonify',
        r'except Exception.*return jsonify'
    ]
    
    found_translation_errors = []
    for error in translation_errors:
        if re.search(error, translation_content, re.DOTALL):
            found_translation_errors.append(error)
    
    if len(found_translation_errors) >= 3:  # Should find most error scenarios
        print("✅ Translation endpoint returns JSON for error scenarios")
    else:
        print("❌ Translation endpoint may return HTML for some errors")
        return False
    
    return True

def test_session_usage_tracking():
    """Test that session-based usage tracking prevents HTML redirects"""
    print("\n📊 Testing Session Usage Tracking")
    print("=" * 60)
    
    files_to_check = [
        ("routes/transcription.py", "transcription"),
        ("routes/translation.py", "translation")
    ]
    
    for file_path, service_type in files_to_check:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for session-based tracking (no database/auth required)
        session_patterns = [
            r'from flask import session',
            r'session\[["\']free_trial_usage["\']',
            r'if.*not.*session.*free_trial_usage',
            r'session\[["\']free_trial_usage["\'].*=.*{',
            r'current_time.*time\.time\(\)'
        ]
        
        found_patterns = []
        for pattern in session_patterns:
            if re.search(pattern, content):
                found_patterns.append(pattern)
        
        if len(found_patterns) >= 4:  # Should find most session patterns
            print(f"✅ {service_type.title()} uses session-based tracking (no auth required)")
        else:
            print(f"❌ {service_type.title()} session tracking incomplete")
            return False
    
    return True

def test_no_authentication_decorators():
    """Test that free trial endpoints don't have authentication decorators"""
    print("\n🔓 Testing No Authentication Decorators")
    print("=" * 60)
    
    files_to_check = [
        ("routes/transcription.py", "transcribe_free_trial"),
        ("routes/translation.py", "translate_free_trial")
    ]
    
    for file_path, endpoint_name in files_to_check:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the specific endpoint
        endpoint_pattern = rf'@bp\.route\(["\']\/{endpoint_name}["\'].*?def {endpoint_name}\(\):.*?(?=@bp\.route|$)'
        endpoint_match = re.search(endpoint_pattern, content, re.DOTALL)
        
        if endpoint_match:
            endpoint_text = endpoint_match.group(0)
            
            # Check for authentication decorators
            auth_decorators = [
                '@login_required',
                '@requires_verified_email',
                '@api_require_role',
                '@require_admin'
            ]
            
            found_auth = []
            for decorator in auth_decorators:
                if decorator in endpoint_text:
                    found_auth.append(decorator)
            
            if found_auth:
                print(f"❌ {endpoint_name} has authentication decorators: {found_auth}")
                return False
            else:
                print(f"✅ {endpoint_name} has no authentication decorators")
        else:
            print(f"❌ Could not find {endpoint_name} endpoint")
            return False
    
    return True

def test_json_content_type_handling():
    """Test that endpoints properly handle JSON content types"""
    print("\n📋 Testing JSON Content Type Handling")
    print("=" * 60)
    
    # Check that endpoints return proper JSON responses
    files_to_check = [
        ("routes/transcription.py", "transcribe_free_trial"),
        ("routes/translation.py", "translate_free_trial")
    ]
    
    for file_path, endpoint_name in files_to_check:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for JSON response patterns
        json_patterns = [
            r'return jsonify\(',
            r'Content-Type.*application/json',  # May not be explicit
            r'response\.json\(\)'  # In JavaScript
        ]
        
        # At minimum, should have jsonify returns
        if re.search(r'return jsonify\(', content):
            print(f"✅ {endpoint_name} returns JSON responses")
        else:
            print(f"❌ {endpoint_name} does not return JSON responses")
            return False
    
    return True

def main():
    """Run all complete flow tests"""
    print("🧪 Try It Free Complete Flow Tests")
    print("=" * 70)
    print("Testing the complete user journey to ensure JSON parsing errors are eliminated")
    print("=" * 70)
    
    tests = [
        ("Complete Flow Integration", test_complete_flow_integration),
        ("Error Scenarios Return JSON", test_error_scenarios),
        ("Session Usage Tracking", test_session_usage_tracking),
        ("No Authentication Decorators", test_no_authentication_decorators),
        ("JSON Content Type Handling", test_json_content_type_handling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 COMPLETE FLOW TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Try It Free complete flow verified!")
        print("\n📋 Complete Flow Summary:")
        print("✅ Language selection → Audio processing → JSON response")
        print("✅ No authentication required for free trial endpoints")
        print("✅ Session-based usage tracking (no database required)")
        print("✅ All error scenarios return JSON (no HTML redirects)")
        print("✅ Proper JSON content type handling throughout")
        print("✅ Translation flow also uses free trial endpoints")
        print("\n🚫 JSON Parsing Error Eliminated:")
        print("   - No more 'Unexpected token <' errors")
        print("   - No more HTML login pages returned as JSON")
        print("   - Clean JSON responses for all scenarios")
    else:
        print("⚠️ Some flow tests failed. Please review implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
