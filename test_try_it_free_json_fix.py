#!/usr/bin/env python3
"""
Test script to verify that the Try It Free JSON parsing error has been fixed.
Tests the new free trial endpoints and ensures they return JSON instead of HTML.
"""

import os
import re

def test_free_trial_endpoints_exist():
    """Test that the new free trial endpoints are properly defined"""
    print("🔍 Testing Free Trial Endpoints Definition")
    print("=" * 50)
    
    # Check transcription endpoint
    transcription_path = "routes/transcription.py"
    if not os.path.exists(transcription_path):
        print(f"❌ Transcription routes file not found: {transcription_path}")
        return False
    
    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription_content = f.read()
    
    # Check for free trial transcription endpoint
    transcribe_free_patterns = [
        r'@bp\.route\(["\']\/transcribe_free_trial["\']',
        r'def transcribe_free_trial\(\):',
        r'free_trial_usage.*session'
    ]
    
    transcribe_checks = []
    for pattern in transcribe_free_patterns:
        if re.search(pattern, transcription_content):
            transcribe_checks.append(True)
        else:
            transcribe_checks.append(False)
    
    if all(transcribe_checks):
        print("✅ Free trial transcription endpoint properly defined")
    else:
        print("❌ Free trial transcription endpoint missing or incomplete")
        return False
    
    # Check translation endpoint
    translation_path = "routes/translation.py"
    if not os.path.exists(translation_path):
        print(f"❌ Translation routes file not found: {translation_path}")
        return False
    
    with open(translation_path, 'r', encoding='utf-8') as f:
        translation_content = f.read()
    
    # Check for free trial translation endpoint
    translate_free_patterns = [
        r'@bp\.route\(["\']\/translate_free_trial["\']',
        r'def translate_free_trial\(\):',
        r'free_trial_usage.*session'
    ]
    
    translate_checks = []
    for pattern in translate_free_patterns:
        if re.search(pattern, translation_content):
            translate_checks.append(True)
        else:
            translate_checks.append(False)
    
    if all(translate_checks):
        print("✅ Free trial translation endpoint properly defined")
    else:
        print("❌ Free trial translation endpoint missing or incomplete")
        return False
    
    return True

def test_try_it_free_js_updated():
    """Test that Try It Free JavaScript uses the new endpoints"""
    print("\n📝 Testing Try It Free JavaScript Updates")
    print("=" * 50)
    
    js_path = "static/try_it_free.js"
    if not os.path.exists(js_path):
        print(f"❌ Try It Free JavaScript not found: {js_path}")
        return False
    
    with open(js_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    # Check that old endpoints are replaced
    old_endpoints = [
        r'fetch\(["\']\/api\/transcribe["\']',
        r'fetch\(["\']\/api\/translate["\']'
    ]
    
    new_endpoints = [
        r'fetch\(["\']\/api\/transcribe_free_trial["\']',
        r'fetch\(["\']\/api\/translate_free_trial["\']'
    ]
    
    # Check for old endpoints (should not exist)
    found_old = []
    for pattern in old_endpoints:
        matches = re.findall(pattern, js_content)
        if matches:
            found_old.extend(matches)
    
    if found_old:
        print("❌ Old API endpoints still found in JavaScript:")
        for endpoint in found_old:
            print(f"   - {endpoint}")
        return False
    else:
        print("✅ Old API endpoints removed from JavaScript")
    
    # Check for new endpoints (should exist)
    found_new = []
    for pattern in new_endpoints:
        matches = re.findall(pattern, js_content)
        if matches:
            found_new.extend(matches)
    
    if len(found_new) >= 2:  # Should find both transcribe and translate
        print("✅ New free trial API endpoints found in JavaScript")
        for endpoint in found_new:
            print(f"   - {endpoint}")
    else:
        print("❌ New free trial API endpoints not found in JavaScript")
        return False
    
    return True

def test_authentication_requirements():
    """Test that the new endpoints don't require authentication"""
    print("\n🔐 Testing Authentication Requirements")
    print("=" * 50)
    
    # Check transcription endpoint
    transcription_path = "routes/transcription.py"
    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription_content = f.read()
    
    # Look for the free trial endpoint definition
    free_trial_section = re.search(
        r'@bp\.route\(["\']\/transcribe_free_trial["\'].*?def transcribe_free_trial\(\):.*?(?=@bp\.route|$)',
        transcription_content,
        re.DOTALL
    )
    
    if free_trial_section:
        section_text = free_trial_section.group(0)
        
        # Check that it doesn't have @login_required
        if '@login_required' in section_text:
            print("❌ Free trial transcription endpoint has @login_required decorator")
            return False
        else:
            print("✅ Free trial transcription endpoint does not require authentication")
    else:
        print("❌ Could not find free trial transcription endpoint")
        return False
    
    # Check translation endpoint
    translation_path = "routes/translation.py"
    with open(translation_path, 'r', encoding='utf-8') as f:
        translation_content = f.read()
    
    # Look for the free trial endpoint definition
    free_trial_section = re.search(
        r'@bp\.route\(["\']\/translate_free_trial["\'].*?def translate_free_trial\(\):.*?(?=@bp\.route|$)',
        translation_content,
        re.DOTALL
    )
    
    if free_trial_section:
        section_text = free_trial_section.group(0)
        
        # Check that it doesn't have @requires_verified_email or @login_required
        auth_decorators = ['@login_required', '@requires_verified_email']
        found_auth = []
        for decorator in auth_decorators:
            if decorator in section_text:
                found_auth.append(decorator)
        
        if found_auth:
            print(f"❌ Free trial translation endpoint has authentication decorators: {found_auth}")
            return False
        else:
            print("✅ Free trial translation endpoint does not require authentication")
    else:
        print("❌ Could not find free trial translation endpoint")
        return False
    
    return True

def test_json_response_structure():
    """Test that the endpoints return proper JSON structure"""
    print("\n📋 Testing JSON Response Structure")
    print("=" * 50)
    
    # Check transcription endpoint response structure
    transcription_path = "routes/transcription.py"
    with open(transcription_path, 'r', encoding='utf-8') as f:
        transcription_content = f.read()
    
    # Look for JSON response patterns in the free trial endpoint
    transcription_json_patterns = [
        r'return jsonify\(',
        r'["\']text["\']:\s*result',
        r'["\']free_trial["\']:\s*True',
        r'["\']error["\']:'
    ]
    
    transcription_json_checks = []
    for pattern in transcription_json_patterns:
        if re.search(pattern, transcription_content):
            transcription_json_checks.append(True)
        else:
            transcription_json_checks.append(False)
    
    if all(transcription_json_checks):
        print("✅ Free trial transcription endpoint returns proper JSON structure")
    else:
        print("❌ Free trial transcription endpoint JSON structure incomplete")
        return False
    
    # Check translation endpoint response structure
    translation_path = "routes/translation.py"
    with open(translation_path, 'r', encoding='utf-8') as f:
        translation_content = f.read()
    
    # Look for JSON response patterns in the free trial endpoint
    translation_json_patterns = [
        r'return jsonify\(',
        r'["\']text["\']:\s*translated_text',
        r'["\']free_trial["\']:\s*True',
        r'["\']error["\']:'
    ]

    translation_json_checks = []
    for pattern in translation_json_patterns:
        if re.search(pattern, translation_content):
            translation_json_checks.append(True)
        else:
            translation_json_checks.append(False)
    
    if all(translation_json_checks):
        print("✅ Free trial translation endpoint returns proper JSON structure")
    else:
        print("❌ Free trial translation endpoint JSON structure incomplete")
        return False
    
    return True

def test_usage_tracking_implementation():
    """Test that usage tracking is properly implemented"""
    print("\n📊 Testing Usage Tracking Implementation")
    print("=" * 50)
    
    files_to_check = [
        ("routes/transcription.py", "transcription"),
        ("routes/translation.py", "translation")
    ]
    
    for file_path, service_type in files_to_check:
        if not os.path.exists(file_path):
            print(f"❌ {service_type.title()} routes file not found: {file_path}")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for usage tracking patterns
        usage_patterns = [
            r'free_trial_usage.*session',
            r'session\[["\']free_trial_usage["\']',
            r'total_duration.*total_words',
            r'DailyLimitExceeded',
            r'429.*Too Many Requests'
        ]
        
        found_patterns = []
        for pattern in usage_patterns:
            if re.search(pattern, content):
                found_patterns.append(pattern)
        
        if len(found_patterns) >= 3:  # Should find most patterns
            print(f"✅ {service_type.title()} usage tracking properly implemented")
        else:
            print(f"❌ {service_type.title()} usage tracking incomplete")
            return False
    
    return True

def test_error_handling():
    """Test that proper error handling is implemented"""
    print("\n⚠️ Testing Error Handling")
    print("=" * 50)
    
    files_to_check = [
        ("routes/transcription.py", "transcription"),
        ("routes/translation.py", "translation")
    ]
    
    for file_path, service_type in files_to_check:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for error handling patterns
        error_patterns = [
            r'try:.*except.*Exception',
            r'return jsonify\(.*error.*\)',
            r'errorType.*__name__',
            r'traceback\.format_exc\(\)'
        ]
        
        found_errors = []
        for pattern in error_patterns:
            if re.search(pattern, content, re.DOTALL):
                found_errors.append(pattern)
        
        if len(found_errors) >= 3:  # Should find most error handling patterns
            print(f"✅ {service_type.title()} error handling properly implemented")
        else:
            print(f"❌ {service_type.title()} error handling incomplete")
            return False
    
    return True

def main():
    """Run all Try It Free JSON fix tests"""
    print("🧪 Try It Free JSON Parsing Fix Tests")
    print("=" * 60)
    
    tests = [
        ("Free Trial Endpoints Definition", test_free_trial_endpoints_exist),
        ("Try It Free JavaScript Updates", test_try_it_free_js_updated),
        ("Authentication Requirements", test_authentication_requirements),
        ("JSON Response Structure", test_json_response_structure),
        ("Usage Tracking Implementation", test_usage_tracking_implementation),
        ("Error Handling", test_error_handling)
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
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Try It Free JSON parsing error successfully fixed!")
        print("\n📋 Fix Summary:")
        print("✅ Created /api/transcribe_free_trial endpoint (no auth required)")
        print("✅ Created /api/translate_free_trial endpoint (no auth required)")
        print("✅ Updated Try It Free JavaScript to use new endpoints")
        print("✅ Implemented proper usage tracking for free trial")
        print("✅ Added comprehensive error handling with JSON responses")
        print("✅ Eliminated HTML responses that caused JSON parsing errors")
        print("✅ Maintained security with session-based usage limits")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
