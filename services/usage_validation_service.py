"""
Usage Validation Service for VocalLocal

This service enforces subscription plan limits in real-time and provides
usage validation before allowing transcription, translation, TTS, and AI operations.
"""

import time
from datetime import datetime
from services.firebase_service import FirebaseService
from services.user_account_service import UserAccountService


class UsageValidationService:
    """Service for validating and enforcing usage limits."""

    # Default plan limits (fallback if Firebase data is unavailable)
    DEFAULT_PLAN_LIMITS = {
        'free': {
            'transcriptionMinutes': 60,  # 60 minutes total for transcription/translation combined
            'translationWords': 0,       # No translation words for free users
            'ttsMinutes': 0,             # No TTS access for free users
            'aiCredits': 0               # No AI credits for free users
        },
        'basic': {
            'transcriptionMinutes': 280,
            'translationWords': 50000,
            'ttsMinutes': 60,
            'aiCredits': 50
        },
        'professional': {
            'transcriptionMinutes': 800,
            'translationWords': 160000,
            'ttsMinutes': 200,
            'aiCredits': 150
        }
    }

    @staticmethod
    def get_user_usage_data(user_email):
        """
        Get comprehensive usage data for a user.

        Args:
            user_email (str): User's email address

        Returns:
            dict: User usage data including subscription, limits, and current usage
        """
        try:
            # Get user ID (email with dots replaced by commas for Firebase)
            user_id = user_email.replace('.', ',')

            # Get user account data
            user_ref = UserAccountService.get_ref(f'users/{user_id}')
            user_data = user_ref.get()

            if not user_data:
                # Initialize user account if it doesn't exist
                UserAccountService.initialize_user_account(
                    user_id=user_id,
                    email=user_email,
                    display_name=user_email.split('@')[0]
                )
                user_data = user_ref.get()

            # Extract subscription and usage data
            subscription = user_data.get('subscription', {})
            usage = user_data.get('usage', {})
            current_period = usage.get('currentPeriod', {})

            # Get subscription plan details
            plan_type = subscription.get('planType', 'free')

            try:
                # Get plan details from Firebase
                firebase_service = FirebaseService()
                plan_ref = firebase_service.get_ref(f'subscriptionPlans/{plan_type}')
                plan_data = plan_ref.get()

                if not plan_data:
                    # Fallback to default limits
                    plan_data = UsageValidationService.DEFAULT_PLAN_LIMITS.get(
                        plan_type,
                        UsageValidationService.DEFAULT_PLAN_LIMITS['free']
                    )
            except Exception as e:
                print(f"Error getting plan data from Firebase: {str(e)}")
                # Fallback to default limits
                plan_data = UsageValidationService.DEFAULT_PLAN_LIMITS.get(
                    plan_type,
                    UsageValidationService.DEFAULT_PLAN_LIMITS['free']
                )

            return {
                'user_id': user_id,
                'plan_type': plan_type,
                'plan_data': plan_data,
                'subscription': subscription,
                'current_usage': current_period,
                'limits': {
                    'transcriptionMinutes': plan_data.get('transcriptionMinutes', 0),
                    'translationWords': plan_data.get('translationWords', 0),
                    'ttsMinutes': plan_data.get('ttsMinutes', 0),
                    'aiCredits': plan_data.get('aiCredits', 0)
                },
                'used': {
                    'transcriptionMinutes': current_period.get('transcriptionMinutes', 0),
                    'translationWords': current_period.get('translationWords', 0),
                    'ttsMinutes': current_period.get('ttsMinutes', 0),
                    'aiCredits': current_period.get('aiCredits', 0)
                }
            }

        except Exception as e:
            print(f"Error getting user usage data: {str(e)}")
            # Return minimal data structure for error cases
            return {
                'user_id': user_email.replace('.', ','),
                'plan_type': 'free',
                'plan_data': UsageValidationService.DEFAULT_PLAN_LIMITS['free'],
                'subscription': {},
                'current_usage': {},
                'limits': UsageValidationService.DEFAULT_PLAN_LIMITS['free'],
                'used': {
                    'transcriptionMinutes': 0,
                    'translationWords': 0,
                    'ttsMinutes': 0,
                    'aiCredits': 0
                }
            }

    @staticmethod
    def validate_transcription_usage(user_email, minutes_requested):
        """
        Validate if user can perform transcription for the requested minutes.

        Args:
            user_email (str): User's email address
            minutes_requested (float): Minutes of transcription requested

        Returns:
            dict: Validation result with allowed status and details
        """
        try:
            # Check if user has Super User or Admin privileges first
            user_role = UsageValidationService._get_user_role(user_email)
            if user_role in ['admin', 'super_user']:
                return {
                    'allowed': True,
                    'service': 'transcription',
                    'requested': minutes_requested,
                    'limit': float('inf'),  # Unlimited
                    'used': 0,
                    'remaining': float('inf'),
                    'plan_type': 'unlimited',
                    'upgrade_required': False,
                    'message': f'✓ Unlimited access for {user_role} role. Request approved.'
                }

            usage_data = UsageValidationService.get_user_usage_data(user_email)

            limit = usage_data['limits']['transcriptionMinutes']
            used = usage_data['used']['transcriptionMinutes']
            remaining = max(0, limit - used)

            allowed = remaining >= minutes_requested

            return {
                'allowed': allowed,
                'service': 'transcription',
                'requested': minutes_requested,
                'limit': limit,
                'used': used,
                'remaining': remaining,
                'plan_type': usage_data['plan_type'],
                'upgrade_required': not allowed and limit > 0,
                'message': UsageValidationService._get_validation_message(
                    'transcription', allowed, remaining, minutes_requested, usage_data['plan_type']
                )
            }

        except Exception as e:
            print(f"Error validating transcription usage: {str(e)}")
            return {
                'allowed': False,
                'service': 'transcription',
                'error': str(e),
                'message': 'Error validating usage. Please try again.'
            }

    @staticmethod
    def validate_translation_usage(user_email, words_requested):
        """
        Validate if user can perform translation for the requested words.

        Args:
            user_email (str): User's email address
            words_requested (int): Number of words to translate

        Returns:
            dict: Validation result with allowed status and details
        """
        try:
            # Check if user has Super User or Admin privileges first
            user_role = UsageValidationService._get_user_role(user_email)
            if user_role in ['admin', 'super_user']:
                return {
                    'allowed': True,
                    'service': 'translation',
                    'requested': words_requested,
                    'limit': float('inf'),  # Unlimited
                    'used': 0,
                    'remaining': float('inf'),
                    'plan_type': 'unlimited',
                    'upgrade_required': False,
                    'message': f'✓ Unlimited access for {user_role} role. Request approved.'
                }

            usage_data = UsageValidationService.get_user_usage_data(user_email)

            limit = usage_data['limits']['translationWords']
            used = usage_data['used']['translationWords']
            remaining = max(0, limit - used)

            allowed = remaining >= words_requested

            return {
                'allowed': allowed,
                'service': 'translation',
                'requested': words_requested,
                'limit': limit,
                'used': used,
                'remaining': remaining,
                'plan_type': usage_data['plan_type'],
                'upgrade_required': not allowed and limit > 0,
                'message': UsageValidationService._get_validation_message(
                    'translation', allowed, remaining, words_requested, usage_data['plan_type']
                )
            }

        except Exception as e:
            print(f"Error validating translation usage: {str(e)}")
            return {
                'allowed': False,
                'service': 'translation',
                'error': str(e),
                'message': 'Error validating usage. Please try again.'
            }

    @staticmethod
    def validate_tts_usage(user_email, minutes_requested):
        """
        Validate if user can perform TTS for the requested minutes.

        Args:
            user_email (str): User's email address
            minutes_requested (float): Minutes of TTS requested

        Returns:
            dict: Validation result with allowed status and details
        """
        try:
            # Check if user has Super User or Admin privileges first
            user_role = UsageValidationService._get_user_role(user_email)
            if user_role in ['admin', 'super_user']:
                return {
                    'allowed': True,
                    'service': 'tts',
                    'requested': minutes_requested,
                    'limit': float('inf'),  # Unlimited
                    'used': 0,
                    'remaining': float('inf'),
                    'plan_type': 'unlimited',
                    'upgrade_required': False,
                    'message': f'✓ Unlimited access for {user_role} role. Request approved.'
                }

            usage_data = UsageValidationService.get_user_usage_data(user_email)

            limit = usage_data['limits']['ttsMinutes']
            used = usage_data['used']['ttsMinutes']
            remaining = max(0, limit - used)

            allowed = remaining >= minutes_requested

            # For free users, TTS is completely blocked
            if usage_data['plan_type'] == 'free':
                return {
                    'allowed': False,
                    'service': 'tts',
                    'requested': minutes_requested,
                    'limit': 0,
                    'used': used,
                    'remaining': 0,
                    'plan_type': 'free',
                    'upgrade_required': True,
                    'message': 'Text-to-Speech is not available on the Free Plan. Please upgrade to access TTS features.'
                }

            return {
                'allowed': allowed,
                'service': 'tts',
                'requested': minutes_requested,
                'limit': limit,
                'used': used,
                'remaining': remaining,
                'plan_type': usage_data['plan_type'],
                'upgrade_required': not allowed and limit > 0,
                'message': UsageValidationService._get_validation_message(
                    'tts', allowed, remaining, minutes_requested, usage_data['plan_type']
                )
            }

        except Exception as e:
            print(f"Error validating TTS usage: {str(e)}")
            return {
                'allowed': False,
                'service': 'tts',
                'error': str(e),
                'message': 'Error validating usage. Please try again.'
            }

    @staticmethod
    def validate_ai_usage(user_email, credits_requested):
        """
        Validate if user can perform AI operations for the requested credits.

        Args:
            user_email (str): User's email address
            credits_requested (int): AI credits requested

        Returns:
            dict: Validation result with allowed status and details
        """
        try:
            # Check if user has Super User or Admin privileges first
            user_role = UsageValidationService._get_user_role(user_email)
            if user_role in ['admin', 'super_user']:
                return {
                    'allowed': True,
                    'service': 'ai',
                    'requested': credits_requested,
                    'limit': float('inf'),  # Unlimited
                    'used': 0,
                    'remaining': float('inf'),
                    'plan_type': 'unlimited',
                    'upgrade_required': False,
                    'message': f'✓ Unlimited access for {user_role} role. Request approved.'
                }

            usage_data = UsageValidationService.get_user_usage_data(user_email)

            limit = usage_data['limits']['aiCredits']
            used = usage_data['used']['aiCredits']
            remaining = max(0, limit - used)

            allowed = remaining >= credits_requested

            return {
                'allowed': allowed,
                'service': 'ai',
                'requested': credits_requested,
                'limit': limit,
                'used': used,
                'remaining': remaining,
                'plan_type': usage_data['plan_type'],
                'upgrade_required': not allowed and limit > 0,
                'message': UsageValidationService._get_validation_message(
                    'ai', allowed, remaining, credits_requested, usage_data['plan_type']
                )
            }

        except Exception as e:
            print(f"Error validating AI usage: {str(e)}")
            return {
                'allowed': False,
                'service': 'ai',
                'error': str(e),
                'message': 'Error validating usage. Please try again.'
            }

    @staticmethod
    def check_tts_access(user_email):
        """
        Check if a user has access to TTS features based on their subscription.

        Args:
            user_email (str): User's email address

        Returns:
            dict: Access information with allowed status and reason
        """
        try:
            # Check if user has Super User or Admin privileges first
            user_role = UsageValidationService._get_user_role(user_email)
            if user_role in ['admin', 'super_user']:
                return {
                    'allowed': True,
                    'plan_type': 'unlimited',
                    'reason': f'Unlimited TTS access for {user_role} role',
                    'upgrade_required': False,
                    'message': 'TTS features are available with unlimited access.'
                }

            usage_data = UsageValidationService.get_user_usage_data(user_email)
            plan_type = usage_data['plan_type']

            # Free users have no TTS access
            if plan_type == 'free':
                return {
                    'allowed': False,
                    'plan_type': plan_type,
                    'reason': 'TTS features are not available on the Free Plan',
                    'upgrade_required': True,
                    'message': 'Upgrade to Basic or Professional plan to access Text-to-Speech features.'
                }

            # All other plans have TTS access
            return {
                'allowed': True,
                'plan_type': plan_type,
                'reason': f'TTS access included in {plan_type.title()} plan',
                'upgrade_required': False,
                'message': 'TTS features are available.'
            }

        except Exception as e:
            print(f"Error checking TTS access: {str(e)}")
            return {
                'allowed': False,
                'plan_type': 'unknown',
                'reason': 'Unable to verify TTS access',
                'upgrade_required': True,
                'message': 'Unable to verify TTS access. Please try again.'
            }

    @staticmethod
    def _get_validation_message(service, allowed, remaining, requested, plan_type):
        """
        Generate appropriate validation message based on the result.

        Args:
            service (str): Service type (transcription, translation, tts, ai)
            allowed (bool): Whether the request is allowed
            remaining (float/int): Remaining usage
            requested (float/int): Requested usage
            plan_type (str): User's plan type

        Returns:
            str: Human-readable validation message
        """
        service_names = {
            'transcription': 'transcription minutes',
            'translation': 'translation words',
            'tts': 'TTS minutes',
            'ai': 'AI credits'
        }

        service_name = service_names.get(service, service)

        if allowed:
            return f"✓ Request approved. {remaining:.1f} {service_name} remaining after this operation."

        if remaining <= 0:
            if plan_type == 'free':
                return f"❌ You've reached your {service_name} limit. Upgrade to Basic or Professional for more usage."
            else:
                return f"❌ You've reached your monthly {service_name} limit. Usage will reset next month or upgrade for more."

        return f"❌ Insufficient {service_name}. You have {remaining:.1f} remaining but requested {requested:.1f}."

    @staticmethod
    def _get_user_role(user_email):
        """
        Get user role from Firebase User model.

        Args:
            user_email (str): User's email address

        Returns:
            str: User role ('admin', 'super_user', 'normal_user')
        """
        try:
            from models.firebase_models import User
            return User.get_user_role(user_email)
        except ImportError:
            try:
                from firebase_models import User
                return User.get_user_role(user_email)
            except ImportError:
                print("Warning: User model not available for role checking")
                return 'normal_user'
        except Exception as e:
            print(f"Error getting user role: {str(e)}")
            return 'normal_user'
