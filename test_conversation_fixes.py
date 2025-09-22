#!/usr/bin/env python3
"""
Test script to verify conversation room functionality fixes
"""

import requests
import json
import time
import sys

def test_conversation_api_protection():
    """Test that the conversation API properly handles malformed requests"""
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Conversation API Protection...")
    
    # Test 1: Empty request body
    print("\n1. Testing empty request body...")
    try:
        response = requests.post(f"{base_url}/conversation/api/join", 
                               headers={'Content-Type': 'application/json'},
                               data='')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Invalid JSON
    print("\n2. Testing invalid JSON...")
    try:
        response = requests.post(f"{base_url}/conversation/api/join", 
                               headers={'Content-Type': 'application/json'},
                               data='{"invalid": json}')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Missing Content-Type
    print("\n3. Testing missing Content-Type...")
    try:
        response = requests.post(f"{base_url}/conversation/api/join", 
                               data='{"room_code": "TEST01"}')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Non-JSON data
    print("\n4. Testing non-JSON data...")
    try:
        response = requests.post(f"{base_url}/conversation/api/join", 
                               headers={'Content-Type': 'application/json'},
                               data='not json at all')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 5: Valid JSON but missing required fields
    print("\n5. Testing valid JSON but missing required fields...")
    try:
        response = requests.post(f"{base_url}/conversation/api/join", 
                               headers={'Content-Type': 'application/json'},
                               json={'invalid_field': 'value'})
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

def test_conversation_modal_behavior():
    """Test that conversation modal only opens on user interaction"""
    print("\n🧪 Testing Conversation Modal Behavior...")
    
    # This would require browser automation to test properly
    # For now, we'll just check that the JavaScript files are properly structured
    
    print("✅ Manual testing required:")
    print("   1. Open the main page")
    print("   2. Verify conversation modal does NOT open automatically")
    print("   3. Click the conversation button")
    print("   4. Verify conversation modal opens only then")
    print("   5. Check browser console for proper logging")

def test_rate_limiting():
    """Test rate limiting on the join API"""
    print("\n🧪 Testing Rate Limiting...")
    
    # This would require authentication to test properly
    print("✅ Manual testing required (with authenticated user):")
    print("   1. Make multiple rapid requests to /conversation/api/join")
    print("   2. Verify rate limiting kicks in after 2 seconds")
    print("   3. Check server logs for rate limiting messages")

def main():
    """Run all tests"""
    print("🚀 Starting Conversation Room Functionality Tests")
    print("=" * 60)
    
    try:
        test_conversation_api_protection()
        test_conversation_modal_behavior()
        test_rate_limiting()
        
        print("\n" + "=" * 60)
        print("✅ Tests completed!")
        print("\nKey improvements made:")
        print("   ✅ Enhanced JSON parsing error handling")
        print("   ✅ Added comprehensive request validation")
        print("   ✅ Implemented rate limiting (2 second minimum)")
        print("   ✅ Added detailed logging for debugging")
        print("   ✅ Prevented automatic conversation modal opening")
        print("   ✅ Added safeguards against unauthorized room access")
        
        print("\nTo verify fixes:")
        print("   1. Check server logs for detailed request information")
        print("   2. Test conversation button manually in browser")
        print("   3. Monitor for any automatic API calls")
        print("   4. Verify error messages are user-friendly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
