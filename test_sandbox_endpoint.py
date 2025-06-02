#!/usr/bin/env python3
"""
Test script to verify the new test sandbox endpoint works correctly
"""

import requests
import time
import io

def test_sandbox_endpoint():
    """Test the /api/test_transcribe_chunk endpoint"""
    
    # Create a small dummy audio file (just some bytes)
    dummy_audio = b'\x00' * 1000  # 1KB of zeros
    
    # Create form data
    files = {
        'audio': ('test_chunk.webm', io.BytesIO(dummy_audio), 'audio/webm')
    }
    
    data = {
        'language': 'en',
        'model': 'gemini-2.0-flash-lite',
        'chunk_number': '0',
        'element_id': 'test-sandbox'
    }
    
    try:
        print("Testing /api/test_transcribe_chunk endpoint...")
        print(f"Sending {len(dummy_audio)} bytes of dummy audio data")
        
        start_time = time.time()
        response = requests.post(
            'http://localhost:5001/api/test_transcribe_chunk',
            files=files,
            data=data,
            timeout=30  # 30 second timeout
        )
        end_time = time.time()
        
        print(f"Response received in {end_time - start_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Test endpoint is working!")
            result = response.json()
            print(f"Response: {result}")
            
            # Check if it's marked as test mode
            if result.get('test_mode'):
                print("✅ Test mode flag is present")
            else:
                print("⚠️ Test mode flag is missing")
                
        elif response.status_code == 403:
            print("⚠️ Test endpoint is disabled (not in development mode)")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Test endpoint returned error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the Flask app is running on port 5001")
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def test_production_endpoint():
    """Test the production endpoint to verify it still has usage tracking"""
    
    # Create a small dummy audio file (just some bytes)
    dummy_audio = b'\x00' * 1000  # 1KB of zeros
    
    # Create form data
    files = {
        'audio': ('test_chunk.webm', io.BytesIO(dummy_audio), 'audio/webm')
    }
    
    data = {
        'language': 'en',
        'model': 'gemini-2.0-flash-lite',
        'chunk_number': '0',
        'element_id': 'basic-transcript'
    }
    
    try:
        print("\nTesting /api/transcribe_chunk endpoint (production)...")
        print(f"Sending {len(dummy_audio)} bytes of dummy audio data")
        
        start_time = time.time()
        response = requests.post(
            'http://localhost:5001/api/transcribe_chunk',
            files=files,
            data=data,
            timeout=30  # 30 second timeout
        )
        end_time = time.time()
        
        print(f"Response received in {end_time - start_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 429:
            print("✅ Production endpoint has usage tracking (429 Too Many Requests)")
            result = response.json()
            if 'FreeTrial_DailyLimitExceeded' in result.get('errorType', ''):
                print("✅ Free trial limit is being enforced")
        elif response.status_code == 200:
            print("⚠️ Production endpoint worked (might have usage remaining)")
            result = response.json()
            print(f"Response: {result}")
        else:
            print(f"❌ Production endpoint returned unexpected error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the Flask app is running on port 5001")
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == '__main__':
    print("=" * 60)
    print("VocalLocal Test Sandbox Endpoint Verification")
    print("=" * 60)
    
    # Test the new test endpoint
    test_sandbox_endpoint()
    
    # Test the production endpoint to verify it still has limits
    test_production_endpoint()
    
    print("\n" + "=" * 60)
    print("Test completed!")
