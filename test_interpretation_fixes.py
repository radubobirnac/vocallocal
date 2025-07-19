#!/usr/bin/env python3
"""
Test script to verify both the Gemini model fix and TTS functionality
for the AI Interpretation service.
"""

import requests
import json
import time
import sys
import os

# Configuration
BASE_URL = "http://localhost:5000"
TEST_TEXT = "Hello, this is a test message for AI interpretation and text-to-speech functionality."

def test_interpretation_api():
    """Test the interpretation API with the fixed Gemini model."""
    print("🧪 Testing Interpretation API...")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/interpret"
    payload = {
        "text": TEST_TEXT,
        "tone": "professional",
        "interpretation_model": "gemini-2.5-flash"
    }
    
    try:
        print(f"📤 Sending request to: {url}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Interpretation API Success!")
            print(f"📝 Interpretation Result: {data.get('interpretation', 'No interpretation found')}")
            return True, data.get('interpretation', '')
        else:
            print(f"❌ Interpretation API Failed!")
            print(f"📄 Error Response: {response.text}")
            return False, ""
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False, ""
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False, ""

def test_tts_api(text):
    """Test the TTS API with interpretation text."""
    print("\n🔊 Testing TTS API...")
    print("=" * 50)
    
    url = f"{BASE_URL}/api/tts"
    payload = {
        "text": text or TEST_TEXT,
        "language": "en",
        "model": "auto"
    }
    
    try:
        print(f"📤 Sending request to: {url}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            audio_data = response.content
            print("✅ TTS API Success!")
            print(f"🎵 Audio Data Size: {len(audio_data)} bytes")
            print(f"🎵 Content Type: {response.headers.get('content-type', 'Unknown')}")
            return True
        else:
            print(f"❌ TTS API Failed!")
            print(f"📄 Error Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_complete_workflow():
    """Test the complete interpretation + TTS workflow."""
    print("\n🔄 Testing Complete Workflow...")
    print("=" * 50)
    
    # Step 1: Generate interpretation
    print("Step 1: Generating interpretation...")
    interpretation_success, interpretation_text = test_interpretation_api()
    
    if not interpretation_success:
        print("❌ Workflow failed at interpretation step")
        return False
    
    # Step 2: Test TTS with interpretation text
    print("\nStep 2: Testing TTS with interpretation text...")
    tts_success = test_tts_api(interpretation_text)
    
    if not tts_success:
        print("❌ Workflow failed at TTS step")
        return False
    
    print("\n✅ Complete workflow successful!")
    return True

def check_server_status():
    """Check if the server is running."""
    print("🌐 Checking Server Status...")
    print("=" * 50)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"⚠️ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not accessible: {e}")
        return False

def check_file_modifications():
    """Check that the required file modifications are in place."""
    print("\n📁 Checking File Modifications...")
    print("=" * 50)
    
    files_to_check = [
        {
            "path": "services/interpretation.py",
            "search_text": "gemini-2.5-flash-preview-05-20",
            "description": "Updated Gemini model in interpretation service"
        },
        {
            "path": "static/script.js",
            "search_text": "basic-interpretation",
            "description": "TTS support for interpretation in script.js"
        }
    ]
    
    all_good = True
    
    for file_check in files_to_check:
        file_path = file_check["path"]
        search_text = file_check["search_text"]
        description = file_check["description"]
        
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if search_text in content:
                        print(f"✅ {description}")
                    else:
                        print(f"❌ {description} - Text not found")
                        all_good = False
            else:
                print(f"❌ {description} - File not found: {file_path}")
                all_good = False
        except Exception as e:
            print(f"❌ {description} - Error reading file: {e}")
            all_good = False
    
    return all_good

def main():
    """Main test function."""
    print("🚀 AI Interpretation TTS Fix Verification")
    print("=" * 60)
    print(f"🎯 Target Server: {BASE_URL}")
    print(f"📝 Test Text: {TEST_TEXT}")
    print("=" * 60)
    
    # Check file modifications
    files_ok = check_file_modifications()
    
    # Check server status
    server_ok = check_server_status()
    
    if not server_ok:
        print("\n❌ Cannot proceed with API tests - server is not accessible")
        print("💡 Please start the Flask application and try again")
        return False
    
    # Test individual components
    interpretation_ok, interpretation_text = test_interpretation_api()
    tts_ok = test_tts_api(TEST_TEXT)
    
    # Test complete workflow
    workflow_ok = test_complete_workflow()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    print(f"📁 File Modifications: {'✅ PASS' if files_ok else '❌ FAIL'}")
    print(f"🌐 Server Status: {'✅ PASS' if server_ok else '❌ FAIL'}")
    print(f"🧪 Interpretation API: {'✅ PASS' if interpretation_ok else '❌ FAIL'}")
    print(f"🔊 TTS API: {'✅ PASS' if tts_ok else '❌ FAIL'}")
    print(f"🔄 Complete Workflow: {'✅ PASS' if workflow_ok else '❌ FAIL'}")
    
    all_tests_passed = all([files_ok, server_ok, interpretation_ok, tts_ok, workflow_ok])
    
    if all_tests_passed:
        print("\n🎉 All tests passed! The interpretation TTS fix is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
