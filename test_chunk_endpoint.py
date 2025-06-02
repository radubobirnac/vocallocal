#!/usr/bin/env python3
"""
Test script to verify the chunk transcription endpoint is working
"""

import requests
import time
import io

def test_chunk_endpoint():
    """Test the /api/transcribe_chunk endpoint with a simple request"""
    
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
        'element_id': 'test'
    }
    
    try:
        print("Testing /api/transcribe_chunk endpoint...")
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
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Endpoint is working!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Endpoint returned error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running on port 5001?")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    test_chunk_endpoint()
