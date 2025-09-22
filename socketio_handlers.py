"""
Socket.IO event handlers for real-time conversation functionality
"""

from flask_socketio import emit, join_room, leave_room, rooms
from flask_login import current_user
from flask import request
import logging
from datetime import datetime, timedelta
import json
from models.firebase_models import ConversationRoom, ConversationMessage, UserLanguagePreferences

# Configure logging
logger = logging.getLogger(__name__)

# Store active rooms and participants in memory (will be moved to Firebase later)
active_rooms = {}
user_sessions = {}  # Maps user_email to session_id
room_cleanup_timers = {}  # For handling disconnection cleanup

def register_socketio_handlers(socketio):
    """Register all Socket.IO event handlers"""
    
    @socketio.on('join_conversation_room')
    def handle_join_room(data):
        """Handle user joining a conversation room"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return

        try:
            room_code = data.get('room_code', '').upper()
            input_language = data.get('input_language', 'en')
            target_language = data.get('target_language', 'es')

            if not room_code:
                emit('error', {'message': 'Room code is required'})
                return

            # Validate room exists in Firebase
            room_data = ConversationRoom.get_by_code(room_code)
            if not room_data:
                emit('error', {'message': 'Room not found'})
                return

            # Check if user is already a participant (use encoded email for Firebase key lookup)
            participants = room_data.get('participants', {})
            encoded_email = ConversationRoom.encode_email_for_firebase_key(current_user.email)
            if encoded_email not in participants:
                logger.warning(f"User {current_user.email} (encoded: {encoded_email}) not found in room {room_code} participants: {list(participants.keys())}")
                emit('error', {'message': 'You are not a participant in this room'})
                return

            # Join the Socket.IO room
            join_room(room_code)

            # Track user session
            user_sessions[current_user.email] = request.sid

            # Update participant status to connected in Firebase
            ConversationRoom.update_participant_status(room_code, current_user.email, 'connected')

            # Update language preferences if provided
            if input_language or target_language:
                UserLanguagePreferences.update_preferences(
                    current_user.email, input_language, target_language
                )

            # Cancel any cleanup timer for this room
            if room_code in room_cleanup_timers:
                room_cleanup_timers[room_code].cancel()
                del room_cleanup_timers[room_code]

            # Get updated room data
            updated_room_data = ConversationRoom.get_by_code(room_code)
            participant_count = updated_room_data.get('participant_count', 0)

            # Notify other participants
            emit('user_joined', {
                'user_email': current_user.email,
                'participant_count': participant_count,
                'input_language': input_language,
                'target_language': target_language
            }, room=room_code, include_self=False)

            # Send room status to the joining user (decode participant emails)
            participants_dict = updated_room_data.get('participants', {})
            decoded_participants = [
                ConversationRoom.decode_email_from_firebase_key(encoded_email)
                for encoded_email in participants_dict.keys()
            ]

            emit('room_joined', {
                'room_code': room_code,
                'participant_count': participant_count,
                'participants': decoded_participants
            })

            logger.info(f"User {current_user.email} joined room {room_code}")

        except Exception as e:
            logger.error(f"Error handling join room: {str(e)}")
            emit('error', {'message': 'Failed to join room'})
    
    @socketio.on('send_transcription')
    def handle_transcription(data):
        """Handle real-time transcription sharing"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return

        try:
            room_code = data.get('room_code', '').upper()
            transcription_text = data.get('text', '')
            is_final = data.get('is_final', False)
            language = data.get('language', 'en')

            if not room_code:
                emit('error', {'message': 'Room code is required'})
                return

            # Validate room exists and user is participant
            room_data = ConversationRoom.get_by_code(room_code)
            if not room_data:
                emit('error', {'message': 'Room not found'})
                return

            participants = room_data.get('participants', {})
            # Use encoded email for Firebase key lookup
            encoded_email = ConversationRoom.encode_email_for_firebase_key(current_user.email)
            if encoded_email not in participants:
                emit('error', {'message': 'Not a participant in this room'})
                return

            # Update room activity
            ConversationRoom.update_last_activity(room_code)

            # Save transcription message to Firebase if final
            if is_final and transcription_text.strip():
                ConversationMessage.create(
                    room_code=room_code,
                    user_email=current_user.email,
                    message_type=ConversationMessage.TYPE_TRANSCRIPTION,
                    content=transcription_text,
                    language=language
                )

            # Broadcast transcription to all participants in the room
            emit('transcription_received', {
                'user_email': current_user.email,
                'text': transcription_text,
                'language': language,
                'is_final': is_final,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_code)

            logger.info(f"Transcription from {current_user.email} in room {room_code}: {len(transcription_text)} chars")

        except Exception as e:
            logger.error(f"Error handling transcription: {str(e)}")
            emit('error', {'message': 'Failed to send transcription'})
    
    @socketio.on('send_translation')
    def handle_translation(data):
        """Handle real-time translation sharing"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return

        try:
            room_code = data.get('room_code', '').upper()
            original_text = data.get('original_text', '')
            translated_text = data.get('translated_text', '')
            target_language = data.get('target_language', '')
            original_message_id = data.get('original_message_id')

            if not room_code:
                emit('error', {'message': 'Room code is required'})
                return

            # Validate room exists and user is participant
            room_data = ConversationRoom.get_by_code(room_code)
            if not room_data:
                emit('error', {'message': 'Room not found'})
                return

            participants = room_data.get('participants', {})
            # Use encoded email for Firebase key lookup
            encoded_email = ConversationRoom.encode_email_for_firebase_key(current_user.email)
            if encoded_email not in participants:
                emit('error', {'message': 'Not a participant in this room'})
                return

            # Update room activity
            ConversationRoom.update_last_activity(room_code)

            # Save translation message to Firebase
            if translated_text.strip():
                ConversationMessage.create(
                    room_code=room_code,
                    user_email=current_user.email,
                    message_type=ConversationMessage.TYPE_TRANSLATION,
                    content=translated_text,
                    language=target_language,
                    target_language=target_language,
                    original_message_id=original_message_id
                )

            # Broadcast translation to all participants in the room
            emit('translation_received', {
                'user_email': current_user.email,
                'original_text': original_text,
                'translated_text': translated_text,
                'target_language': target_language,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_code)

            logger.info(f"Translation from {current_user.email} in room {room_code}")

        except Exception as e:
            logger.error(f"Error handling translation: {str(e)}")
            emit('error', {'message': 'Failed to send translation'})
    
    @socketio.on('update_language_settings')
    def handle_language_update(data):
        """Handle language settings update during conversation"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return

        try:
            room_code = data.get('room_code', '').upper()
            input_language = data.get('input_language')
            target_language = data.get('target_language')

            if not room_code:
                emit('error', {'message': 'Room code is required'})
                return

            # Validate room exists and user is participant
            room_data = ConversationRoom.get_by_code(room_code)
            if not room_data:
                emit('error', {'message': 'Room not found'})
                return

            participants = room_data.get('participants', {})
            # Check if user is participant using encoded email key
            encoded_email = ConversationRoom.encode_email_for_firebase_key(current_user.email)
            if encoded_email not in participants:
                emit('error', {'message': 'Not a participant in this room'})
                return

            # Update language preferences in Firebase
            UserLanguagePreferences.update_preferences(
                current_user.email, input_language, target_language
            )

            # Get updated preferences
            updated_prefs = UserLanguagePreferences.get_preferences(current_user.email)

            # Notify other participants of language change
            emit('language_settings_updated', {
                'user_email': current_user.email,
                'input_language': updated_prefs['input_language'],
                'target_language': updated_prefs['target_language']
            }, room=room_code, include_self=False)

            # Confirm to the user
            emit('language_settings_confirmed', {
                'input_language': updated_prefs['input_language'],
                'target_language': updated_prefs['target_language']
            })

            logger.info(f"Language settings updated for {current_user.email} in room {room_code}")

        except Exception as e:
            logger.error(f"Error updating language settings: {str(e)}")
            emit('error', {'message': 'Failed to update language settings'})
    
    @socketio.on('leave_conversation_room')
    def handle_leave_room(data):
        """Handle user explicitly leaving a conversation room"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return

        try:
            room_code = data.get('room_code', '').upper()

            if not room_code:
                emit('error', {'message': 'Room code is required'})
                return

            # Leave the Socket.IO room
            leave_room(room_code)

            # Update participant status in Firebase
            ConversationRoom.update_participant_status(room_code, current_user.email, 'disconnected')

            # Handle user leaving
            handle_user_leave_room(room_code, current_user.email)

            # Remove user session tracking
            if current_user.email in user_sessions:
                del user_sessions[current_user.email]

            logger.info(f"User {current_user.email} left room {room_code}")

        except Exception as e:
            logger.error(f"Error handling leave room: {str(e)}")
            emit('error', {'message': 'Failed to leave room'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle user disconnection"""
        if not current_user.is_authenticated:
            return

        try:
            # Find which rooms the user was in by checking Firebase
            # Since we don't have active_rooms in memory anymore, we need to check all rooms
            # This is less efficient but more reliable with Firebase backend

            # For now, we'll track the user's current room in the session
            # In a production environment, you might want to query Firebase for all rooms
            # where the user is a participant

            # Remove user session tracking
            if current_user.email in user_sessions:
                del user_sessions[current_user.email]

            logger.info(f"User {current_user.email} disconnected")

        except Exception as e:
            logger.error(f"Error handling disconnect: {str(e)}")

def handle_user_leave_room(room_code, user_email):
    """Handle user leaving a room (disconnect or explicit leave)"""
    try:
        # Update participant status in Firebase
        ConversationRoom.update_participant_status(room_code, user_email, 'disconnected')

        # Get updated room data
        room_data = ConversationRoom.get_by_code(room_code)
        if not room_data:
            return

        participants = room_data.get('participants', {})

        # Count connected participants (decode email keys)
        connected_participants = [
            ConversationRoom.decode_email_from_firebase_key(encoded_email)
            for encoded_email, data in participants.items()
            if data.get('status') == 'connected'
        ]

        # Notify other participants
        if connected_participants:
            from socketio_config import get_socketio
            socketio = get_socketio()
            if socketio:
                socketio.emit('user_left', {
                    'user_email': user_email,
                    'participant_count': len(connected_participants)
                }, room=room_code)

        # Schedule room cleanup if no connected participants
        if not connected_participants:
            schedule_room_cleanup(room_code)

        logger.info(f"User {user_email} left room {room_code}")

    except Exception as e:
        logger.error(f"Error handling user leave room: {str(e)}")

def schedule_room_cleanup(room_code):
    """Schedule room cleanup after 5 minutes of inactivity"""
    import threading

    def cleanup_room():
        try:
            # Check if any users reconnected by querying Firebase
            room_data = ConversationRoom.get_by_code(room_code)

            if room_data:
                participants = room_data.get('participants', {})
                connected_users = [
                    email for email, data in participants.items()
                    if data.get('status') == 'connected'
                ]

                if not connected_users:
                    # Update room status to closed
                    ConversationRoom.update_status(room_code, ConversationRoom.STATUS_CLOSED)

                    # Delete room messages (optional - you might want to keep for history)
                    # ConversationMessage.delete_room_messages(room_code)

                    logger.info(f"Room {room_code} marked as closed due to inactivity")
                else:
                    logger.info(f"Room {room_code} cleanup cancelled - users reconnected")

            # Remove cleanup timer
            if room_code in room_cleanup_timers:
                del room_cleanup_timers[room_code]

        except Exception as e:
            logger.error(f"Error during room cleanup: {str(e)}")

    # Cancel existing timer if any
    if room_code in room_cleanup_timers:
        room_cleanup_timers[room_code].cancel()

    # Schedule new cleanup timer (5 minutes)
    timer = threading.Timer(300, cleanup_room)  # 300 seconds = 5 minutes
    timer.start()
    room_cleanup_timers[room_code] = timer

    logger.info(f"Scheduled cleanup for room {room_code} in 5 minutes")
