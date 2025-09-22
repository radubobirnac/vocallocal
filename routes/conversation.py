"""
Conversation routes for real-time multilingual communication
"""

from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room, rooms
import string
import random
import logging
from datetime import datetime, timedelta
from models.firebase_models import ConversationRoom, ConversationMessage, UserLanguagePreferences

# Rate limiting for join API
join_api_requests = {}  # Track requests per user

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('conversation', __name__, url_prefix='/conversation')

def generate_room_code():
    """Generate a 6-character alphanumeric room code"""
    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(characters, k=6))

    # Ensure uniqueness by checking if room already exists
    max_attempts = 10
    attempts = 0

    while attempts < max_attempts:
        existing_room = ConversationRoom.get_by_code(code)
        if not existing_room:
            return code

        # Generate new code if collision
        code = ''.join(random.choices(characters, k=6))
        attempts += 1

    # If we still have collisions after max attempts, add timestamp
    import time
    timestamp_suffix = str(int(time.time()))[-2:]
    return code[:4] + timestamp_suffix

@bp.route('/create', methods=['POST'])
@login_required
def create_room():
    """Create a new conversation room"""
    try:
        # Generate unique room code
        room_code = generate_room_code()

        # Create room in Firebase
        room_data = ConversationRoom.create(room_code, current_user.email)

        if not room_data:
            return jsonify({'success': False, 'error': 'Failed to create room'}), 500

        # Generate shareable link
        shareable_link = f"/conversation/join/{room_code}"

        logger.info(f"Room {room_code} created by {current_user.email}")

        return jsonify({
            'success': True,
            'room_code': room_code,
            'shareable_link': shareable_link,
            'room_data': room_data,
            'creator_auto_added': room_data.get('participant_count', 0) > 0,
            'direct_room_url': f'/conversation/room/{room_code}'
        })

    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/join/<room_code>')
@login_required
def join_room_page(room_code):
    """Render the room joining page"""
    try:
        # Validate room exists and is active
        room_data = ConversationRoom.get_by_code(room_code.upper())

        if not room_data:
            return render_template('error.html', error=f"Room {room_code} not found or is no longer active")

        # Check if room is full
        max_participants = room_data.get('max_participants', 2)
        current_participants = room_data.get('participant_count', 0)

        if current_participants >= max_participants:
            return render_template('error.html', error=f"Room {room_code} is full")

        # Check if room is closed
        if room_data.get('status') == ConversationRoom.STATUS_CLOSED:
            return render_template('error.html', error=f"Room {room_code} is closed")

        # Get user's language preferences
        user_prefs = UserLanguagePreferences.get_preferences(current_user.email)

        return render_template('conversation/join.html',
                             room_code=room_code.upper(),
                             user_preferences=user_prefs)

    except Exception as e:
        logger.error(f"Error accessing room {room_code}: {str(e)}")
        return render_template('error.html', error=f"Room {room_code} not found or is no longer active")

@bp.route('/room/')
@login_required
def join_room_bilingual():
    """Redirect to bilingual mode functionality"""
    from flask import redirect, url_for
    # Redirect to main page with bilingual mode parameter
    return redirect(url_for('index', bilingual_mode='true'))

@bp.route('/room/<room_code>')
@login_required
def conversation_room(room_code):
    """Render the conversation room interface"""
    try:
        logger.info(f"User {current_user.email} attempting to access room {room_code}")

        # Validate room exists
        room_data = ConversationRoom.get_by_code(room_code.upper())

        if not room_data:
            logger.warning(f"Room {room_code} not found for user {current_user.email}")
            return render_template('error.html', error=f"Room {room_code} not found")

        # Check if user is a participant in this room
        participants = room_data.get('participants', {})
        # Use encoded email for participant lookup (Firebase keys use encoded emails)
        encoded_email = ConversationRoom.encode_email_for_firebase_key(current_user.email)
        if encoded_email not in participants:
            logger.warning(f"User {current_user.email} (encoded: {encoded_email}) is not a participant in room {room_code}")
            logger.info(f"Available participants: {list(participants.keys())}")
            return render_template('error.html', error=f"You are not a participant in room {room_code}. Please join the room first.")

        # Check if room is still active
        if room_data.get('status') == ConversationRoom.STATUS_CLOSED:
            logger.warning(f"Room {room_code} is closed for user {current_user.email}")
            return render_template('error.html', error=f"Room {room_code} is closed")

        # Get user's language preferences
        user_prefs = UserLanguagePreferences.get_preferences(current_user.email)

        # Get recent messages for the room
        recent_messages = ConversationMessage.get_room_messages(room_code.upper(), limit=50)

        # Prepare room data with decoded participant emails for template
        room_data_for_template = room_data.copy()
        room_data_for_template['participants'] = ConversationRoom.get_participants_with_decoded_emails(room_data)

        logger.info(f"User {current_user.email} successfully accessing room {room_code}")
        return render_template('conversation/room.html',
                             room_code=room_code.upper(),
                             user_email=current_user.email,
                             room_data=room_data_for_template,
                             user_preferences=user_prefs,
                             recent_messages=recent_messages,
                             auto_bilingual=True,  # Always activate bilingual mode for conversation rooms
                             current_user=current_user)

    except Exception as e:
        logger.error(f"Error accessing conversation room {room_code}: {str(e)}")
        return render_template('error.html', error=f"Unable to access room {room_code}")

@bp.route('/api/join', methods=['POST'])
@login_required
def join_room_api():
    """API endpoint to join a room"""
    try:
        # Log request details for debugging
        logger.info(f"Join room API called by {current_user.email}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request referrer: {request.referrer}")

        # Rate limiting - prevent rapid requests
        now = datetime.now()
        user_email = current_user.email

        if user_email in join_api_requests:
            last_request = join_api_requests[user_email]
            if (now - last_request).total_seconds() < 2:  # Minimum 2 seconds between requests
                logger.warning(f"Rate limit exceeded for user {user_email}")
                return jsonify({'success': False, 'error': 'Please wait before making another request'}), 429

        join_api_requests[user_email] = now

        # Check if request has JSON content type
        if not request.is_json:
            logger.error(f"Invalid content type: {request.content_type}")
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400

        # Try to parse JSON data
        try:
            data = request.get_json()
            if data is None:
                logger.error("Request body is empty or invalid JSON")
                logger.error(f"Raw request data: {request.get_data()}")
                return jsonify({'success': False, 'error': 'Invalid JSON data; request body is empty or malformed'}), 400
        except Exception as json_error:
            logger.error(f"JSON parsing error: {str(json_error)}")
            logger.error(f"Raw request data: {request.get_data()}")
            return jsonify({'success': False, 'error': 'Invalid data; couldn\'t parse JSON object. Are you sending a JSON object with valid key names?'}), 400

        # Validate required fields
        if not isinstance(data, dict):
            logger.error(f"Data is not a dictionary: {type(data)}")
            return jsonify({'success': False, 'error': 'Invalid data format; expected JSON object'}), 400

        logger.info(f"Parsed JSON data: {data}")

        # Additional validation for expected data structure
        room_code = data.get('room_code', '').strip().upper()
        input_language = data.get('input_language', 'en').strip()
        target_language = data.get('target_language', 'es').strip()

        if not room_code:
            logger.error("Room code is missing or empty")
            return jsonify({'success': False, 'error': 'Room code is required'}), 400

        # Validate room code format (should be 6 alphanumeric characters)
        if len(room_code) != 6 or not room_code.isalnum():
            logger.error(f"Invalid room code format: {room_code}")
            return jsonify({'success': False, 'error': 'Invalid room code format'}), 400

        # Validate language codes
        if not input_language or not target_language:
            logger.error(f"Invalid language codes: input={input_language}, target={target_language}")
            return jsonify({'success': False, 'error': 'Valid input and target languages are required'}), 400

        # Validate room exists and is active
        room_data = ConversationRoom.get_by_code(room_code)

        if not room_data:
            return jsonify({'success': False, 'error': 'Room not found'}), 404

        # Check if room is closed
        if room_data.get('status') == ConversationRoom.STATUS_CLOSED:
            return jsonify({'success': False, 'error': 'Room is closed'}), 400

        # Add user to room participants
        logger.info(f"Attempting to add participant {current_user.email} to room {room_code}")
        success, message = ConversationRoom.add_participant(
            room_code, current_user.email, input_language, target_language
        )
        logger.info(f"Add participant result: success={success}, message={message}")

        if not success:
            logger.error(f"Failed to add participant {current_user.email} to room {room_code}: {message}")
            return jsonify({'success': False, 'error': message}), 400

        # Save language preferences to user profile
        UserLanguagePreferences.update_preferences(
            current_user.email, input_language, target_language
        )

        # Add to user's conversation history
        UserLanguagePreferences.add_to_history(current_user.email, room_code, room_data)

        logger.info(f"User {current_user.email} joined room {room_code}")

        return jsonify({
            'success': True,
            'room_code': room_code,
            'redirect_url': f'/conversation/room/{room_code}'
        })

    except Exception as e:
        logger.error(f"Error joining room: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/language-preferences', methods=['POST'])
@login_required
def update_language_preferences():
    """Update user's language preferences"""
    try:
        data = request.json
        input_language = data.get('input_language')
        target_language = data.get('target_language')

        if not input_language or not target_language:
            return jsonify({'success': False, 'error': 'Both input and target languages are required'}), 400

        # Save language preferences to user profile in Firebase
        success = UserLanguagePreferences.update_preferences(
            current_user.email, input_language, target_language
        )

        if not success:
            return jsonify({'success': False, 'error': 'Failed to update preferences'}), 500

        logger.info(f"Language preferences updated for {current_user.email}: {input_language} -> {target_language}")

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error updating language preferences: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/room-cleanup', methods=['POST'])
@login_required
def cleanup_rooms():
    """Manual room cleanup endpoint (for admin use)"""
    try:
        # Only allow admin users to trigger cleanup
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        cleaned_count = ConversationRoom.cleanup_inactive_rooms()

        logger.info(f"Room cleanup completed by {current_user.email}: {cleaned_count} rooms cleaned")

        return jsonify({
            'success': True,
            'cleaned_count': cleaned_count
        })

    except Exception as e:
        logger.error(f"Error during room cleanup: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
