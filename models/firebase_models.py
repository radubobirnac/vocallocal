"""Firebase data models for VocalLocal."""
from firebase_config import initialize_firebase
from datetime import datetime
import json
import re

class FirebaseModel:
    """Base class for Firebase models."""

    @staticmethod
    def get_ref(path):
        """Get Firebase reference for the path."""
        db_ref = initialize_firebase()
        return db_ref.child(path)

class User(FirebaseModel):
    """User model for Firebase."""

    @staticmethod
    def create(username, email, password_hash=None, is_admin=False, oauth_provider=None, oauth_id=None):
        """Create a new user."""
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'is_admin': is_admin,
            'created_at': datetime.now().isoformat(),
            'oauth_provider': oauth_provider,
            'oauth_id': oauth_id
        }

        # Use email as unique ID (replace dots with commas for Firebase path)
        user_id = email.replace('.', ',')
        User.get_ref('users').child(user_id).set(user_data)
        return user_id

    @staticmethod
    def get_by_email(email):
        """Get user by email."""
        if not email:
            return None
        user_id = email.replace('.', ',')
        user_data = User.get_ref('users').child(user_id).get()
        return user_data if user_data else None

    @staticmethod
    def get_by_oauth(provider, oauth_id):
        """Get user by OAuth provider and ID."""
        users = User.get_ref('users').get()
        if not users:
            return None

        for user_id, user_data in users.items():
            if (user_data.get('oauth_provider') == provider and
                user_data.get('oauth_id') == oauth_id):
                return user_data
        return None

    @staticmethod
    def update_oauth(email, oauth_provider, oauth_id):
        """Update user's OAuth information."""
        user_id = email.replace('.', ',')
        User.get_ref('users').child(user_id).update({
            'oauth_provider': oauth_provider,
            'oauth_id': oauth_id
        })

    @staticmethod
    def update_last_login(email):
        """Update user's last login timestamp."""
        user_id = email.replace('.', ',')
        User.get_ref('users').child(user_id).update({
            'last_login': datetime.now().isoformat()
        })

    @staticmethod
    def get_or_create(email, name=None, picture=None):
        """Get an existing user or create a new one if it doesn't exist.

        Args:
            email: User's email address
            name: User's display name (optional)
            picture: URL to user's profile picture (optional)

        Returns:
            A UserObject instance compatible with Flask-Login
        """
        # Check if user exists
        user_data = User.get_by_email(email)

        if not user_data:
            # Create a new user with OAuth information
            username = name or email.split('@')[0]
            User.create(
                username=username,
                email=email,
                oauth_provider='google',
                oauth_id=email,  # Use email as OAuth ID for simplicity
                is_admin=False
            )
            # Get the newly created user
            user_data = User.get_by_email(email)
        else:
            # Update OAuth information if needed
            if not user_data.get('oauth_provider'):
                User.update_oauth(email, 'google', email)

        # Update last login time
        User.update_last_login(email)

        # Create user object compatible with Flask-Login
        class UserObject:
            def __init__(self, email, data):
                self.id = email
                self.email = email
                self.username = data.get('username')
                self.is_admin = data.get('is_admin', False)
                self._data = data  # Store the full user data

            def is_authenticated(self):
                return True

            def is_active(self):
                return True

            def is_anonymous(self):
                return False

            def get_id(self):
                return self.id

            def check_password(self, password):
                """Check if the provided password matches the stored hash."""
                password_hash = self._data.get('password_hash', '')
                from werkzeug.security import check_password_hash
                return check_password_hash(password_hash, password) if password_hash else False

        return UserObject(email, user_data)

    @staticmethod
    def get_all_users():
        """Get all users from Firebase."""
        users_data = User.get_ref('users').get()
        if not users_data:
            return []

        # Convert to list of user objects with email included
        users = []
        for user_id, user_data in users_data.items():
            # Add email to user data if not already present
            if 'email' not in user_data and ',' in user_id:
                user_data['email'] = user_id.replace(',', '.')
            users.append(user_data)

        return users

class UserActivity(FirebaseModel):
    """User activity model for Firebase."""

    @staticmethod
    def log(user_email, activity_type, details=None):
        """Log user activity."""
        activity_data = {
            'user_email': user_email,
            'activity_type': activity_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

        UserActivity.get_ref('user_activities').push(activity_data)

class Transcription(FirebaseModel):
    """Transcription model for Firebase."""

    @staticmethod
    def save(user_email, text, language, model, audio_duration=None):
        """Save a transcription."""
        transcription_data = {
            'user_email': user_email,
            'text': text,
            'language': language,
            'model': model,
            'audio_duration': audio_duration,
            'timestamp': datetime.now().isoformat()
        }

        # Use user email as part of the path
        user_id = user_email.replace('.', ',')
        Transcription.get_ref(f'transcriptions/{user_id}').push(transcription_data)

    @staticmethod
    def get_by_user(user_email, limit=10):
        """Get transcriptions by user."""
        user_id = user_email.replace('.', ',')
        transcriptions = Transcription.get_ref(f'transcriptions/{user_id}').order_by_child('timestamp').limit_to_last(limit).get()
        return transcriptions if transcriptions else {}

class Translation(FirebaseModel):
    """Translation model for Firebase."""

    @staticmethod
    def save(user_email, original_text, translated_text, source_language, target_language, model):
        """Save a translation."""
        translation_data = {
            'user_email': user_email,
            'original_text': original_text,
            'translated_text': translated_text,
            'source_language': source_language,
            'target_language': target_language,
            'model': model,
            'timestamp': datetime.now().isoformat()
        }

        # Use user email as part of the path
        user_id = user_email.replace('.', ',')
        Translation.get_ref(f'translations/{user_id}').push(translation_data)

    @staticmethod
    def get_by_user(user_email, limit=10):
        """Get translations by user."""
        user_id = user_email.replace('.', ',')
        translations = Translation.get_ref(f'translations/{user_id}').order_by_child('timestamp').limit_to_last(limit).get()
        return translations if translations else {}
