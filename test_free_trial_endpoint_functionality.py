#!/usr/bin/env python3
"""
Test script to verify that the free trial transcription endpoint works without AttributeError.
Creates a simple test to ensure the method call is successful.
"""

import os
import sys
import tempfile
import wave
import struct

def create_test_audio_file():
    """Create a simple test audio file for testing"""
    # Create a temporary WAV file with a simple tone
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    
    # WAV file parameters
    sample_rate = 44100
    duration = 1  # 1 second
    frequency = 440  # A4 note
    
    # Generate audio data
    frames = []
    for i in range(int(sample_rate * duration)):
        # Simple sine wave
        value = int(32767 * 0.3 * (i % (sample_rate // frequency)) / (sample_rate // frequency))
        frames.append(struct.pack('<h', value))
    
    # Write WAV file
    with wave.open(temp_file.name, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(frames))
    
    return temp_file.name

def test_transcription_service_import():
    """Test that the transcription service can be imported without errors"""
    print("📦 Testing TranscriptionService Import")
    print("=" * 50)
    
    try:
        # Add the current directory to Python path
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Try to import the transcription service
        from services.transcription import transcription_service
        print("✅ Successfully imported transcription_service")
        
        # Check if the transcribe method exists
        if hasattr(transcription_service, 'transcribe'):
            print("✅ transcribe() method exists on transcription_service")
        else:
            print("❌ transcribe() method not found on transcription_service")
            return False
        
        # Check if the incorrect method does NOT exist
        if hasattr(transcription_service, 'transcribe_audio'):
            print("⚠️ transcribe_audio() method exists (unexpected)")
        else:
            print("✅ transcribe_audio() method does not exist (correct)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import transcription service: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_method_signature():
    """Test that the transcribe method has the expected signature"""
    print("\n🔍 Testing Method Signature")
    print("=" * 50)
    
    try:
        from services.transcription import transcription_service
        import inspect
        
        # Get the method signature
        transcribe_method = getattr(transcription_service, 'transcribe')
        signature = inspect.signature(transcribe_method)
        
        print(f"✅ Method signature: {signature}")
        
        # Check parameters
        params = list(signature.parameters.keys())
        expected_params = ['audio_data', 'language', 'model']
        
        missing_params = []
        for param in expected_params:
            if param not in params:
                missing_params.append(param)
        
        if missing_params:
            print(f"❌ Missing parameters: {missing_params}")
            return False
        else:
            print("✅ All expected parameters present")
        
        # Check if model has a default value
        model_param = signature.parameters.get('model')
        if model_param and model_param.default != inspect.Parameter.empty:
            print(f"✅ Model parameter has default value: {model_param.default}")
        else:
            print("⚠️ Model parameter has no default value")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking method signature: {e}")
        return False

def test_basic_method_call():
    """Test that the transcribe method can be called without AttributeError"""
    print("\n🧪 Testing Basic Method Call")
    print("=" * 50)
    
    try:
        from services.transcription import transcription_service
        
        # Create minimal test audio data (empty bytes for this test)
        test_audio_data = b'\x00' * 1024  # 1KB of silence
        test_language = 'en'
        test_model = 'gemini-2.0-flash-lite'
        
        print("✅ Preparing to call transcribe() method...")
        print(f"   - Audio data size: {len(test_audio_data)} bytes")
        print(f"   - Language: {test_language}")
        print(f"   - Model: {test_model}")
        
        # This test just verifies the method exists and can be called
        # We don't expect it to succeed with dummy data, but it shouldn't have AttributeError
        try:
            result = transcription_service.transcribe(test_audio_data, test_language, test_model)
            print("✅ Method call completed without AttributeError")
            print(f"   - Result type: {type(result)}")
            if isinstance(result, str):
                print(f"   - Result length: {len(result)} characters")
            return True
            
        except AttributeError as e:
            print(f"❌ AttributeError occurred: {e}")
            return False
        except Exception as e:
            # Other exceptions are expected with dummy data
            print(f"✅ Method call completed without AttributeError (other error expected: {type(e).__name__})")
            return True
            
    except Exception as e:
        print(f"❌ Error during method call test: {e}")
        return False

def test_free_trial_endpoint_code():
    """Test that the free trial endpoint code is syntactically correct"""
    print("\n📝 Testing Free Trial Endpoint Code")
    print("=" * 50)
    
    try:
        # Read the transcription routes file
        routes_path = "routes/transcription.py"
        if not os.path.exists(routes_path):
            print(f"❌ Routes file not found: {routes_path}")
            return False
        
        with open(routes_path, 'r', encoding='utf-8') as f:
            routes_content = f.read()
        
        # Try to compile the code to check for syntax errors
        compile(routes_content, routes_path, 'exec')
        print("✅ Routes file compiles without syntax errors")
        
        # Check for the specific method call
        if 'transcription_service.transcribe(audio_content, language, model)' in routes_content:
            print("✅ Found correct method call in free trial endpoint")
        else:
            print("❌ Correct method call not found in free trial endpoint")
            return False
        
        # Check that incorrect method call is not present
        if 'transcription_service.transcribe_audio(' in routes_content:
            print("❌ Found incorrect method call (transcribe_audio)")
            return False
        else:
            print("✅ No incorrect method calls found")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in routes file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking routes file: {e}")
        return False

def test_error_handling_structure():
    """Test that the error handling structure is correct"""
    print("\n⚠️ Testing Error Handling Structure")
    print("=" * 50)
    
    try:
        routes_path = "routes/transcription.py"
        with open(routes_path, 'r', encoding='utf-8') as f:
            routes_content = f.read()
        
        # Find the free trial function
        import re
        free_trial_pattern = r'def transcribe_free_trial\(\):.*?(?=def|\Z)'
        free_trial_match = re.search(free_trial_pattern, routes_content, re.DOTALL)
        
        if not free_trial_match:
            print("❌ Free trial function not found")
            return False
        
        free_trial_code = free_trial_match.group(0)
        
        # Check for proper error handling
        error_handling_elements = [
            'try:',
            'except Exception as e:',
            'return jsonify(',
            'traceback.format_exc()'
        ]
        
        missing_elements = []
        for element in error_handling_elements:
            if element not in free_trial_code:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing error handling elements: {missing_elements}")
            return False
        else:
            print("✅ All error handling elements present")
        
        # Check that the transcribe call is within the try block
        try_block_pattern = r'try:(.*?)except'
        try_block_match = re.search(try_block_pattern, free_trial_code, re.DOTALL)
        
        if try_block_match:
            try_block = try_block_match.group(1)
            if 'transcription_service.transcribe(' in try_block:
                print("✅ Transcribe call is properly wrapped in try-except")
            else:
                print("❌ Transcribe call not found in try block")
                return False
        else:
            print("❌ Try-except block structure not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking error handling: {e}")
        return False

def main():
    """Run all functionality tests"""
    print("🧪 Free Trial Endpoint Functionality Tests")
    print("=" * 60)
    print("Testing that the AttributeError fix allows proper functionality")
    print("=" * 60)
    
    tests = [
        ("TranscriptionService Import", test_transcription_service_import),
        ("Method Signature", test_method_signature),
        ("Basic Method Call", test_basic_method_call),
        ("Free Trial Endpoint Code", test_free_trial_endpoint_code),
        ("Error Handling Structure", test_error_handling_structure)
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
    print("📊 FUNCTIONALITY TEST SUMMARY")
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
        print("🎉 Free trial endpoint functionality verified!")
        print("\n📋 Functionality Summary:")
        print("✅ TranscriptionService imports successfully")
        print("✅ transcribe() method exists with correct signature")
        print("✅ Method can be called without AttributeError")
        print("✅ Free trial endpoint code is syntactically correct")
        print("✅ Proper error handling structure in place")
        print("\n🚫 AttributeError Eliminated:")
        print("   - 'TranscriptionService' object has no attribute 'transcribe_audio'")
        print("   - Free trial endpoint now uses correct transcribe() method")
        print("   - Try It Free functionality should work without errors")
    else:
        print("⚠️ Some functionality tests failed. Please review implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
