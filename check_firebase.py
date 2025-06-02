"""
Script to check Firebase database structure and verify transcription history.
"""
import os
import sys
from datetime import datetime
import traceback
from firebase_config import initialize_firebase
from models.firebase_models import Transcription, Translation, User

def check_firebase_connection():
    """Check if Firebase connection is working."""
    print("Checking Firebase connection...")
    try:
        db_ref = initialize_firebase()
        print("✅ Firebase connection successful")
        return db_ref
    except Exception as e:
        print(f"❌ Firebase connection failed: {str(e)}")
        traceback.print_exc()
        return None

def check_database_structure(db_ref):
    """Check if the database structure is correct."""
    print("\nChecking database structure...")
    try:
        # Check if users collection exists
        users = db_ref.child('users').get()
        if users:
            print(f"✅ Users collection exists with {len(users)} users")
            # Print first user email (with dots replaced by commas)
            if users:
                first_user_id = list(users.keys())[0]
                print(f"   First user ID: {first_user_id}")
                # Try to convert back to email
                if ',' in first_user_id:
                    email = first_user_id.replace(',', '.')
                    print(f"   First user email: {email}")
        else:
            print("❌ Users collection is empty or doesn't exist")

        # Check if transcriptions collection exists
        transcriptions = db_ref.child('transcriptions').get()
        if transcriptions:
            print(f"✅ Transcriptions collection exists with {len(transcriptions)} user folders")
            # Print first user's transcriptions
            if transcriptions:
                first_user_id = list(transcriptions.keys())[0]
                user_transcriptions = db_ref.child(f'transcriptions/{first_user_id}').get()
                if user_transcriptions:
                    print(f"   User {first_user_id} has {len(user_transcriptions)} transcriptions")
                    # Print details of the first transcription
                    first_transcription_id = list(user_transcriptions.keys())[0]
                    first_transcription = user_transcriptions[first_transcription_id]
                    print(f"   First transcription: {first_transcription}")
                else:
                    print(f"   User {first_user_id} has no transcriptions")
        else:
            print("❌ Transcriptions collection is empty or doesn't exist")

        # Check if translations collection exists
        translations = db_ref.child('translations').get()
        if translations:
            print(f"✅ Translations collection exists with {len(translations)} user folders")
        else:
            print("❌ Translations collection is empty or doesn't exist")

        return True
    except Exception as e:
        print(f"❌ Error checking database structure: {str(e)}")
        traceback.print_exc()
        return False

def check_user_transcriptions(email):
    """Check transcriptions for a specific user."""
    if not email:
        print("No email provided. Please provide a user email.")
        return

    print(f"\nChecking transcriptions for user: {email}")
    try:
        # Get user transcriptions
        transcriptions = Transcription.get_by_user(email, limit=50)
        if transcriptions:
            print(f"✅ Found {len(transcriptions)} transcriptions for user {email}")
            # Print details of each transcription
            for id, transcription in transcriptions.items():
                print(f"   ID: {id}")
                print(f"   Timestamp: {transcription.get('timestamp', 'N/A')}")
                print(f"   Language: {transcription.get('language', 'N/A')}")
                print(f"   Model: {transcription.get('model', 'N/A')}")
                text = transcription.get('text', '')
                print(f"   Text: {text[:100]}{'...' if len(text) > 100 else ''}")
                print()
        else:
            print(f"❌ No transcriptions found for user {email}")
            
            # Check if the user's transcription path exists
            user_id = email.replace('.', ',')
            path_exists = Transcription.get_ref(f'transcriptions/{user_id}').get() is not None
            print(f"   Transcription path exists: {path_exists}")
            
            # Try to create a test transcription
            create_test = input("Would you like to create a test transcription for this user? (y/n): ")
            if create_test.lower() == 'y':
                create_test_transcription(email)
    except Exception as e:
        print(f"❌ Error checking user transcriptions: {str(e)}")
        traceback.print_exc()

def create_test_transcription(email):
    """Create a test transcription for a user."""
    print(f"\nCreating test transcription for user: {email}")
    try:
        Transcription.save(
            user_email=email,
            text="This is a test transcription created by the diagnostic script.",
            language="en",
            model="test-model",
            audio_duration=10
        )
        print("✅ Test transcription created successfully")
        
        # Verify it was saved
        print("Verifying transcription was saved...")
        transcriptions = Transcription.get_by_user(email, limit=1)
        if transcriptions:
            print("✅ Transcription verified in database")
        else:
            print("❌ Transcription not found in database after saving")
    except Exception as e:
        print(f"❌ Error creating test transcription: {str(e)}")
        traceback.print_exc()

def main():
    """Main function."""
    print("Firebase Database Diagnostic Tool")
    print("================================\n")
    
    # Check Firebase connection
    db_ref = check_firebase_connection()
    if not db_ref:
        print("Cannot proceed without Firebase connection.")
        return
    
    # Check database structure
    if not check_database_structure(db_ref):
        print("Database structure check failed.")
    
    # Check user transcriptions if email provided
    if len(sys.argv) > 1:
        email = sys.argv[1]
        check_user_transcriptions(email)
    else:
        print("\nTo check transcriptions for a specific user, run:")
        print("python check_firebase.py user@example.com")

if __name__ == "__main__":
    main()
