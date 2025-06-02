"""
Script to create a test transcription in Firebase.
"""
import sys
import traceback
from datetime import datetime
from firebase_config import initialize_firebase
from models.firebase_models import Transcription

def create_test_transcription(email):
    """Create a test transcription for a user."""
    if not email:
        print("No email provided. Please provide a user email.")
        return False
    
    print(f"Creating test transcription for user: {email}")
    try:
        # Create a test transcription
        timestamp = datetime.now().isoformat()
        
        # First try using the model's save method
        print("Using Transcription.save() method...")
        Transcription.save(
            user_email=email,
            text="This is a test transcription created at " + timestamp,
            language="en",
            model="test-model",
            audio_duration=10
        )
        
        # Verify it was saved
        print("Verifying transcription was saved...")
        transcriptions = Transcription.get_by_user(email, limit=1)
        if transcriptions:
            print("✅ Transcription verified in database using get_by_user")
            print(f"Found {len(transcriptions)} transcriptions")
            if transcriptions:
                first_key = list(transcriptions.keys())[0]
                print(f"First transcription: {transcriptions[first_key]}")
        else:
            print("❌ Transcription not found in database using get_by_user")
            
            # Try direct database access
            print("Trying direct database access...")
            user_id = email.replace('.', ',')
            db_ref = initialize_firebase()
            direct_result = db_ref.child(f'transcriptions/{user_id}').get()
            
            if direct_result:
                print("✅ Transcription found with direct database access")
                print(f"Result: {direct_result}")
            else:
                print("❌ Transcription not found with direct database access")
                
                # Try creating directly
                print("Trying to create transcription directly...")
                transcription_data = {
                    'user_email': email,
                    'text': "This is a direct test transcription created at " + timestamp,
                    'language': "en",
                    'model': "direct-test-model",
                    'audio_duration': 10,
                    'timestamp': timestamp
                }
                
                result = db_ref.child(f'transcriptions/{user_id}').push(transcription_data)
                if result:
                    print(f"✅ Direct transcription created with key: {result.key if hasattr(result, 'key') else 'unknown'}")
                    
                    # Verify again
                    direct_result = db_ref.child(f'transcriptions/{user_id}').get()
                    if direct_result:
                        print("✅ Direct transcription verified in database")
                        print(f"Result: {direct_result}")
                    else:
                        print("❌ Direct transcription not found in database")
                else:
                    print("❌ Failed to create direct transcription")
        
        return True
    except Exception as e:
        print(f"❌ Error creating test transcription: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Main function."""
    print("Test Transcription Creator")
    print("=========================\n")
    
    if len(sys.argv) > 1:
        email = sys.argv[1]
        create_test_transcription(email)
    else:
        print("Please provide a user email as an argument.")
        print("Example: python create_test_transcription.py user@example.com")

if __name__ == "__main__":
    main()
