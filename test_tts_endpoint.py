#!/usr/bin/env python3
"""
Test the TTS endpoint directly to verify it's working
"""

import requests
import json

def test_tts_endpoint():
    """Test the TTS endpoint with a simple request."""
    print("🔧 Testing TTS Endpoint")
    print("=" * 50)
    
    # TTS endpoint URL
    url = "http://localhost:5001/api/tts"
    
    # Test payload
    payload = {
        "text": "This is a test of the text-to-speech functionality.",
        "language": "en",
        "tts_model": "gemini-2.5-flash-tts"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Making TTS request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ TTS request successful!")
            print(f"Audio data size: {len(response.content)} bytes")
            print(f"Content type: {response.headers.get('content-type', 'Unknown')}")
            
            # Save the audio file for testing
            with open("test_tts_output.mp3", "wb") as f:
                f.write(response.content)
            print("💾 Audio saved as test_tts_output.mp3")
            
            return True
        elif response.status_code == 403:
            print("❌ TTS request forbidden (403)")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
            return False
        elif response.status_code == 401:
            print("❌ TTS request unauthorized (401) - Need to login first")
            print("This test requires authentication. Please login through the web interface first.")
            return False
        else:
            print(f"❌ TTS request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - Is the server running on localhost:5001?")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def main():
    """Main function."""
    print("🚀 TTS Endpoint Test")
    print("=" * 60)
    
    print("📋 Prerequisites:")
    print("  1. Server must be running on localhost:5001")
    print("  2. User must be logged in through web interface")
    print("  3. User must have verified email")
    print("")
    
    success = test_tts_endpoint()
    
    if success:
        print(f"\n" + "="*60)
        print(f"🎉 TTS ENDPOINT WORKING!")
        print(f"="*60)
        print(f"")
        print(f"The TTS endpoint is functioning correctly.")
        print(f"You should now be able to use the interpretation TTS button.")
        print(f"")
    else:
        print(f"\n" + "="*60)
        print(f"❌ TTS ENDPOINT ISSUE")
        print(f"="*60)
        print(f"")
        print(f"The TTS endpoint is not working as expected.")
        print(f"Please check the error details above.")
        print(f"")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
