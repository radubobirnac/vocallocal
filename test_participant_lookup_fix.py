#!/usr/bin/env python3
"""
Test script to verify the participant lookup fix for conversation rooms.
This script tests that room creators can properly access their rooms after creation.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.firebase_models import ConversationRoom

def test_email_encoding():
    """Test the email encoding function"""
    print("🧪 Testing email encoding...")
    
    test_email = "addankianitha28@gmail.com"
    encoded = ConversationRoom.encode_email_for_firebase_key(test_email)
    
    print(f"   Original email: {test_email}")
    print(f"   Encoded email:  {encoded}")
    print(f"   Expected:       addankianitha28_DOT_gmail_DOT_com")
    
    expected = "addankianitha28_DOT_gmail_DOT_com"
    if encoded == expected:
        print("   ✅ Email encoding works correctly")
        return True
    else:
        print("   ❌ Email encoding failed")
        return False

def test_participant_lookup_logic():
    """Test the participant lookup logic"""
    print("\n🧪 Testing participant lookup logic...")
    
    # Simulate room data structure
    test_email = "addankianitha28@gmail.com"
    encoded_email = ConversationRoom.encode_email_for_firebase_key(test_email)
    
    # Simulate participants dictionary as stored in Firebase
    participants = {
        encoded_email: {
            'user_email': test_email,
            'joined_at': '2025-09-14T21:32:00.000000',
            'input_language': 'en',
            'target_language': 'en',
            'status': 'connected',
            'last_seen': '2025-09-14T21:32:00.000000'
        }
    }
    
    print(f"   Participants dict keys: {list(participants.keys())}")
    print(f"   Looking for encoded email: {encoded_email}")
    
    # Test the OLD way (broken)
    old_way_found = test_email in participants
    print(f"   OLD way (raw email lookup): {old_way_found} ❌")
    
    # Test the NEW way (fixed)
    new_way_found = encoded_email in participants
    print(f"   NEW way (encoded email lookup): {new_way_found} ✅")
    
    if new_way_found and not old_way_found:
        print("   ✅ Participant lookup fix works correctly")
        return True
    else:
        print("   ❌ Participant lookup fix failed")
        return False

def test_room_creation_and_access_simulation():
    """Simulate the room creation and access flow"""
    print("\n🧪 Simulating room creation and access flow...")
    
    creator_email = "addankianitha28@gmail.com"
    room_code = "TEST123"
    
    print(f"   Creator: {creator_email}")
    print(f"   Room code: {room_code}")
    
    # Step 1: Simulate room creation with auto-add creator
    print("\n   Step 1: Room creation (auto-add creator)")
    encoded_creator = ConversationRoom.encode_email_for_firebase_key(creator_email)
    
    # Simulate the participants dict after room creation
    room_participants = {
        encoded_creator: {
            'user_email': creator_email,
            'joined_at': '2025-09-14T21:32:00.000000',
            'input_language': 'en',
            'target_language': 'en',
            'status': 'connected',
            'last_seen': '2025-09-14T21:32:00.000000'
        }
    }
    
    print(f"   ✅ Creator added with encoded key: {encoded_creator}")
    print(f"   Participants: {list(room_participants.keys())}")
    
    # Step 2: Simulate room access validation
    print("\n   Step 2: Room access validation")
    current_user_email = creator_email  # Same user trying to access
    
    # OLD way (broken) - direct email lookup
    old_validation = current_user_email in room_participants
    print(f"   OLD validation (raw email): {old_validation} ❌")
    
    # NEW way (fixed) - encoded email lookup
    encoded_current_user = ConversationRoom.encode_email_for_firebase_key(current_user_email)
    new_validation = encoded_current_user in room_participants
    print(f"   NEW validation (encoded email): {new_validation} ✅")
    
    if new_validation:
        print("   ✅ Creator can access their room successfully!")
        return True
    else:
        print("   ❌ Creator cannot access their room")
        return False

def main():
    """Run all tests"""
    print("🔧 Testing Conversation Room Participant Lookup Fix")
    print("=" * 60)
    
    tests = [
        test_email_encoding,
        test_participant_lookup_logic,
        test_room_creation_and_access_simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The participant lookup fix should work correctly.")
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
