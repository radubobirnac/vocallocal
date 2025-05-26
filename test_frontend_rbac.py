#!/usr/bin/env python3
"""
Frontend RBAC Test Script for VocalLocal
Tests the integration between backend RBAC and frontend access control.
"""

import sys
import os
import requests
import json

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_endpoints():
    """Test the API endpoints that support frontend RBAC."""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Frontend RBAC API Endpoints")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        "/api/user/role-info",
        "/api/user/info"
    ]
    
    for endpoint in endpoints:
        print(f"\n🔗 Testing {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            else:
                print(f"   Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed - is the server running on {base_url}?")
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timed out")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_usage_check_endpoint():
    """Test the usage check endpoint with different scenarios."""
    base_url = "http://localhost:5000"
    endpoint = "/api/check-usage"
    
    print(f"\n🔍 Testing {endpoint}")
    print("-" * 30)
    
    test_cases = [
        {
            "name": "Transcription Usage Check",
            "data": {"service": "transcription", "amount": 5.0}
        },
        {
            "name": "Translation Usage Check", 
            "data": {"service": "translation", "amount": 100}
        },
        {
            "name": "TTS Usage Check",
            "data": {"service": "tts", "amount": 2.0}
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   📋 {test_case['name']}")
        try:
            response = requests.post(
                f"{base_url}{endpoint}",
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                allowed = data.get('allowed', False)
                role = data.get('role', 'unknown')
                message = data.get('message', 'No message')
                
                status_icon = "✅" if allowed else "❌"
                print(f"      {status_icon} Allowed: {allowed}")
                print(f"      👤 Role: {role}")
                print(f"      💬 Message: {message}")
            else:
                print(f"      ❌ Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"      ❌ Connection failed - is the server running?")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")

def print_frontend_integration_guide():
    """Print guide for testing frontend integration."""
    print("\n📋 Frontend Integration Test Guide")
    print("=" * 50)
    
    print("""
To test the complete RBAC integration:

1. 🚀 Start the VocalLocal application:
   python app.py

2. 🌐 Open your browser and navigate to:
   http://localhost:5000

3. 🔐 Login with your super user account:
   Email: addankianitha28@gmail.com

4. ⚙️ Open the Settings panel (gear icon)

5. 🧪 Test Model Access:
   - Check transcription model dropdown
   - Check translation model dropdown  
   - Check TTS model dropdown
   - Check interpretation model dropdown

6. ✅ Expected Results for Super Users:
   - All models should be selectable (no lock icons)
   - No subscription prompts should appear
   - Console should show: "Usage enforcement bypassed for super_user role"
   - Console should show: "User role loaded for usage enforcement: super_user"

7. 🔍 Check Browser Console:
   - Press F12 to open Developer Tools
   - Go to Console tab
   - Look for RBAC-related messages

8. 🎯 Test Actual Usage:
   - Try transcribing audio with premium models
   - Try translating text with premium models
   - Verify no usage limit modals appear

Console Messages to Look For:
✅ "User role loaded for usage enforcement: super_user"
✅ "Usage enforcement bypassed for super_user role"
✅ "Transcription usage check bypassed for super_user role"
✅ "Translation usage check bypassed for super_user role"
✅ "Model access validated: [model] for [service] (user: [email])"

❌ If you see subscription prompts or usage limit modals, 
   the RBAC integration needs further debugging.
""")

def main():
    """Main function."""
    print("VocalLocal Frontend RBAC Integration Test")
    print("=" * 60)
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test usage check endpoint
    test_usage_check_endpoint()
    
    # Print integration guide
    print_frontend_integration_guide()
    
    print(f"\n🎉 Frontend RBAC Test Completed!")
    print("=" * 60)
    print("Next: Follow the Frontend Integration Test Guide above")
    print("to test the complete user experience in the browser.")

if __name__ == "__main__":
    main()
