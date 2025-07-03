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

    # Role constants for RBAC system
    ROLE_ADMIN = 'admin'
    ROLE_SUPER_USER = 'super_user'
    ROLE_NORMAL_USER = 'normal_user'

    VALID_ROLES = [ROLE_ADMIN, ROLE_SUPER_USER, ROLE_NORMAL_USER]

    @staticmethod
    def create(username, email, password_hash=None, is_admin=False, oauth_provider=None, oauth_id=None, role=None):
        """Create a new user."""
        # Determine role based on is_admin flag or explicit role parameter
        # Default all new users to Normal User role unless explicitly specified
        if role and role in User.VALID_ROLES:
            user_role = role
        elif is_admin:
            user_role = User.ROLE_ADMIN
        else:
            user_role = User.ROLE_NORMAL_USER

        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'is_admin': is_admin,  # Keep for backward compatibility
            'role': user_role,
            'created_at': datetime.now().isoformat(),
            'oauth_provider': oauth_provider,
            'oauth_id': oauth_id,
            'email_verified': oauth_provider is not None,  # OAuth users are pre-verified
            'email_verified_at': datetime.now().isoformat() if oauth_provider else None
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
    def update_user_role(email, new_role):
        """Update user's role."""
        if new_role not in User.VALID_ROLES:
            raise ValueError(f"Invalid role: {new_role}. Must be one of {User.VALID_ROLES}")

        user_id = email.replace('.', ',')
        User.get_ref('users').child(user_id).update({
            'role': new_role,
            'is_admin': new_role == User.ROLE_ADMIN  # Update is_admin for backward compatibility
        })

        return True

    @staticmethod
    def get_user_role(email):
        """Get user's role."""
        user_data = User.get_by_email(email)
        if not user_data:
            return None

        # Return role if it exists, otherwise determine from is_admin flag
        role = user_data.get('role')
        if role and role in User.VALID_ROLES:
            return role

        # Fallback to determining role from is_admin flag
        is_admin = user_data.get('is_admin', False)
        return User.ROLE_ADMIN if is_admin else User.ROLE_NORMAL_USER

    @staticmethod
    def is_admin(email):
        """Check if user is an admin."""
        role = User.get_user_role(email)
        return role == User.ROLE_ADMIN

    @staticmethod
    def is_super_user(email):
        """Check if user is a super user."""
        role = User.get_user_role(email)
        return role == User.ROLE_SUPER_USER

    @staticmethod
    def is_normal_user(email):
        """Check if user is a normal user."""
        role = User.get_user_role(email)
        return role == User.ROLE_NORMAL_USER

    @staticmethod
    def has_admin_privileges(email):
        """Check if user has admin privileges (admin role only)."""
        return User.is_admin(email)

    @staticmethod
    def has_premium_access(email):
        """Check if user has premium access (admin or super user)."""
        role = User.get_user_role(email)
        return role in [User.ROLE_ADMIN, User.ROLE_SUPER_USER]

    @staticmethod
    def is_email_verified(email):
        """Check if user's email is verified."""
        user_data = User.get_by_email(email)
        if not user_data:
            return False

        # OAuth users are automatically verified
        if user_data.get('oauth_provider'):
            return True

        return user_data.get('email_verified', False)

    @staticmethod
    def mark_email_verified(email):
        """Mark user's email as verified."""
        if not email:
            return False

        user_id = email.replace('.', ',')
        try:
            User.get_ref('users').child(user_id).update({
                'email_verified': True,
                'email_verified_at': datetime.now().isoformat()
            })
            return True
        except Exception:
            return False

    @staticmethod
    def requires_email_verification(email):
        """Check if user requires email verification to access features."""
        user_data = User.get_by_email(email)
        if not user_data:
            return True  # New users need verification

        # OAuth users don't need verification
        if user_data.get('oauth_provider'):
            return False

        # Manual registration users need verification
        return not user_data.get('email_verified', False)

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
                self.role = data.get('role', User.ROLE_NORMAL_USER)
                self.email_verified = data.get('email_verified', data.get('oauth_provider') is not None)
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

            def has_role(self, role):
                """Check if user has a specific role."""
                return self.role == role

            def has_admin_privileges(self):
                """Check if user has admin privileges."""
                return self.role == User.ROLE_ADMIN

            def has_premium_access(self):
                """Check if user has premium access (admin or super user)."""
                return self.role in [User.ROLE_ADMIN, User.ROLE_SUPER_USER]

            def is_super_user(self):
                """Check if user is a super user."""
                return self.role == User.ROLE_SUPER_USER

            def is_normal_user(self):
                """Check if user is a normal user."""
                return self.role == User.ROLE_NORMAL_USER

            def is_email_verified(self):
                """Check if user's email is verified."""
                return self.email_verified

            def requires_email_verification(self):
                """Check if user requires email verification."""
                # OAuth users don't need verification
                if self._data.get('oauth_provider'):
                    return False
                # Manual registration users need verification
                return not self.email_verified

            def mark_email_verified(self):
                """Mark user's email as verified."""
                success = User.mark_email_verified(self.email)
                if success:
                    self.email_verified = True
                return success

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
        print(f"Saving transcription for user: {user_email}")
        print(f"Text length: {len(text) if text else 0}")
        print(f"Language: {language}")
        print(f"Model: {model}")

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
        print(f"Using Firebase path: transcriptions/{user_id}")

        try:
            ref = Transcription.get_ref(f'transcriptions/{user_id}')
            result = ref.push(transcription_data)
            print(f"Successfully saved transcription with key: {result.key if hasattr(result, 'key') else 'unknown'}")
            return True
        except Exception as e:
            print(f"Error saving transcription: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def get_by_user(user_email, limit=10):
        """Get transcriptions by user."""
        user_id = user_email.replace('.', ',')
        try:
            # Try to get with ordering by timestamp
            transcriptions = Transcription.get_ref(f'transcriptions/{user_id}').order_by_child('timestamp').limit_to_last(limit).get()
            return transcriptions if transcriptions else {}
        except Exception as e:
            print(f"Error fetching transcriptions with ordering: {str(e)}")
            # If index is not defined, try without ordering
            try:
                transcriptions = Transcription.get_ref(f'transcriptions/{user_id}').get()
                return transcriptions if transcriptions else {}
            except Exception as e2:
                print(f"Error fetching transcriptions without ordering: {str(e2)}")
                return {}

class Translation(FirebaseModel):
    """Translation model for Firebase."""

    @staticmethod
    def get_by_user(user_email, limit=10):
        """Get translations by user."""
        user_id = user_email.replace('.', ',')
        try:
            # Try to get with ordering by timestamp
            translations = Translation.get_ref(f'translations/{user_id}').order_by_child('timestamp').limit_to_last(limit).get()
            return translations if translations else {}
        except Exception as e:
            print(f"Error fetching translations with ordering: {str(e)}")
            # If index is not defined, try without ordering
            try:
                translations = Translation.get_ref(f'translations/{user_id}').get()
                return translations if translations else {}
            except Exception as e2:
                print(f"Error fetching translations without ordering: {str(e2)}")
                return {}

