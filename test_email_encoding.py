#!/usr/bin/env python3
"""
Test script to verify email encoding/decoding for Firebase keys
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.firebase_models import ConversationRoom

def test_email_encoding():
    """Test email encoding and decoding functions"""
    
    test_emails = [
        "user@example.com",
        "test.user@gmail.com", 
        "complex.email+tag@domain.co.uk",
        "user.with.dots@test.org",
        "simple@test.com"
    ]
    
    print("🧪 Testing Email Encoding/Decoding for Firebase Keys")
    print("=" * 60)
    
    all_passed = True
    
    for email in test_emails:
        print(f"\n📧 Testing: {email}")
        
        # Encode
        encoded = ConversationRoom.encode_email_for_firebase_key(email)
        print(f"   Encoded: {encoded}")
        
        # Decode
        decoded = ConversationRoom.decode_email_from_firebase_key(encoded)
        print(f"   Decoded: {decoded}")
        
        # Verify
        if decoded == email:
            print(f"   ✅ PASS: Encoding/decoding successful")
        else:
            print(f"   ❌ FAIL: Original != Decoded")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests PASSED! Email encoding/decoding works correctly.")
    else:
        print("❌ Some tests FAILED! Check the encoding/decoding logic.")
    
    return all_passed

def test_firebase_key_restrictions():
    """Test that encoded emails don't contain Firebase-restricted characters"""
    
    print("\n🔒 Testing Firebase Key Restrictions")
    print("=" * 60)
    
    restricted_chars = ['.', '#', '$', '[', ']', '/']
    test_emails = [
        "user@example.com",
        "test.user@gmail.com", 
        "complex.email+tag@domain.co.uk"
    ]
    
    all_passed = True
    
    for email in test_emails:
        encoded = ConversationRoom.encode_email_for_firebase_key(email)
        print(f"\n📧 Testing: {email}")
        print(f"   Encoded: {encoded}")
        
        has_restricted = False
        for char in restricted_chars:
            if char in encoded:
                print(f"   ❌ FAIL: Contains restricted character '{char}'")
                has_restricted = True
                all_passed = False
        
        if not has_restricted:
            print(f"   ✅ PASS: No restricted characters found")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All Firebase key restriction tests PASSED!")
    else:
        print("❌ Some Firebase key restriction tests FAILED!")
    
    return all_passed

if __name__ == "__main__":
    print("🚀 Starting Firebase Email Encoding Tests\n")
    
    # Run tests
    encoding_passed = test_email_encoding()
    restriction_passed = test_firebase_key_restrictions()
    
    print(f"\n📊 Test Results Summary:")
    print(f"   Email Encoding/Decoding: {'✅ PASS' if encoding_passed else '❌ FAIL'}")
    print(f"   Firebase Key Restrictions: {'✅ PASS' if restriction_passed else '❌ FAIL'}")
    
    if encoding_passed and restriction_passed:
        print(f"\n🎉 All tests PASSED! The fix should resolve the Firebase JSON parsing error.")
        sys.exit(0)
    else:
        print(f"\n❌ Some tests FAILED! The fix needs more work.")
        sys.exit(1)
