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
                # Fallback URL for development - remove in production
                db_url = "https://vocal-local-e1e70-default-rtdb.firebaseio.com"
                print(f"Warning: Using default Firebase URL: {db_url}")

            # Try multiple authentication methods in order of preference
            cred = None
            auth_methods_tried = []

            # Method 1: Use service account credentials from environment variable
            cred_json = os.getenv('FIREBASE_CREDENTIALS')
            if cred_json and not cred:
                auth_methods_tried.append("FIREBASE_CREDENTIALS env var")
                # If the credentials are provided as a JSON string
                try:
                    # Check if it's a JSON string
                    if cred_json.startswith('{'):
                        cred_dict = json.loads(cred_json)
                        cred = credentials.Certificate(cred_dict)
                        print("Using Firebase credentials from environment variable")
                    else:
                        # Assume it's a file path
                        if os.path.exists(cred_json):
                            cred = credentials.Certificate(cred_json)
                            print(f"Using Firebase credentials from file: {cred_json}")
                except Exception as e:
                    print(f"Error using credentials from environment: {str(e)}")

            # Method 2: For local development with service account file
            if not cred:
                cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
                auth_methods_tried.append(f"FIREBASE_CREDENTIALS_PATH: {cred_path}")

                # Try different path resolutions
                possible_paths = [
                    cred_path,  # As provided in .env
                    os.path.join(os.path.dirname(__file__), cred_path),  # Relative to this file
                    os.path.abspath(cred_path)  # Absolute path
                ]

                for path in possible_paths:
                    try:
                        if os.path.exists(path):
                            print(f"Found Firebase credentials at: {path}")
                            cred = credentials.Certificate(path)
                            break
                    except Exception as e:
                        print(f"Error loading credentials from {path}: {str(e)}")

            # Method 3: Try Application Default Credentials as a fallback
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

            # Initialize app with database URL
            firebase_admin.initialize_app(cred, {
                'databaseURL': db_url
            })
            print("Firebase initialized successfully")

        except Exception as e:
            print(f"Error initializing Firebase: {str(e)}")
            traceback.print_exc()
            raise

    # Import db after initialization to avoid circular imports
    from firebase_admin import db
    return db.reference()




