#!/usr/bin/env python3
"""
Test script for progressive transcription functionality.

This script tests:
1. The new /api/transcribe_chunk endpoint
2. Progressive transcription JavaScript functions
3. Integration between frontend and backend
"""

import os
import sys
import time
import wave
import struct
import tempfile
import requests
from pathlib import Path

def create_test_audio(duration_seconds=70, filename="test_chunk.wav"):
    """Create a test audio file for testing"""
    sample_rate = 44100
    frequency = 440  # A4 note
    
    # Generate sine wave
    frames = []
    for i in range(int(duration_seconds * sample_rate)):
        # Create a simple sine wave
        value = int(32767 * 0.3 * (i % (sample_rate // frequency)) / (sample_rate // frequency))
        frames.append(struct.pack('<h', value))
    
    # Write to WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(frames))
    
    print(f"Created test audio file: {filename} ({duration_seconds}s)")
    return filename

def test_chunk_endpoint(audio_file, base_url="http://localhost:5001"):
    """Test the /api/transcribe_chunk endpoint"""
    print(f"\nTesting /api/transcribe_chunk endpoint...")
    
    url = f"{base_url}/api/transcribe_chunk"
    
    # Prepare the request
    with open(audio_file, 'rb') as f:
        files = {'audio': f}
        data = {
            'language': 'en',
            'model': 'gemini-2.0-flash-lite',
            'chunk_number': '0',
            'element_id': 'test-transcript'
        }
        
        print(f"Sending request to {url}")
        print(f"Data: {data}")
        
        try:
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"Response: {result}")
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
            return False

def test_javascript_functions():
    """Test that the JavaScript functions are properly defined"""
    print(f"\nTesting JavaScript function definitions...")
    
    js_files = [
        'static/script.js',
        'static/try_it_free.js'
    ]
    
    required_functions = [
        'startProgressiveTranscription',
        'stopProgressiveTranscription',
        'processCurrentChunk',
        'sendChunkForTranscription',
        'appendChunkResult',
        'simpleDeduplication'
    ]
    
    for js_file in js_files:
        if not os.path.exists(js_file):
            print(f"❌ JavaScript file not found: {js_file}")
            continue
            
        print(f"Checking {js_file}...")
        
        with open(js_file, 'r') as f:
            content = f.read()
            
        for func in required_functions:
            if f"function {func}" in content or f"{func} =" in content:
                print(f"  ✅ {func} found")
            else:
                print(f"  ❌ {func} not found")

def test_backend_service():
    """Test the backend transcription service"""
    print(f"\nTesting backend transcription service...")
    
    try:
        # Import the service
        sys.path.append('.')
        from services.transcription import transcription_service
        
        # Check if the new method exists
        if hasattr(transcription_service, 'transcribe_simple_chunk'):
            print("✅ transcribe_simple_chunk method found")
            
            # Create a small test audio file
            test_file = create_test_audio(5, "small_test.wav")
            
            try:
                with open(test_file, 'rb') as f:
                    audio_data = f.read()
                
                print("Testing transcribe_simple_chunk...")
                result = transcription_service.transcribe_simple_chunk(
                    audio_data, 'en', 'gemini-2.0-flash-lite'
                )
                
                print(f"✅ Transcription successful: {len(result)} characters")
                print(f"Result preview: {result[:100]}...")
                
                # Clean up
                os.unlink(test_file)
                return True
                
            except Exception as e:
                print(f"❌ Transcription failed: {str(e)}")
                # Clean up
                if os.path.exists(test_file):
                    os.unlink(test_file)
                return False
        else:
            print("❌ transcribe_simple_chunk method not found")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import transcription service: {str(e)}")
        return False

def main():
    """Main test function"""
    print("Progressive Transcription Test Suite")
    print("=" * 50)
    
    # Test 1: JavaScript functions
    test_javascript_functions()
    
    # Test 2: Backend service
    backend_success = test_backend_service()
    
    # Test 3: API endpoint (only if backend works)
    if backend_success:
        # Create test audio file
        test_audio = create_test_audio(70, "test_progressive_chunk.wav")
        
        try:
            # Test the endpoint
            endpoint_success = test_chunk_endpoint(test_audio)
            
            # Clean up
            os.unlink(test_audio)
            
            if endpoint_success:
                print(f"\n🎉 All tests passed! Progressive transcription is ready.")
            else:
                print(f"\n⚠️  Backend works but API endpoint failed. Check server logs.")
                
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            # Clean up
            if os.path.exists(test_audio):
                os.unlink(test_audio)
    else:
        print(f"\n❌ Backend service failed. Fix backend issues first.")
    
    print(f"\nTest completed.")

if __name__ == "__main__":
    main()
