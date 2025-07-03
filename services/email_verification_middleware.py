"""
Email verification middleware for VocalLocal application.
Provides decorators and utilities to enforce email verification requirements.
"""
from functools import wraps
from flask import jsonify, request, session, redirect, url_for, flash
from flask_login import current_user
import logging
from firebase_models import User

# Set up logging
logger = logging.getLogger(__name__)

class EmailVerificationMiddleware:
    """Middleware for enforcing email verification requirements."""
    
    @staticmethod
    def requires_verified_email(f):
        """
        Decorator that requires email verification for API endpoints.
        Returns JSON error response for unverified users.
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip verification for OAuth users
            if hasattr(current_user, '_data') and current_user._data.get('oauth_provider'):
                return f(*args, **kwargs)
            
            # Check if user's email is verified
            if not current_user.is_authenticated:
                return jsonify({
                    'success': False,
                    'error': 'authentication_required',
                    'message': 'Authentication required'
                }), 401
            
            if not User.is_email_verified(current_user.email):
                return jsonify({
                    'success': False,
                    'error': 'email_verification_required',
                    'message': 'Email verification required to access this feature',
                    'verification_required': True,
                    'email': current_user.email
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def requires_verified_email_page(f):
        """
        Decorator that requires email verification for page routes.
        Redirects unverified users to verification page.
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip verification for OAuth users
            if hasattr(current_user, '_data') and current_user._data.get('oauth_provider'):
                return f(*args, **kwargs)
            
            # Check if user's email is verified
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if not User.is_email_verified(current_user.email):
                # Store the intended destination
                session['verification_redirect'] = request.url
                flash('Please verify your email address to access this feature.', 'warning')
                return redirect(url_for('auth.verify_email'))
            
            return f(*args, **kwargs)
        return decorated_function
    
    @staticmethod
    def check_verification_status(email: str) -> dict:
        """
        Check email verification status for a user.
        
        Args:
            email (str): User's email address
            
        Returns:
            dict: Verification status information
        """
        try:
            # OAuth users are automatically verified
            user_data = User.get_by_email(email)
            if user_data and user_data.get('oauth_provider'):
                return {
                    'verified': True,
                    'oauth_user': True,
                    'requires_verification': False
                }
            
            # Check manual registration users
            is_verified = User.is_email_verified(email)
            requires_verification = User.requires_email_verification(email)
            
            return {
                'verified': is_verified,
                'oauth_user': False,
                'requires_verification': requires_verification
            }
            
        except Exception as e:
            logger.error(f'Error checking verification status for {email}: {str(e)}')
            return {
                'verified': False,
                'oauth_user': False,
                'requires_verification': True,
                'error': str(e)
            }
    
    @staticmethod
    def get_verification_error_response(feature_name: str = "this feature") -> dict:
        """
        Get standardized error response for unverified users.
        
        Args:
            feature_name (str): Name of the feature being accessed
            
        Returns:
            dict: Error response data
        """
        return {
            'success': False,
            'error': 'email_verification_required',
            'message': f'Email verification is required to access {feature_name}',
            'verification_required': True,
            'email': current_user.email if current_user.is_authenticated else None,
            'action_required': 'verify_email'
        }
    
    @staticmethod
    def enhance_access_control_response(access_response: dict, email: str) -> dict:
        """
        Enhance existing access control responses with email verification checks.
        
        Args:
            access_response (dict): Existing access control response
            email (str): User's email address
            
        Returns:
            dict: Enhanced response with verification status
        """
        # If access is already denied, don't override
        if not access_response.get('allowed', False):
            return access_response
        
        # Check email verification
        verification_status = EmailVerificationMiddleware.check_verification_status(email)
        
        if verification_status['requires_verification']:
            return {
                'allowed': False,
                'reason': 'Email verification required',
                'verification_required': True,
                'email': email,
                'original_access': access_response
            }
        
        # Add verification status to successful response
        access_response['email_verified'] = verification_status['verified']
        access_response['oauth_user'] = verification_status['oauth_user']
        
        return access_response

class VerificationAwareAccessControl:
    """Enhanced access control that includes email verification checks."""
    
    @staticmethod
    def check_feature_access(feature_name: str, user_email: str = None) -> dict:
        """
        Check if user can access a feature, including email verification.
        
        Args:
            feature_name (str): Name of the feature
            user_email (str): User's email (defaults to current_user.email)
            
        Returns:
            dict: Access control response
        """
        if not user_email and current_user.is_authenticated:
            user_email = current_user.email
        
        if not user_email:
            return {
                'allowed': False,
                'reason': 'Authentication required',
                'authentication_required': True
            }
        
        # Check email verification first
        verification_status = EmailVerificationMiddleware.check_verification_status(user_email)
        
        if verification_status['requires_verification']:
            return {
                'allowed': False,
                'reason': f'Email verification required to access {feature_name}',
                'verification_required': True,
                'email': user_email,
                'feature': feature_name
            }
        
        # If verified, return success (can be enhanced with other checks)
        return {
            'allowed': True,
            'reason': f'Access granted to {feature_name}',
            'email_verified': verification_status['verified'],
            'oauth_user': verification_status['oauth_user'],
            'feature': feature_name
        }
    
    @staticmethod
    def check_transcription_access(user_email: str = None) -> dict:
        """Check transcription feature access with verification."""
        return VerificationAwareAccessControl.check_feature_access('transcription', user_email)
    
    @staticmethod
    def check_translation_access(user_email: str = None) -> dict:
        """Check translation feature access with verification."""
        return VerificationAwareAccessControl.check_feature_access('translation', user_email)
    
    @staticmethod
    def check_tts_access(user_email: str = None) -> dict:
        """Check TTS feature access with verification."""
        base_access = VerificationAwareAccessControl.check_feature_access('text-to-speech', user_email)
        
        # If verification fails, return that error
        if not base_access['allowed'] and base_access.get('verification_required'):
            return base_access
        
        # If verified, check TTS-specific restrictions (plan-based)
        if base_access['allowed']:
            # Import here to avoid circular imports
            from services.plan_access_control import PlanAccessControl
            
            try:
                user_plan = PlanAccessControl.get_user_plan()
                
                # Free users don't have TTS access
                if user_plan == 'free':
                    return {
                        'allowed': False,
                        'reason': 'Text-to-Speech is not available on the Free Plan',
                        'upgrade_required': True,
                        'required_plan': 'basic',
                        'email_verified': base_access.get('email_verified', True)
                    }
                
                # Paid users have access
                return {
                    'allowed': True,
                    'reason': 'TTS access granted',
                    'plan': user_plan,
                    'email_verified': base_access.get('email_verified', True)
                }
                
            except Exception as e:
                logger.error(f'Error checking TTS plan access: {str(e)}')
                return {
                    'allowed': False,
                    'reason': 'Unable to verify TTS access',
                    'error': str(e)
                }
        
        return base_access
    
    @staticmethod
    def check_interpretation_access(user_email: str = None) -> dict:
        """Check interpretation feature access with verification."""
        return VerificationAwareAccessControl.check_feature_access('interpretation', user_email)

# Convenience decorators
requires_verified_email = EmailVerificationMiddleware.requires_verified_email
requires_verified_email_page = EmailVerificationMiddleware.requires_verified_email_page
