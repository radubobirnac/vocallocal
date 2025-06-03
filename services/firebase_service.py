"""Firebase service for VocalLocal."""
import os
import logging
import json
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)

# Try to import Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    logger.warning("Firebase Admin SDK not available. Using mock implementation.")
    FIREBASE_AVAILABLE = False

class FirebaseService:
    """Service for Firebase interactions (Auth, Firestore, Storage)."""

    _instance = None

    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure one Firebase connection."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize Firebase connection with appropriate credentials."""
        self.initialized = False

        if not FIREBASE_AVAILABLE:
            logger.warning("Using mock Firebase services (Firebase Admin SDK not installed)")
            self._setup_mock_services()
            return

        try:
            # Check if already initialized
            if not firebase_admin._apps:
                cred = None

                # Method 1: Try credential files in common locations
                credential_file_paths = [
                    "firebase-credentials.json",  # App root
                    "/etc/secrets/firebase-credentials.json",  # Deployment platforms
                    "/app/firebase-credentials.json",  # Heroku-style
                    os.path.expanduser("~/firebase-credentials.json")  # User home
                ]

                for path in credential_file_paths:
                    if os.path.exists(path):
                        try:
                            cred = credentials.Certificate(path)
                            logger.info(f"Using Firebase credentials from: {path}")
                            break
                        except Exception as e:
                            logger.warning(f"Error loading credentials from {path}: {str(e)}")

                # Method 2: Try environment variables (fallback)
                if not cred:
                    cred_json = os.environ.get('FIREBASE_CREDENTIALS_JSON') or os.environ.get('FIREBASE_CREDENTIALS')
                    if cred_json:
                        try:
                            cred_dict = json.loads(cred_json)
                            cred = credentials.Certificate(cred_dict)
                            logger.info("Using Firebase credentials from environment variable")
                        except Exception as e:
                            logger.warning(f"Error using environment variable credentials: {str(e)}")

                # Method 3: Try custom file path
                if not cred:
                    cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
                    if cred_path and os.path.exists(cred_path):
                        try:
                            cred = credentials.Certificate(cred_path)
                            logger.info(f"Using Firebase credentials from custom path: {cred_path}")
                        except Exception as e:
                            logger.warning(f"Error loading credentials from {cred_path}: {str(e)}")

                # Method 4: Fall back to application default credentials
                if not cred:
                    cred = None  # This will use Application Default Credentials

                # Initialize app with database URL and storage bucket if available
                db_url = os.environ.get('FIREBASE_DATABASE_URL')
                storage_bucket = os.environ.get('FIREBASE_STORAGE_BUCKET', 'vocal-local-e1e70.appspot.com')

                config = {}
                if db_url:
                    config['databaseURL'] = db_url
                if storage_bucket:
                    config['storageBucket'] = storage_bucket

                firebase_admin.initialize_app(cred, config)

            # Initialize services
            self.db = firestore.client()

            # Initialize storage bucket with explicit bucket name
            try:
                storage_bucket_name = os.environ.get('FIREBASE_STORAGE_BUCKET', 'vocal-local-e1e70.appspot.com')
                self.bucket = storage.bucket(storage_bucket_name)
                logger.info(f"Firebase storage initialized with bucket: {storage_bucket_name}")
            except Exception as storage_error:
                logger.warning(f"Failed to initialize Firebase storage: {str(storage_error)}")
                self.bucket = None

            self.initialized = True
            logger.info("Firebase services initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            # Set up mock services for any environment when Firebase fails
            self._setup_mock_services()
            logger.warning("Using mock Firebase services due to initialization failure")

    def _setup_mock_services(self):
        """Set up mock services for local development."""
        self.db = MagicMock()
        self.bucket = MagicMock()

        # Create a mock reference that behaves like Firebase Realtime Database
        class MockRef:
            def get(self):
                return {}
            def set(self, data):
                return True
            def push(self, data):
                return MockRef()
            def child(self, path):
                return MockRef()

        # Add get_ref method to self for mock mode
        self._mock_ref = MockRef()

        self.initialized = True
        logger.warning("Using mock Firebase services")

    def store_file_metadata(self, user_id, file_id, metadata):
        """Store file metadata in Firestore."""
        if not self.initialized:
            logger.error("Firebase service not initialized")
            return False

        try:
            doc_ref = self.db.collection('files').document(file_id)
            metadata['user_id'] = user_id

            # Add server timestamp if using real Firestore
            if FIREBASE_AVAILABLE:
                metadata['timestamp'] = firestore.SERVER_TIMESTAMP

            doc_ref.set(metadata)
            return True
        except Exception as e:
            logger.error(f"Failed to store metadata: {str(e)}")
            return False

    def upload_to_storage(self, file_path, destination_path):
        """Upload a file to Firebase Storage."""
        if not self.initialized:
            logger.error("Firebase service not initialized")
            return None

        if not self.bucket:
            logger.error("Firebase storage bucket not available")
            return None

        try:
            blob = self.bucket.blob(destination_path)
            blob.upload_from_filename(file_path)
            return blob.public_url
        except Exception as e:
            logger.error(f"Failed to upload to storage: {str(e)}")
            return None

    def get_file_metadata(self, file_id):
        """Get file metadata from Firestore."""
        if not self.initialized:
            logger.error("Firebase service not initialized")
            return None

        try:
            doc_ref = self.db.collection('files').document(file_id)
            doc = doc_ref.get()

            if doc.exists:
                return doc.to_dict()
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to get metadata: {str(e)}")
            return None

    def update_file_metadata(self, file_id, updates):
        """Update file metadata in Firestore."""
        if not self.initialized:
            logger.error("Firebase service not initialized")
            return False

        try:
            doc_ref = self.db.collection('files').document(file_id)
            doc_ref.update(updates)
            return True
        except Exception as e:
            logger.error(f"Failed to update metadata: {str(e)}")
            return False

    def get_ref(self, path):
        """Get Firebase Realtime Database reference."""
        if not self.initialized:
            logger.error("Firebase service not initialized")
            return None

        # If using mock services, return mock reference
        if hasattr(self, '_mock_ref'):
            logger.debug(f"Returning mock reference for path: {path}")
            return self._mock_ref

        try:
            # Import Firebase Realtime Database
            from firebase_admin import db
            return db.reference(path)
        except Exception as e:
            logger.error(f"Failed to get Firebase reference for {path}: {str(e)}")
            return None

    def verify_id_token(self, id_token):
        """Verify Firebase ID token."""
        if not self.initialized or not FIREBASE_AVAILABLE:
            logger.error("Firebase service not initialized or not available")
            return None

        try:
            return auth.verify_id_token(id_token)
        except Exception as e:
            logger.error(f"Failed to verify ID token: {str(e)}")
            return None
