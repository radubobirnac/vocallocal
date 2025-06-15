"""
User API Routes for VocalLocal

This module provides Flask routes for user-related API endpoints,
including user plan information, role information, and user data.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import logging
from services.user_account_service import UserAccountService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('user', __name__, url_prefix='/api/user')

@bp.route('/plan', methods=['GET'])
@login_required
def get_user_plan():
    """
    API endpoint to get current user's subscription plan information.
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'not-authenticated',
                    'message': 'User must be authenticated'
                }
            }), 401

        # Get user account data from Firebase
        # Encode email for Firebase path safety (replace dots with commas)
        user_id = current_user.email.replace('.', ',')
        user_account = UserAccountService.get_user_account(user_id)
        
        if not user_account:
            # Return default free plan if no account data exists
            return jsonify({
                'success': True,
                'plan': {
                    'plan_type': 'free',
                    'status': 'active',
                    'billing_cycle': 'monthly',
                    'limits': {
                        'transcription_minutes': 60,
                        'translation_words': 1000,
                        'tts_minutes': 5,
                        'ai_credits': 5
                    }
                }
            })

        # Extract subscription information
        subscription = user_account.get('subscription', {})
        plan_type = subscription.get('planType', 'free')
        status = subscription.get('status', 'active')
        billing_cycle = subscription.get('billingCycle', 'monthly')
        
        # Define plan limits based on plan type
        plan_limits = {
            'free': {
                'transcription_minutes': 60,  # 60 minutes total for transcription/translation combined
                'translation_words': 0,       # No translation words for free users
                'tts_minutes': 0,             # No TTS access for free users
                'ai_credits': 0               # No AI credits for free users
            },
            'basic': {
                'transcription_minutes': 280,
                'translation_words': 50000,
                'tts_minutes': 60,
                'ai_credits': 50
            },
            'professional': {
                'transcription_minutes': 800,
                'translation_words': 160000,
                'tts_minutes': 200,
                'ai_credits': 150
            }
        }
        
        limits = plan_limits.get(plan_type, plan_limits['free'])
        
        return jsonify({
            'success': True,
            'plan': {
                'plan_type': plan_type,
                'status': status,
                'billing_cycle': billing_cycle,
                'limits': limits,
                'start_date': subscription.get('startDate'),
                'end_date': subscription.get('endDate'),
                'renewal_date': subscription.get('renewalDate')
            }
        })

    except Exception as e:
        logger.error(f"Error in get_user_plan: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal-error',
                'message': 'An error occurred while fetching user plan',
                'details': str(e)
            }
        }), 500

@bp.route('/role-info', methods=['GET'])
@login_required
def get_user_role_info():
    """
    API endpoint to get current user's role and access information.
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'not-authenticated',
                    'message': 'User must be authenticated'
                }
            }), 401

        # Get user role from current_user object
        user_role = getattr(current_user, 'role', 'normal_user')
        is_admin = getattr(current_user, 'is_admin', False)
        
        # Determine if user has premium access
        has_premium_access = False
        has_admin_privileges = False
        
        if user_role == 'admin' or is_admin:
            has_premium_access = True
            has_admin_privileges = True
            user_role = 'admin'
        elif user_role == 'super_user':
            has_premium_access = True
            has_admin_privileges = False
        else:
            # Check subscription plan for premium access
            try:
                # Encode email for Firebase path safety (replace dots with commas)
                user_id = current_user.email.replace('.', ',')
                user_account = UserAccountService.get_user_account(user_id)
                if user_account:
                    subscription = user_account.get('subscription', {})
                    plan_type = subscription.get('planType', 'free')
                    status = subscription.get('status', 'inactive')
                    
                    if status == 'active' and plan_type in ['basic', 'professional']:
                        has_premium_access = True
            except Exception as e:
                logger.warning(f"Could not check subscription for premium access: {str(e)}")

        return jsonify({
            'success': True,
            'role': user_role,
            'plan_type': 'free',  # Default, will be updated by subscription check
            'has_premium_access': has_premium_access,
            'has_admin_privileges': has_admin_privileges,
            'is_authenticated': True,
            'user_email': current_user.email
        })

    except Exception as e:
        logger.error(f"Error in get_user_role_info: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal-error',
                'message': 'An error occurred while fetching user role info',
                'details': str(e)
            }
        }), 500

@bp.route('/info', methods=['GET'])
@login_required
def get_user_info():
    """
    API endpoint to get basic user information.
    """
    try:
        if not current_user.is_authenticated:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'not-authenticated',
                    'message': 'User must be authenticated'
                }
            }), 401

        return jsonify({
            'success': True,
            'user': {
                'email': current_user.email,
                'username': getattr(current_user, 'username', current_user.email.split('@')[0]),
                'role': getattr(current_user, 'role', 'normal_user'),
                'is_admin': getattr(current_user, 'is_admin', False),
                'is_authenticated': True
            }
        })

    except Exception as e:
        logger.error(f"Error in get_user_info: {str(e)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'internal-error',
                'message': 'An error occurred while fetching user info',
                'details': str(e)
            }
        }), 500


@bp.route('/api/user/tts-access', methods=['GET'])
@login_required
def check_tts_access():
    """
    Check if the current user has access to TTS features.

    Returns:
        JSON response with TTS access information
    """
    try:
        from services.usage_validation_service import UsageValidationService

        user_email = current_user.email
        tts_access = UsageValidationService.check_tts_access(user_email)

        return jsonify(tts_access)

    except Exception as e:
        logger.error(f"Error checking TTS access: {str(e)}")
        return jsonify({
            'allowed': False,
            'plan_type': 'unknown',
            'reason': 'Unable to verify TTS access',
            'upgrade_required': True,
            'message': 'Unable to verify TTS access. Please try again.'
        }), 500
