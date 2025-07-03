"""
Email-related routes for VocalLocal application.
Handles email validation and related functionality.
"""
from flask import Blueprint, request, jsonify
from services.email_service import email_service
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
email_bp = Blueprint('email', __name__, url_prefix='/api')

@email_bp.route('/validate-email', methods=['POST'])
def validate_email():
    """
    Validate email address with comprehensive checks.
    
    Returns:
        JSON response with validation results
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'valid': False,
                'errors': ['Email address is required']
            }), 400
        
        email = data['email']
        
        # Validate email using simplified format-only validation
        validation_result = email_service.validate_email(email)
        
        # Log validation attempt (without sensitive data)
        logger.info(f'Email validation attempt for domain: {email.split("@")[1] if "@" in email else "invalid"}')
        
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f'Email validation error: {str(e)}')
        return jsonify({
            'valid': False,
            'errors': ['Unable to validate email. Please try again.']
        }), 500

@email_bp.route('/send-welcome-email', methods=['POST'])
def send_welcome_email():
    """
    Send welcome email to a user (admin/testing endpoint).
    
    Returns:
        JSON response with send results
    """
    try:
        data = request.get_json()
        
        if not data or not all(key in data for key in ['username', 'email']):
            return jsonify({
                'success': False,
                'message': 'Username and email are required'
            }), 400
        
        username = data['username']
        email = data['email']
        user_tier = data.get('user_tier', 'free')
        
        # Send welcome email
        result = email_service.send_welcome_email(username, email, user_tier)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f'Welcome email sending error: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'Failed to send welcome email: {str(e)}'
        }), 500

@email_bp.route('/test-email-config', methods=['GET'])
def test_email_config():
    """
    Test email configuration (admin/debugging endpoint).
    
    Returns:
        JSON response with configuration status
    """
    try:
        # Check if email service is properly configured
        config_status = {
            'smtp_server': email_service.smtp_server,
            'smtp_port': email_service.smtp_port,
            'use_tls': email_service.use_tls,
            'use_ssl': email_service.use_ssl,
            'username': email_service.username,
            'password_configured': bool(email_service.password),
            'default_sender': email_service.default_sender
        }
        
        return jsonify({
            'configured': bool(email_service.password),
            'config': config_status
        })
        
    except Exception as e:
        logger.error(f'Email config test error: {str(e)}')
        return jsonify({
            'configured': False,
            'error': str(e)
        }), 500
