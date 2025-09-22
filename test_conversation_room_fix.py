#!/usr/bin/env python3
"""
Test script to verify the Firebase conversation room fix
"""

import sys
import os
import time
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_conversation_room_operations():
    """Test conversation room creation and participant operations"""
    
    print("🧪 Testing Conversation Room Operations with Email Encoding Fix")
    print("=" * 70)
    
    try:
        # Import Firebase models
        from models.firebase_models import ConversationRoom
        
        # Test data
        room_code = f"TEST{int(time.time() % 10000):04d}"  # Generate unique room code
        creator_email = "creator@example.com"
        participant_email = "participant.test@gmail.com"  # Email with period to test encoding
        
        print(f"📝 Test Parameters:")
        print(f"   Room Code: {room_code}")
        print(f"   Creator Email: {creator_email}")
        print(f"   Participant Email: {participant_email}")
        
        # Step 1: Create room
        print(f"\n🏗️  Step 1: Creating conversation room...")
        room_data = ConversationRoom.create(room_code, creator_email, max_participants=3)
        
        if room_data:
            print(f"   ✅ Room created successfully")
            print(f"   Room status: {room_data.get('status')}")
            print(f"   Participant count: {room_data.get('participant_count')}")
        else:
            print(f"   ❌ Failed to create room")
            return False
        
        # Step 2: Add creator as participant
        print(f"\n👤 Step 2: Adding creator as participant...")
        success, message = ConversationRoom.add_participant(
            room_code, creator_email, "en", "es"
        )
        
        if success:
            print(f"   ✅ Creator added successfully: {message}")
        else:
            print(f"   ❌ Failed to add creator: {message}")
            return False
        
        # Step 3: Add second participant (with period in email)
        print(f"\n👥 Step 3: Adding participant with period in email...")
        success, message = ConversationRoom.add_participant(
            room_code, participant_email, "es", "en"
        )
        
        if success:
            print(f"   ✅ Participant added successfully: {message}")
        else:
            print(f"   ❌ Failed to add participant: {message}")
            return False
        
        # Step 4: Verify room data
        print(f"\n🔍 Step 4: Verifying room data...")
        updated_room_data = ConversationRoom.get_by_code(room_code)
        
        if updated_room_data:
            print(f"   ✅ Room data retrieved successfully")
            print(f"   Status: {updated_room_data.get('status')}")
            print(f"   Participant count: {updated_room_data.get('participant_count')}")
            
            # Check participants with encoded keys
            participants = updated_room_data.get('participants', {})
            print(f"   Participants (encoded keys): {list(participants.keys())}")
            
            # Test the helper function for decoded participants
            decoded_participants = ConversationRoom.get_participants_with_decoded_emails(updated_room_data)
            print(f"   Participants (decoded keys): {list(decoded_participants.keys())}")
            
            # Verify both emails are present
            if creator_email in decoded_participants and participant_email in decoded_participants:
                print(f"   ✅ Both participants found with correct decoded emails")
            else:
                print(f"   ❌ Participant emails not found correctly")
                return False
        else:
            print(f"   ❌ Failed to retrieve room data")
            return False
        
        # Step 5: Update participant status
        print(f"\n🔄 Step 5: Testing participant status update...")
        success = ConversationRoom.update_participant_status(room_code, participant_email, 'connected')
        
        if success:
            print(f"   ✅ Participant status updated successfully")
        else:
            print(f"   ❌ Failed to update participant status")
            return False
        
        # Step 6: Remove participant
        print(f"\n🚪 Step 6: Testing participant removal...")
        success, message = ConversationRoom.remove_participant(room_code, participant_email)
        
        if success:
            print(f"   ✅ Participant removed successfully: {message}")
        else:
            print(f"   ❌ Failed to remove participant: {message}")
            return False
        
        # Step 7: Cleanup - remove room
        print(f"\n🧹 Step 7: Cleaning up test room...")
        try:
            room_ref = ConversationRoom.get_ref(f'conversation_rooms/{room_code}')
            room_ref.delete()
            print(f"   ✅ Test room cleaned up successfully")
        except Exception as e:
            print(f"   ⚠️  Cleanup warning: {str(e)}")
        
        print(f"\n🎉 All conversation room operations completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Conversation Room Fix Verification\n")
    
    # Initialize Firebase
    try:
        from firebase_config import initialize_firebase
        initialize_firebase()
        print("✅ Firebase initialized successfully\n")
    except Exception as e:
        print(f"❌ Firebase initialization failed: {str(e)}")
        print("Make sure Firebase credentials are properly configured.")
        sys.exit(1)
    
    # Run the test
    success = test_conversation_room_operations()
    
    print(f"\n📊 Test Result: {'✅ SUCCESS' if success else '❌ FAILURE'}")
    
    if success:
        print(f"\n🎉 The Firebase JSON parsing error fix is working correctly!")
        print(f"   - Email addresses are properly encoded for Firebase keys")
        print(f"   - All conversation room operations work as expected")
        print(f"   - Participants can join rooms without Firebase errors")
        sys.exit(0)
    else:
        print(f"\n❌ The fix needs more work or there are other issues.")
        sys.exit(1)
