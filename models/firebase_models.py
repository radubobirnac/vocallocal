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

    # Role constants
    ROLE_ADMIN = 'admin'
    ROLE_SUPER_USER = 'super_user'
    ROLE_NORMAL_USER = 'normal_user'

    VALID_ROLES = [ROLE_ADMIN, ROLE_SUPER_USER, ROLE_NORMAL_USER]

    @staticmethod
    def create(username, email, password_hash=None, is_admin=False, oauth_provider=None, oauth_id=None, role=None):
        """Create a new user."""
        # Determine role based on is_admin flag or explicit role parameter
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

            # Send welcome email to new Google OAuth user
            try:
                from services.email_service import EmailService
                email_service = EmailService()
                welcome_result = email_service.send_welcome_email(
                    username=username,
                    email=email,
                    user_tier='free'
                )
                if welcome_result['success']:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f'Welcome email sent successfully to new Google OAuth user: {email}')
                else:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Failed to send welcome email to Google OAuth user {email}: {welcome_result["message"]}')
            except Exception as welcome_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error sending welcome email to Google OAuth user {email}: {str(welcome_error)}')
                # Don't fail the user creation if welcome email fails

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


class ConversationRoom(FirebaseModel):
    """Conversation room model for real-time multilingual communication."""

    # Room status constants
    STATUS_WAITING = 'waiting'
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CLOSED = 'closed'

    VALID_STATUSES = [STATUS_WAITING, STATUS_ACTIVE, STATUS_INACTIVE, STATUS_CLOSED]

    @staticmethod
    def sanitize_for_firebase(data):
        """Ensure all data is JSON-serializable for Firebase."""
        if isinstance(data, dict):
            return {key: ConversationRoom.sanitize_for_firebase(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [ConversationRoom.sanitize_for_firebase(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

    @staticmethod
    def encode_email_for_firebase_key(email):
        """
        Encode email address to be used as Firebase key.
        Firebase keys cannot contain periods, so we replace them with underscores.
        """
        if not email:
            return email
        # Replace periods with underscores and other problematic characters
        return email.replace('.', '_DOT_').replace('#', '_HASH_').replace('$', '_DOLLAR_').replace('[', '_LBRACKET_').replace(']', '_RBRACKET_').replace('/', '_SLASH_')

    @staticmethod
    def decode_email_from_firebase_key(encoded_email):
        """
        Decode Firebase key back to email address.
        """
        if not encoded_email:
            return encoded_email
        # Reverse the encoding
        return encoded_email.replace('_DOT_', '.').replace('_HASH_', '#').replace('_DOLLAR_', '$').replace('_LBRACKET_', '[').replace('_RBRACKET_', ']').replace('_SLASH_', '/')

    @staticmethod
    def get_participants_with_decoded_emails(room_data):
        """
        Get participants data with decoded email addresses as keys.
        This is useful for frontend display and API responses.
        """
        if not room_data:
            return {}

        participants = room_data.get('participants', {})
        decoded_participants = {}

        for encoded_email, participant_data in participants.items():
            decoded_email = ConversationRoom.decode_email_from_firebase_key(encoded_email)
            decoded_participants[decoded_email] = participant_data

        return decoded_participants

    @staticmethod
    def create(room_code, creator_email, max_participants=2, auto_add_creator=True):
        """Create a new conversation room."""
        room_data = {
            'room_code': room_code,
            'creator_email': creator_email,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'status': ConversationRoom.STATUS_WAITING,
            'max_participants': max_participants,
            'participant_count': 0,
            'participants': {},
            'settings': {
                'auto_cleanup_minutes': 5,
                'max_duration_minutes': 120
            }
        }

        try:
            # Sanitize room data before sending to Firebase
            sanitized_room_data = ConversationRoom.sanitize_for_firebase(room_data)
            ConversationRoom.get_ref(f'conversation_rooms/{room_code}').set(sanitized_room_data)

            # Automatically add creator as participant if requested
            if auto_add_creator:
                print(f"[DEBUG] Auto-adding creator {creator_email} to room {room_code}")
                success, message = ConversationRoom.add_participant(
                    room_code, creator_email, "en", "en"  # Default languages
                )
                if success:
                    print(f"[DEBUG] Creator successfully added to room: {message}")
                    # Get updated room data with creator as participant
                    updated_room_data = ConversationRoom.get_by_code(room_code)
                    return updated_room_data if updated_room_data else sanitized_room_data
                else:
                    print(f"[WARNING] Failed to auto-add creator to room: {message}")
                    # Return original room data even if creator addition failed
                    return sanitized_room_data

            return sanitized_room_data
        except Exception as e:
            print(f"Error creating conversation room: {str(e)}")
            return None

    @staticmethod
    def get_by_code(room_code):
        """Get room by room code."""
        try:
            room_data = ConversationRoom.get_ref(f'conversation_rooms/{room_code}').get()
            return room_data
        except Exception as e:
            print(f"Error fetching room {room_code}: {str(e)}")
            return None

    @staticmethod
    def update_status(room_code, status):
        """Update room status."""
        if status not in ConversationRoom.VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")

        try:
            ConversationRoom.get_ref(f'conversation_rooms/{room_code}').update({
                'status': status,
                'last_activity': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            print(f"Error updating room status: {str(e)}")
            return False

    @staticmethod
    def update_last_activity(room_code):
        """Update room's last activity timestamp."""
        try:
            ConversationRoom.get_ref(f'conversation_rooms/{room_code}').update({
                'last_activity': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            print(f"Error updating room activity: {str(e)}")
            return False

    @staticmethod
    def add_participant(room_code, user_email, input_language, target_language):
        """Add a participant to the room."""
        try:
            print(f"[DEBUG] Adding participant {user_email} to room {room_code}")
            print(f"[DEBUG] Languages: input={input_language}, target={target_language}")

            # Get room reference
            room_ref = ConversationRoom.get_ref(f'conversation_rooms/{room_code}')
            print(f"[DEBUG] Got room reference for {room_code}")

            # Get room data
            room_data = room_ref.get()
            print(f"[DEBUG] Retrieved room data: {type(room_data)}")

            if not room_data:
                print(f"[DEBUG] Room {room_code} not found")
                return False, "Room not found"

            participants = room_data.get('participants', {})
            max_participants = room_data.get('max_participants', 2)
            print(f"[DEBUG] Current participants: {len(participants)}, max: {max_participants}")

            if len(participants) >= max_participants:
                print(f"[DEBUG] Room {room_code} is full")
                return False, "Room is full"

            # Ensure all existing participant data is JSON-serializable
            # This fixes any existing datetime objects that might not be properly serialized
            sanitized_participants = ConversationRoom.sanitize_for_firebase(participants)
            print(f"[DEBUG] Sanitized existing participants data")

            # Create participant data
            participant_data = {
                'user_email': user_email,
                'joined_at': datetime.now().isoformat(),
                'input_language': input_language,
                'target_language': target_language,
                'status': 'connected',
                'last_seen': datetime.now().isoformat()
            }
            print(f"[DEBUG] Created participant data: {participant_data}")

            # Encode email for Firebase key (Firebase keys cannot contain periods)
            encoded_email = ConversationRoom.encode_email_for_firebase_key(user_email)
            print(f"[DEBUG] Encoded email '{user_email}' to '{encoded_email}' for Firebase key")

            # Add new participant to sanitized participants using encoded email as key
            sanitized_participants[encoded_email] = participant_data
            print(f"[DEBUG] Added participant to sanitized participants dict with encoded key")

            # Prepare update data with proper JSON serialization
            update_data = {
                'participants': sanitized_participants,
                'participant_count': len(sanitized_participants),
                'status': ConversationRoom.STATUS_ACTIVE if len(sanitized_participants) > 1 else ConversationRoom.STATUS_WAITING,
                'last_activity': datetime.now().isoformat()
            }

            # Sanitize all update data to ensure Firebase compatibility
            update_data = ConversationRoom.sanitize_for_firebase(update_data)
            print(f"[DEBUG] Prepared and sanitized update data: {update_data}")

            # Validate that all data is JSON-serializable before sending to Firebase
            try:
                import json
                json.dumps(update_data)
                print(f"[DEBUG] Update data is JSON-serializable")
            except (TypeError, ValueError) as json_error:
                print(f"[ERROR] Update data is not JSON-serializable: {json_error}")
                return False, f"Data serialization error: {str(json_error)}"

            # Update room
            print(f"[DEBUG] Attempting to update room {room_code}")
            room_ref.update(update_data)
            print(f"[DEBUG] Successfully updated room {room_code}")

            return True, "Participant added successfully"

        except Exception as e:
            print(f"[ERROR] Error adding participant to room {room_code}: {str(e)}")
            print(f"[ERROR] Exception type: {type(e)}")
            print(f"[ERROR] Exception args: {e.args}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return False, f"Failed to add participant: {str(e)}"

    @staticmethod
    def remove_participant(room_code, user_email):
        """Remove a participant from the room."""
        try:
            room_ref = ConversationRoom.get_ref(f'conversation_rooms/{room_code}')
            room_data = room_ref.get()

            if not room_data:
                return False, "Room not found"

            participants = room_data.get('participants', {})

            # Encode email for Firebase key lookup
            encoded_email = ConversationRoom.encode_email_for_firebase_key(user_email)

            if encoded_email in participants:
                del participants[encoded_email]

                # Update room
                new_status = ConversationRoom.STATUS_INACTIVE if len(participants) == 0 else ConversationRoom.STATUS_ACTIVE

                room_ref.update({
                    'participants': participants,
                    'participant_count': len(participants),
                    'status': new_status,
                    'last_activity': datetime.now().isoformat()
                })

                return True, "Participant removed successfully"

            return False, "Participant not found in room"

        except Exception as e:
            print(f"Error removing participant: {str(e)}")
            return False, str(e)

    @staticmethod
    def update_participant_status(room_code, user_email, status):
        """Update participant status (connected/disconnected)."""
        try:
            room_ref = ConversationRoom.get_ref(f'conversation_rooms/{room_code}')
            room_data = room_ref.get()

            if not room_data:
                return False

            participants = room_data.get('participants', {})

            # Encode email for Firebase key lookup
            encoded_email = ConversationRoom.encode_email_for_firebase_key(user_email)

            if encoded_email in participants:
                participants[encoded_email]['status'] = status
                participants[encoded_email]['last_seen'] = datetime.now().isoformat()

                if status == 'disconnected':
                    participants[encoded_email]['disconnected_at'] = datetime.now().isoformat()

                room_ref.update({
                    'participants': participants,
                    'last_activity': datetime.now().isoformat()
                })

                return True

            return False

        except Exception as e:
            print(f"Error updating participant status: {str(e)}")
            return False

    @staticmethod
    def cleanup_inactive_rooms(inactive_minutes=5):
        """Clean up rooms that have been inactive for specified minutes."""
        try:
            rooms_ref = ConversationRoom.get_ref('conversation_rooms')
            rooms = rooms_ref.get()

            if not rooms:
                return 0

            cleaned_count = 0
            current_time = datetime.now()

            for room_code, room_data in rooms.items():
                if not room_data:
                    continue

                last_activity = datetime.fromisoformat(room_data.get('last_activity', current_time.isoformat()))
                time_diff = (current_time - last_activity).total_seconds() / 60

                # Check if room should be cleaned up
                should_cleanup = False

                # Room is inactive for too long
                if time_diff > inactive_minutes:
                    should_cleanup = True

                # Room has no participants
                if room_data.get('participant_count', 0) == 0:
                    should_cleanup = True

                # Room status is closed
                if room_data.get('status') == ConversationRoom.STATUS_CLOSED:
                    should_cleanup = True

                if should_cleanup:
                    rooms_ref.child(room_code).delete()
                    cleaned_count += 1

            return cleaned_count

        except Exception as e:
            print(f"Error cleaning up rooms: {str(e)}")
            return 0


class ConversationMessage(FirebaseModel):
    """Conversation message model for storing transcriptions and translations."""

    # Message type constants
    TYPE_TRANSCRIPTION = 'transcription'
    TYPE_TRANSLATION = 'translation'
    TYPE_SYSTEM = 'system'

    VALID_TYPES = [TYPE_TRANSCRIPTION, TYPE_TRANSLATION, TYPE_SYSTEM]

    @staticmethod
    def create(room_code, user_email, message_type, content, language=None, target_language=None, original_message_id=None):
        """Create a new conversation message."""
        if message_type not in ConversationMessage.VALID_TYPES:
            raise ValueError(f"Invalid message type: {message_type}")

        message_data = {
            'room_code': room_code,
            'user_email': user_email,
            'type': message_type,
            'content': content,
            'language': language,
            'target_language': target_language,
            'original_message_id': original_message_id,
            'timestamp': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat()
        }

        try:
            # Generate unique message ID
            message_ref = ConversationMessage.get_ref(f'conversation_messages/{room_code}').push()
            message_id = message_ref.key
            message_data['message_id'] = message_id

            # Save message
            message_ref.set(message_data)

            # Update room's last activity
            ConversationRoom.update_last_activity(room_code)

            return message_data

        except Exception as e:
            print(f"Error creating conversation message: {str(e)}")
            return None

    @staticmethod
    def get_room_messages(room_code, limit=50):
        """Get messages for a specific room."""
        try:
            messages_ref = ConversationMessage.get_ref(f'conversation_messages/{room_code}')
            messages = messages_ref.order_by_child('timestamp').limit_to_last(limit).get()
            return messages if messages else {}
        except Exception as e:
            print(f"Error fetching room messages: {str(e)}")
            return {}

    @staticmethod
    def get_user_messages(room_code, user_email, limit=20):
        """Get messages from a specific user in a room."""
        try:
            messages_ref = ConversationMessage.get_ref(f'conversation_messages/{room_code}')
            all_messages = messages_ref.order_by_child('user_email').equal_to(user_email).limit_to_last(limit).get()
            return all_messages if all_messages else {}
        except Exception as e:
            print(f"Error fetching user messages: {str(e)}")
            return {}

    @staticmethod
    def delete_room_messages(room_code):
        """Delete all messages for a room (used during cleanup)."""
        try:
            ConversationMessage.get_ref(f'conversation_messages/{room_code}').delete()
            return True
        except Exception as e:
            print(f"Error deleting room messages: {str(e)}")
            return False


class UserLanguagePreferences(FirebaseModel):
    """User language preferences for conversations."""

    @staticmethod
    def get_preferences(user_email):
        """Get user's language preferences."""
        try:
            user_id = user_email.replace('.', ',')
            prefs = UserLanguagePreferences.get_ref(f'user_language_preferences/{user_id}').get()

            # Return default preferences if none exist
            if not prefs:
                return {
                    'input_language': 'en',
                    'target_language': 'es',
                    'updated_at': datetime.now().isoformat()
                }

            return prefs
        except Exception as e:
            print(f"Error fetching language preferences: {str(e)}")
            return {
                'input_language': 'en',
                'target_language': 'es',
                'updated_at': datetime.now().isoformat()
            }

    @staticmethod
    def update_preferences(user_email, input_language=None, target_language=None):
        """Update user's language preferences."""
        try:
            user_id = user_email.replace('.', ',')
            current_prefs = UserLanguagePreferences.get_preferences(user_email)

            # Update only provided preferences
            if input_language:
                current_prefs['input_language'] = input_language
            if target_language:
                current_prefs['target_language'] = target_language

            current_prefs['updated_at'] = datetime.now().isoformat()

            UserLanguagePreferences.get_ref(f'user_language_preferences/{user_id}').set(current_prefs)
            return True

        except Exception as e:
            print(f"Error updating language preferences: {str(e)}")
            return False

    @staticmethod
    def get_conversation_history(user_email, limit=10):
        """Get user's recent conversation rooms."""
        try:
            user_id = user_email.replace('.', ',')
            history = UserLanguagePreferences.get_ref(f'user_conversation_history/{user_id}').order_by_child('last_joined').limit_to_last(limit).get()
            return history if history else {}
        except Exception as e:
            print(f"Error fetching conversation history: {str(e)}")
            return {}

    @staticmethod
    def add_to_history(user_email, room_code, room_data):
        """Add a room to user's conversation history."""
        try:
            user_id = user_email.replace('.', ',')
            history_entry = {
                'room_code': room_code,
                'joined_at': datetime.now().isoformat(),
                'last_joined': datetime.now().isoformat(),
                'creator_email': room_data.get('creator_email'),
                'participant_count': room_data.get('participant_count', 0)
            }

            UserLanguagePreferences.get_ref(f'user_conversation_history/{user_id}/{room_code}').set(history_entry)
            return True

        except Exception as e:
            print(f"Error adding to conversation history: {str(e)}")
            return False
