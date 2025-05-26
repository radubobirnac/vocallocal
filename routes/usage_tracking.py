"""
Usage Tracking Routes for VocalLocal (Firebase Free Plan Compatible)

This module provides Flask routes for usage tracking that work
with Firebase's free plan without requiring Cloud Functions.
"""

from flask import Blueprint, request, jsonify, session, render_template
from flask_login import login_required, current_user
import logging
from services.usage_tracking_service import UsageTrackingService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('usage_tracking', __name__, url_prefix='/api/usage')

@bp.route('/deduct/transcription', methods=['POST'])
@login_required
def deduct_transcription_usage():
    """
    API endpoint to deduct transcription usage from a user's account.

    Expected JSON payload:
    {
        "userId": "user_id",
        "minutesUsed": 5.5
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-request',
                    'message': 'No JSON data provided'
                }
            }), 400

        user_id = data.get('userId')
        minutes_used = data.get('minutesUsed', 0)

        # Validate input
        if not user_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-argument',
                    'message': 'userId is required'
                }
            }), 400

        if not isinstance(minutes_used, (int, float)) or minutes_used < 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-argument',
                    'message': 'minutesUsed must be a positive number'
                }
            }), 400

        # Check if user can deduct usage for this user ID
        if current_user.email != user_id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'permission-denied',
                    'message': 'You can only deduct usage for your own account'
                }
            }), 403

        # Deduct usage
        result = UsageTrackingService.deduct_transcription_usage(user_id, minutes_used)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in deduct_transcription_usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal-error',
                'message': 'An error occurred while deducting transcription usage',
                'details': str(e)
            }
        }), 500

@bp.route('/deduct/translation', methods=['POST'])
@login_required
def deduct_translation_usage():
    """
    API endpoint to deduct translation usage from a user's account.

    Expected JSON payload:
    {
        "userId": "user_id",
        "wordsUsed": 150
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-request',
                    'message': 'No JSON data provided'
                }
            }), 400

        user_id = data.get('userId')
        words_used = data.get('wordsUsed', 0)

        # Validate input
        if not user_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-argument',
                    'message': 'userId is required'
                }
            }), 400

        if not isinstance(words_used, int) or words_used < 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-argument',
                    'message': 'wordsUsed must be a positive integer'
                }
            }), 400

        # Check permissions
        if current_user.email != user_id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'permission-denied',
                    'message': 'You can only deduct usage for your own account'
                }
            }), 403

        # Deduct usage
        result = UsageTrackingService.deduct_translation_usage(user_id, words_used)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in deduct_translation_usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal-error',
                'message': 'An error occurred while deducting translation usage',
                'details': str(e)
            }
        }), 500

@bp.route('/deduct/tts', methods=['POST'])
@login_required
def deduct_tts_usage():
    """
    API endpoint to deduct TTS usage from a user's account.

    Expected JSON payload:
    {
        "userId": "user_id",
        "minutesUsed": 2.3
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-request',
                    'message': 'No JSON data provided'
                }
            }), 400

        user_id = data.get('userId')
        minutes_used = data.get('minutesUsed', 0)

        # Validate input
        if not user_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-argument',
                    'message': 'userId is required'
                }
            }), 400

        if not isinstance(minutes_used, (int, float)) or minutes_used < 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-argument',
                    'message': 'minutesUsed must be a positive number'
                }
            }), 400

        # Check permissions
        if current_user.email != user_id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'permission-denied',
                    'message': 'You can only deduct usage for your own account'
                }
            }), 403

        # Deduct usage
        result = UsageTrackingService.deduct_tts_usage(user_id, minutes_used)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in deduct_tts_usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal-error',
                'message': 'An error occurred while deducting TTS usage',
                'details': str(e)
            }
        }), 500

@bp.route('/deduct/ai-credits', methods=['POST'])
@login_required
def deduct_ai_credits():
    """
    API endpoint to deduct AI credits from a user's account.

    Expected JSON payload:
    {
        "userId": "user_id",
        "creditsUsed": 10
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-request',
                    'message': 'No JSON data provided'
                }
            }), 400

        user_id = data.get('userId')
        credits_used = data.get('creditsUsed', 0)

        # Validate input
        if not user_id:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-argument',
                    'message': 'userId is required'
                }
            }), 400

        if not isinstance(credits_used, int) or credits_used < 0:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'invalid-argument',
                    'message': 'creditsUsed must be a positive integer'
                }
            }), 400

        # Check permissions
        if current_user.email != user_id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'permission-denied',
                    'message': 'You can only deduct usage for your own account'
                }
            }), 403

        # Deduct usage
        result = UsageTrackingService.deduct_ai_credits(user_id, credits_used)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in deduct_ai_credits: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal-error',
                'message': 'An error occurred while deducting AI credits',
                'details': str(e)
            }
        }), 500

@bp.route('/get/<user_id>', methods=['GET'])
@login_required
def get_user_usage(user_id):
    """
    API endpoint to get current usage data for a user.
    """
    try:
        # Check permissions
        if current_user.email != user_id and not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'permission-denied',
                    'message': 'You can only view usage for your own account'
                }
            }), 403

        # Get usage data
        usage_data = UsageTrackingService.get_user_usage(user_id)

        if usage_data is None:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'not-found',
                    'message': 'User not found or no usage data available'
                }
            }), 404

        return jsonify({
            'success': True,
            'usage': usage_data
        })

    except Exception as e:
        logger.error(f"Error in get_user_usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal-error',
                'message': 'An error occurred while retrieving usage data',
                'details': str(e)
            }
        }), 500

@bp.route('/reset/<user_id>', methods=['POST'])
@login_required
def reset_current_period_usage(user_id):
    """
    API endpoint to reset current period usage for a user (admin only).
    """
    try:
        # Only admins can reset usage
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'permission-denied',
                    'message': 'Only administrators can reset usage'
                }
            }), 403

        # Reset usage
        result = UsageTrackingService.reset_current_period_usage(user_id)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in reset_current_period_usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal-error',
                'message': 'An error occurred while resetting usage',
                'details': str(e)
            }
        }), 500

@bp.route('/test', methods=['GET'])
@login_required
def test_usage_tracking_page():
    """
    Test page for usage tracking functionality.
    """
    return render_template('test_usage_tracking.html')