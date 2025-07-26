#!/usr/bin/env python3
"""
Test script to verify that the TranscriptionService AttributeError is fixed.
Tests that the free trial endpoint uses the correct method name and parameters.
"""

import os
import re

def test_transcription_service_method_exists():
    """Test that the TranscriptionService has the correct transcribe method"""
    print("🔍 Testing TranscriptionService Method Existence")
    print("=" * 50)
    
    service_path = "services/transcription.py"
    if not os.path.exists(service_path):
        print(f"❌ TranscriptionService file not found: {service_path}")
        return False
    
    with open(service_path, 'r', encoding='utf-8') as f:
        service_content = f.read()
    
    # Check for the transcribe method definition
    transcribe_method_patterns = [
        r'def transcribe\(self,.*audio_data.*language.*model',
        r'@track_transcription_metrics.*def transcribe\(',
        r'def transcribe\(.*\):.*""".*Transcribe audio data'
    ]
    
    found_method = False
    for pattern in transcribe_method_patterns:
        if re.search(pattern, service_content, re.DOTALL):
            found_method = True
            print("✅ Found transcribe() method in TranscriptionService")
            break
    
    if not found_method:
        print("❌ transcribe() method not found in TranscriptionService")
        return False
    
    # Check that transcribe_audio method does NOT exist (to confirm the error)
    transcribe_audio_pattern = r'def transcribe_audio\('
    if re.search(transcribe_audio_pattern, service_content):
        print("⚠️ Found transcribe_audio() method - this might cause confusion")
    else:
        print("✅ Confirmed: transcribe_audio() method does not exist (as expected)")
    
    return True

def test_free_trial_endpoint_uses_correct_method():
    """Test that the free trial endpoint uses the correct transcribe method"""
    print("\n🔧 Testing Free Trial Endpoint Method Call")
    print("=" * 50)
    
    transcription_routes_path = "routes/transcription.py"
    if not os.path.exists(transcription_routes_path):
        print(f"❌ Transcription routes file not found: {transcription_routes_path}")
        return False
    
    with open(transcription_routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    # Find the free trial endpoint
    free_trial_pattern = r'def transcribe_free_trial\(\):.*?(?=def|\Z)'
    free_trial_match = re.search(free_trial_pattern, routes_content, re.DOTALL)
    
    if not free_trial_match:
        print("❌ transcribe_free_trial() function not found")
        return False
    
    free_trial_code = free_trial_match.group(0)
    
    # Check for correct method call
    correct_method_patterns = [
        r'transcription_service\.transcribe\(',
        r'transcription_service\.transcribe\(audio_content,\s*language,\s*model\)'
    ]
    
    found_correct_call = False
    for pattern in correct_method_patterns:
        if re.search(pattern, free_trial_code):
            found_correct_call = True
            print("✅ Free trial endpoint uses correct transcribe() method")
            break
    
    if not found_correct_call:
        print("❌ Free trial endpoint does not use correct transcribe() method")
        return False
    
    # Check that incorrect method call is NOT present
    incorrect_method_patterns = [
        r'transcription_service\.transcribe_audio\(',
        r'transcription_service\.process_audio\(',
        r'transcription_service\.transcribe_simple\('
    ]
    
    found_incorrect_call = False
    for pattern in incorrect_method_patterns:
        if re.search(pattern, free_trial_code):
            found_incorrect_call = True
            print(f"❌ Found incorrect method call: {pattern}")
            break
    
    if not found_incorrect_call:
        print("✅ No incorrect method calls found")
    
    return found_correct_call and not found_incorrect_call

def test_main_endpoint_method_consistency():
    """Test that both main and free trial endpoints use the same method"""
    print("\n🔄 Testing Method Consistency Between Endpoints")
    print("=" * 50)
    
    transcription_routes_path = "routes/transcription.py"
    with open(transcription_routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    # Find the main transcription endpoint
    main_endpoint_pattern = r'@bp\.route\(["\']\/transcribe["\'].*?def transcribe_audio\(\):.*?(?=@bp\.route|def transcribe_free_trial|\Z)'
    main_endpoint_match = re.search(main_endpoint_pattern, routes_content, re.DOTALL)
    
    if not main_endpoint_match:
        print("❌ Main transcription endpoint not found")
        return False
    
    main_endpoint_code = main_endpoint_match.group(0)
    
    # Find the free trial endpoint
    free_trial_pattern = r'def transcribe_free_trial\(\):.*?(?=def|\Z)'
    free_trial_match = re.search(free_trial_pattern, routes_content, re.DOTALL)
    
    if not free_trial_match:
        print("❌ Free trial endpoint not found")
        return False
    
    free_trial_code = free_trial_match.group(0)
    
    # Check that both use the same transcribe method
    transcribe_call_pattern = r'transcription_service\.transcribe\('
    
    main_uses_transcribe = bool(re.search(transcribe_call_pattern, main_endpoint_code))
    free_trial_uses_transcribe = bool(re.search(transcribe_call_pattern, free_trial_code))
    
    if main_uses_transcribe and free_trial_uses_transcribe:
        print("✅ Both endpoints use the same transcribe() method")
        return True
    elif main_uses_transcribe and not free_trial_uses_transcribe:
        print("❌ Main endpoint uses transcribe() but free trial does not")
        return False
    elif not main_uses_transcribe and free_trial_uses_transcribe:
        print("❌ Free trial uses transcribe() but main endpoint does not")
        return False
    else:
        print("❌ Neither endpoint uses transcribe() method")
        return False

def test_method_signature_compatibility():
    """Test that the method signature is compatible with the call"""
    print("\n📋 Testing Method Signature Compatibility")
    print("=" * 50)
    
    # Check the transcription service method signature
    service_path = "services/transcription.py"
    with open(service_path, 'r', encoding='utf-8') as f:
        service_content = f.read()
    
    # Find the transcribe method signature
    transcribe_signature_pattern = r'def transcribe\(self,\s*([^)]+)\):'
    signature_match = re.search(transcribe_signature_pattern, service_content)
    
    if not signature_match:
        print("❌ Could not find transcribe method signature")
        return False
    
    signature_params = signature_match.group(1)
    print(f"✅ Found transcribe method signature: transcribe(self, {signature_params})")
    
    # Check that it expects audio_data, language, and model parameters
    required_params = ['audio_data', 'language', 'model']
    missing_params = []
    
    for param in required_params:
        if param not in signature_params:
            missing_params.append(param)
    
    if missing_params:
        print(f"❌ Missing required parameters: {missing_params}")
        return False
    else:
        print("✅ All required parameters present in method signature")
    
    # Check the free trial endpoint call
    transcription_routes_path = "routes/transcription.py"
    with open(transcription_routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    # Find the method call in free trial endpoint
    call_pattern = r'transcription_service\.transcribe\(([^)]+)\)'
    call_match = re.search(call_pattern, routes_content)
    
    if not call_match:
        print("❌ Could not find transcribe method call")
        return False
    
    call_params = call_match.group(1)
    print(f"✅ Found method call: transcribe({call_params})")
    
    # Check that the call provides the expected parameters
    expected_call_params = ['audio_content', 'language', 'model']
    for param in expected_call_params:
        if param not in call_params:
            print(f"❌ Missing parameter in call: {param}")
            return False
    
    print("✅ Method call provides all required parameters")
    return True

def test_import_statement():
    """Test that the transcription service is properly imported"""
    print("\n📦 Testing Transcription Service Import")
    print("=" * 50)
    
    transcription_routes_path = "routes/transcription.py"
    with open(transcription_routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    # Check for import statement
    import_patterns = [
        r'from services\.transcription import transcription_service',
        r'import.*transcription_service',
        r'transcription_service.*=.*TranscriptionService'
    ]
    
    found_import = False
    for pattern in import_patterns:
        if re.search(pattern, routes_content):
            found_import = True
            print("✅ Found transcription service import")
            break
    
    if not found_import:
        print("❌ Transcription service import not found")
        return False
    
    # Check that the import is in the free trial function
    free_trial_pattern = r'def transcribe_free_trial\(\):.*?(?=def|\Z)'
    free_trial_match = re.search(free_trial_pattern, routes_content, re.DOTALL)
    
    if free_trial_match:
        free_trial_code = free_trial_match.group(0)
        if 'from services.transcription import transcription_service' in free_trial_code:
            print("✅ Import statement found in free trial function")
            return True
        else:
            print("⚠️ Import statement not in free trial function (may be at module level)")
            return True
    
    return True

def main():
    """Run all transcription service method fix tests"""
    print("🧪 TranscriptionService AttributeError Fix Tests")
    print("=" * 60)
    
    tests = [
        ("TranscriptionService Method Existence", test_transcription_service_method_exists),
        ("Free Trial Endpoint Method Call", test_free_trial_endpoint_uses_correct_method),
        ("Method Consistency Between Endpoints", test_main_endpoint_method_consistency),
        ("Method Signature Compatibility", test_method_signature_compatibility),
        ("Transcription Service Import", test_import_statement)
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
        print("🎉 TranscriptionService AttributeError successfully fixed!")
        print("\n📋 Fix Summary:")
        print("✅ Corrected method name: transcribe_audio() → transcribe()")
        print("✅ Proper method signature: transcribe(audio_data, language, model)")
        print("✅ Consistent with main transcription endpoint")
        print("✅ Proper parameter passing: (audio_content, language, model)")
        print("✅ Import statement verified")
        print("\n🚫 AttributeError Eliminated:")
        print("   - No more 'TranscriptionService' object has no attribute 'transcribe_audio'")
        print("   - Free trial endpoint now uses correct method")
        print("   - Consistent method calls across all endpoints")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
