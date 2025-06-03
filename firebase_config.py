"""Firebase configuration for VocalLocal."""
import os
import json
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv
import traceback

# Load environment variables with explicit path
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

def initialize_firebase():
    """Initialize Firebase connection."""
    # Check if already initialized
    if not firebase_admin._apps:
        try:
            # Get database URL from environment or use default for development
            db_url = os.getenv('FIREBASE_DATABASE_URL')
            if not db_url:
                db_url = "https://vocal-local-e1e70-default-rtdb.firebaseio.com"
                print(f"Warning: Using default Firebase URL: {db_url}")

            # Get storage bucket from environment or use default
            storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET')
            if not storage_bucket:
                storage_bucket = "vocal-local-e1e70.appspot.com"
                print(f"Warning: Using default storage bucket: {storage_bucket}")

            # Prepare config for Firebase initialization
            config = {
                'databaseURL': db_url,
                'storageBucket': storage_bucket
            }

            cred = None
            auth_methods_tried = []

            # Method 1: Try credential files in common deployment locations
            credential_file_paths = [
                "firebase-credentials.json",  # Local development and app root
                os.path.join(os.path.dirname(__file__), "firebase-credentials.json"),  # Relative to this file
                "/etc/secrets/firebase-credentials.json",  # Render and other platforms
                "/etc/secrets/firebase-credentials",  # Alternative naming
                "/app/firebase-credentials.json",  # Heroku and similar platforms
                os.path.expanduser("~/firebase-credentials.json")  # User home directory
            ]

            for path in credential_file_paths:
                if os.path.exists(path):
                    auth_methods_tried.append(f"Credential file: {path}")
                    try:
                        print(f"Found Firebase credentials at: {path}")
                        cred = credentials.Certificate(path)
                        print(f"Using Firebase credentials from: {path}")
                        break
                    except Exception as e:
                        print(f"Error loading credentials from {path}: {str(e)}")

            # Method 2: Try environment variables (for advanced users)
            if not cred:
                # Try FIREBASE_CREDENTIALS_JSON first (new format)
                cred_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
                if not cred_json:
                    # Fallback to legacy FIREBASE_CREDENTIALS
                    cred_json = os.getenv('FIREBASE_CREDENTIALS')

                if cred_json:
                    auth_methods_tried.append("Environment variable (JSON)")
                    try:
                        print("Found Firebase credentials in environment variable")
                        cred_dict = json.loads(cred_json)
                        cred = credentials.Certificate(cred_dict)
                        print("Using Firebase credentials from environment variable")
                    except Exception as e:
                        print(f"Error using environment variable credentials: {str(e)}")

            # Method 3: Try custom file path from environment
            if not cred:
                cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
                if cred_path and os.path.exists(cred_path):
                    auth_methods_tried.append(f"Custom path: {cred_path}")
                    try:
                        print(f"Found Firebase credentials at custom path: {cred_path}")
                        cred = credentials.Certificate(cred_path)
                        print(f"Using Firebase credentials from: {cred_path}")
                    except Exception as e:
                        print(f"Error loading credentials from {cred_path}: {str(e)}")

            # Method 4: Try Application Default Credentials as a fallback
            if not cred:
                auth_methods_tried.append("Application Default Credentials")
                try:
                    print("Attempting to use Application Default Credentials")
                    # This will use ADC if available
                    cred = None  # Using None will trigger ADC
                    print("Using Application Default Credentials")
                except Exception as e:
                    print(f"Error using Application Default Credentials: {str(e)}")

            # If all methods failed, raise an error
            if cred is None and firebase_admin._apps:
                # If Firebase is already initialized, we can proceed
                print("Firebase already initialized, proceeding without new credentials")
            elif cred is None:
                raise ValueError(f"Could not initialize Firebase. Tried: {', '.join(auth_methods_tried)}")

            # Initialize app with database URL and storage bucket
            firebase_admin.initialize_app(cred, config)
            print("Firebase initialized successfully")

        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            traceback.print_exc()
            raise

    # Import db after initialization to avoid circular imports
    from firebase_admin import db
    return db.reference()
