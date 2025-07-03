"""
Email verification routes for VocalLocal application.
Handles verification code sending, validation, and user verification status.
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
import logging
from services.email_verification_service import email_verification_service
from firebase_models import User

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
email_verification_bp = Blueprint('email_verification', __name__)

@email_verification_bp.route('/api/send-verification-code', methods=['POST'])
def send_verification_code():
    """
    Send verification code to user's email.
    Can be called during registration or for resending codes.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided',
                'error_type': 'invalid_request'
            }), 400
        
        email = data.get('email', '').strip().lower()
        username = data.get('username', '')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email address is required',
                'error_type': 'missing_email'
            }), 400
        
        # Basic email format validation - simplified for inclusivity
        if '@' not in email or len(email.split('@')) != 2:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address',
                'error_type': 'invalid_email'
            }), 400

        # Check that domain part exists and has at least one dot (for TLD)
        domain_part = email.split('@')[1]
        if not domain_part or '.' not in domain_part:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address',
                'error_type': 'invalid_email'
            }), 400

        # Ensure there's content after the last dot (TLD requirement)
        if domain_part.endswith('.') or len(domain_part.split('.')[-1]) < 2:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address',
                'error_type': 'invalid_email'
            }), 400
        
        # Check if email is already verified
        if User.is_email_verified(email):
            return jsonify({
                'success': False,
                'message': 'Email address is already verified',
                'error_type': 'already_verified'
            }), 400
        
        # Send verification code
        result = email_verification_service.send_verification_code(email, username)
        
        if result['success']:
            # Store email in session for verification process
            session['verification_email'] = email
            session['verification_username'] = username
            
            return jsonify({
                'success': True,
                'message': 'Verification code sent successfully',
                'expires_in_minutes': result.get('expires_in_minutes', 10)
            }), 200
        else:
            status_code = 429 if result.get('error_type') == 'rate_limit' else 400
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f'Error sending verification code: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_type': 'server_error'
        }), 500

@email_verification_bp.route('/api/verify-email-code', methods=['POST'])
def verify_email_code():
    """
    Verify the submitted email verification code.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided',
                'error_type': 'invalid_request'
            }), 400
        
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email address is required',
                'error_type': 'missing_email'
            }), 400
        
        if not code:
            return jsonify({
                'success': False,
                'message': 'Verification code is required',
                'error_type': 'missing_code'
            }), 400
        
        # Verify the code
        result = email_verification_service.verify_code(email, code)

        if result['success']:
            # Check if this is a new registration (user doesn't exist yet)
            existing_user = User.get_by_email(email)

            if not existing_user and 'pending_registration' in session:
                # Create the user account now that email is verified
                registration_data = session['pending_registration']
                if registration_data['email'] == email:
                    try:
                        User.create(
                            username=registration_data['username'],
                            email=registration_data['email'],
                            password_hash=registration_data['password_hash']
                        )
                        logger.info(f'User account created for {email} after email verification')

                        # Clear registration session data
                        session.pop('pending_registration', None)

                    except Exception as e:
                        logger.error(f'Failed to create user account for {email}: {str(e)}')
                        return jsonify({
                            'success': False,
                            'message': 'Email verified but failed to create account. Please contact support.',
                            'error_type': 'account_creation_failed'
                        }), 500

            # Mark user's email as verified in Firebase (for existing users)
            if existing_user:
                User.mark_email_verified(email)

            # Clear verification session data
            session.pop('verification_email', None)
            session.pop('verification_username', None)

            logger.info(f'Email verification completed for {email}')

            return jsonify({
                'success': True,
                'message': 'Email verified successfully!',
                'verified': True
            }), 200
        else:
            status_code = 400
            if result.get('error_type') in ['expired', 'too_many_attempts']:
                status_code = 410  # Gone - code expired
            elif result.get('error_type') == 'no_code':
                status_code = 404  # Not found
            
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f'Error verifying email code: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_type': 'server_error'
        }), 500

@email_verification_bp.route('/api/resend-verification-code', methods=['POST'])
def resend_verification_code():
    """
    Resend verification code to user's email.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided',
                'error_type': 'invalid_request'
            }), 400
        
        email = data.get('email', '').strip().lower()
        username = data.get('username', '')
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email address is required',
                'error_type': 'missing_email'
            }), 400
        
        # Check if email is already verified
        if User.is_email_verified(email):
            return jsonify({
                'success': False,
                'message': 'Email address is already verified',
                'error_type': 'already_verified'
            }), 400
        
        # Resend verification code
        result = email_verification_service.send_verification_code(email, username)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'New verification code sent successfully',
                'expires_in_minutes': result.get('expires_in_minutes', 10)
            }), 200
        else:
            status_code = 429 if result.get('error_type') == 'rate_limit' else 400
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f'Error resending verification code: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_type': 'server_error'
        }), 500

@email_verification_bp.route('/api/check-verification-status', methods=['POST'])
def check_verification_status():
    """
    Check if an email address is verified.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided',
                'error_type': 'invalid_request'
            }), 400
        
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email address is required',
                'error_type': 'missing_email'
            }), 400
        
        # Check verification status
        is_verified = User.is_email_verified(email)
        requires_verification = User.requires_email_verification(email)
        
        return jsonify({
            'success': True,
            'email': email,
            'is_verified': is_verified,
            'requires_verification': requires_verification
        }), 200
        
    except Exception as e:
        logger.error(f'Error checking verification status: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_type': 'server_error'
        }), 500

@email_verification_bp.route('/api/user-verification-status', methods=['GET'])
@login_required
def get_user_verification_status():
    """
    Get current user's email verification status.
    Requires authentication.
    """
    try:
        if not current_user or not current_user.email:
            return jsonify({
                'success': False,
                'message': 'User not authenticated',
                'error_type': 'not_authenticated'
            }), 401
        
        # Check verification status
        is_verified = User.is_email_verified(current_user.email)
        requires_verification = User.requires_email_verification(current_user.email)
        
        return jsonify({
            'success': True,
            'email': current_user.email,
            'is_verified': is_verified,
            'requires_verification': requires_verification,
            'oauth_user': hasattr(current_user, '_data') and current_user._data.get('oauth_provider') is not None
        }), 200
        
    except Exception as e:
        logger.error(f'Error getting user verification status: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_type': 'server_error'
        }), 500

@email_verification_bp.route('/api/request-verification', methods=['POST'])
@login_required
def request_verification():
    """
    Request email verification for current authenticated user.
    """
    try:
        if not current_user or not current_user.email:
            return jsonify({
                'success': False,
                'message': 'User not authenticated',
                'error_type': 'not_authenticated'
            }), 401
        
        # Check if already verified
        if User.is_email_verified(current_user.email):
            return jsonify({
                'success': False,
                'message': 'Email address is already verified',
                'error_type': 'already_verified'
            }), 400
        
        # Send verification code
        result = email_verification_service.send_verification_code(
            current_user.email, 
            current_user.username
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Verification code sent to your email',
                'expires_in_minutes': result.get('expires_in_minutes', 10)
            }), 200
        else:
            status_code = 429 if result.get('error_type') == 'rate_limit' else 400
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f'Error requesting verification for user: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_type': 'server_error'
        }), 500
